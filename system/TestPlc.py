# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
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
from TestSliceSfa import TestSliceSfa
from TestUserSfa import TestUserSfa

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
    # restore the doc text
    actual.__doc__=method.__doc__
    return actual

def slice_mapper (method):
    def actual(self):
        overall=True
        slice_method = TestSlice.__dict__[method.__name__]
        for slice_spec in self.plc_spec['slices']:
            site_spec = self.locate_site (slice_spec['sitename'])
            test_site = TestSite(self,site_spec)
            test_slice=TestSlice(self,test_site,slice_spec)
            if not slice_method(test_slice,self.options): overall=False
        return overall
    # restore the doc text
    actual.__doc__=method.__doc__
    return actual

def slice_sfa_mapper (method):
    def actual(self):
        overall=True
        slice_method = TestSliceSfa.__dict__[method.__name__]
        for slice_spec in self.plc_spec['sfa']['sfa_slice_specs']:
            site_spec = self.locate_site (slice_spec['sitename'])
            test_site = TestSite(self,site_spec)
            test_slice=TestSliceSfa(self,test_site,slice_spec)
            if not slice_method(test_slice,self.options): overall=False
        return overall
    # restore the doc text
    actual.__doc__=method.__doc__
    return actual

SEP='<sep>'
SEPSFA='<sep_sfa>'

class TestPlc:

    default_steps = [
        'display', 'resources_pre', SEP,
        'delete_vs','create_vs','install', 'configure', 'start', SEP,
        'fetch_keys', 'store_keys', 'clear_known_hosts', SEP,
        'initscripts', 'sites', 'nodes', 'slices', 'nodegroups', 'leases', SEP,
        'reinstall_node', 'init_node','bootcd', 'configure_qemu', 'export_qemu', 'kill_all_qemus', 'start_node', SEP,
	'install_sfa', 'configure_sfa', 'cross_configure_sfa', 'import_sfa', 'start_sfa', SEPSFA,
        'configure_sfi@1', 'add_user_sfa@1', 'add_sfa@1', 'create_sfa@1', SEPSFA, 
        'update_user_sfa@1', 'update_sfa@1', 'view_sfa@1', SEPSFA,
        'install_unittest_sfa','unittest_sfa',SEPSFA,
        # we used to run plcsh_stress_test, and then nodes_ssh_debug and nodes_ssh_boot
        # but as the stress test might take a while, we sometimes missed the debug mode..
        'nodes_ssh_debug', 'plcsh_stress_test@1', SEP,
        'nodes_ssh_boot', 'check_slice', 'check_initscripts', SEP,
        'check_slice_sfa@1', 'delete_slice_sfa@1', 'delete_user_sfa@1', SEPSFA,
        'check_tcp',  'check_hooks@1',  SEP,
        'force_gather_logs', 'force_resources_post', SEP,
        ]
    other_steps = [ 
        'show_boxes', 'resources_list','resources_release','resources_release_plc','resources_release_qemu',SEP,
        'stop', 'vs_start', SEP,
        'clean_initscripts', 'clean_nodegroups','clean_all_sites', SEP,
        'clean_sites', 'clean_nodes', 'clean_slices', 'clean_keys', SEP,
        'clean_leases', 'list_leases', SEP,
        'populate' , SEP,
        'list_all_qemus', 'list_qemus', 'kill_qemus', SEP,
        'plcclean_sfa', 'dbclean_sfa', 'stop_sfa','uninstall_sfa', 'clean_sfi', SEP,
        'db_dump' , 'db_restore', SEP,
        'standby_1 through 20',SEP,
        ]

    @staticmethod
    def printable_steps (list):
        single_line=" ".join(list)+" "
        return single_line.replace(" "+SEP+" "," \\\n").replace(" "+SEPSFA+" "," \\\n")
    @staticmethod
    def valid_step (step):
        return step != SEP and step != SEPSFA

    # turn off the sfa-related steps when build has skipped SFA
    # this is originally for centos5 as recent SFAs won't build on this platformb
    @staticmethod
    def check_whether_build_has_sfa (rpms_url):
        # warning, we're now building 'sface' so let's be a bit more picky
        retcod=os.system ("curl --silent %s/ | grep -q sfa-"%rpms_url)
        # full builds are expected to return with 0 here
        if retcod!=0:
            # move all steps containing 'sfa' from default_steps to other_steps
            sfa_steps= [ step for step in TestPlc.default_steps if step.find('sfa')>=0 ]
            TestPlc.other_steps += sfa_steps
            for step in sfa_steps: TestPlc.default_steps.remove(step)

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

    def locate_first_node(self):
        nodename=self.plc_spec['slices'][0]['nodenames'][0]
        (site,node) = self.locate_node(nodename)
        test_site = TestSite (self, site)
        test_node = TestNode (self, test_site,node)
        return test_node

    def locate_first_sliver (self):
        slice_spec=self.plc_spec['slices'][0]
        slicename=slice_spec['slice_fields']['name']
        nodename=slice_spec['nodenames'][0]
        return self.locate_sliver_obj(nodename,slicename)

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
        'print summary of nodes location'
        for (box,nodes) in self.gather_hostBoxes().iteritems():
            print box,":"," + ".join( [ node.name() for node in nodes ] )
        return True

    # make this a valid step
    def kill_all_qemus(self):
        'kill all qemu instances on the qemu boxes involved by this setup'
        # this is the brute force version, kill all qemus on that host box
        for (box,nodes) in self.gather_hostBoxes().iteritems():
            # pass the first nodename, as we don't push template-qemu on testboxes
            nodedir=nodes[0].nodedir()
            TestBox(box,self.options.buildname).kill_all_qemus(nodedir)
        return True

    # make this a valid step
    def list_all_qemus(self):
        'list all qemu instances on the qemu boxes involved by this setup'
        for (box,nodes) in self.gather_hostBoxes().iteritems():
            # this is the brute force version, kill all qemus on that host box
            TestBox(box,self.options.buildname).list_all_qemus()
        return True

    # kill only the right qemus
    def list_qemus(self):
        'list qemu instances for our nodes'
        for (box,nodes) in self.gather_hostBoxes().iteritems():
            # the fine-grain version
            for node in nodes:
                node.list_qemu()
        return True

    # kill only the right qemus
    def kill_qemus(self):
        'kill the qemu instances for our nodes'
        for (box,nodes) in self.gather_hostBoxes().iteritems():
            # the fine-grain version
            for node in nodes:
                node.kill_qemu()
        return True

    #################### display config
    def display (self):
        "show test configuration after localization"
        self.display_pass (1)
        self.display_pass (2)
        return True

    # entry point
    always_display_keys=['PLC_WWW_HOST','nodes','sites',]
    def display_pass (self,passno):
        for (key,val) in self.plc_spec.iteritems():
            if not self.options.verbose and key not in TestPlc.always_display_keys: continue
            if passno == 2:
                if key == 'sites':
                    for site in val:
                        self.display_site_spec(site)
                        for node in site['nodes']:
                            self.display_node_spec(node)
                elif key=='initscripts':
                    for initscript in val:
                        self.display_initscript_spec (initscript)
                elif key=='slices':
                    for slice in val:
                        self.display_slice_spec (slice)
                elif key=='keys':
                    for key in val:
                        self.display_key_spec (key)
            elif passno == 1:
                if key not in ['sites','initscripts','slices','keys', 'sfa']:
                    print '+   ',key,':',val

    def display_site_spec (self,site):
        print '+ ======== site',site['site_fields']['name']
        for (k,v) in site.iteritems():
            if not self.options.verbose and k not in TestPlc.always_display_keys: continue
            if k=='nodes':
                if v: 
                    print '+       ','nodes : ',
                    for node in v:  
                        print node['node_fields']['hostname'],'',
                    print ''
            elif k=='users':
                if v: 
                    print '+       users : ',
                    for user in v:  
                        print user['name'],'',
                    print ''
            elif k == 'site_fields':
                print '+       login_base',':',v['login_base']
            elif k == 'address_fields':
                pass
            else:
                print '+       ',
                utils.pprint(k,v)
        
    def display_initscript_spec (self,initscript):
        print '+ ======== initscript',initscript['initscript_fields']['name']

    def display_key_spec (self,key):
        print '+ ======== key',key['name']

    def display_slice_spec (self,slice):
        print '+ ======== slice',slice['slice_fields']['name']
        for (k,v) in slice.iteritems():
            if k=='nodenames':
                if v: 
                    print '+       nodes : ',
                    for nodename in v:  
                        print nodename,'',
                    print ''
            elif k=='usernames':
                if v: 
                    print '+       users : ',
                    for username in v:  
                        print username,'',
                    print ''
            elif k=='slice_fields':
                print '+       fields',':',
                print 'max_nodes=',v['max_nodes'],
                print ''
            else:
                print '+       ',k,v

    def display_node_spec (self,node):
        print "+           node=%s host_box=%s"%(node['name'],node['host_box']),
        print "hostname=",node['node_fields']['hostname'],
        print "ip=",node['interface_fields']['ip']
        if self.options.verbose:
            utils.pprint("node details",node,depth=3)

    # another entry point for just showing the boxes involved
    def display_mapping (self):
        TestPlc.display_mapping_plc(self.plc_spec)
        return True

    @staticmethod
    def display_mapping_plc (plc_spec):
        print '+ MyPLC',plc_spec['name']
        print '+\tvserver address = root@%s:/vservers/%s'%(plc_spec['hostname'],plc_spec['vservername'])
        print '+\tIP = %s/%s'%(plc_spec['PLC_API_HOST'],plc_spec['vserverip'])
        for site_spec in plc_spec['sites']:
            for node_spec in site_spec['nodes']:
                TestPlc.display_mapping_node(node_spec)

    @staticmethod
    def display_mapping_node (node_spec):
        print '+   NODE %s'%(node_spec['name'])
        print '+\tqemu box %s'%node_spec['host_box']
        print '+\thostname=%s'%node_spec['node_fields']['hostname']

    def resources_pre (self):
        "run site-dependant pre-test script as defined in LocalTestResources"
        from LocalTestResources import local_resources
        return local_resources.step_pre(self)
 
    def resources_post (self):
        "run site-dependant post-test script as defined in LocalTestResources"
        from LocalTestResources import local_resources
        return local_resources.step_post(self)
 
    def resources_list (self):
        "run site-dependant list script as defined in LocalTestResources"
        from LocalTestResources import local_resources
        return local_resources.step_list(self)
 
    def resources_release (self):
        "run site-dependant release script as defined in LocalTestResources"
        from LocalTestResources import local_resources
        return local_resources.step_release(self)
 
    def resources_release_plc (self):
        "run site-dependant release script as defined in LocalTestResources"
        from LocalTestResources import local_resources
        return local_resources.step_release_plc(self)
 
    def resources_release_qemu (self):
        "run site-dependant release script as defined in LocalTestResources"
        from LocalTestResources import local_resources
        return local_resources.step_release_qemu(self)
 
    def delete_vs(self):
        "vserver delete the test myplc"
        self.run_in_host("vserver --silent %s delete"%self.vservername)
        return True

    ### install
    # historically the build was being fetched by the tests
    # now the build pushes itself as a subdir of the tests workdir
    # so that the tests do not have to worry about extracting the build (svn, git, or whatever)
    def create_vs (self):
        "vserver creation (no install done)"
        # push the local build/ dir to the testplc box 
        if self.is_local():
            # a full path for the local calls
            build_dir=os.path.dirname(sys.argv[0])
            # sometimes this is empty - set to "." in such a case
            if not build_dir: build_dir="."
            build_dir += "/build"
        else:
            # use a standard name - will be relative to remote buildname
            build_dir="build"
            # remove for safety; do *not* mkdir first, otherwise we end up with build/build/
            self.test_ssh.rmdir(build_dir)
            self.test_ssh.copy(build_dir,recursive=True)
        # the repo url is taken from arch-rpms-url 
        # with the last step (i386) removed
        repo_url = self.options.arch_rpms_url
        for level in [ 'arch' ]:
	    repo_url = os.path.dirname(repo_url)
        # pass the vbuild-nightly options to vtest-init-vserver
        test_env_options=""
        test_env_options += " -p %s"%self.options.personality
        test_env_options += " -d %s"%self.options.pldistro
        test_env_options += " -f %s"%self.options.fcdistro
        script="vtest-init-vserver.sh"
        vserver_name = self.vservername
        vserver_options="--netdev eth0 --interface %s"%self.vserverip
        try:
            vserver_hostname=socket.gethostbyaddr(self.vserverip)[0]
            vserver_options += " --hostname %s"%vserver_hostname
        except:
            print "Cannot reverse lookup %s"%self.vserverip
            print "This is considered fatal, as this might pollute the test results"
            return False
        create_vserver="%(build_dir)s/%(script)s %(test_env_options)s %(vserver_name)s %(repo_url)s -- %(vserver_options)s"%locals()
        return self.run_in_host(create_vserver) == 0

    ### install_rpm 
    def install(self):
        "yum install myplc, noderepo, and the plain bootstrapfs"

        # workaround for getting pgsql8.2 on centos5
        if self.options.fcdistro == "centos5":
            self.run_in_guest("rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-3.noarch.rpm")

        # compute nodefamily
        if self.options.personality == "linux32":
            arch = "i386"
        elif self.options.personality == "linux64":
            arch = "x86_64"
        else:
            raise Exception, "Unsupported personality %r"%self.options.personality
        nodefamily="%s-%s-%s"%(self.options.pldistro,self.options.fcdistro,arch)

        pkgs_list=[]
        pkgs_list.append ("slicerepo-%s"%nodefamily)
        pkgs_list.append ("myplc")
        pkgs_list.append ("noderepo-%s"%nodefamily)
        pkgs_list.append ("bootstrapfs-%s-plain"%nodefamily)
        pkgs_string=" ".join(pkgs_list)
        self.run_in_guest("yum -y install %s"%pkgs_string)
        return self.run_in_guest("rpm -q %s"%pkgs_string)==0

    ### 
    def configure(self):
        "run plc-config-tty"
        tmpname='%s.plc-config-tty'%(self.name())
        fileconf=open(tmpname,'w')
        for var in [ 'PLC_NAME',
                     'PLC_ROOT_USER',
                     'PLC_ROOT_PASSWORD',
                     'PLC_SLICE_PREFIX',
                     'PLC_MAIL_ENABLED',
                     'PLC_MAIL_SUPPORT_ADDRESS',
                     'PLC_DB_HOST',
                     'PLC_DB_PASSWORD',
		     # Above line was added for integrating SFA Testing
                     'PLC_API_HOST',
                     'PLC_WWW_HOST',
                     'PLC_BOOT_HOST',
                     'PLC_NET_DNS1',
                     'PLC_NET_DNS2',
                     'PLC_RESERVATION_GRANULARITY',
                     'PLC_OMF_ENABLED',
                     ]:
            fileconf.write ('e %s\n%s\n'%(var,self.plc_spec[var]))
        fileconf.write('w\n')
        fileconf.write('q\n')
        fileconf.close()
        utils.system('cat %s'%tmpname)
        self.run_in_guest_piped('cat %s'%tmpname,'plc-config-tty')
        utils.system('rm %s'%tmpname)
        return True

    def start(self):
        "service plc start"
        self.run_in_guest('service plc start')
        return True

    def stop(self):
        "service plc stop"
        self.run_in_guest('service plc stop')
        return True
        
    def vs_start (self):
        "start the PLC vserver"
        self.start_guest()
        return True

    # stores the keys from the config for further use
    def store_keys(self):
        "stores test users ssh keys in keys/"
        for key_spec in self.plc_spec['keys']:
		TestKey(self,key_spec).store_key()
        return True

    def clean_keys(self):
        "removes keys cached in keys/"
        utils.system("rm -rf %s/keys/"%os.path(sys.argv[0]))

    # fetches the ssh keys in the plc's /etc/planetlab and stores them in keys/
    # for later direct access to the nodes
    def fetch_keys(self):
        "gets ssh keys in /etc/planetlab/ and stores them locally in keys/"
        dir="./keys"
        if not os.path.isdir(dir):
            os.mkdir(dir)
        vservername=self.vservername
        overall=True
        prefix = 'debug_ssh_key'
        for ext in [ 'pub', 'rsa' ] :
            src="/vservers/%(vservername)s/etc/planetlab/%(prefix)s.%(ext)s"%locals()
            dst="keys/%(vservername)s-debug.%(ext)s"%locals()
            if self.test_ssh.fetch(src,dst) != 0: overall=False
        return overall

    def sites (self):
        "create sites with PLCAPI"
        return self.do_sites()
    
    def clean_sites (self):
        "delete sites with PLCAPI"
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
        "Delete all sites in PLC, and related objects"
        print 'auth_root',self.auth_root()
        site_ids = [s['site_id'] for s in self.apiserver.GetSites(self.auth_root(), {}, ['site_id'])]
        for site_id in site_ids:
            print 'Deleting site_id',site_id
            self.apiserver.DeleteSite(self.auth_root(),site_id)

    def nodes (self):
        "create nodes with PLCAPI"
        return self.do_nodes()
    def clean_nodes (self):
        "delete nodes with PLCAPI"
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
        "create nodegroups with PLCAPI"
        return self.do_nodegroups("add")
    def clean_nodegroups (self):
        "delete nodegroups with PLCAPI"
        return self.do_nodegroups("delete")

    YEAR = 365*24*3600
    @staticmethod
    def translate_timestamp (start,grain,timestamp):
        if timestamp < TestPlc.YEAR:    return start+timestamp*grain
        else:                           return timestamp

    @staticmethod
    def timestamp_printable (timestamp):
        return time.strftime('%m-%d %H:%M:%S UTC',time.gmtime(timestamp))

    def leases(self):
        "create leases (on reservable nodes only, use e.g. run -c default -c resa)"
        now=int(time.time())
        grain=self.apiserver.GetLeaseGranularity(self.auth_root())
        print 'API answered grain=',grain
        start=(now/grain)*grain
        start += grain
        # find out all nodes that are reservable
        nodes=self.all_reservable_nodenames()
        if not nodes: 
            utils.header ("No reservable node found - proceeding without leases")
            return True
        ok=True
        # attach them to the leases as specified in plc_specs
        # this is where the 'leases' field gets interpreted as relative of absolute
        for lease_spec in self.plc_spec['leases']:
            # skip the ones that come with a null slice id
            if not lease_spec['slice']: continue
            lease_spec['t_from']=TestPlc.translate_timestamp(start,grain,lease_spec['t_from'])
            lease_spec['t_until']=TestPlc.translate_timestamp(start,grain,lease_spec['t_until'])
            lease_addition=self.apiserver.AddLeases(self.auth_root(),nodes,
                                                    lease_spec['slice'],lease_spec['t_from'],lease_spec['t_until'])
            if lease_addition['errors']:
                utils.header("Cannot create leases, %s"%lease_addition['errors'])
                ok=False
            else:
                utils.header('Leases on nodes %r for %s from %d (%s) until %d (%s)'%\
                              (nodes,lease_spec['slice'],
                               lease_spec['t_from'],TestPlc.timestamp_printable(lease_spec['t_from']),
                               lease_spec['t_until'],TestPlc.timestamp_printable(lease_spec['t_until'])))
                
        return ok

    def clean_leases (self):
        "remove all leases in the myplc side"
        lease_ids= [ l['lease_id'] for l in self.apiserver.GetLeases(self.auth_root())]
        utils.header("Cleaning leases %r"%lease_ids)
        self.apiserver.DeleteLeases(self.auth_root(),lease_ids)
        return True

    def list_leases (self):
        "list all leases known to the myplc"
        leases = self.apiserver.GetLeases(self.auth_root())
        now=int(time.time())
        for l in leases:
            current=l['t_until']>=now
            if self.options.verbose or current:
                utils.header("%s %s from %s until %s"%(l['hostname'],l['name'],
                                                       TestPlc.timestamp_printable(l['t_from']), 
                                                       TestPlc.timestamp_printable(l['t_until'])))
        return True

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
                                                                ['value'])[0]['value']
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

    # return a list of tuples (nodename,qemuname)
    def all_node_infos (self) :
        node_infos = []
        for site_spec in self.plc_spec['sites']:
            node_infos += [ (node_spec['node_fields']['hostname'],node_spec['host_box']) \
                                for node_spec in site_spec['nodes'] ]
        return node_infos
    
    def all_nodenames (self): return [ x[0] for x in self.all_node_infos() ]
    def all_reservable_nodenames (self): 
        res=[]
        for site_spec in self.plc_spec['sites']:
            for node_spec in site_spec['nodes']:
                node_fields=node_spec['node_fields']
                if 'node_type' in node_fields and node_fields['node_type']=='reservable':
                    res.append(node_fields['hostname'])
        return res

    # silent_minutes : during the first <silent_minutes> minutes nothing gets printed
    def nodes_check_boot_state (self, target_boot_state, timeout_minutes, silent_minutes,period=15):
        if self.options.dry_run:
            print 'dry_run'
            return True
        # compute timeout
        timeout = datetime.datetime.now()+datetime.timedelta(minutes=timeout_minutes)
        graceout = datetime.datetime.now()+datetime.timedelta(minutes=silent_minutes)
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
                if boot_state == target_boot_state:
                    utils.header ("%s has reached the %s state"%(hostname,target_boot_state))
                else:
                    # if it's a real node, never mind
                    (site_spec,node_spec)=self.locate_hostname(hostname)
                    if TestNode.is_real_model(node_spec['node_fields']['model']):
                        utils.header("WARNING - Real node %s in %s - ignored"%(hostname,boot_state))
                        # let's cheat
                        boot_state = target_boot_state
                    elif datetime.datetime.now() > graceout:
                        utils.header ("%s still in '%s' state"%(hostname,boot_state))
                        graceout=datetime.datetime.now()+datetime.timedelta(1)
                status[hostname] = boot_state
            # refresh tocheck
            tocheck = [ hostname for (hostname,boot_state) in status.iteritems() if boot_state != target_boot_state ]
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
        return self.nodes_check_boot_state('boot',timeout_minutes=30,silent_minutes=20)

    def check_nodes_ssh(self,debug,timeout_minutes,silent_minutes,period=15):
        # compute timeout
        timeout = datetime.datetime.now()+datetime.timedelta(minutes=timeout_minutes)
        graceout = datetime.datetime.now()+datetime.timedelta(minutes=silent_minutes)
        vservername=self.vservername
        if debug: 
            message="debug"
            local_key = "keys/%(vservername)s-debug.rsa"%locals()
        else: 
            message="boot"
	    local_key = "keys/key1.rsa"
        node_infos = self.all_node_infos()
        utils.header("checking ssh access (expected in %s mode) to nodes:"%message)
        for (nodename,qemuname) in node_infos:
            utils.header("hostname=%s -- qemubox=%s"%(nodename,qemuname))
        utils.header("max timeout is %d minutes, silent for %d minutes (period is %s)"%\
                         (timeout_minutes,silent_minutes,period))
        while node_infos:
            for node_info in node_infos:
                (hostname,qemuname) = node_info
                # try to run 'hostname' in the node
                command = TestSsh (hostname,key=local_key).actual_command("hostname;uname -a")
                # don't spam logs - show the command only after the grace period 
                success = utils.system ( command, silent=datetime.datetime.now() < graceout)
                if success==0:
                    utils.header('Successfully entered root@%s (%s)'%(hostname,message))
                    # refresh node_infos
                    node_infos.remove(node_info)
                else:
                    # we will have tried real nodes once, in case they're up - but if not, just skip
                    (site_spec,node_spec)=self.locate_hostname(hostname)
                    if TestNode.is_real_model(node_spec['node_fields']['model']):
                        utils.header ("WARNING : check ssh access into real node %s - skipped"%hostname)
			node_infos.remove(node_info)
            if  not node_infos:
                return True
            if datetime.datetime.now() > timeout:
                for (hostname,qemuname) in node_infos:
                    utils.header("FAILURE to ssh into %s (on %s)"%(hostname,qemuname))
                return False
            # otherwise, sleep for a while
            time.sleep(period)
        # only useful in empty plcs
        return True
        
    def nodes_ssh_debug(self):
        "Tries to ssh into nodes in debug mode with the debug ssh key"
        return self.check_nodes_ssh(debug=True,timeout_minutes=10,silent_minutes=5)
    
    def nodes_ssh_boot(self):
        "Tries to ssh into nodes in production mode with the root ssh key"
        return self.check_nodes_ssh(debug=False,timeout_minutes=40,silent_minutes=15)
    
    @node_mapper
    def init_node (self): 
        "all nodes : init a clean local directory for holding node-dep stuff like iso image..."
        pass
    @node_mapper
    def bootcd (self): 
        "all nodes: invoke GetBootMedium and store result locally"
        pass
    @node_mapper
    def configure_qemu (self): 
        "all nodes: compute qemu config qemu.conf and store it locally"
        pass
    @node_mapper
    def reinstall_node (self): 
        "all nodes: mark PLCAPI boot_state as reinstall"
        pass
    @node_mapper
    def export_qemu (self): 
        "all nodes: push local node-dep directory on the qemu box"
        pass
        
    ### check hooks : invoke scripts from hooks/{node,slice}
    def check_hooks_node (self): 
        return self.locate_first_node().check_hooks()
    def check_hooks_sliver (self) : 
        return self.locate_first_sliver().check_hooks()
    
    def check_hooks (self):
        "runs unit tests in the node and slice contexts - see hooks/{node,slice}"
        return self.check_hooks_node() and self.check_hooks_sliver()

    ### initscripts
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
        "check that the initscripts have triggered"
        return self.do_check_initscripts()
    
    def initscripts (self):
        "create initscripts with PLCAPI"
        for initscript in self.plc_spec['initscripts']:
            utils.pprint('Adding Initscript in plc %s'%self.plc_spec['name'],initscript)
            self.apiserver.AddInitScript(self.auth_root(),initscript['initscript_fields'])
        return True

    def clean_initscripts (self):
        "delete initscripts with PLCAPI"
        for initscript in self.plc_spec['initscripts']:
            initscript_name = initscript['initscript_fields']['name']
            print('Attempting to delete %s in plc %s'%(initscript_name,self.plc_spec['name']))
            try:
                self.apiserver.DeleteInitScript(self.auth_root(),initscript_name)
                print initscript_name,'deleted'
            except:
                print 'deletion went wrong - probably did not exist'
        return True

    ### manage slices
    def slices (self):
        "create slices with PLCAPI"
        return self.do_slices()

    def clean_slices (self):
        "delete slices with PLCAPI"
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
        
    @slice_mapper
    def check_slice(self): 
        "tries to ssh-enter the slice with the user key, to ensure slice creation"
        pass

    @node_mapper
    def clear_known_hosts (self): 
        "remove test nodes entries from the local known_hosts file"
        pass
    
    @node_mapper
    def start_node (self) : 
        "all nodes: start the qemu instance (also runs qemu-bridge-init start)"
        pass

    def check_tcp (self):
        "check TCP connectivity between 2 slices (or in loopback if only one is defined)"
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
        "runs PLCAPI stress test, that checks Add/Update/Delete on all types - preserves contents"
        # install the stress-test in the plc image
        location = "/usr/share/plc_api/plcsh_stress_test.py"
        remote="/vservers/%s/%s"%(self.vservername,location)
        self.test_ssh.copy_abs("plcsh_stress_test.py",remote)
        command = location
        command += " -- --check"
        if self.options.size == 1:
            command +=  " --tiny"
        return ( self.run_in_guest(command) == 0)

    # populate runs the same utility without slightly different options
    # in particular runs with --preserve (dont cleanup) and without --check
    # also it gets run twice, once with the --foreign option for creating fake foreign entries

    ### install_sfa_rpm
    def install_sfa(self):
        "yum install sfa, sfa-plc and sfa-client"
        # ignore yum retcod
        self.run_in_guest("yum -y install sfa sfa-client sfa-plc sfa-sfatables")
        return  self.run_in_guest("rpm -q sfa sfa-client sfa-plc sfa-sfatables")==0
        

    def dbclean_sfa(self):
        "thoroughly wipes off the SFA database"
        self.run_in_guest("sfa-nuke-plc.py")==0
        return True

    def plcclean_sfa(self):
        "cleans the PLC entries that were created as a side effect of running the script"
        # ignore result 
        sfa_spec=self.plc_spec['sfa']

        slicename='%s_%s'%(sfa_spec['login_base'],sfa_spec['slicename'])
        try: self.apiserver.DeleteSlice(self.auth_root(),slicename)
        except: print "Slice %s already absent from PLC db"%slicename

        username="%s@%s"%(sfa_spec['regularuser'],sfa_spec['domain'])
        try: self.apiserver.DeletePerson(self.auth_root(),username)
        except: print "User %s already absent from PLC db"%username

        print "REMEMBER TO RUN import_sfa AGAIN"
        return True

    def uninstall_sfa(self):
        "uses rpm to uninstall sfa - ignore result"
        self.run_in_guest("rpm -e sfa sfa-sfatables sfa-client sfa-plc")
        self.run_in_guest("rm -rf /var/lib/sfa")
        self.run_in_guest("rm -rf /etc/sfa")
        self.run_in_guest("rm -rf /var/log/sfa_access.log /var/log/sfa_import_plc.log /var/log/sfa.daemon")
        # xxx tmp 
        self.run_in_guest("rpm -e --noscripts sfa-plc")
        return True

    ### install_sfa_rpm
    def install_unittest_sfa(self):
        "yum install sfa-tests"
        # ignore yum retcod
        self.run_in_guest("yum -y install sfa-tests")
        return  self.run_in_guest("rpm -q sfa-tests")==0

    def unittest_sfa(self):
        "run SFA unittests"
        return self.run_in_guest("/usr/share/sfa/tests/testAll.py")==0

    ###
    def confdir(self):
        dirname="conf.%s"%self.plc_spec['name']
        if not os.path.isdir(dirname):
            utils.system("mkdir -p %s"%dirname)
        if not os.path.isdir(dirname):
            raise "Cannot create config dir for plc %s"%self.name()
        return dirname

    def conffile(self,filename):
        return "%s/%s"%(self.confdir(),filename)
    def confsubdir(self,dirname,clean):
        subdirname="%s/%s"%(self.confdir(),dirname)
        if clean:
            utils.system("rm -rf %s"%subdirname)
        if not os.path.isdir(subdirname): 
            utils.system("mkdir -p %s"%subdirname)
        if not os.path.isdir(subdirname):
            raise "Cannot create config subdir %s for plc %s"%(dirname,self.name())
        return subdirname
        
    def conffile_clean (self,filename):
        filename=self.conffile(filename)
        return utils.system("rm -rf %s"%filename)==0
    
    ###
    def configure_sfa(self):
        "run sfa-config-tty"
        tmpname=self.conffile("sfa-config-tty")
        fileconf=open(tmpname,'w')
        for var in [ 'SFA_REGISTRY_ROOT_AUTH',
                     'SFA_INTERFACE_HRN',
#                     'SFA_REGISTRY_LEVEL1_AUTH',
		     'SFA_REGISTRY_HOST',
		     'SFA_AGGREGATE_HOST',
                     'SFA_SM_HOST',
                     'SFA_PLC_USER',
                     'SFA_PLC_PASSWORD',
                     'SFA_PLC_DB_HOST',
                     'SFA_PLC_DB_USER',
                     'SFA_PLC_DB_PASSWORD',
		     'SFA_PLC_URL',
                     ]:
            fileconf.write ('e %s\n%s\n'%(var,self.plc_spec['sfa'][var]))
        # the way plc_config handles booleans just sucks..
        for var in ['SFA_API_DEBUG']:
            val='false'
            if self.plc_spec['sfa'][var]: val='true'
            fileconf.write ('e %s\n%s\n'%(var,val))
        fileconf.write('w\n')
        fileconf.write('R\n')
        fileconf.write('q\n')
        fileconf.close()
        utils.system('cat %s'%tmpname)
        self.run_in_guest_piped('cat %s'%tmpname,'sfa-config-tty')
        return True

    def aggregate_xml_line(self):
        return '<aggregate addr="%s" hrn="%s" port="12346"/>' % \
            (self.vserverip,self.plc_spec['sfa']['SFA_REGISTRY_ROOT_AUTH'])

    def registry_xml_line(self):
        return '<registry addr="%s" hrn="%s" port="12345"/>' % \
            (self.vserverip,self.plc_spec['sfa']['SFA_REGISTRY_ROOT_AUTH'])


    # a cross step that takes all other plcs in argument
    def cross_configure_sfa(self, other_plcs):
        # of course with a single plc, other_plcs is an empty list
        if not other_plcs:
            return True
        agg_fname=self.conffile("agg.xml")
        file(agg_fname,"w").write("<aggregates>%s</aggregates>\n" % \
                                     " ".join([ plc.aggregate_xml_line() for plc in other_plcs ]))
        utils.header ("(Over)wrote %s"%agg_fname)
        reg_fname=self.conffile("reg.xml")
        file(reg_fname,"w").write("<registries>%s</registries>\n" % \
                                     " ".join([ plc.registry_xml_line() for plc in other_plcs ]))
        utils.header ("(Over)wrote %s"%reg_fname)
        return self.test_ssh.copy_abs(agg_fname,'/vservers/%s/etc/sfa/aggregates.xml'%self.vservername)==0 \
            and  self.test_ssh.copy_abs(reg_fname,'/vservers/%s/etc/sfa/registries.xml'%self.vservername)==0

    def import_sfa(self):
        "sfa-import-plc"
	auth=self.plc_spec['sfa']['SFA_REGISTRY_ROOT_AUTH']
        return self.run_in_guest('sfa-import-plc.py')==0
# not needed anymore
#        self.run_in_guest('cp /etc/sfa/authorities/%s/%s.pkey /etc/sfa/authorities/server.key'%(auth,auth))

    def start_sfa(self):
        "service sfa start"
        return self.run_in_guest('service sfa start')==0

    def configure_sfi(self):
        sfa_spec=self.plc_spec['sfa']
        "sfi client configuration"
	dir_name=self.confsubdir("dot-sfi",clean=True)
	file_name=dir_name + os.sep + sfa_spec['piuser'] + '.pkey'
        fileconf=open(file_name,'w')
        fileconf.write (self.plc_spec['keys'][0]['private'])
        fileconf.close()
        utils.header ("(Over)wrote %s"%file_name)

	file_name=dir_name + os.sep + 'sfi_config'
        fileconf=open(file_name,'w')
	SFI_AUTH="%s.%s"%(sfa_spec['SFA_REGISTRY_ROOT_AUTH'],sfa_spec['login_base'])
        fileconf.write ("SFI_AUTH='%s'"%SFI_AUTH)
	fileconf.write('\n')
	SFI_USER=SFI_AUTH + '.' + sfa_spec['piuser']
        fileconf.write ("SFI_USER='%s'"%SFI_USER)
	fileconf.write('\n')
	SFI_REGISTRY='http://' + sfa_spec['SFA_PLC_DB_HOST'] + ':12345/'
        fileconf.write ("SFI_REGISTRY='%s'"%SFI_REGISTRY)
	fileconf.write('\n')
	SFI_SM='http://' + sfa_spec['SFA_PLC_DB_HOST'] + ':12347/'
        fileconf.write ("SFI_SM='%s'"%SFI_SM)
	fileconf.write('\n')
        fileconf.close()
        utils.header ("(Over)wrote %s"%file_name)

	file_name=dir_name + os.sep + 'person.xml'
        fileconf=open(file_name,'w')
	for record in sfa_spec['sfa_person_xml']:
	   person_record=record
	fileconf.write(person_record)
	fileconf.write('\n')
        fileconf.close()
        utils.header ("(Over)wrote %s"%file_name)

	file_name=dir_name + os.sep + 'slice.xml'
        fileconf=open(file_name,'w')
	for record in sfa_spec['sfa_slice_xml']:
	    slice_record=record
	#slice_record=sfa_spec['sfa_slice_xml']
	fileconf.write(slice_record)
	fileconf.write('\n')
        utils.header ("(Over)wrote %s"%file_name)
        fileconf.close()

	file_name=dir_name + os.sep + 'slice.rspec'
        fileconf=open(file_name,'w')
	slice_rspec=''
	for (key, value) in sfa_spec['sfa_slice_rspec'].items():
	    slice_rspec +=value 
	fileconf.write(slice_rspec)
	fileconf.write('\n')
        fileconf.close()
        utils.header ("(Over)wrote %s"%file_name)
        
        # push to the remote root's .sfi
        location = "root/.sfi"
        remote="/vservers/%s/%s"%(self.vservername,location)
	self.test_ssh.copy_abs(dir_name, remote, recursive=True)

        return True

    def clean_sfi (self):
        self.run_in_guest("rm -rf /root/.sfi")
        return True

    def add_user_sfa(self):
        return TestUserSfa(self).add_user()

    @slice_sfa_mapper
    def add_sfa(self):
        "run sfi.py add (on Registry)"
        pass

    @slice_sfa_mapper
    def create_sfa(self):
        "run sfi.py create (on SM) for 1st-time creation"
        pass

    def update_user_sfa(self):
        return TestUserSfa(self).update_user()

    @slice_sfa_mapper
    def update_sfa(self):
        "run sfi.py create (on SM) on existing object"
        pass

    def view_sfa(self):
        "run sfi.py list and sfi.py show (both on Registry) and sfi.py slices and sfi.py resources (both on SM)"
        sfa_spec=self.plc_spec['sfa']
	auth=sfa_spec['SFA_REGISTRY_ROOT_AUTH']
	return \
	self.run_in_guest("sfi.py -d /root/.sfi/ list %s.%s"%(auth,sfa_spec['login_base']))==0 and \
	self.run_in_guest("sfi.py -d /root/.sfi/ show %s.%s"%(auth,sfa_spec['login_base']))==0 and \
	self.run_in_guest("sfi.py -d /root/.sfi/ slices")==0 and \
	self.run_in_guest("sfi.py -d /root/.sfi/ resources -o resources")==0

    @slice_sfa_mapper
    def check_slice_sfa(self): 
	"tries to ssh-enter the SFA slice"
        pass

    def delete_user_sfa(self):
	"run sfi.py delete (on SM) for user"
	test_user_sfa=TestUserSfa(self)
	return test_user_sfa.delete_user()

    @slice_sfa_mapper
    def delete_slice_sfa(self):
	"run sfi.py delete (on SM), sfi.py remove (on Registry) to clean slices"
        pass

    def stop_sfa(self):
        "service sfa stop"
        self.run_in_guest('service sfa stop')==0
        return True

    def populate (self):
        "creates random entries in the PLCAPI"
        # install the stress-test in the plc image
        location = "/usr/share/plc_api/plcsh_stress_test.py"
        remote="/vservers/%s/%s"%(self.vservername,location)
        self.test_ssh.copy_abs("plcsh_stress_test.py",remote)
        command = location
        command += " -- --preserve --short-names"
        local = (self.run_in_guest(command) == 0);
        # second run with --foreign
        command += ' --foreign'
        remote = (self.run_in_guest(command) == 0);
        return ( local and remote)

    def gather_logs (self):
        "gets all possible logs from plc's/qemu node's/slice's for future reference"
        # (1.a) get the plc's /var/log/ and store it locally in logs/myplc.var-log.<plcname>/*
        # (1.b) get the plc's  /var/lib/pgsql/data/pg_log/ -> logs/myplc.pgsql-log.<plcname>/*
        # (2) get all the nodes qemu log and store it as logs/node.qemu.<node>.log
        # (3) get the nodes /var/log and store is as logs/node.var-log.<node>/*
        # (4) as far as possible get the slice's /var/log as logs/sliver.var-log.<sliver>/*
        # (1.a)
        print "-------------------- TestPlc.gather_logs : PLC's /var/log"
        self.gather_var_logs ()
        # (1.b)
        print "-------------------- TestPlc.gather_logs : PLC's /var/lib/psql/data/pg_log/"
        self.gather_pgsql_logs ()
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

    def gather_pgsql_logs (self):
        utils.system("mkdir -p logs/myplc.pgsql-log.%s"%self.name())
        to_plc = self.actual_command_in_guest("tar -C /var/lib/pgsql/data/pg_log/ -cf - .")        
        command = to_plc + "| tar -C logs/myplc.pgsql-log.%s -xf -"%self.name()
        utils.system(command)

    def gather_nodes_var_logs (self):
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite (self,site_spec)
            for node_spec in site_spec['nodes']:
                test_node=TestNode(self,test_site,node_spec)
                test_ssh = TestSsh (test_node.name(),key="keys/key1.rsa")
                command = test_ssh.actual_command("tar -C /var/log -cf - .")
                command = command + "| tar -C logs/node.var-log.%s -xf -"%test_node.name()
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
        'dump the planetlab5 DB in /root in the PLC - filename has time'
        dump=self.dbfile("planetab5")
        self.run_in_guest('pg_dump -U pgsqluser planetlab5 -f '+ dump)
        utils.header('Dumped planetlab5 database in %s'%dump)
        return True

    def db_restore(self):
        'restore the planetlab5 DB - looks broken, but run -n might help'
        dump=self.dbfile("planetab5")
        ##stop httpd service
        self.run_in_guest('service httpd stop')
        # xxx - need another wrapper
        self.run_in_guest_piped('echo drop database planetlab5','psql --user=pgsqluser template1')
        self.run_in_guest('createdb -U postgres --encoding=UNICODE --owner=pgsqluser planetlab5')
        self.run_in_guest('psql -U pgsqluser planetlab5 -f '+dump)
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
