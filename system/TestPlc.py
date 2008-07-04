# $Id$
import os, os.path
import datetime
import time
import sys
import traceback
from types import StringTypes
import socket

import utils
from TestSite import TestSite
from TestNode import TestNode
from TestUser import TestUser
from TestKey import TestKey
from TestSlice import TestSlice
from TestSliver import TestSliver
from TestBox import TestBox
from TestSsh import TestSsh
from TestApiserver import TestApiserver

# step methods must take (self) and return a boolean (options is a member of the class)

def standby(minutes,dry_run):
    utils.header('Entering StandBy for %d mn'%minutes)
    if dry_run:
        print 'dry_run'
    else:
        time.sleep(60*minutes)
    return True

def standby_generic (func):
    def actual(self):
        minutes=int(func.__name__.split("_")[1])
        return standby(minutes,self.options.dry_run)
    return actual

def node_mapper (method):
    def actual(self):
        overall=True
        node_method = TestNode.__dict__[method.__name__]
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite (self,site_spec)
            for node_spec in site_spec['nodes']:
                test_node = TestNode (self,test_site,node_spec)
                if not node_method(test_node): overall=False
        return overall
    return actual

def slice_mapper_options (method):
    def actual(self):
        overall=True
        slice_method = TestSlice.__dict__[method.__name__]
        for slice_spec in self.plc_spec['slices']:
            site_spec = self.locate_site (slice_spec['sitename'])
            test_site = TestSite(self,site_spec)
            test_slice=TestSlice(self,test_site,slice_spec)
            if not slice_method(test_slice,self.options): overall=False
        return overall
    return actual

SEP='<sep>'

class TestPlc:

    default_steps = ['uninstall','install','install_rpm', 
                     'configure', 'start', SEP,
                     'store_keys', 'clear_known_hosts', 'initscripts', SEP,
                     'sites', 'nodes', 'slices', 'nodegroups', SEP,
                     'init_node','bootcd', 'configure_qemu', 'export_qemu',
                     'kill_all_qemus', 'reinstall_node','start_node', SEP,
                     'nodes_booted', 'nodes_ssh', 'check_slice',
                     'check_initscripts', 'check_tcp', 'plcsh_stress_test', SEP,
                     'force_gather_logs', 'force_kill_qemus', 'force_record_tracker','force_free_tracker' ]
    other_steps = [ 'stop_all_vservers','fresh_install', 'cache_rpm', 'stop', 'vs_start', SEP,
                    'clean_initscripts', 'clean_nodegroups','clean_all_sites', SEP,
                    'clean_sites', 'clean_nodes', 
                    'clean_slices', 'clean_keys', SEP,
                    'show_boxes', 'list_all_qemus', 'list_qemus', SEP,
                    'db_dump' , 'db_restore', ' cleanup_tracker',
                    'standby_1 through 20'
                    ]

    @staticmethod
    def printable_steps (list):
        return " ".join(list).replace(" "+SEP+" "," \\\n")
    @staticmethod
    def valid_step (step):
        return step != SEP

    def __init__ (self,plc_spec,options):
	self.plc_spec=plc_spec
        self.options=options
	self.test_ssh=TestSsh(self.plc_spec['hostname'],self.options.buildname)
        try:
            self.vserverip=plc_spec['vserverip']
            self.vservername=plc_spec['vservername']
            self.url="https://%s:443/PLCAPI/"%plc_spec['vserverip']
            self.vserver=True
        except:
            raise Exception,'chroot-based myplc testing is deprecated'
	self.apiserver=TestApiserver(self.url,options.dry_run)
        
    def name(self):
        name=self.plc_spec['name']
        return "%s.%s"%(name,self.vservername)

    def hostname(self):
        return self.plc_spec['hostname']

    def is_local (self):
        return self.test_ssh.is_local()

    # define the API methods on this object through xmlrpc
    # would help, but not strictly necessary
    def connect (self):
	pass

    def actual_command_in_guest (self,command):
        return self.test_ssh.actual_command(self.host_to_guest(command))
    
    def start_guest (self):
      return utils.system(self.test_ssh.actual_command(self.start_guest_in_host()))
    
    def run_in_guest (self,command):
        return utils.system(self.actual_command_in_guest(command))
    
    def run_in_host (self,command):
        return self.test_ssh.run_in_buildname(command)

    #command gets run in the vserver
    def host_to_guest(self,command):
        return "vserver %s exec %s"%(self.vservername,command)
    
    #command gets run in the vserver
    def start_guest_in_host(self):
        return "vserver %s start"%(self.vservername)
    
    # xxx quick n dirty
    def run_in_guest_piped (self,local,remote):
        return utils.system(local+" | "+self.test_ssh.actual_command(self.host_to_guest(remote),keep_stdin=True))

    def auth_root (self):
	return {'Username':self.plc_spec['PLC_ROOT_USER'],
		'AuthMethod':'password',
		'AuthString':self.plc_spec['PLC_ROOT_PASSWORD'],
                'Role' : self.plc_spec['role']
                }
    def locate_site (self,sitename):
        for site in self.plc_spec['sites']:
            if site['site_fields']['name'] == sitename:
                return site
            if site['site_fields']['login_base'] == sitename:
                return site
        raise Exception,"Cannot locate site %s"%sitename
        
    def locate_node (self,nodename):
        for site in self.plc_spec['sites']:
            for node in site['nodes']:
                if node['name'] == nodename:
                    return (site,node)
        raise Exception,"Cannot locate node %s"%nodename
        
    def locate_hostname (self,hostname):
        for site in self.plc_spec['sites']:
            for node in site['nodes']:
                if node['node_fields']['hostname'] == hostname:
                    return (site,node)
        raise Exception,"Cannot locate hostname %s"%hostname
        
    def locate_key (self,keyname):
        for key in self.plc_spec['keys']:
            if key['name'] == keyname:
                return key
        raise Exception,"Cannot locate key %s"%keyname

    def locate_slice (self, slicename):
        for slice in self.plc_spec['slices']:
            if slice['slice_fields']['name'] == slicename:
                return slice
        raise Exception,"Cannot locate slice %s"%slicename

    # all different hostboxes used in this plc
    def gather_hostBoxes(self):
        # maps on sites and nodes, return [ (host_box,test_node) ]
        tuples=[]
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite (self,site_spec)
            for node_spec in site_spec['nodes']:
                test_node = TestNode (self, test_site, node_spec)
                if not test_node.is_real():
                    tuples.append( (test_node.host_box(),test_node) )
        # transform into a dict { 'host_box' -> [ test_node .. ] }
        result = {}
        for (box,node) in tuples:
            if not result.has_key(box):
                result[box]=[node]
            else:
                result[box].append(node)
        return result
                    
    # a step for checking this stuff
    def show_boxes (self):
        for (box,nodes) in self.gather_hostBoxes().iteritems():
            print box,":"," + ".join( [ node.name() for node in nodes ] )
        return True

    # make this a valid step
    def kill_all_qemus(self):
        # this is the brute force version, kill all qemus on that host box
        for (box,nodes) in self.gather_hostBoxes().iteritems():
            # pass the first nodename, as we don't push template-qemu on testboxes
            nodedir=nodes[0].nodedir()
            TestBox(box,self.options.buildname).kill_all_qemus(nodedir)
        return True

    # make this a valid step
    def list_all_qemus(self):
        for (box,nodes) in self.gather_hostBoxes().iteritems():
            # this is the brute force version, kill all qemus on that host box
            TestBox(box,self.options.buildname).list_all_qemus()
        return True

    # kill only the right qemus
    def list_qemus(self):
        for (box,nodes) in self.gather_hostBoxes().iteritems():
            # the fine-grain version
            for node in nodes:
                node.list_qemu()
        return True

    # kill only the right qemus
    def kill_qemus(self):
        for (box,nodes) in self.gather_hostBoxes().iteritems():
            # the fine-grain version
            for node in nodes:
                node.kill_qemu()
        return True


    ### utility methods for handling the pool of IP addresses allocated to plcs
    # Logic
    # (*) running plcs are recorded in the file named ~/running-test-plcs
    # (*) this file contains a line for each running plc, older first
    # (*) each line contains the vserver name + the hostname of the (vserver) testbox where it sits
    # (*) the free_tracker method performs a vserver stop on the oldest entry
    # (*) the record_tracker method adds an entry at the bottom of the file
    # (*) the cleanup_tracker method stops all known vservers and removes the tracker file

    TRACKER_FILE="~/running-test-plcs"

    def record_tracker (self):
        command="echo %s %s >> %s"%(self.vservername,self.test_ssh.hostname,TestPlc.TRACKER_FILE)
        (code,output) = utils.output_of (self.test_ssh.actual_command(command))
        if code != 0:
            print "WARNING : COULD NOT record_tracker %s as a running plc on %s"%(self.vservername,self.test_ssh.hostname)
            return False
        print "Recorded %s in running plcs on host %s"%(self.vservername,self.test_ssh.hostname)
        return True

    def free_tracker (self):
        command="head -1 %s"%TestPlc.TRACKER_FILE
        (code,line) = utils.output_of(self.test_ssh.actual_command(command))
        if code != 0:
            print "No entry found in %s on %s"%(TestPlc.TRACKER_FILE,self.test_ssh.hostname)
            return False
        try:
            [vserver_to_stop,hostname] = line.split()
        except:
            print "WARNING: free_tracker: Could not parse %s - skipped"%TestPlc.TRACKER_FILE
            return False
        stop_command = "vserver --silent %s stop"%vserver_to_stop
        utils.system(self.test_ssh.actual_command(stop_command))
        x=TestPlc.TRACKER_FILE
        flush_command = "tail --lines=+2 %s > %s.tmp ; mv %s.tmp %s"%(x,x,x,x)
        utils.system(self.test_ssh.actual_command(flush_command))
        return True

    # this should/could stop only the ones in TRACKER_FILE if that turns out to be reliable
    def cleanup_tracker (self):
        stop_all = "cd /vservers ; for i in * ; do vserver --silent $i stop ; done"
        utils.system(self.test_ssh.actual_command(stop_all))
        clean_tracker = "rm -f %s"%TestPlc.TRACKER_FILE
        utils.system(self.test_ssh.actual_command(clean_tracker))

    def uninstall(self):
        self.run_in_host("vserver --silent %s delete"%self.vservername)
        return True

    ### install
    def install(self):
        if self.is_local():
            # a full path for the local calls
            build_dir=os.path.dirname(sys.argv[0])
            # sometimes this is empty - set to "." in such a case
            if not build_dir: build_dir="."
            build_dir += "/build"
        else:
            # use a standard name - will be relative to remote buildname
            build_dir="build"
	# run checkout in any case - would do an update if already exists
        build_checkout = "svn checkout %s %s"%(self.options.build_url,build_dir)
        if self.run_in_host(build_checkout) != 0:
            return False
        # the repo url is taken from arch-rpms-url 
        # with the last step (i386.) removed
        repo_url = self.options.arch_rpms_url
        for level in [ 'arch' ]:
	    repo_url = os.path.dirname(repo_url)
        if self.options.arch == "i386":
            personality_option="-p linux32"
        else:
            personality_option="-p linux64"
        script="vtest-init-vserver.sh"
        vserver_name = self.vservername
        vserver_options="--netdev eth0 --interface %s"%self.vserverip
        try:
            vserver_hostname=socket.gethostbyaddr(self.vserverip)[0]
            vserver_options += " --hostname %s"%vserver_hostname
        except:
            pass
        create_vserver="%(build_dir)s/%(script)s %(personality_option)s %(vserver_name)s %(repo_url)s -- %(vserver_options)s"%locals()
        return self.run_in_host(create_vserver) == 0

    ### install_rpm 
    def install_rpm(self):
        return self.run_in_guest("yum -y install myplc-native")==0

    ### 
    def configure(self):
        tmpname='%s.plc-config-tty'%(self.name())
        fileconf=open(tmpname,'w')
        for var in [ 'PLC_NAME',
                     'PLC_ROOT_PASSWORD',
                     'PLC_ROOT_USER',
                     'PLC_MAIL_ENABLED',
                     'PLC_MAIL_SUPPORT_ADDRESS',
                     'PLC_DB_HOST',
                     'PLC_API_HOST',
                     'PLC_WWW_HOST',
                     'PLC_BOOT_HOST',
                     'PLC_NET_DNS1',
                     'PLC_NET_DNS2']:
            fileconf.write ('e %s\n%s\n'%(var,self.plc_spec[var]))
        fileconf.write('w\n')
        fileconf.write('q\n')
        fileconf.close()
        utils.system('cat %s'%tmpname)
        self.run_in_guest_piped('cat %s'%tmpname,'plc-config-tty')
        utils.system('rm %s'%tmpname)
        return True

    def start(self):
        self.run_in_guest('service plc start')
        return True

    def stop(self):
        self.run_in_guest('service plc stop')
        return True
        
    def vs_start (self):
        self.start_guest()
        return True

    # could use a TestKey class
    def store_keys(self):
        for key_spec in self.plc_spec['keys']:
		TestKey(self,key_spec).store_key()
        return True

    def clean_keys(self):
        utils.system("rm -rf %s/keys/"%os.path(sys.argv[0]))

    def sites (self):
        return self.do_sites()
    
    def clean_sites (self):
        return self.do_sites(action="delete")
    
    def do_sites (self,action="add"):
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite (self,site_spec)
            if (action != "add"):
                utils.header("Deleting site %s in %s"%(test_site.name(),self.name()))
                test_site.delete_site()
                # deleted with the site
                #test_site.delete_users()
                continue
            else:
                utils.header("Creating site %s & users in %s"%(test_site.name(),self.name()))
                test_site.create_site()
                test_site.create_users()
        return True

    def clean_all_sites (self):
        print 'auth_root',self.auth_root()
        site_ids = [s['site_id'] for s in self.apiserver.GetSites(self.auth_root(), {}, ['site_id'])]
        for site_id in site_ids:
            print 'Deleting site_id',site_id
            self.apiserver.DeleteSite(self.auth_root(),site_id)

    def nodes (self):
        return self.do_nodes()
    def clean_nodes (self):
        return self.do_nodes(action="delete")

    def do_nodes (self,action="add"):
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite (self,site_spec)
            if action != "add":
                utils.header("Deleting nodes in site %s"%test_site.name())
                for node_spec in site_spec['nodes']:
                    test_node=TestNode(self,test_site,node_spec)
                    utils.header("Deleting %s"%test_node.name())
                    test_node.delete_node()
            else:
                utils.header("Creating nodes for site %s in %s"%(test_site.name(),self.name()))
                for node_spec in site_spec['nodes']:
                    utils.pprint('Creating node %s'%node_spec,node_spec)
                    test_node = TestNode (self,test_site,node_spec)
                    test_node.create_node ()
        return True

    def nodegroups (self):
        return self.do_nodegroups("add")
    def clean_nodegroups (self):
        return self.do_nodegroups("delete")

    # create nodegroups if needed, and populate
    def do_nodegroups (self, action="add"):
        # 1st pass to scan contents
        groups_dict = {}
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite (self,site_spec)
            for node_spec in site_spec['nodes']:
                test_node=TestNode (self,test_site,node_spec)
                if node_spec.has_key('nodegroups'):
                    nodegroupnames=node_spec['nodegroups']
                    if isinstance(nodegroupnames,StringTypes):
                        nodegroupnames = [ nodegroupnames ]
                    for nodegroupname in nodegroupnames:
                        if not groups_dict.has_key(nodegroupname):
                            groups_dict[nodegroupname]=[]
                        groups_dict[nodegroupname].append(test_node.name())
        auth=self.auth_root()
        overall = True
        for (nodegroupname,group_nodes) in groups_dict.iteritems():
            if action == "add":
                print 'nodegroups:','dealing with nodegroup',nodegroupname,'on nodes',group_nodes
                # first, check if the nodetagtype is here
                tag_types = self.apiserver.GetTagTypes(auth,{'tagname':nodegroupname})
                if tag_types:
                    tag_type_id = tag_types[0]['tag_type_id']
                else:
                    tag_type_id = self.apiserver.AddTagType(auth,
                                                            {'tagname':nodegroupname,
                                                             'description': 'for nodegroup %s'%nodegroupname,
                                                             'category':'test',
                                                             'min_role_id':10})
                print 'located tag (type)',nodegroupname,'as',tag_type_id
                # create nodegroup
                nodegroups = self.apiserver.GetNodeGroups (auth, {'groupname':nodegroupname})
                if not nodegroups:
                    self.apiserver.AddNodeGroup(auth, nodegroupname, tag_type_id, 'yes')
                    print 'created nodegroup',nodegroupname,'from tagname',nodegroupname,'and value','yes'
                # set node tag on all nodes, value='yes'
                for nodename in group_nodes:
                    try:
                        self.apiserver.AddNodeTag(auth, nodename, nodegroupname, "yes")
                    except:
                        traceback.print_exc()
                        print 'node',nodename,'seems to already have tag',nodegroupname
                    # check anyway
                    try:
                        expect_yes = self.apiserver.GetNodeTags(auth,
                                                                {'hostname':nodename,
                                                                 'tagname':nodegroupname},
                                                                ['tagvalue'])[0]['tagvalue']
                        if expect_yes != "yes":
                            print 'Mismatch node tag on node',nodename,'got',expect_yes
                            overall=False
                    except:
                        if not self.options.dry_run:
                            print 'Cannot find tag',nodegroupname,'on node',nodename
                            overall = False
            else:
                try:
                    print 'cleaning nodegroup',nodegroupname
                    self.apiserver.DeleteNodeGroup(auth,nodegroupname)
                except:
                    traceback.print_exc()
                    overall=False
        return overall

    def all_hostnames (self) :
        hostnames = []
        for site_spec in self.plc_spec['sites']:
            hostnames += [ node_spec['node_fields']['hostname'] \
                           for node_spec in site_spec['nodes'] ]
        return hostnames

    # gracetime : during the first <gracetime> minutes nothing gets printed
    def do_nodes_booted (self, minutes, gracetime,period=15):
        if self.options.dry_run:
            print 'dry_run'
            return True
        # compute timeout
        timeout = datetime.datetime.now()+datetime.timedelta(minutes=minutes)
        graceout = datetime.datetime.now()+datetime.timedelta(minutes=gracetime)
        # the nodes that haven't checked yet - start with a full list and shrink over time
        tocheck = self.all_hostnames()
        utils.header("checking nodes %r"%tocheck)
        # create a dict hostname -> status
        status = dict ( [ (hostname,'undef') for hostname in tocheck ] )
        while tocheck:
            # get their status
            tocheck_status=self.apiserver.GetNodes(self.auth_root(), tocheck, ['hostname','boot_state' ] )
            # update status
            for array in tocheck_status:
                hostname=array['hostname']
                boot_state=array['boot_state']
                if boot_state == 'boot':
                    utils.header ("%s has reached the 'boot' state"%hostname)
                else:
                    # if it's a real node, never mind
                    (site_spec,node_spec)=self.locate_hostname(hostname)
                    if TestNode.is_real_model(node_spec['node_fields']['model']):
                        utils.header("WARNING - Real node %s in %s - ignored"%(hostname,boot_state))
                        # let's cheat
                        boot_state = 'boot'
                    elif datetime.datetime.now() > graceout:
                        utils.header ("%s still in '%s' state"%(hostname,boot_state))
                        graceout=datetime.datetime.now()+datetime.timedelta(1)
                status[hostname] = boot_state
            # refresh tocheck
            tocheck = [ hostname for (hostname,boot_state) in status.iteritems() if boot_state != 'boot' ]
            if not tocheck:
                return True
            if datetime.datetime.now() > timeout:
                for hostname in tocheck:
                    utils.header("FAILURE due to %s in '%s' state"%(hostname,status[hostname]))
                return False
            # otherwise, sleep for a while
            time.sleep(period)
        # only useful in empty plcs
        return True

    def nodes_booted(self):
        return self.do_nodes_booted(minutes=20,gracetime=15)

    def do_nodes_ssh(self,minutes,gracetime,period=15):
        # compute timeout
        timeout = datetime.datetime.now()+datetime.timedelta(minutes=minutes)
        graceout = datetime.datetime.now()+datetime.timedelta(minutes=gracetime)
        tocheck = self.all_hostnames()
#        self.scan_publicKeys(tocheck)
        utils.header("checking Connectivity on nodes %r"%tocheck)
        while tocheck:
            for hostname in tocheck:
                # try to ssh in nodes
                node_test_ssh = TestSsh (hostname,key="/etc/planetlab/root_ssh_key.rsa")
                success=self.run_in_guest(node_test_ssh.actual_command("hostname"))==0
                if success:
                    utils.header('The node %s is sshable -->'%hostname)
                    # refresh tocheck
                    tocheck.remove(hostname)
                else:
                    # we will have tried real nodes once, in case they're up - but if not, just skip
                    (site_spec,node_spec)=self.locate_hostname(hostname)
                    if TestNode.is_real_model(node_spec['node_fields']['model']):
                        utils.header ("WARNING : check ssh access into real node %s - skipped"%hostname)
			tocheck.remove(hostname)
                    elif datetime.datetime.now() > graceout:
                        utils.header("Could not ssh-enter root context on %s"%hostname)
            if  not tocheck:
                return True
            if datetime.datetime.now() > timeout:
                for hostname in tocheck:
                    utils.header("FAILURE to ssh into %s"%hostname)
                return False
            # otherwise, sleep for a while
            time.sleep(period)
        # only useful in empty plcs
        return True
        
    def nodes_ssh(self):
        return self.do_nodes_ssh(minutes=10,gracetime=5)
    
    @node_mapper
    def init_node (self): pass
    @node_mapper
    def bootcd (self): pass
    @node_mapper
    def configure_qemu (self): pass
    @node_mapper
    def reinstall_node (self): pass
    @node_mapper
    def export_qemu (self): pass
        
    def do_check_initscripts(self):
        overall = True
        for slice_spec in self.plc_spec['slices']:
            if not slice_spec.has_key('initscriptname'):
                continue
            initscript=slice_spec['initscriptname']
            for nodename in slice_spec['nodenames']:
                (site,node) = self.locate_node (nodename)
                # xxx - passing the wrong site - probably harmless
                test_site = TestSite (self,site)
                test_slice = TestSlice (self,test_site,slice_spec)
                test_node = TestNode (self,test_site,node)
                test_sliver = TestSliver (self, test_node, test_slice)
                if not test_sliver.check_initscript(initscript):
                    overall = False
        return overall
	    
    def check_initscripts(self):
	    return self.do_check_initscripts()
	            
    def initscripts (self):
        for initscript in self.plc_spec['initscripts']:
            utils.pprint('Adding Initscript in plc %s'%self.plc_spec['name'],initscript)
            self.apiserver.AddInitScript(self.auth_root(),initscript['initscript_fields'])
        return True

    def clean_initscripts (self):
        for initscript in self.plc_spec['initscripts']:
            initscript_name = initscript['initscript_fields']['name']
            print('Attempting to delete %s in plc %s'%(initscript_name,self.plc_spec['name']))
            try:
                self.apiserver.DeleteInitScript(self.auth_root(),initscript_name)
                print initscript_name,'deleted'
            except:
                print 'deletion went wrong - probably did not exist'
        return True

    def slices (self):
        return self.do_slices()

    def clean_slices (self):
        return self.do_slices("delete")

    def do_slices (self,  action="add"):
        for slice in self.plc_spec['slices']:
            site_spec = self.locate_site (slice['sitename'])
            test_site = TestSite(self,site_spec)
            test_slice=TestSlice(self,test_site,slice)
            if action != "add":
                utils.header("Deleting slices in site %s"%test_site.name())
                test_slice.delete_slice()
            else:    
                utils.pprint("Creating slice",slice)
                test_slice.create_slice()
                utils.header('Created Slice %s'%slice['slice_fields']['name'])
        return True
        
    @slice_mapper_options
    def check_slice(self): pass

    @node_mapper
    def clear_known_hosts (self): pass
    
    @node_mapper
    def start_node (self) : pass

    def all_sliver_objs (self):
        result=[]
        for slice_spec in self.plc_spec['slices']:
            slicename = slice_spec['slice_fields']['name']
            for nodename in slice_spec['nodenames']:
                result.append(self.locate_sliver_obj (nodename,slicename))
        return result

    def locate_sliver_obj (self,nodename,slicename):
        (site,node) = self.locate_node(nodename)
        slice = self.locate_slice (slicename)
        # build objects
        test_site = TestSite (self, site)
        test_node = TestNode (self, test_site,node)
        # xxx the slice site is assumed to be the node site - mhh - probably harmless
        test_slice = TestSlice (self, test_site, slice)
        return TestSliver (self, test_node, test_slice)

    def check_tcp (self):
        specs = self.plc_spec['tcp_test']
        overall=True
        for spec in specs:
            port = spec['port']
            # server side
            s_test_sliver = self.locate_sliver_obj (spec['server_node'],spec['server_slice'])
            if not s_test_sliver.run_tcp_server(port,timeout=10):
                overall=False
                break

            # idem for the client side
            c_test_sliver = self.locate_sliver_obj(spec['server_node'],spec['server_slice'])
            if not c_test_sliver.run_tcp_client(s_test_sliver.test_node.name(),port):
                overall=False
        return overall

    def plcsh_stress_test (self):
        # install the stress-test in the plc image
        location = "/usr/share/plc_api/plcsh-stress-test.py"
        remote="/vservers/%s/%s"%(self.vservername,location)
        self.test_ssh.copy_abs("plcsh-stress-test.py",remote)
        command = location
        command += " -- --check"
        if self.options.small_test:
            command +=  " --tiny"
        return ( self.run_in_guest(command) == 0)

    def gather_logs (self):
        # (1) get the plc's /var/log and store it locally in logs/myplc.var-log.<plcname>/*
        # (2) get all the nodes qemu log and store it as logs/node.qemu.<node>.log
        # (3) get the nodes /var/log and store is as logs/node.var-log.<node>/*
        # (4) as far as possible get the slice's /var/log as logs/sliver.var-log.<sliver>/*
        # (1)
        print "-------------------- TestPlc.gather_logs : PLC's /var/log"
        self.gather_var_logs ()
        # (2) 
        print "-------------------- TestPlc.gather_logs : nodes's QEMU logs"
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite (self,site_spec)
            for node_spec in site_spec['nodes']:
                test_node=TestNode(self,test_site,node_spec)
                test_node.gather_qemu_logs()
        # (3)
        print "-------------------- TestPlc.gather_logs : nodes's /var/log"
        self.gather_nodes_var_logs()
        # (4)
        print "-------------------- TestPlc.gather_logs : sample sliver's /var/log"
        self.gather_slivers_var_logs()
        return True

    def gather_slivers_var_logs(self):
        for test_sliver in self.all_sliver_objs():
            remote = test_sliver.tar_var_logs()
            utils.system("mkdir -p logs/sliver.var-log.%s"%test_sliver.name())
            command = remote + " | tar -C logs/sliver.var-log.%s -xf -"%test_sliver.name()
            utils.system(command)
        return True

    def gather_var_logs (self):
        utils.system("mkdir -p logs/myplc.var-log.%s"%self.name())
        to_plc = self.actual_command_in_guest("tar -C /var/log/ -cf - .")        
        command = to_plc + "| tar -C logs/myplc.var-log.%s -xf -"%self.name()
        utils.system(command)
        command = "chmod a+r,a+x logs/myplc.var-log.%s/httpd"%self.name()
        utils.system(command)

    def gather_nodes_var_logs (self):
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite (self,site_spec)
            for node_spec in site_spec['nodes']:
                test_node=TestNode(self,test_site,node_spec)
                test_ssh = TestSsh (test_node.name(),key="/etc/planetlab/root_ssh_key.rsa")
                to_plc = self.actual_command_in_guest ( test_ssh.actual_command("tar -C /var/log -cf - ."))
                command = to_plc + "| tar -C logs/node.var-log.%s -xf -"%test_node.name()
                utils.system("mkdir -p logs/node.var-log.%s"%test_node.name())
                utils.system(command)


    # returns the filename to use for sql dump/restore, using options.dbname if set
    def dbfile (self, database):
        # uses options.dbname if it is found
        try:
            name=self.options.dbname
            if not isinstance(name,StringTypes):
                raise Exception
        except:
            t=datetime.datetime.now()
            d=t.date()
            name=str(d)
        return "/root/%s-%s.sql"%(database,name)

    def db_dump(self):
        dump=self.dbfile("planetab4")
        self.run_in_guest('pg_dump -U pgsqluser planetlab4 -f '+ dump)
        utils.header('Dumped planetlab4 database in %s'%dump)
        return True

    def db_restore(self):
        dump=self.dbfile("planetab4")
        ##stop httpd service
        self.run_in_guest('service httpd stop')
        # xxx - need another wrapper
        self.run_in_guest_piped('echo drop database planetlab4','psql --user=pgsqluser template1')
        self.run_in_guest('createdb -U postgres --encoding=UNICODE --owner=pgsqluser planetlab4')
        self.run_in_guest('psql -U pgsqluser planetlab4 -f '+dump)
        ##starting httpd service
        self.run_in_guest('service httpd start')

        utils.header('Database restored from ' + dump)

    @standby_generic 
    def standby_1(): pass
    @standby_generic 
    def standby_2(): pass
    @standby_generic 
    def standby_3(): pass
    @standby_generic 
    def standby_4(): pass
    @standby_generic 
    def standby_5(): pass
    @standby_generic 
    def standby_6(): pass
    @standby_generic 
    def standby_7(): pass
    @standby_generic 
    def standby_8(): pass
    @standby_generic 
    def standby_9(): pass
    @standby_generic 
    def standby_10(): pass
    @standby_generic 
    def standby_11(): pass
    @standby_generic 
    def standby_12(): pass
    @standby_generic 
    def standby_13(): pass
    @standby_generic 
    def standby_14(): pass
    @standby_generic 
    def standby_15(): pass
    @standby_generic 
    def standby_16(): pass
    @standby_generic 
    def standby_17(): pass
    @standby_generic 
    def standby_18(): pass
    @standby_generic 
    def standby_19(): pass
    @standby_generic 
    def standby_20(): pass
    
