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
    def affiche_results(self, test_case_name, status, timers):
        timers=datetime.datetime.now()
        fileHandle = open (self.path+'/results.txt', 'a' )
        fileHandle.write ( str(test_case_name)+'                    ' +str(status)+'                    '+str(timers))
        fileHandle.close()

        

    def config_plc(self,plc_spec):
# Thierry 2007-07-05 
# now plc-config-tty silently creates needed directories
#        os.system('mkdir -p /etc/planetlab/configs')

        fileconf=open('tty_conf','w')
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
        os.system('set -x ; cat tty_conf')
        os.system('set -x ; chroot /plc/root  plc-config-tty < tty_conf')
        os.system('set -x ; service plc start')
        os.system('set -x; service sendmail stop')
        os.system('set -x; chroot /plc/root service sendmail restart')
        
    def cleanup_plc(self):
        os.system('service plc safestop')
        #####detecting the last myplc version installed and remove it
        os.system('set -x; rpm -e myplc')
        print "=======================>Remove Myplc DONE!"
        ##### Clean up the /plc directory
        os.system('set -x; rm -rf  /plc/data')
        print "=======================>Clean up  DONE!"
        
    def install_plc(self,url):
        print url
        os.system('set -x; rpm -ivh '+url)
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
        test_node.create_boot_cd(node_spec,path)
        return test_node
    
    def db_dump(self):
        
        t=datetime.datetime.now()
        d=t.date()
        dump='/var/lib/pgsql/backups/planetlab4-'+str(d)+'-2nodes'
        os.system('chroot /plc/root pg_dump -U pgsqluser planetlab4 -f '+ dump)
        print 'dump is done',dump
        

        
