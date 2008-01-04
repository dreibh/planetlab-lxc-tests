# $Id$
import os, os.path
import sys
import xmlrpclib
import datetime
import traceback
import utils
from TestSite import TestSite
from TestNode import TestNode
from TestUser import TestUser
from TestKey import TestKey

# step methods must take (self, options) and return a boolean

class TestPlc:

    def __init__ (self,plc_spec):
	self.plc_spec=plc_spec
	self.url="https://%s:443/PLCAPI/"%plc_spec['hostname']
	self.server=xmlrpclib.Server(self.url,allow_none=True)
	self.path=os.path.dirname(sys.argv[0])
        try:
            self.vserverip=plc_spec['vserverip']
            self.vservername=plc_spec['vservername']
            self.vserver=True
        except:
            self.vserver=False
        
    def name(self):
        name=self.plc_spec['name']
        if self.vserver:
            return name+"[%s]"%self.vservername
        else:
            return name+"[chroot]"

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
        if self.plc_spec['hostname'] == "localhost":
            return command
        else:
            return "ssh " + self.plc_spec['hostname'] + " " + command

    def full_command(self,command):
        return self.ssh_command(self.run_command(command))

    def run_in_guest (self,command):
        return utils.system(self.full_command(command))
    def run_in_host (self,command):
        return utils.system(self.ssh_command(command))

    # xxx quick n dirty
    def run_in_guest_piped (self,local,remote):
        return utils.system(local+" | "+self.full_command(command))

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
        if self.vserver:
            return self.uninstall_vserver(options)
        else:
            return self.uninstall_chroot(options)

    ### install
    def install_chroot(self,options):
        utils.header('Installing from %s'%options.myplc_url)
        url=options.myplc_url
        utils.system('rpm -Uvh '+url)
        utils.system('service plc mount')
        return True

    # xxx this would not work with hostname != localhost as mylc-init-vserver was extracted locally
    def install_vserver_create(self,options):
        # we need build dir for myplc-init-vserver
        build_dir=self.path+"/build"
        if not os.path.isdir(build_dir):
            if utils.system("svn checkout %s %s"%(options.build_url,build_dir)) != 0:
                raise Exception,"Cannot checkout build dir"
        # the repo url is taken from myplc-url 
        # with the last two steps (i386/myplc...) removed
        repo_url = options.myplc_url
        repo_url = os.path.dirname(repo_url)
        repo_url = os.path.dirname(repo_url)
        command="%s/myplc-init-vserver.sh %s %s -- --interface eth0:%s"%\
            (build_dir,self.vservername,repo_url,self.vserverip)
        if utils.system(command) != 0:
            raise Exception,"Could not create vserver for %s"%self.vservername
        return True

    def install_vserver_native(self,options):
        self.run_in_guest("yum -y install myplc-native")
        return True

    def install(self,options):
        if self.vserver:
            return self.install_vserver_create(options)
            return self.install_vserver_yum(options)
        else:
            return self.install_chroot(options)

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
        self.run_in_guest('plc-config-tty < %s'%tmpname)
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

    ### would need a TestSlice class
    def do_slices (self, add_or_delete="add"):
        for slice in self.plc_spec['slices']:
            site_spec = self.locate_site (slice['sitename'])
            test_site = TestSite(self,site_spec)
            owner_spec = test_site.locate_user(slice['owner'])
            auth = TestUser(self,test_site,owner_spec).auth()
            slice_fields = slice['slice_fields']
            slice_name = slice_fields['name']
            if (add_or_delete == "delete"):
                self.server.DeleteSlice(auth,slice_fields['name'])
                utils.header("Deleted slice %s"%slice_fields['name'])
                continue
            utils.show_spec("Creating slice",slice_fields)
            self.server.AddSlice(auth,slice_fields)
            utils.header('Created Slice %s'%slice_fields['name'])
            for username in slice['usernames']:
                user_spec=test_site.locate_user(username)
                test_user=TestUser(self,test_site,user_spec)
                self.server.AddPersonToSlice(auth, test_user.name(), slice_name)

            hostnames=[]
            for nodename in slice['nodenames']:
                node_spec=test_site.locate_node(nodename)
                test_node=TestNode(self,test_site,node_spec)
                hostnames += [test_node.name()]
            utils.header("Adding %r in %s"%(hostnames,slice_name))
            self.server.AddSliceToNodes(auth, slice_name, hostnames)
            if slice.has_key('initscriptname'):
                isname=slice['initscriptname']
                utils.header("Adding initscript %s in %s"%(isname,slice_name))
                self.server.AddSliceAttribute(self.auth_root(), slice_name,
                                              'initscript',isname)
        return True
        
    def start_nodes (self, options):
        self.kill_all_vmwares()
        utils.header("Starting vmware nodes")
        for site_spec in self.plc_spec['sites']:
            TestSite(self,site_spec).start_nodes (options)
        return True

    def stop_nodes (self, options):
        self.kill_all_vmwares ()
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
