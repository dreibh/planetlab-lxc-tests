# $Id$
import os
import sys
import xmlrpclib
import datetime
import pprint
import traceback
import utils
from TestSite import TestSite
from TestNode import TestNode
from TestUser import TestUser

# step methods must take (self, options) and return a boolean

class TestPlc:

    def __init__ (self,plc_spec):
	self.plc_spec=plc_spec
	self.url="https://%s:443/PLCAPI/"%plc_spec['hostname']
	self.server=xmlrpclib.Server(self.url,allow_none=True)
	self.path=os.path.dirname(sys.argv[0])
        try:
            self.vserver=plc_spec['vserver']
        except:
            self.vserver=None
        
    def name(self):
        return self.plc_spec['name']

    def connect (self):
	# tricky : define les methodes de l'API sur cet object
	pass
    
    def auth_root (self):
	return {'Username':self.plc_spec['PLC_ROOT_USER'],
		'AuthMethod':'password',
		'AuthString':self.plc_spec['PLC_ROOT_PASSWORD'],
                'Role' : self.plc_spec['role']
                }
    def display_results(self, test_case_name, status, timers):
        timers=datetime.datetime.now()
        fileHandle = open (self.path+'/results.txt', 'a' )
        fileHandle.write ( str(test_case_name)+'\t' +str(status)+'\t'+str(timers)+'\n')
        fileHandle.close()
        
    def init_node (self,test_site,node_spec,path):

        test_node = TestNode(self, test_site, node_spec)
        test_node.create_node (test_site.locate_user("pi"))
        test_node.create_node ("tech")
        test_node.create_boot_cd(path)
        return test_node
    
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
        os.system('pgrep vmware | xargs -r kill')
        os.system('pgrep vmplayer | xargs -r kill ')
        os.system('pgrep vmware | xargs -r kill -9')
        os.system('pgrep vmplayer | xargs -r kill -9')
        
    # step methods
    def uninstall(self,options):
        os.system('set -x; service plc safestop')
        #####detecting the last myplc version installed and remove it
        os.system('set -x; rpm -e myplc')
        ##### Clean up the /plc directory
        os.system('set -x; rm -rf  /plc/data')
        return True
        
    def install(self,options):
        utils.header('Installing from %s'%options.myplc_url)
        url=options.myplc_url
        os.system('set -x; rpm -Uvh '+url)
        os.system('set -x; service plc mount')
        return True

    def configure(self,options):
        tmpname='/tmp/plc-config-tty-%d'%os.getpid()
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
        os.system('set -x ; cat %s'%tmpname)
        os.system('set -x ; chroot /plc/root  plc-config-tty < %s'%tmpname)
        os.system('set -x ; service plc start')
        os.system('set -x; service sendmail stop')
        os.system('set -x; chroot /plc/root service sendmail restart')
        os.system('set -x; rm %s'%tmpname)
        return True
        
    def sites (self,options):
        return self.do_sites(options)
    
    def clean_sites (self,options):
        return self.do_sites(options,"delete")
    
    def do_sites (self,options,action="add"):
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite (self,site_spec)
            if (action == "delete"):
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
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite (self,site_spec)
            utils.header("Creating nodes for site %s in %s"%(test_site.name(),self.name()))
            for node_spec in site_spec['nodes']:
                utils.header('Creating node %s'%node_spec)
                pprint.PrettyPrinter(indent=4).pprint(node_spec)
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
            utils.header('Adding Initscript %s in plc %s'%\
                         (initscript['name'],self.plc_spec['name']))
            pprint.PrettyPrinter(indent=4).pprint(initscript)
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
            pprint.PrettyPrinter(indent=4).pprint(slice_fields)
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

    def db_dump(self, options):
        # uses options.dbname if it is found
        try:
            name=options.dbname
        except:
            t=datetime.datetime.now()
            d=t.date()
            name=str(d)
        dump='/data/%s.sql'%name
        os.system('chroot /plc/root pg_dump -U pgsqluser planetlab4 -f '+ dump)
        utils.header('Dumped planetlab4 database in %s'%dump)
        return True

