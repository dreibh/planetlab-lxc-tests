#
# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
# #################### history
#
# This is a complete rewrite of TestResources/Tracker/Pool
# we don't use trackers anymore and just probe/sense the running 
# boxes to figure out where we are
# in order to implement some fairness in the round-robin allocation scheme
# we need an indication of the 'age' of each running entity, 
# hence the 'timestamp-*' steps in TestPlc
# 
# this should be much more flexible:
# * supports several plc boxes 
# * supports several qemu guests per host
# * no need to worry about tracker being in sync or not
#
# #################### howto use
#
# each site is to write its own LocalSubstrate.py, 
# (see e.g. LocalSubstrate.inria.py)
# LocalSubstrate.py is expected to be in /root on the testmaster box
# and needs to define
# MYPLCs
# . the vserver-capable boxes used for hosting myplcs
# .  and their admissible load (max # of myplcs)
# . the pool of DNS-names and IP-addresses available for myplcs
# QEMU nodes
# . the kvm-qemu capable boxes to host qemu instances
# .  and their admissible load (max # of myplcs)
# . the pool of DNS-names and IP-addresses available for nodes
# 
# ####################

import os.path, sys
import time
import re
import traceback
import subprocess
import commands
import socket
from optparse import OptionParser

import utils
from TestSsh import TestSsh
from TestMapper import TestMapper

def header (message,banner=True):
    if not message: return
    if banner: print "===============",
    print message
    sys.stdout.flush()

def timestamp_sort(o1,o2): 
    if not o1.timestamp:        return -1
    elif not o2.timestamp:      return 1
    else:                       return o2.timestamp-o1.timestamp

####################
# pool class
# allows to pick an available IP among a pool
# input is expressed as a list of tuples (hostname,ip,user_data)
# that can be searched iteratively for a free slot
# e.g.
# pool = [ (hostname1,user_data1),  
#          (hostname2,user_data2),  
#          (hostname3,user_data2),  
#          (hostname4,user_data4) ]
# assuming that ip1 and ip3 are taken (pingable), then we'd get
# pool=Pool(pool)
# pool.next_free() -> entry2
# pool.next_free() -> entry4
# pool.next_free() -> None
# that is, even if ip2 is not busy/pingable when the second next_free() is issued

class PoolItem:
    def __init__ (self,hostname,userdata):
        self.hostname=hostname
        self.userdata=userdata
        # slot holds 'busy' or 'free' or 'fake' or None
        self.status=None
        self.ip=None

    def line(self):
        return "Pooled %s (%s) -> %s"%(self.hostname,self.userdata, self.status)
    def get_ip(self):
        if self.ip: return self.ip
        ip=socket.gethostbyname(self.hostname)
        self.ip=ip
        return ip

class Pool:

    def __init__ (self, tuples,message):
        self.pool= [ PoolItem (h,u) for (h,u) in tuples ] 
        self.message=message
        self._sensed=False

    def sense (self):
        if self._sensed: return
        print 'Checking IP pool',self.message,
        for item in self.pool:
            if self.check_ping (item.hostname): item.status='busy'
            else:                               item.status='free'
        self._sensed=True
        print 'Done'

    def list (self):
        for i in self.pool: print i.line()

    def retrieve_userdata (self, hostname):
        for i in self.pool: 
            if i.hostname==hostname: return i.userdata
        return None

    def get_ip (self, hostname):
        # use cached if in pool
        for i in self.pool: 
            if i.hostname==hostname: return i.get_ip()
        # otherwise just ask dns again
        return socket.gethostbyname(hostname)

    def next_free (self):
        for i in self.pool:
            if i.status in ['busy','fake']: continue
            i.status='fake'
            return (i.hostname,i.userdata)
        raise Exception,"No IP address available in pool %s"%self.message

# OS-dependent ping option (support for macos, for convenience)
    ping_timeout_option = None
# checks whether a given hostname/ip responds to ping
    def check_ping (self,hostname):
        if not Pool.ping_timeout_option:
            (status,osname) = commands.getstatusoutput("uname -s")
            if status != 0:
                raise Exception, "TestPool: Cannot figure your OS name"
            if osname == "Linux":
                Pool.ping_timeout_option="-w"
            elif osname == "Darwin":
                Pool.ping_timeout_option="-t"

        command="ping -c 1 %s 1 %s"%(Pool.ping_timeout_option,hostname)
        (status,output) = commands.getstatusoutput(command)
        if status==0:   print '+',
        else:           print '-',
        return status == 0

####################
class Box:
    def __init__ (self,hostname):
        self.hostname=hostname
    def simple_hostname (self):
        return self.hostname.split('.')[0]
    def test_ssh (self): return TestSsh(self.hostname,username='root',unknown_host=False)
    def reboot (self):
        self.test_ssh().run("shutdown -r now",message="Rebooting %s"%self.hostname)

    def run(self,argv,message=None,trash_err=False,dry_run=False):
        if dry_run:
            print 'DRY_RUN:',
            print " ".join(argv)
            return 0
        else:
            header(message)
            if not trash_err:
                return subprocess.call(argv)
            else:
                return subprocess.call(argv,stderr=file('/dev/null','w'))
                
    def run_ssh (self, argv, message, trash_err=False):
        ssh_argv = self.test_ssh().actual_argv(argv)
        result=self.run (ssh_argv, message, trash_err)
        if result!=0:
            print "WARNING: failed to run %s on %s"%(" ".join(argv),self.hostname)
        return result

    def backquote (self, argv, trash_err=False):
        if not trash_err:
            return subprocess.Popen(argv,stdout=subprocess.PIPE).communicate()[0]
        else:
            return subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=file('/dev/null','w')).communicate()[0]

    def backquote_ssh (self, argv, trash_err=False):
        # first probe the ssh link
        probe_argv=self.test_ssh().actual_argv(['hostname'])
        hostname=self.backquote ( probe_argv, trash_err=True )
        if not hostname:
            print "root@%s unreachable"%self.hostname
            return ''
        else:
            return self.backquote( self.test_ssh().actual_argv(argv), trash_err)

############################################################
class BuildInstance:
    def __init__ (self, buildname, pid, buildbox):
        self.buildname=buildname
        self.buildbox=buildbox
        self.pids=[pid]

    def add_pid(self,pid):
        self.pids.append(pid)

    def line (self):
        return "== %s == (pids=%r)"%(self.buildname,self.pids)

class BuildBox (Box):
    def __init__ (self,hostname):
        Box.__init__(self,hostname)
        self.build_instances=[]

    def add_build (self,buildname,pid):
        for build in self.build_instances:
            if build.buildname==buildname: 
                build.add_pid(pid)
                return
        self.build_instances.append(BuildInstance(buildname, pid, self))

    def list(self):
        if not self.build_instances: 
            header ('No build process on %s (%s)'%(self.hostname,self.uptime()))
        else:
            header ("Builds on %s (%s)"%(self.hostname,self.uptime()))
            for b in self.build_instances: 
                header (b.line(),banner=False)

    def uptime(self):
        if hasattr(self,'_uptime') and self._uptime: return self._uptime
        return '*undef* uptime'

    # inspect box and find currently running builds
    matcher=re.compile("\s*(?P<pid>[0-9]+).*-[bo]\s+(?P<buildname>[^\s]+)(\s|\Z)")
    def sense(self,reboot=False,verbose=True):
        if reboot:
            self.reboot(box)
            return
        print 'b',
        command=['uptime']
        self._uptime=self.backquote_ssh(command,trash_err=True).strip()
        if not self._uptime: self._uptime='unreachable'
        pids=self.backquote_ssh(['pgrep','build'],trash_err=True)
        if not pids: return
        command=['ps','-o','pid,command'] + [ pid for pid in pids.split("\n") if pid]
        ps_lines=self.backquote_ssh (command).split('\n')
        for line in ps_lines:
            if not line.strip() or line.find('PID')>=0: continue
            m=BuildBox.matcher.match(line)
            if m: self.add_build (m.group('buildname'),m.group('pid'))
            else: header('command %r returned line that failed to match'%command)

############################################################
class PlcInstance:
    def __init__ (self, vservername, ctxid, plcbox):
        self.vservername=vservername
        self.ctxid=ctxid
        self.plc_box=plcbox
        # unknown yet
        self.timestamp=None

    def set_timestamp (self,timestamp): self.timestamp=timestamp
    def set_now (self): self.timestamp=int(time.time())
    def pretty_timestamp (self): return time.strftime("%Y-%m-%d:%H-%M",time.localtime(self.timestamp))

    def line (self):
        msg="== %s == (ctx=%s)"%(self.vservername,self.ctxid)
        if self.timestamp: msg += " @ %s"%self.pretty_timestamp()
        else:              msg += " *unknown timestamp*"
        if self.ctxid==0: msg+=" not (yet?) running"
        return msg

    def kill (self):
        msg="vserver stopping %s on %s"%(self.vservername,self.plc_box.hostname)
        self.plc_box.run_ssh(['vserver',self.vservername,'stop'],msg)
        self.plc_box.forget(self)

class PlcBox (Box):
    def __init__ (self, hostname, max_plcs):
        Box.__init__(self,hostname)
        self.plc_instances=[]
        self.max_plcs=max_plcs

    def add_vserver (self,vservername,ctxid):
        for plc in self.plc_instances:
            if plc.vservername==vservername: 
                header("WARNING, duplicate myplc %s running on %s"%\
                           (vservername,self.hostname),banner=False)
                return
        self.plc_instances.append(PlcInstance(vservername,ctxid,self))
    
    def forget (self, plc_instance):
        self.plc_instances.remove(plc_instance)

    # fill one slot even though this one is not started yet
    def add_fake (self, plcname):
        fake=PlcInstance('fake_'+plcname,0,self)
        fake.set_now()
        self.plc_instances.append(fake)

    def line(self): 
        msg="%s [max=%d,%d free] (%s)"%(self.hostname, self.max_plcs,self.free_spots(),self.uname())
        return msg
        
    def list(self):
        if not self.plc_instances: 
            header ('No vserver running on %s'%(self.line()))
        else:
            header ("Active plc VMs on %s"%self.line())
            for p in self.plc_instances: 
                header (p.line(),banner=False)

    def free_spots (self):
        return self.max_plcs - len(self.plc_instances)

    def uname(self):
        if hasattr(self,'_uname') and self._uname: return self._uname
        return '*undef* uname'

    def plc_instance_by_vservername (self, vservername):
        for p in self.plc_instances:
            if p.vservername==vservername: return p
        return None

    def sense (self, reboot=False, soft=False):
        if reboot:
            # remove mark for all running servers to avoid resurrection
            stop_command=['rm','-rf','/etc/vservers/*/apps/init/mark']
            self.run_ssh(stop_command,"Removing all vserver marks on %s"%self.hostname)
            if not soft:
                self.reboot()
                return
            else:
                self.run_ssh(['service','util-vserver','stop'],"Stopping all running vservers")
            return
        print 'p',
        self._uname=self.backquote_ssh(['uname','-r']).strip()
        # try to find fullname (vserver_stat truncates to a ridiculously short name)
        # fetch the contexts for all vservers on that box
        map_command=['grep','.','/etc/vservers/*/context','/dev/null',]
        context_map=self.backquote_ssh (map_command)
        # at this point we have a set of lines like
        # /etc/vservers/2010.01.20--k27-f12-32-vplc03/context:40144
        ctx_dict={}
        for map_line in context_map.split("\n"):
            if not map_line: continue
            [path,xid] = map_line.split(':')
            ctx_dict[xid]=os.path.basename(os.path.dirname(path))
        # at this point ctx_id maps context id to vservername

        command=['vserver-stat']
        vserver_stat = self.backquote_ssh (command)
        for vserver_line in vserver_stat.split("\n"):
            if not vserver_line: continue
            context=vserver_line.split()[0]
            if context=="CTX": continue
            longname=ctx_dict[context]
            self.add_vserver(longname,context)
#            print self.margin_outline(self.vplcname(longname)),"%(vserver_line)s [=%(longname)s]"%locals()

        # scan timestamps
        command=   ['grep','.']
        command += ['/vservers/%s/timestamp'%b for b in ctx_dict.values()]
        command += ['/dev/null']
        ts_lines=self.backquote_ssh(command,trash_err=True).split('\n')
        for ts_line in ts_lines:
            if not ts_line.strip(): continue
            # expect /vservers/<vservername>/timestamp:<timestamp>
            try:
                (_,__,vservername,tail)=ts_line.split('/')
                (_,timestamp)=tail.split(':')
                timestamp=int(timestamp)
                q=self.plc_instance_by_vservername(vservername)
                if not q: 
                    print 'WARNING unattached plc instance',ts_line
                    continue
                q.set_timestamp(timestamp)
            except:  print 'WARNING, could not parse ts line',ts_line
        



############################################################
class QemuInstance: 
    def __init__ (self, nodename, pid, qemubox):
        self.nodename=nodename
        self.pid=pid
        self.qemu_box=qemubox
        # not known yet
        self.buildname=None
        self.timestamp=None
        
    def set_buildname (self,buildname): self.buildname=buildname
    def set_timestamp (self,timestamp): self.timestamp=timestamp
    def set_now (self): self.timestamp=int(time.time())
    def pretty_timestamp (self): return time.strftime("%Y-%m-%d:%H-%M",time.localtime(self.timestamp))
    
    def line (self):
        msg = "== %s == (pid=%s)"%(self.nodename,self.pid)
        if self.buildname: msg += " <--> %s"%self.buildname
        else:              msg += " *unknown build*"
        if self.timestamp: msg += " @ %s"%self.pretty_timestamp()
        else:              msg += " *unknown timestamp*"
        if self.pid:       msg += "pid=%s"%self.pid
        else:              msg += " not (yet?) running"
        return msg
    
    def kill(self):
        if self.pid==0: print "cannot kill qemu %s with pid==0"%self.nodename
        msg="Killing qemu %s with pid=%s on box %s"%(self.nodename,self.pid,self.qemu_box.hostname)
        self.qemu_box.run_ssh(['kill',"%s"%self.pid],msg)
        self.qemu_box.forget(self)


class QemuBox (Box):
    def __init__ (self, hostname, max_qemus):
        Box.__init__(self,hostname)
        self.qemu_instances=[]
        self.max_qemus=max_qemus

    def add_node (self,nodename,pid):
        for qemu in self.qemu_instances:
            if qemu.nodename==nodename: 
                header("WARNING, duplicate qemu %s running on %s"%\
                           (nodename,self.hostname), banner=False)
                return
        self.qemu_instances.append(QemuInstance(nodename,pid,self))

    def forget (self, qemu_instance):
        self.qemu_instances.remove(qemu_instance)

    # fill one slot even though this one is not started yet
    def add_fake (self, nodename):
        fake=QemuInstance('fake_'+nodename,0,self)
        fake.set_now()
        self.qemu_instances.append(fake)

    def line (self):
        msg="%s [max=%d,%d free] (%s)"%(self.hostname, self.max_qemus,self.free_spots(),self.driver())
        return msg

    def list(self):
        if not self.qemu_instances: 
            header ('No qemu process on %s'%(self.line()))
        else:
            header ("Active qemu processes on %s"%(self.line()))
            for q in self.qemu_instances: 
                header (q.line(),banner=False)

    def free_spots (self):
        return self.max_qemus - len(self.qemu_instances)

    def driver(self):
        if hasattr(self,'_driver') and self._driver: return self._driver
        return '*undef* driver'

    def qemu_instance_by_pid (self,pid):
        for q in self.qemu_instances:
            if q.pid==pid: return q
        return None

    def qemu_instance_by_nodename_buildname (self,nodename,buildname):
        for q in self.qemu_instances:
            if q.nodename==nodename and q.buildname==buildname:
                return q
        return None

    matcher=re.compile("\s*(?P<pid>[0-9]+).*-cdrom\s+(?P<nodename>[^\s]+)\.iso")
    def sense(self, reboot=False, soft=False):
        if reboot:
            if not soft:
                self.reboot()
            else:
                self.run_ssh(box,['pkill','qemu'],"Killing qemu instances")
            return
        print 'q',
        modules=self.backquote_ssh(['lsmod']).split('\n')
        self._driver='*NO kqemu/kmv_intel MODULE LOADED*'
        for module in modules:
            if module.find('kqemu')==0:
                self._driver='kqemu module loaded'
            # kvm might be loaded without vkm_intel (we dont have AMD)
            elif module.find('kvm_intel')==0:
                self._driver='kvm_intel module loaded'
        ########## find out running pids
        pids=self.backquote_ssh(['pgrep','qemu'])
        if not pids: return
        command=['ps','-o','pid,command'] + [ pid for pid in pids.split("\n") if pid]
        ps_lines = self.backquote_ssh (command).split("\n")
        for line in ps_lines:
            if not line.strip() or line.find('PID') >=0 : continue
            m=QemuBox.matcher.match(line)
            if m: self.add_node (m.group('nodename'),m.group('pid'))
            else: header('command %r returned line that failed to match'%command)
        ########## retrieve alive instances and map to build
        live_builds=[]
        command=['grep','.','*/*/qemu.pid','/dev/null']
        pid_lines=self.backquote_ssh(command,trash_err=True).split('\n')
        for pid_line in pid_lines:
            if not pid_line.strip(): continue
            # expect <build>/<nodename>/qemu.pid:<pid>pid
            try:
                (buildname,nodename,tail)=pid_line.split('/')
                (_,pid)=tail.split(':')
                q=self.qemu_instance_by_pid (pid)
                if not q: continue
                q.set_buildname(buildname)
                live_builds.append(buildname)
            except: print 'WARNING, could not parse pid line',pid_line
        # retrieve timestamps
        command=   ['grep','.']
        command += ['%s/*/timestamp'%b for b in live_builds]
        command += ['/dev/null']
        ts_lines=self.backquote_ssh(command,trash_err=True).split('\n')
        for ts_line in ts_lines:
            if not ts_line.strip(): continue
            # expect <build>/<nodename>/timestamp:<timestamp>
            try:
                (buildname,nodename,tail)=ts_line.split('/')
                nodename=nodename.replace('qemu-','')
                (_,timestamp)=tail.split(':')
                timestamp=int(timestamp)
                q=self.qemu_instance_by_nodename_buildname(nodename,buildname)
                if not q: 
                    print 'WARNING unattached qemu instance',ts_line,nodename,buildname
                    continue
                q.set_timestamp(timestamp)
            except:  print 'WARNING, could not parse ts line',ts_line

############################################################
class Options: pass

class Substrate:

    def test (self): 
        self.sense()

    def __init__ (self):
        self.options=Options()
        self.options.dry_run=False
        self.options.verbose=False
        self.options.probe=True
        self.options.soft=True
        self.build_boxes = [ BuildBox(h) for h in self.build_boxes_spec() ]
        self.plc_boxes = [ PlcBox (h,m) for (h,m) in self.plc_boxes_spec ()]
        self.qemu_boxes = [ QemuBox (h,m) for (h,m) in self.qemu_boxes_spec ()]
        self.all_boxes = self.build_boxes + self.plc_boxes + self.qemu_boxes
        self._sensed=False

        self.vplc_pool = Pool (self.vplc_ips(),"for vplcs")
        self.vnode_pool = Pool (self.vnode_ips(),"for vnodes")

        self.vnode_pool.list()


#    def build_box_names (self):
#        return [ h for h in self.build_boxes_spec() ]
#    def plc_boxes (self):
#        return [ h for (h,m) in self.plc_boxes_spec() ]
#    def qemu_boxes (self):
#        return [ h for (h,m) in self.qemu_boxes_spec() ]

    def sense (self,force=False):
        if self._sensed and not force: return
        print 'Sensing local substrate...',
        for b in self.all_boxes: b.sense()
        print 'Done'
        self._sensed=True

    ########## 
    def provision (self,plcs,options):
        try:
            self.sense()
            self.list_all()
            # attach each plc to a plc box and an IP address
            plcs = [ self.provision_plc (plc,options) for plc in plcs ]
            # attach each node/qemu to a qemu box with an IP address
            plcs = [ self.provision_qemus (plc,options) for plc in plcs ]
            # update the SFA spec accordingly
            plcs = [ self.localize_sfa_rspec(plc,options) for plc in plcs ]
            return plcs
        except Exception, e:
            print '* Could not provision this test on current substrate','--',e,'--','exiting'
            traceback.print_exc()
            sys.exit(1)

    # find an available plc box (or make space)
    # and a free IP address (using options if present)
    def provision_plc (self, plc, options):
        #### we need to find one plc box that still has a slot
        plc_box=None
        max_free=0
        # use the box that has max free spots for load balancing
        for pb in self.plc_boxes:
            free=pb.free_spots()
            if free>max_free:
                plc_box=pb
                max_free=free
        # everything is already used
        if not plc_box:
            # find the oldest of all our instances
            all_plc_instances=reduce(lambda x, y: x+y, 
                                     [ pb.plc_instances for pb in self.plc_boxes ],
                                     [])
            all_plc_instances.sort(timestamp_sort)
            plc_instance_to_kill=all_plc_instances[0]
            plc_box=plc_instance_to_kill.plc_box
            plc_instance_to_kill.kill()
            print 'killed oldest = %s on %s'%(plc_instance_to_kill.line(),
                                             plc_instance_to_kill.plc_box.hostname)

        utils.header( 'plc %s -> box %s'%(plc['name'],plc_box.line()))
        plc_box.add_fake(plc['name'])
        #### OK we have a box to run in, let's find an IP address
        # look in options
        if options.ips_vplc:
            vplc_hostname=options.ips_vplc.pop()
        else:
            self.vplc_pool.sense()
            (vplc_hostname,unused)=self.vplc_pool.next_free()
        vplc_ip = self.vplc_pool.get_ip(vplc_hostname)

        #### compute a helpful vserver name
        # remove domain in hostname
        vplc_simple = vplc_hostname.split('.')[0]
        vservername = "%s-%d-%s" % (options.buildname,plc['index'],vplc_simple)
        plc_name = "%s_%s"%(plc['name'],vplc_simple)

        #### apply in the plc_spec
        # # informative
        # label=options.personality.replace("linux","")
        mapper = {'plc': [ ('*' , {'hostname':plc_box.hostname,
                                   # 'name':'%s-'+label,
                                   'name': plc_name,
                                   'vservername':vservername,
                                   'vserverip':vplc_ip,
                                   'PLC_DB_HOST':vplc_hostname,
                                   'PLC_API_HOST':vplc_hostname,
                                   'PLC_BOOT_HOST':vplc_hostname,
                                   'PLC_WWW_HOST':vplc_hostname,
                                   'PLC_NET_DNS1' : self.network_settings() [ 'interface_fields:dns1' ],
                                   'PLC_NET_DNS2' : self.network_settings() [ 'interface_fields:dns2' ],
                                   } ) ]
                  }

        utils.header("Attaching %s on IP %s in vserver %s"%(plc['name'],vplc_hostname,vservername))
        # mappers only work on a list of plcs
        return TestMapper([plc],options).map(mapper)[0]

    ##########
    def provision_qemus (self, plc, options):
        test_mapper = TestMapper ([plc], options)
        nodenames = test_mapper.node_names()
        maps=[]
        for nodename in nodenames:
            #### similarly we want to find a qemu box that can host us
            qemu_box=None
            max_free=0
            # use the box that has max free spots for load balancing
            for qb in self.qemu_boxes:
                free=qb.free_spots()
            if free>max_free:
                qemu_box=qb
                max_free=free
            # everything is already used
            if not qemu_box:
                # find the oldest of all our instances
                all_qemu_instances=reduce(lambda x, y: x+y, 
                                         [ qb.qemu_instances for qb in self.qemu_boxes ],
                                         [])
                all_qemu_instances.sort(timestamp_sort)
                qemu_instance_to_kill=all_qemu_instances[0]
                qemu_box=qemu_instance_to_kill.qemu_box
                qemu_instance_to_kill.kill()
                print 'killed oldest = %s on %s'%(qemu_instance_to_kill.line(),
                                                 qemu_instance_to_kill.qemu_box.hostname)

            utils.header( 'node %s -> qemu box %s'%(nodename,qemu_box.line()))
            qemu_box.add_fake(nodename)
            #### OK we have a box to run in, let's find an IP address
            # look in options
            if options.ips_vnode:
                qemu_hostname=options.ips_vnode.pop()
                mac=self.vnode_pool.retrieve_userdata(qemu_hostname)
                print 'case 1 hostname',qemu_hostname,'mac',mac
            else:
                self.vnode_pool.sense()
                (qemu_hostname,mac)=self.vnode_pool.next_free()
                print 'case 2 hostname',qemu_hostname,'mac',mac
            ip=self.vnode_pool.get_ip (qemu_hostname)
            utils.header("Attaching %s on IP %s MAC %s"%(plc['name'],qemu_hostname,mac))

            if qemu_hostname.find('.')<0:
                qemu_hostname += "."+self.domain()
            nodemap={'host_box':qemu_box.hostname,
                     'node_fields:hostname':qemu_hostname,
                     'interface_fields:ip':ip, 
                     'interface_fields:mac':mac,
                     }
            nodemap.update(self.network_settings())
            maps.append ( (nodename, nodemap) )

        return test_mapper.map({'node':maps})[0]

    def localize_sfa_rspec (self,plc,options):
       
        plc['sfa']['SFA_REGISTRY_HOST'] = plc['PLC_DB_HOST']
        plc['sfa']['SFA_AGGREGATE_HOST'] = plc['PLC_DB_HOST']
        plc['sfa']['SFA_SM_HOST'] = plc['PLC_DB_HOST']
        plc['sfa']['SFA_PLC_DB_HOST'] = plc['PLC_DB_HOST']
        plc['sfa']['SFA_PLC_URL'] = 'https://' + plc['PLC_API_HOST'] + ':443/PLCAPI/' 
        for site in plc['sites']:
            for node in site['nodes']:
                plc['sfa']['sfa_slice_rspec']['part4'] = node['node_fields']['hostname']
	return plc

    #################### show results for interactive mode
    def list_all (self):
        self.sense()
        for b in self.all_boxes: b.list()

    def get_box (self,box):
        for b in self.build_boxes + self.plc_boxes + self.qemu_boxes:
            if b.simple_hostname()==box:
                return b
        print "Could not find box %s"%box
        return None

    def list_box(self,box):
        b=self.get_box(box)
        if not b: return
        b.sense()
        b.list()

    # can be run as a utility to manage the local infrastructure
    def main (self):
        parser=OptionParser()
        (options,args)=parser.parse_args()
        if not args:
            self.list_all()
        else:
            for box in args:
                self.list_box(box)
