# $Id$
import os, os.path
import datetime
import time
import sys
import xmlrpclib
import datetime
import traceback
from types import StringTypes

import utils
from TestSite import TestSite
from TestNode import TestNode
from TestUser import TestUser
from TestKey import TestKey
from TestSlice import TestSlice

# step methods must take (self, options) and return a boolean

class TestPlc:

    def __init__ (self,plc_spec):
	self.plc_spec=plc_spec
	self.path=os.path.dirname(sys.argv[0])
        try:
            self.vserverip=plc_spec['vserverip']
            self.vservername=plc_spec['vservername']
            self.url="https://%s:443/PLCAPI/"%plc_spec['vserverip']
            self.vserver=True
        except:
            self.vserver=False
            self.url="https://%s:443/PLCAPI/"%plc_spec['hostname']
        utils.header('Using API url %s'%self.url)
	self.server=xmlrpclib.Server(self.url,allow_none=True)
        
    def name(self):
        name=self.plc_spec['name']
        if self.vserver:
            return name+"[%s]"%self.vservername
        else:
            return name+"[chroot]"

    def is_local (self):
        return self.plc_spec['hostname'] == 'localhost'

    # define the API methods on this object through xmlrpc
    # would help, but not strictly necessary
    def connect (self):
	pass
    
    # build the full command so command gets run in the chroot/vserver
    def run_command(self,command):
        if self.vserver:
            return "vserver %s exec %s"%(self.vservername,command)
        else:
            return "chroot /plc/root %s"%command

    def ssh_command(self,command):
        if self.is_local():
            return command
        else:
            return "ssh %s sh -c '\"%s\"'"%(self.plc_spec['hostname'],command)

    def full_command(self,command):
        return self.ssh_command(self.run_command(command))

    def run_in_guest (self,command):
        return utils.system(self.full_command(command))
    def run_in_host (self,command):
        return utils.system(self.ssh_command(command))

    # xxx quick n dirty
    def run_in_guest_piped (self,local,remote):
        return utils.system(local+" | "+self.full_command(remote))

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
        
    def locate_key (self,keyname):
        for key in self.plc_spec['keys']:
            if key['name'] == keyname:
                return key
        raise Exception,"Cannot locate key %s"%keyname
        
    def kill_all_vmwares(self):
        utils.header('Killing any running vmware or vmplayer instance')
        utils.system('pgrep vmware | xargs -r kill')
        utils.system('pgrep vmplayer | xargs -r kill ')
        utils.system('pgrep vmware | xargs -r kill -9')
        utils.system('pgrep vmplayer | xargs -r kill -9')

    def kill_all_qemus(self):
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite (self,site_spec)
            for node_spec in site_spec['nodes']:
                test_node=TestNode (self,test_site,node_spec)
                model=node_spec['node_fields']['model']
                host_box=node_spec['node_fields']['host_box']
                hostname=node_spec['node_fields']['hostname']
                print model
                if model.find("qemu") >= 0:
                    utils.system('ssh root@%s  killall qemu'%host_box)
                    test_node.stop_qemu(host_box,hostname)
                    
    #################### step methods

    ### uninstall
    def uninstall_chroot(self,options):
        self.run_in_host('service plc safestop')
        #####detecting the last myplc version installed and remove it
        self.run_in_host('rpm -e myplc')
        ##### Clean up the /plc directory
        self.run_in_host('rm -rf  /plc/data')
        return True

    def uninstall_vserver(self,options):
        self.run_in_host("vserver --silent %s delete"%self.vservername)
        return True

    def uninstall(self,options):
        # if there's a chroot-based myplc running, and then a native-based myplc is being deployed
        # it sounds safer to have the former uninstalled too
        # now the vserver method cannot be invoked for chroot instances as vservername is required
        if self.vserver:
            self.uninstall_vserver(options)
            self.uninstall_chroot(options)
        else:
            self.uninstall_chroot(options)
        return True

    ### install
    def install_chroot(self,options):
        # nothing to do
        return True

    # xxx this would not work with hostname != localhost as mylc-init-vserver was extracted locally
    def install_vserver(self,options):
        # we need build dir for vtest-init-vserver
        if self.is_local():
            # a full path for the local calls
            build_dir=self.path+"/build"
        else:
            # use a standard name - will be relative to HOME 
            build_dir="tests-system-build"
        build_checkout = "svn checkout %s %s"%(options.build_url,build_dir)
        if self.run_in_host(build_checkout) != 0:
            raise Exception,"Cannot checkout build dir"
        # the repo url is taken from myplc-url 
        # with the last two steps (i386/myplc...) removed
        repo_url = options.myplc_url
        repo_url = os.path.dirname(repo_url)
        repo_url = os.path.dirname(repo_url)
        create_vserver="%s/vtest-init-vserver.sh %s %s -- --interface eth0:%s"%\
            (build_dir,self.vservername,repo_url,self.vserverip)
        if self.run_in_host(create_vserver) != 0:
            raise Exception,"Could not create vserver for %s"%self.vservername
        return True

    def install(self,options):
        if self.vserver:
            return self.install_vserver(options)
        else:
            return self.install_chroot(options)

    ### install_rpm
    def install_rpm_chroot(self,options):
        utils.header('Installing from %s'%options.myplc_url)
        url=options.myplc_url
        self.run_in_host('rpm -Uvh '+url)
        self.run_in_host('service plc mount')
        return True

    def install_rpm_vserver(self,options):
        self.run_in_guest("yum -y install myplc-native")
        return True

    def install_rpm(self,options):
        if self.vserver:
            return self.install_rpm_vserver(options)
        else:
            return self.install_rpm_chroot(options)

    ### 
    def configure(self,options):
        tmpname='%s/%s.plc-config-tty'%(options.path,self.name())
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

    # the chroot install is slightly different to this respect
    def start(self, options):
        if self.vserver:
            self.run_in_guest('service plc start')
        else:
            self.run_in_host('service plc start')
        return True
        
    def stop(self, options):
        if self.vserver:
            self.run_in_guest('service plc stop')
        else:
            self.run_in_host('service plc stop')
        return True
        
    # could use a TestKey class
    def store_keys(self, options):
        for key_spec in self.plc_spec['keys']:
            TestKey(self,key_spec).store_key()
        return True

    def clean_keys(self, options):
        utils.system("rm -rf %s/keys/"%self.path)

    def sites (self,options):
        return self.do_sites(options)
    
    def clean_sites (self,options):
        return self.do_sites(options,action="delete")
    
    def do_sites (self,options,action="add"):
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

    def nodes (self, options):
        return self.do_nodes(options)
    def clean_nodes (self, options):
        return self.do_nodes(options,action="delete")

    def do_nodes (self, options,action="add"):
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
                    utils.show_spec('Creating node %s'%node_spec,node_spec)
                    test_node = TestNode (self,test_site,node_spec)
                    test_node.create_node ()
        return True

    # create nodegroups if needed, and populate
    # no need for a clean_nodegroups if we are careful enough
    def nodegroups (self, options):
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
        for (nodegroupname,group_nodes) in groups_dict.iteritems():
            try:
                self.server.GetNodeGroups(auth,{'name':nodegroupname})[0]
            except:
                self.server.AddNodeGroup(auth,{'name':nodegroupname})
            for node in group_nodes:
                self.server.AddNodeToNodeGroup(auth,node,nodegroupname)
        return True

    def check_nodes(self,options):
        time.sleep(10)#Wait for the qemu to mount. Only  matter of display
        status=True
        start_time = datetime.datetime.now()
        dead_time=datetime.datetime.now()+ datetime.timedelta(minutes=5)
        booted_nodes=[]
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite (self,site_spec)
            utils.header("Starting checking for nodes in site %s"%self.name())
            notfullybooted_nodes=[ node_spec['node_fields']['hostname'] for node_spec in site_spec['nodes'] ]
            nbr_nodes= len(notfullybooted_nodes)
            while (status):
                for node_spec in site_spec['nodes']:
                    hostname=node_spec['node_fields']['hostname']
                    if (hostname in notfullybooted_nodes): #to avoid requesting already booted node
                        test_node=TestNode (self,test_site,node_spec)
                        host_box=node_spec['node_fields']['host_box']
                        node_status=test_node.get_node_status(hostname,host_box)
                        if (node_status):
                            booted_nodes.append(hostname)
                            del notfullybooted_nodes[notfullybooted_nodes.index(hostname)]
                if ( not notfullybooted_nodes): break
                elif ( start_time  <= dead_time ) :
                    start_time=datetime.datetime.now()+ datetime.timedelta(minutes=2)
                    time.sleep(15)
                else: status=False
            for nodeup in booted_nodes : utils.header("Node %s correctly installed and booted"%nodeup)
            for nodedown  in notfullybooted_nodes : utils.header("Node %s not fully booted"%nodedown)
            return status
    
    def bootcd (self, options):
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite (self,site_spec)
            for node_spec in site_spec['nodes']:
                test_node=TestNode (self,test_site,node_spec)
                test_node.create_boot_cd(options.path)
        return True
                
    def initscripts (self, options):
        for initscript in self.plc_spec['initscripts']:
            utils.show_spec('Adding Initscript in plc %s'%self.plc_spec['name'],initscript)
            self.server.AddInitScript(self.auth_root(),initscript['initscript_fields'])
        return True

    def slices (self, options):
        return self.do_slices()

    def clean_slices (self, options):
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
                utils.show_spec("Creating slice",slice)
                test_slice.create_slice()
                utils.header('Created Slice %s'%slice['slice_fields']['name'])
        return True
        
    def check_slices(self, options):
        for slice_spec in self.plc_spec['slices']:
            site_spec = self.locate_site (slice_spec['sitename'])
            test_site = TestSite(self,site_spec)
            test_slice=TestSlice(self,test_site,slice_spec)
            status=test_slice.do_check_slices()
            return status
    
    def start_nodes (self, options):
        self.kill_all_vmwares()
        self.kill_all_qemus()
        utils.header("Starting vmware nodes")
        for site_spec in self.plc_spec['sites']:
            TestSite(self,site_spec).start_nodes (options)
        return True

    def stop_nodes (self, options):
        self.kill_all_vmwares ()
        self.kill_all_qemus()
        return True

    # returns the filename to use for sql dump/restore, using options.dbname if set
    def dbfile (self, database, options):
        # uses options.dbname if it is found
        try:
            name=options.dbname
            if not isinstance(name,StringTypes):
                raise Exception
        except:
            t=datetime.datetime.now()
            d=t.date()
            name=str(d)
        return "/root/%s-%s.sql"%(database,name)

    def db_dump(self, options):
        
        dump=self.dbfile("planetab4",options)
        self.run_in_guest('pg_dump -U pgsqluser planetlab4 -f '+ dump)
        utils.header('Dumped planetlab4 database in %s'%dump)
        return True

    def db_restore(self, options):
        dump=self.dbfile("planetab4",options)
        ##stop httpd service
        self.run_in_guest('service httpd stop')
        # xxx - need another wrapper
        self.run_in_guest_piped('echo drop database planetlab4','psql --user=pgsqluser template1')
        self.run_in_guest('createdb -U postgres --encoding=UNICODE --owner=pgsqluser planetlab4')
        self.run_in_guest('psql -U pgsqluser planetlab4 -f '+dump)
        ##starting httpd service
        self.run_in_guest('service httpd start')

        utils.header('Database restored from ' + dump)
