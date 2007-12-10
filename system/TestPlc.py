# $Id$
import os
import sys
import xmlrpclib
import datetime
from TestSite import TestSite
from TestNode import TestNode

class TestPlc:

    def __init__ (self,plc_spec):
	self.plc_spec=plc_spec
	self.url="https://%s:443/PLCAPI/"%plc_spec['hostname']
	self.server=xmlrpclib.Server(self.url,allow_none=True)
	self.path=os.path.dirname(sys.argv[0])
        
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
        

    def config_plc(self,plc_spec):
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
            fileconf.write ('e %s\n%s\n'%(var,plc_spec[var]))
        fileconf.write('w\n')
        fileconf.write('q\n')
        fileconf.close()
        os.system('set -x ; cat %s'%tmpname)
        os.system('set -x ; chroot /plc/root  plc-config-tty < %s'%tmpname)
        os.system('set -x ; service plc start')
        os.system('set -x; service sendmail stop')
        os.system('set -x; chroot /plc/root service sendmail restart')
        os.system('set -x; rm %s'%tmpname)
        
    def cleanup_plc(self):
        os.system('set -x; service plc safestop')
        #####detecting the last myplc version installed and remove it
        os.system('set -x; rpm -e myplc')
        ##### Clean up the /plc directory
        os.system('set -x; rm -rf  /plc/data')
        
    def install_plc(self,url):
        os.system('set -x; rpm -Uvh '+url)
        os.system('set -x; service plc mount')
      
    def init_site (self,site_spec):
        test_site = TestSite (self,site_spec)
        test_site.create_site()
        for key in site_spec['users']:
            test_site.create_user(key)
            test_site.enable_user(key)
            test_site.add_key_user(key)            
        return test_site

    def init_node (self,test_site,node_spec,path):

        test_node = TestNode(self, test_site, node_spec)
        test_node.create_node ("pi")
        test_node.create_node ("tech")
        test_node.create_boot_cd(path)
        return test_node
    
    def db_dump(self):
        
        t=datetime.datetime.now()
        d=t.date()
        dump='/var/lib/pgsql/backups/planetlab4-'+str(d)+'-2nodes'
        os.system('chroot /plc/root pg_dump -U pgsqluser planetlab4 -f '+ dump)
        print 'dump is done',dump
        

        
