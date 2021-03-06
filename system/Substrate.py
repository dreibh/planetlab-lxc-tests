#
# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010-2015 INRIA
#
# #################### history
#
# see also Substrate.readme
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
# #################### implem. note
#
# this model relies on 'sensing' the substrate,
# i.e. probing all the boxes for their running instances of vservers and qemu
# this is how we get rid of tracker inconsistencies
# however there is a 'black hole' between the time where a given address is
# allocated and when it actually gets used/pingable
# this is why we still need a shared knowledge among running tests
# in a file named /root/starting
# this is connected to the Pool class
#
# ####################

import os.path, sys
import time
import re
import traceback
import subprocess
import socket
from optparse import OptionParser

import utils
from TestSsh import TestSsh
from TestMapper import TestMapper
from functools import reduce

# too painful to propagate this cleanly
verbose = None

def header (message, banner=True):
    if not message: return
    if banner:
        print("===============", end=' ')
    print(message)
    sys.stdout.flush()

def timestamp_key(o): return o.timestamp

def short_hostname (hostname):
    return hostname.split('.')[0]

####################
# the place were other test instances tell about their not-yet-started
# instances, that go undetected through sensing
class Starting:

    location = '/root/starting'

    def __init__ (self):
        self.tuples=[]

    def __repr__(self):
        return '<Starting>'

    def load (self):
        try:
            with open(Starting.location) as starting:
                self.tuples = [line.strip().split('@') for line in starting.readlines()]
        except:
            self.tuples = []

    def vnames (self) :
        self.load()
        return [ x for (x, _) in self.tuples ]

    def add (self, vname, bname):
        if not vname in self.vnames():
            with open(Starting.location, 'a') as out:
                out.write("{}@{}\n".format(vname, bname))

    def delete_vname (self, vname):
        self.load()
        if vname in self.vnames():
            with open(Starting.location, 'w') as f:
                for (v, b) in self.tuples:
                    if v != vname:
                        f.write("{}@{}\n".format(v, b))

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
    def __init__ (self, hostname, userdata):
        self.hostname = hostname
        self.userdata = userdata
        # slot holds 'busy' or 'free' or 'mine' or 'starting' or None
        # 'mine' is for our own stuff, 'starting' from the concurrent tests
        self.status = None
        self.ip = None

    def __repr__(self):
        return "<PoolItem {} {}>".format(self.hostname, self.userdata)

    def line(self):
        return "Pooled {} ({}) -> {}".format(self.hostname, self.userdata, self.status)

    def char (self):
        if   self.status == None:       return '?'
        elif self.status == 'busy':     return '*'
        elif self.status == 'free':     return '.'
        elif self.status == 'mine':     return 'M'
        elif self.status == 'starting': return 'S'

    def get_ip(self):
        if self.ip:
            return self.ip
        self.ip = socket.gethostbyname(self.hostname)
        return self.ip

class Pool:

    def __init__ (self, tuples, message, substrate):
        self.pool_items = [ PoolItem (hostname, userdata) for (hostname, userdata) in tuples ]
        self.message = message
        # where to send notifications upon load_starting
        self.substrate = substrate

    def __repr__(self):
        return "<Pool {} : {} .. {}>".format(self.message, self.pool_items[0], self.pool_items[-1])

    def list (self, verbose=False):
        print(self)
        for i in self.pool_items: print(i.line())

    def line (self):
        line = self.message
        for i in self.pool_items: line += ' ' + i.char()
        return line

    def _item (self, hostname):
        for i in self.pool_items:
            if i.hostname == hostname: return i
        raise Exception ("Could not locate hostname {} in pool {}".format(hostname, self.message))

    def retrieve_userdata (self, hostname):
        return self._item(hostname).userdata

    def get_ip (self, hostname):
        try:
            return self._item(hostname).get_ip()
        except:
            return socket.gethostbyname(hostname)

    def set_mine (self, hostname):
        try:
            self._item(hostname).status='mine'
        except:
            print('WARNING: host {} not found in IP pool {}'.format(hostname, self.message))

    def next_free (self):
        for i in self.pool_items:
            if i.status == 'free':
                i.status = 'mine'
                return (i.hostname, i.userdata)
        return None

    ####################
    # we have a starting instance of our own
    def add_starting (self, vname, bname):
        Starting().add(vname, bname)
        for i in self.pool_items:
            if i.hostname == vname:
                i.status = 'mine'

    # load the starting instances from the common file
    # remember that might be ours
    # return the list of (vname,bname) that are not ours
    def load_starting (self):
        starting = Starting()
        starting.load()
        new_tuples = []
        for (v, b) in starting.tuples:
            for i in self.pool_items:
                if i.hostname == v and i.status == 'free':
                    i.status = 'starting'
                    new_tuples.append( (v, b,) )
        return new_tuples

    def release_my_starting (self):
        for i in self.pool_items:
            if i.status == 'mine':
                Starting().delete_vname(i.hostname)
                i.status = None


    ##########
    def _sense (self):
        for item in self.pool_items:
            if item.status is not None:
                print(item.char(), end=' ')
                continue
            if self.check_ping (item.hostname):
                item.status = 'busy'
                print('*', end=' ')
            else:
                item.status = 'free'
                print('.', end=' ')
            sys.stdout.flush()

    def sense (self):
        print('Sensing IP pool', self.message, end=' ')
        sys.stdout.flush()
        self._sense()
        print('Done')
        for vname, bname in self.load_starting():
            self.substrate.add_starting_dummy(bname, vname)
        print("After having loaded 'starting': IP pool")
        print(self.line())
    # OS-dependent ping option (support for macos, for convenience)
    ping_timeout_option = None
    # returns True when a given hostname/ip responds to ping
    def check_ping (self, hostname):
        if '.' not in hostname:
            hostname = self.substrate.fqdn(hostname)
        if not Pool.ping_timeout_option:
            (status, osname) = subprocess.getstatusoutput("uname -s")
            if status != 0:
                raise Exception("TestPool: Cannot figure your OS name")
            if osname == "Linux":
                Pool.ping_timeout_option = "-w"
            elif osname == "Darwin":
                Pool.ping_timeout_option = "-t"

        command = "ping -c 1 {} 1 {}".format(Pool.ping_timeout_option, hostname)
        (status, output) = subprocess.getstatusoutput(command)
#        print ("""
#----------
#Ping command <{command}> has returned {status}
#--
#{output}
#----------
#        """.format(**locals()))
        return status == 0

####################
class Box:
    def __init__ (self, hostname):
        self.hostname = hostname
        self._probed = None
    def __repr__(self):
        return "<Box {}>".format(self.hostname)
    def shortname (self):
        return short_hostname(self.hostname)
    def test_ssh (self):
        return TestSsh(self.hostname, username='root', unknown_host=False)
    def reboot (self, options):
        self.test_ssh().run("shutdown -r now",
                            message="Rebooting {}".format(self.hostname),
                            dry_run=options.dry_run)

    def hostname_fedora (self, virt=None):
        # this truly is an opening bracket
        result = "{}".format(self.hostname) + " {"
        if virt:
            result += "{}-".format(virt)
        result += "{} {}".format(self.fedora(), self.memory())
        # too painful to propagate this cleanly
        global verbose
        if verbose:
            result += "-{}".format(self.uname())
        # and the matching closing bracket
        result += "}"
        return result

    separator = "===composite==="

    # probe the ssh link
    # take this chance to gather useful stuff
    def probe (self):
        # try it only once
        if self._probed is not None: return self._probed
        composite_command = [ ]
        composite_command += [ "hostname" ]
        composite_command += [ ";" , "echo", Box.separator , ";" ]
        composite_command += [ "uptime" ]
        composite_command += [ ";" , "echo", Box.separator , ";" ]
        composite_command += [ "uname", "-r"]
        composite_command += [ ";" , "echo", Box.separator , ";" ]
        composite_command += [ "cat" , "/etc/fedora-release" ]
        composite_command += [ ";" , "echo", Box.separator , ";" ]
        composite_command += [ "grep", "MemTotal", "/proc/meminfo" ]

        # due to colons and all, this is going wrong on the local box (typically testmaster)
        # I am reluctant to change TestSsh as it might break all over the place, so
        if self.test_ssh().is_local():
            probe_argv = [ "bash", "-c", " ".join (composite_command) ]
        else:
            probe_argv = self.test_ssh().actual_argv(composite_command)
        composite = self.backquote ( probe_argv, trash_err=True )
        self._hostname = self._uptime = self._uname = self._fedora = self._memory = "** Unknown **"
        if not composite:
            print("root@{} unreachable".format(self.hostname))
            self._probed = ''
        else:
            try:
                pieces = composite.split(Box.separator)
                pieces = [ x.strip() for x in pieces ]
                # get raw data
                [hostname, uptime, uname, fedora, memory] = pieces
                # customize
                self._hostname = hostname
                self._uptime = ', '.join([ x.strip() for x in uptime.split(',')[2:]]).replace("load average", "load")
                self._uname = uname
                self._fedora = fedora.replace("Fedora release ","f").split(" ")[0]
                # translate into Mb
                self._memory = int(memory.split()[1])/(1024)
            except Exception as e:
                import traceback
                print('BEG issue with pieces')
                traceback.print_exc()
            self._probed = self._hostname
        return self._probed

    # use argv=['bash','-c',"the command line"]
    def uptime(self):
        self.probe()
        if hasattr(self,'_uptime') and self._uptime: return self._uptime
        return '*unprobed* uptime'
    def uname(self):
        self.probe()
        if hasattr(self,'_uname') and self._uname: return self._uname
        return '*unprobed* uname'
    def fedora(self):
        self.probe()
        if hasattr(self,'_fedora') and self._fedora: return self._fedora
        return '*unprobed* fedora'
    def memory(self):
        self.probe()
        if hasattr(self,'_memory') and self._memory: return "{} Mb".format(self._memory)
        return '*unprobed* memory'

    def run(self, argv, message=None, trash_err=False, dry_run=False):
        if dry_run:
            print('DRY_RUN:', end=' ')
            print(" ".join(argv))
            return 0
        else:
            header(message)
            if not trash_err:
                return subprocess.call(argv)
            else:
                with open('/dev/null', 'w') as null:
                    return subprocess.call(argv, stderr=null)

    def run_ssh (self, argv, message, trash_err=False, dry_run=False):
        ssh_argv = self.test_ssh().actual_argv(argv)
        result = self.run (ssh_argv, message, trash_err, dry_run=dry_run)
        if result != 0:
            print("WARNING: failed to run {} on {}".format(" ".join(argv), self.hostname))
        return result

    def backquote (self, argv, trash_err=False):
        # in python3 we need to set universal_newlines=True
        if not trash_err:
            out_err = subprocess.Popen(argv, stdout=subprocess.PIPE,
                                       universal_newlines=True).communicate()
        else:
            with open('/dev/null', 'w') as null:
                out_err = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=null,
                                           universal_newlines=True).communicate()
        # only interested in stdout here
        return out_err[0]

    # if you have any shell-expanded arguments like *
    # and if there's any chance the command is adressed to the local host
    def backquote_ssh (self, argv, trash_err=False):
        if not self.probe(): return ''
        return self.backquote(self.test_ssh().actual_argv(argv), trash_err)

############################################################
class BuildInstance:
    def __init__ (self, buildname, pid, buildbox):
        self.buildname = buildname
        self.buildbox = buildbox
        self.pids = [pid]
    def __repr__(self):
        return "<BuildInstance {} in {}>".format(self.buildname, self.buildbox)

    def add_pid(self,pid):
        self.pids.append(pid)

    def line (self):
        return "== {} == (pids={})".format(self.buildname, self.pids)

class BuildBox (Box):
    def __init__ (self, hostname):
        Box.__init__(self, hostname)
        self.build_instances = []
    def __repr__(self):
        return "<BuildBox {}>".format(self.hostname)

    def add_build(self, buildname, pid):
        for build in self.build_instances:
            if build.buildname == buildname:
                build.add_pid(pid)
                return
        self.build_instances.append(BuildInstance(buildname, pid, self))

    def list(self, verbose=False):
        if not self.build_instances:
            header ('No build process on {} ({})'.format(self.hostname_fedora(), self.uptime()))
        else:
            header ("Builds on {} ({})".format(self.hostname_fedora(), self.uptime()))
            for b in self.build_instances:
                header (b.line(), banner=False)

    def reboot (self, options):
        if not options.soft:
            Box.reboot(self, options)
        else:
            self.soft_reboot (options)

build_matcher=re.compile("\s*(?P<pid>[0-9]+).*-[bo]\s+(?P<buildname>[^\s]+)(\s|\Z)")
build_matcher_initvm=re.compile("\s*(?P<pid>[0-9]+).*initvm.*\s+(?P<buildname>[^\s]+)\s*\Z")

class BuildLxcBox (BuildBox):
    def soft_reboot (self, options):
            command=['pkill','lbuild']
            self.run_ssh(command, "Terminating vbuild processes", dry_run=options.dry_run)

    # inspect box and find currently running builds
    def sense(self, options):
        print('xb', end=' ')
        sys.stdout.flush()
        pids = self.backquote_ssh(['pgrep','lbuild'], trash_err=True)
        if not pids: return
        command = ['ps', '-o', 'pid,command'] + [ pid for pid in pids.split("\n") if pid]
        ps_lines = self.backquote_ssh(command).split('\n')
        for line in ps_lines:
            if not line.strip() or line.find('PID') >= 0: continue
            m = build_matcher.match(line)
            if m:
                date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
                buildname = m.group('buildname').replace('@DATE@', date)
                self.add_build(buildname, m.group('pid'))
                continue
            m = build_matcher_initvm.match(line)
            if m:
                # buildname is expansed here
                self.add_build(buildname, m.group('pid'))
                continue
            header('BuildLxcBox.sense: command {} returned line that failed to match'.format(command))
            header(">>{}<<".format(line))

############################################################
class PlcInstance:
    def __init__ (self, plcbox):
        self.plc_box = plcbox
        # unknown yet
        self.timestamp = 0
    def __repr__(self):
        return "<PlcInstance {}>".format(self.plc_box)

    def set_timestamp (self,timestamp):
        self.timestamp = timestamp
    def set_now (self):
        self.timestamp = int(time.time())
    def pretty_timestamp (self):
        return time.strftime("%Y-%m-%d:%H-%M", time.localtime(self.timestamp))

class PlcLxcInstance (PlcInstance):
    # does lxc have a context id of any kind ?
    def __init__ (self, plcbox, lxcname, pid):
        PlcInstance.__init__(self, plcbox)
        self.lxcname = lxcname
        self.pid = pid
    def __repr__(self):
        return "<PlcLxcInstance {}>".format(self.lxcname)

    def vplcname (self):
        return self.lxcname.split('-')[-1]
    def buildname (self):
        return self.lxcname.rsplit('-',2)[0]

    def line (self):
        msg="== {} ==".format(self.vplcname())
        msg += " [={}]".format(self.lxcname)
        if self.pid==-1:  msg+=" not (yet?) running"
        else:              msg+=" (pid={})".format(self.pid)
        if self.timestamp: msg += " @ {}".format(self.pretty_timestamp())
        else:              msg += " *unknown timestamp*"
        return msg

    def kill (self):
        command="rsync lxc-driver.sh  {}:/root".format(self.plc_box.hostname)
        subprocess.getstatusoutput(command)
        msg="lxc container stopping {} on {}".format(self.lxcname, self.plc_box.hostname)
        self.plc_box.run_ssh(['/root/lxc-driver.sh', '-c', 'stop_lxc', '-n', self.lxcname], msg)
        self.plc_box.forget(self)

##########
class PlcBox (Box):
    def __init__ (self, hostname, max_plcs):
        Box.__init__(self, hostname)
        self.plc_instances = []
        self.max_plcs = max_plcs
    def __repr__(self):
        return "<PlcBox {}>".format(self.hostname)

    def free_slots (self):
        return self.max_plcs - len(self.plc_instances)

    # fill one slot even though this one is not started yet
    def add_dummy (self, plcname):
        dummy=PlcLxcInstance(self, 'dummy_'+plcname, 0)
        dummy.set_now()
        self.plc_instances.append(dummy)

    def forget (self, plc_instance):
        self.plc_instances.remove(plc_instance)

    def reboot (self, options):
        if not options.soft:
            Box.reboot(self, options)
        else:
            self.soft_reboot (options)

    def list(self, verbose=False):
        if not self.plc_instances:
            header ('No plc running on {}'.format(self.line()))
        else:
            header ("Active plc VMs on {}".format(self.line()))
            self.plc_instances.sort(key=timestamp_key)
            for p in self.plc_instances:
                header (p.line(), banner=False)

## we do not this at INRIA any more
class PlcLxcBox (PlcBox):

    def add_lxc (self, lxcname, pid):
        for plc in self.plc_instances:
            if plc.lxcname == lxcname:
                header("WARNING, duplicate myplc {} running on {}"\
                       .format(lxcname, self.hostname), banner=False)
                return
        self.plc_instances.append(PlcLxcInstance(self, lxcname, pid))


    # a line describing the box
    def line(self):
        return "{} [max={},free={}] ({})".format(self.hostname_fedora(virt="lxc"),
                                                 self.max_plcs, self.free_slots(),
                                                 self.uptime())

    def plc_instance_by_lxcname(self, lxcname):
        for p in self.plc_instances:
            if p.lxcname == lxcname:
                return p
        return None

    # essentially shutdown all running containers
    def soft_reboot(self, options):
        command="rsync lxc-driver.sh  {}:/root".format(self.hostname)
        subprocess.getstatusoutput(command)
        self.run_ssh( ['/root/lxc-driver.sh','-c','stop_all'],
                      "Stopping all running lxc containers on {}".format(self.hostname),
                      dry_run=options.dry_run)


    # sense is expected to fill self.plc_instances with PlcLxcInstance's
    # to describe the currently running VM's
    def sense(self, options):
        print("xp", end=' ')
        sys.stdout.flush()
        command = "rsync lxc-driver.sh  {}:/root".format(self.hostname)
        subprocess.getstatusoutput(command)
        command = ['/root/lxc-driver.sh', '-c', 'sense_all']
        lxc_stat = self.backquote_ssh (command)
        for lxc_line in lxc_stat.split("\n"):
            if not lxc_line:
                continue
            # we mix build and plc VMs
            if 'vplc' not in lxc_line:
                continue
            lxcname = lxc_line.split(";")[0]
            pid = lxc_line.split(";")[1]
            timestamp = lxc_line.split(";")[2]
            self.add_lxc(lxcname,pid)
            try: timestamp = int(timestamp)
            except: timestamp = 0
            p = self.plc_instance_by_lxcname(lxcname)
            if not p:
                print('WARNING zombie plc',self.hostname,lxcname)
                print('... was expecting',lxcname,'in',[i.lxcname for i in self.plc_instances])
                continue
            p.set_timestamp(timestamp)

############################################################
class QemuInstance:
    def __init__(self, nodename, pid, qemubox):
        self.nodename = nodename
        self.pid = pid
        self.qemu_box = qemubox
        # not known yet
        self.buildname = None
        self.timestamp = 0
    def __repr__(self):
        return "<QemuInstance {}>".format(self.nodename)

    def set_buildname (self, buildname):
        self.buildname = buildname
    def set_timestamp (self, timestamp):
        self.timestamp = timestamp
    def set_now (self):
        self.timestamp = int(time.time())
    def pretty_timestamp (self):
        return time.strftime("%Y-%m-%d:%H-%M", time.localtime(self.timestamp))

    def line (self):
        msg = "== {} ==".format(short_hostname(self.nodename))
        msg += " [={}]".format(self.buildname)
        if self.pid:       msg += " (pid={})".format(self.pid)
        else:              msg += " not (yet?) running"
        if self.timestamp: msg += " @ {}".format(self.pretty_timestamp())
        else:              msg += " *unknown timestamp*"
        return msg

    def kill(self):
        if self.pid == 0:
            print("cannot kill qemu {} with pid==0".format(self.nodename))
            return
        msg = "Killing qemu {} with pid={} on box {}".format(self.nodename, self.pid, self.qemu_box.hostname)
        self.qemu_box.run_ssh(['kill', "{}".format(self.pid)], msg)
        self.qemu_box.forget(self)


class QemuBox (Box):
    def __init__ (self, hostname, max_qemus):
        Box.__init__(self, hostname)
        self.qemu_instances = []
        self.max_qemus = max_qemus
    def __repr__(self):
        return "<QemuBox {}>".format(self.hostname)

    def add_node(self, nodename, pid):
        for qemu in self.qemu_instances:
            if qemu.nodename == nodename:
                header("WARNING, duplicate qemu {} running on {}"\
                       .format(nodename,self.hostname), banner=False)
                return
        self.qemu_instances.append(QemuInstance(nodename, pid, self))

    def node_names (self):
        return [ qi.nodename for qi in self.qemu_instances ]

    def forget (self, qemu_instance):
        self.qemu_instances.remove(qemu_instance)

    # fill one slot even though this one is not started yet
    def add_dummy(self, nodename):
        dummy=QemuInstance('dummy_'+nodename, 0, self)
        dummy.set_now()
        self.qemu_instances.append(dummy)

    def line (self):
        return "{} [max={},free={}] ({}) {}"\
            .format(self.hostname_fedora(virt="qemu"),
                    self.max_qemus, self.free_slots(),
                    self.uptime(), self.driver())

    def list(self, verbose=False):
        if not self.qemu_instances:
            header ('No qemu on {}'.format(self.line()))
        else:
            header ("Qemus on {}".format(self.line()))
            self.qemu_instances.sort(key=timestamp_key)
            for q in self.qemu_instances:
                header (q.line(), banner=False)

    def free_slots (self):
        return self.max_qemus - len(self.qemu_instances)

    def driver(self):
        if hasattr(self,'_driver') and self._driver:
            return self._driver
        return '*undef* driver'

    def qemu_instance_by_pid(self, pid):
        for q in self.qemu_instances:
            if q.pid == pid:
                return q
        return None

    def qemu_instance_by_nodename_buildname (self, nodename, buildname):
        for q in self.qemu_instances:
            if q.nodename == nodename and q.buildname == buildname:
                return q
        return None

    def reboot (self, options):
        if not options.soft:
            Box.reboot(self, options)
        else:
            self.run_ssh(['pkill','qemu'], "Killing qemu instances",
                         dry_run=options.dry_run)

    matcher=re.compile("\s*(?P<pid>[0-9]+).*-cdrom\s+(?P<nodename>[^\s]+)\.iso")

    def sense(self, options):
        print('qn', end=' ')
        sys.stdout.flush()
        modules = self.backquote_ssh(['lsmod']).split('\n')
        self._driver = '*NO kqemu/kvm_intel MODULE LOADED*'
        for module in modules:
            if module.find('kqemu') == 0:
                self._driver = 'kqemu module loaded'
            # kvm might be loaded without kvm_intel (we dont have AMD)
            elif module.find('kvm_intel') == 0:
                self._driver = 'kvm_intel OK'
        ########## find out running pids
        pids = self.backquote_ssh(['pgrep','qemu'])
        if not pids:
            return
        command = ['ps','-o','pid,command'] + [ pid for pid in pids.split("\n") if pid]
        ps_lines = self.backquote_ssh(command).split("\n")
        for line in ps_lines:
            if not line.strip() or line.find('PID') >=0 :
                continue
            m = QemuBox.matcher.match(line)
            if m:
                self.add_node(m.group('nodename'), m.group('pid'))
                continue
            header('QemuBox.sense: command {} returned line that failed to match'.format(command))
            header(">>{}<<".format(line))
        ########## retrieve alive instances and map to build
        live_builds=[]
        command = ['grep', '.', '/vservers/*/*/qemu.pid', '/dev/null']
        pid_lines = self.backquote_ssh(command, trash_err=True).split('\n')
        for pid_line in pid_lines:
            if not pid_line.strip():
                continue
            # expect <build>/<nodename>/qemu.pid:<pid>pid
            try:
                (_, __, buildname, nodename, tail) = pid_line.split('/')
                (_,pid) = tail.split(':')
                q = self.qemu_instance_by_pid(pid)
                if not q:
                    continue
                q.set_buildname(buildname)
                live_builds.append(buildname)
            except:
                print('WARNING, could not parse pid line', pid_line)
        # retrieve timestamps
        if not live_builds:
            return
        command =  ['grep','.']
        command += ['/vservers/{}/*/timestamp'.format(b) for b in live_builds]
        command += ['/dev/null']
        ts_lines = self.backquote_ssh(command, trash_err=True).split('\n')
        for ts_line in ts_lines:
            if not ts_line.strip():
                continue
            # expect <build>/<nodename>/timestamp:<timestamp>
            try:
                (_, __, buildname, nodename, tail) = ts_line.split('/')
                nodename = nodename.replace('qemu-', '')
                (_, timestamp) = tail.split(':')
                timestamp = int(timestamp)
                q = self.qemu_instance_by_nodename_buildname(nodename, buildname)
                if not q:
                    # this warning corresponds to qemu instances that were not killed properly
                    # and that have a dangling qemu.pid - and not even all of them as they need
                    # to be attached to a build that has a node running...
                    # it is more confusing than helpful, so let's just trash it
                    #print 'WARNING zombie qemu',self.hostname,ts_line
                    #print '... was expecting (',short_hostname(nodename),buildname,') in',\
                    #    [ (short_hostname(i.nodename),i.buildname) for i in self.qemu_instances ]
                    continue
                q.set_timestamp(timestamp)
            except:
                print('WARNING, could not parse ts line',ts_line)

####################
class TestInstance:
    def __init__(self, buildname, pid=0):
        self.pids = []
        if pid != 0:
            self.pid.append(pid)
        self.buildname = buildname
        # latest trace line
        self.trace = ''
        # has a KO test
        self.broken_steps = []
        self.timestamp = 0
    def __repr__(self):
        return "<TestInstance {}>".format(self.buildname)

    def set_timestamp(self, timestamp):
        self.timestamp = timestamp
    def set_now(self):
        self.timestamp = int(time.time())
    def pretty_timestamp(self):
        return time.strftime("%Y-%m-%d:%H-%M", time.localtime(self.timestamp))
    def is_running (self):
        return len(self.pids) != 0
    def add_pid(self, pid):
        self.pids.append(pid)
    def set_broken(self, plcindex, step):
        self.broken_steps.append( (plcindex, step,) )

    def second_letter(self):
        if not self.broken_steps:
            return '='
        else:
            really_broken = [ step for (i,step) in self.broken_steps if '_ignore' not in step ]
            # W is for warning like what's in the build mail
            if len(really_broken) == 0:
                return 'W'
            else:
                return 'B'

    def line (self):
        # make up a 2-letter sign
        # first letter : '=', unless build is running : '*'
        double = '*' if self.pids else '='
        # second letter : '=' if fine, 'W' for warnings (only ignored steps) 'B' for broken
        letter2 = self.second_letter()
        double += letter2
        msg = " {} {} ==".format(double, self.buildname)
        if not self.pids:
            pass
        elif len(self.pids)==1:
            msg += " (pid={})".format(self.pids[0])
        else:
            msg += " !!!pids={}!!!".format(self.pids)
        msg += " @{}".format(self.pretty_timestamp())
        if letter2 != '=':
            msg2 = ( ' BROKEN' if letter2 == 'B' else ' WARNING' )
            # sometimes we have an empty plcindex
            msg += " [{}=".format(msg2) \
                   + " ".join(["{}@{}".format(s, i) if i else s for (i, s) in self.broken_steps]) \
                   + "]"
        return msg

class TestBox(Box):
    def __init__(self, hostname):
        Box.__init__(self, hostname)
        self.starting_ips = []
        self.test_instances = []
    def __repr__(self):
        return "<TestBox {}>".format(self.hostname)

    def reboot(self, options):
        # can't reboot a vserver VM
        self.run_ssh(['pkill', 'run_log'], "Terminating current runs",
                      dry_run=options.dry_run)
        self.run_ssh(['rm', '-f', Starting.location], "Cleaning {}".format(Starting.location),
                      dry_run=options.dry_run)

    def get_test(self, buildname):
        for i in self.test_instances:
            if i.buildname == buildname:
                return i

    # we scan ALL remaining test results, even the ones not running
    def add_timestamp(self, buildname, timestamp):
        i = self.get_test(buildname)
        if i:
            i.set_timestamp(timestamp)
        else:
            i = TestInstance(buildname, 0)
            i.set_timestamp(timestamp)
            self.test_instances.append(i)

    def add_running_test(self, pid, buildname):
        i = self.get_test(buildname)
        if not i:
            self.test_instances.append(TestInstance(buildname, pid))
            return
        if i.pids:
            print("WARNING: 2 concurrent tests run on same build {}".format(buildname))
        i.add_pid(pid)

    def add_broken(self, buildname, plcindex, step):
        i = self.get_test(buildname)
        if not i:
            i = TestInstance(buildname)
            self.test_instances.append(i)
        i.set_broken(plcindex, step)

    matcher_proc=re.compile (".*/proc/(?P<pid>[0-9]+)/cwd.*/root/(?P<buildname>[^/]+)$")
    matcher_grep=re.compile ("/root/(?P<buildname>[^/]+)/logs/trace.*:TRACE:\s*(?P<plcindex>[0-9]+).*step=(?P<step>\S+).*")
    matcher_grep_missing=re.compile ("grep: /root/(?P<buildname>[^/]+)/logs/trace: No such file or directory")

    def sense(self, options):
        print('tm', end=' ')
        self.starting_ips = [ x for x in self.backquote_ssh( ['cat', Starting.location], trash_err=True).strip().split('\n') if x ]

        # scan timestamps on all tests
        # this is likely to not invoke ssh so we need to be a bit smarter to get * expanded
        # xxx would make sense above too
        command = ['bash', '-c', "grep . /root/*/timestamp /dev/null"]
        ts_lines = self.backquote_ssh(command, trash_err=True).split('\n')
        for ts_line in ts_lines:
            if not ts_line.strip():
                continue
            # expect /root/<buildname>/timestamp:<timestamp>
            try:
                (ts_file, timestamp) = ts_line.split(':')
                ts_file = os.path.dirname(ts_file)
                buildname = os.path.basename(ts_file)
                timestamp = int(timestamp)
                t = self.add_timestamp(buildname, timestamp)
            except:
                print('WARNING, could not parse ts line', ts_line)

        # let's try to be robust here -- tests that fail very early like e.g.
        # "Cannot make space for a PLC instance: vplc IP pool exhausted", that occurs as part of provision
        # will result in a 'trace' symlink to an inexisting 'trace-<>.txt' because no step has gone through
        # simple 'trace' should exist though as it is created by run_log
        command = ['bash', '-c', "grep KO /root/*/logs/trace /dev/null 2>&1" ]
        trace_lines = self.backquote_ssh(command).split('\n')
        for line in trace_lines:
            if not line.strip():
                continue
            m = TestBox.matcher_grep_missing.match(line)
            if m:
                buildname = m.group('buildname')
                self.add_broken(buildname, '', 'NO STEP DONE')
                continue
            m = TestBox.matcher_grep.match(line)
            if m:
                buildname = m.group('buildname')
                plcindex = m.group('plcindex')
                step = m.group('step')
                self.add_broken(buildname, plcindex, step)
                continue
            header("TestBox.sense: command {} returned line that failed to match\n{}".format(command, line))
            header(">>{}<<".format(line))

        pids = self.backquote_ssh (['pgrep', 'run_log'], trash_err=True)
        if not pids:
            return
        command = ['ls','-ld'] + ["/proc/{}/cwd".format(pid) for pid in pids.split("\n") if pid]
        ps_lines = self.backquote_ssh(command).split('\n')
        for line in ps_lines:
            if not line.strip():
                continue
            m = TestBox.matcher_proc.match(line)
            if m:
                pid = m.group('pid')
                buildname = m.group('buildname')
                self.add_running_test(pid, buildname)
                continue
            header("TestBox.sense: command {} returned line that failed to match\n{}".format(command, line))
            header(">>{}<<".format(line))


    def line (self):
        return self.hostname_fedora()

    def list (self, verbose=False):
        # verbose shows all tests
        if verbose:
            instances = self.test_instances
            msg="tests"
        else:
            instances = [ i for i in self.test_instances if i.is_running() ]
            msg="running tests"

        if not instances:
            header ("No {} on {}".format(msg, self.line()))
        else:
            header ("{} on {}".format(msg, self.line()))
            instances.sort(key=timestamp_key)
            for i in instances:
                print(i.line())
        # show 'starting' regardless of verbose
        if self.starting_ips:
            header("Starting IP addresses on {}".format(self.line()))
            self.starting_ips.sort()
            for starting in self.starting_ips:
                print(starting)
        else:
            header("Empty 'starting' on {}".format(self.line()))

############################################################
class Options: pass

class Substrate:

    def __init__(self):
        self.options = Options()
        self.options.dry_run = False
        self.options.verbose = False
        self.options.reboot = False
        self.options.soft = False
        self.test_box = TestBox (self.test_box_spec())
        self.build_lxc_boxes = [ BuildLxcBox(h) for h in self.build_lxc_boxes_spec() ]
        self.plc_lxc_boxes = [ PlcLxcBox (h, m) for (h, m) in self.plc_lxc_boxes_spec ()]
        self.qemu_boxes = [ QemuBox (h, m) for (h, m) in self.qemu_boxes_spec ()]
        self._sensed = False

        self.vplc_pool = Pool(self.vplc_ips(), "for vplcs", self)
        self.vnode_pool = Pool(self.vnode_ips(), "for vnodes", self)

        self.build_boxes = self.build_lxc_boxes
        self.plc_boxes = self.plc_lxc_boxes
        self.default_boxes = self.plc_boxes + self.qemu_boxes
        self.all_boxes = self.build_boxes + [ self.test_box ] + self.plc_boxes + self.qemu_boxes
    def __repr__(self):
        return "<Substrate {}>".format(self.summary_line())

    def summary_line (self):
        msg  = "["
        msg += " {} xp".format(len(self.plc_lxc_boxes))
        msg += " {} xq".format(len(self.qemu_boxes))
        msg += "]"
        return msg

    def fqdn (self, hostname):
        if hostname.find('.') < 0:
            return "{}.{}".format(hostname, self.domain())
        return hostname

    # return True if actual sensing takes place
    def sense(self, force=False):
        if self._sensed and not force:
            return False
        print('Sensing local substrate...', end=' ')
        sys.stdout.flush()
        for b in self.default_boxes:
            b.sense(self.options)
        print('Done')
        self._sensed = True
        return True

    def list(self, verbose=False):
        for b in self.default_boxes:
            b.list()

    def add_dummy_plc(self, plc_boxname, plcname):
        for pb in self.plc_boxes:
            if pb.hostname == plc_boxname:
                pb.add_dummy(plcname)
                return True
    def add_dummy_qemu(self, qemu_boxname, qemuname):
        for qb in self.qemu_boxes:
            if qb.hostname == qemu_boxname:
                qb.add_dummy(qemuname)
                return True

    def add_starting_dummy(self, bname, vname):
        return self.add_dummy_plc(bname, vname) or self.add_dummy_qemu(bname, vname)

    ##########
    def provision(self, plcs, options):
        try:
            # attach each plc to a plc box and an IP address
            plcs = [ self.provision_plc(plc, options) for plc in plcs ]
            # attach each node/qemu to a qemu box with an IP address
            plcs = [ self.provision_qemus(plc,options) for plc in plcs ]
            # update the SFA spec accordingly
            plcs = [ self.localize_sfa_rspec(plc, options) for plc in plcs ]
            self.list()
            return plcs
        except Exception as e:
            print('* Could not provision this test on current substrate','--',e,'--','exiting')
            traceback.print_exc()
            sys.exit(1)

    # it is expected that a couple of options like ips_bplc and ips_vplc
    # are set or unset together
    @staticmethod
    def check_options(x, y):
        if not x and not y:
            return True
        return len(x) == len(y)

    # find an available plc box (or make space)
    # and a free IP address (using options if present)
    def provision_plc(self, plc, options):

        assert Substrate.check_options(options.ips_bplc, options.ips_vplc)

        #### let's find an IP address for that plc
        # look in options
        if options.ips_vplc:
            # this is a rerun
            # we don't check anything here,
            # it is the caller's responsability to cleanup and make sure this makes sense
            plc_boxname = options.ips_bplc.pop()
            vplc_hostname = options.ips_vplc.pop()
        else:
            if self.sense():
                self.list()
            plc_boxname = None
            vplc_hostname = None
            # try to find an available IP
            self.vplc_pool.sense()
            couple = self.vplc_pool.next_free()
            if couple:
                (vplc_hostname, unused) = couple
            #### we need to find one plc box that still has a slot
            max_free = 0
            # use the box that has max free spots for load balancing
            for pb in self.plc_boxes:
                free = pb.free_slots()
                if free > max_free:
                    plc_boxname = pb.hostname
                    max_free = free
            # if there's no available slot in the plc_boxes, or we need a free IP address
            # make space by killing the oldest running instance
            if not plc_boxname or not vplc_hostname:
                # find the oldest of all our instances
                all_plc_instances = reduce(lambda x, y: x+y,
                                           [ pb.plc_instances for pb in self.plc_boxes ],
                                           [])
                all_plc_instances.sort(key=timestamp_key)
                try:
                    plc_instance_to_kill = all_plc_instances[0]
                except:
                    msg = ""
                    if not plc_boxname:
                        msg += " PLC boxes are full"
                    if not vplc_hostname:
                        msg += " vplc IP pool exhausted"
                    msg += " {}".format(self.summary_line())
                    raise Exception("Cannot make space for a PLC instance:" + msg)
                freed_plc_boxname = plc_instance_to_kill.plc_box.hostname
                freed_vplc_hostname = plc_instance_to_kill.vplcname()
                message = 'killing oldest plc instance = {} on {}'\
                    .format(plc_instance_to_kill.line(), freed_plc_boxname)
                plc_instance_to_kill.kill()
                # use this new plcbox if that was the problem
                if not plc_boxname:
                    plc_boxname = freed_plc_boxname
                # ditto for the IP address
                if not vplc_hostname:
                    vplc_hostname = freed_vplc_hostname
                    # record in pool as mine
                    self.vplc_pool.set_mine(vplc_hostname)

        #
        self.add_dummy_plc(plc_boxname, plc['name'])
        vplc_ip = self.vplc_pool.get_ip(vplc_hostname)
        self.vplc_pool.add_starting(vplc_hostname, plc_boxname)

        #### compute a helpful vserver name
        # remove domain in hostname
        vplc_short = short_hostname(vplc_hostname)
        vservername = "{}-{}-{}".format(options.buildname, plc['index'], vplc_short)
        plc_name = "{}_{}".format(plc['name'], vplc_short)

        utils.header('PROVISION plc {} in box {} at IP {} as {}'\
                     .format(plc['name'], plc_boxname, vplc_hostname, vservername))

        #### apply in the plc_spec
        # # informative
        # label = options.personality.replace("linux","")
        mapper = {'plc' : [ ('*' , {'host_box' : plc_boxname,
                                    'name' : plc_name,
                                    'vservername' : vservername,
                                    'vserverip' : vplc_ip,
                                    'settings:PLC_DB_HOST' : vplc_hostname,
                                    'settings:PLC_API_HOST' : vplc_hostname,
                                    'settings:PLC_BOOT_HOST' : vplc_hostname,
                                    'settings:PLC_WWW_HOST' : vplc_hostname,
                                    'settings:PLC_NET_DNS1' : self.network_settings() [ 'interface_fields:dns1' ],
                                    'settings:PLC_NET_DNS2' : self.network_settings() [ 'interface_fields:dns2' ],
                                } ) ]
              }


        # mappers only work on a list of plcs
        return TestMapper([plc], options).map(mapper)[0]

    ##########
    def provision_qemus(self, plc, options):

        assert Substrate.check_options(options.ips_bnode, options.ips_vnode)

        test_mapper = TestMapper([plc], options)
        nodenames = test_mapper.node_names()
        maps = []
        for nodename in nodenames:

            if options.ips_vnode:
                # as above, it's a rerun, take it for granted
                qemu_boxname = options.ips_bnode.pop()
                vnode_hostname = options.ips_vnode.pop()
            else:
                if self.sense():
                    self.list()
                qemu_boxname = None
                vnode_hostname = None
                # try to find an available IP
                self.vnode_pool.sense()
                couple = self.vnode_pool.next_free()
                if couple:
                    (vnode_hostname, unused) = couple
                # find a physical box
                max_free = 0
                # use the box that has max free spots for load balancing
                for qb in self.qemu_boxes:
                    free = qb.free_slots()
                    if free>max_free:
                        qemu_boxname = qb.hostname
                        max_free = free
                # if we miss the box or the IP, kill the oldest instance
                if not qemu_boxname or not vnode_hostname:
                # find the oldest of all our instances
                    all_qemu_instances = reduce(lambda x, y: x+y,
                                                [ qb.qemu_instances for qb in self.qemu_boxes ],
                                                [])
                    all_qemu_instances.sort(key=timestamp_key)
                    try:
                        qemu_instance_to_kill = all_qemu_instances[0]
                    except:
                        msg = ""
                        if not qemu_boxname:
                            msg += " QEMU boxes are full"
                        if not vnode_hostname:
                            msg += " vnode IP pool exhausted"
                        msg += " {}".format(self.summary_line())
                        raise Exception("Cannot make space for a QEMU instance:"+msg)
                    freed_qemu_boxname = qemu_instance_to_kill.qemu_box.hostname
                    freed_vnode_hostname = short_hostname(qemu_instance_to_kill.nodename)
                    # kill it
                    message = 'killing oldest qemu node = {} on {}'.format(qemu_instance_to_kill.line(),
                                                                           freed_qemu_boxname)
                    qemu_instance_to_kill.kill()
                    # use these freed resources where needed
                    if not qemu_boxname:
                        qemu_boxname = freed_qemu_boxname
                    if not vnode_hostname:
                        vnode_hostname = freed_vnode_hostname
                        self.vnode_pool.set_mine(vnode_hostname)

            self.add_dummy_qemu(qemu_boxname, vnode_hostname)
            mac = self.vnode_pool.retrieve_userdata(vnode_hostname)
            ip = self.vnode_pool.get_ip(vnode_hostname)
            self.vnode_pool.add_starting(vnode_hostname, qemu_boxname)

            vnode_fqdn = self.fqdn(vnode_hostname)
            nodemap = {'host_box' : qemu_boxname,
                       'node_fields:hostname' : vnode_fqdn,
                       'interface_fields:ip' : ip,
                       'ipaddress_fields:ip_addr' : ip,
                       'interface_fields:mac' : mac,
                   }
            nodemap.update(self.network_settings())
            maps.append( (nodename, nodemap) )

            utils.header("PROVISION node {} in box {} at IP {} with MAC {}"\
                         .format(nodename, qemu_boxname, vnode_hostname, mac))

        return test_mapper.map({'node':maps})[0]

    def localize_sfa_rspec(self, plc, options):

        plc['sfa']['settings']['SFA_REGISTRY_HOST'] = plc['settings']['PLC_DB_HOST']
        plc['sfa']['settings']['SFA_AGGREGATE_HOST'] = plc['settings']['PLC_DB_HOST']
        plc['sfa']['settings']['SFA_DB_HOST'] = plc['settings']['PLC_DB_HOST']
        plc['sfa']['settings']['SFA_PLC_URL'] = 'https://{}:443/PLCAPI/'.format(plc['settings']['PLC_API_HOST'])
        return plc

    #################### release:
    def release(self, options):
        self.vplc_pool.release_my_starting()
        self.vnode_pool.release_my_starting()
        pass

    #################### show results for interactive mode
    def get_box(self, boxname):
        for b in self.build_boxes + self.plc_boxes + self.qemu_boxes + [self.test_box] :
            if b.shortname() == boxname:
                return b
            try:
                if b.shortname() == boxname.split('.')[0]:
                    return b
            except:
                pass
        print("Could not find box {}".format(boxname))
        return None

    # deal with the mix of boxes and names and stores the current focus
    # as a list of Box instances in self.focus_all
    def normalize(self, box_or_names):
        self.focus_all = []
        for box in box_or_names:
            if not isinstance(box, Box):
                box = self.get_box(box)
            if not box:
                print('Warning - could not handle box',box)
            self.focus_all.append(box)
        # elaborate by type
        self.focus_build = [ x for x in self.focus_all if isinstance(x, BuildBox) ]
        self.focus_plc = [ x for x in self.focus_all if isinstance(x, PlcBox) ]
        self.focus_qemu = [ x for x in self.focus_all if isinstance(x, QemuBox) ]

    def list_boxes(self):
        print('Sensing', end=' ')
        sys.stdout.flush()
        for box in self.focus_all:
            box.sense(self.options)
        print('Done')
        for box in self.focus_all:
            box.list(self.options.verbose)

    def reboot_boxes(self):
        for box in self.focus_all:
            box.reboot(self.options)

    def sanity_check(self):
        print('Sanity check')
        self.sanity_check_plc()
        self.sanity_check_qemu()

    def sanity_check_plc(self):
        pass

    def sanity_check_qemu(self):
        all_nodes = []
        for box in self.focus_qemu:
            all_nodes += box.node_names()
        hash = {}
        for node in all_nodes:
            if node not in hash:
                hash[node] = 0
            hash[node]+=1
        for (node,count) in list(hash.items()):
            if count!=1:
                print('WARNING - duplicate node', node)


    ####################
    # can be run as a utility to probe/display/manage the local infrastructure
    def main(self):
        parser = OptionParser()
        parser.add_option('-r', "--reboot", action='store_true', dest='reboot', default=False,
                          help='reboot mode (use shutdown -r)')
        parser.add_option('-s', "--soft", action='store_true', dest='soft', default=False,
                          help='soft mode for reboot (terminates processes)')
        parser.add_option('-t', "--testbox", action='store_true', dest='testbox', default=False,
                          help='add test box')
        parser.add_option('-b', "--build", action='store_true', dest='builds', default=False,
                          help='add build boxes')
        parser.add_option('-p', "--plc", action='store_true', dest='plcs', default=False,
                          help='add plc boxes')
        parser.add_option('-q', "--qemu", action='store_true', dest='qemus', default=False,
                          help='add qemu boxes')
        parser.add_option('-a', "--all", action='store_true', dest='all', default=False,
                          help='address all known  boxes, like -b -t -p -q')
        parser.add_option('-v', "--verbose", action='store_true', dest='verbose', default=False,
                          help='verbose mode')
        parser.add_option('-n', "--dry_run", action='store_true', dest='dry_run', default=False,
                          help='dry run mode')
        (self.options, args) = parser.parse_args()

        boxes = args
        if self.options.testbox: boxes += [self.test_box]
        if self.options.builds: boxes += self.build_boxes
        if self.options.plcs: boxes += self.plc_boxes
        if self.options.qemus: boxes += self.qemu_boxes
        if self.options.all: boxes += self.all_boxes

        global verbose
        verbose = self.options.verbose
        # default scope is -b -p -q -t
        if not boxes:
            boxes = self.build_boxes + self.plc_boxes + self.qemu_boxes + [self.test_box]

        self.normalize(boxes)

        if self.options.reboot:
            self.reboot_boxes()
        else:
            self.list_boxes()
            self.sanity_check()
