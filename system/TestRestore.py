#!/usr/bin/env python

import os, sys, time
from optparse import OptionParser
import xmlrpclib

class TestRestore:

    subversion_id = "$Id$"

    def __init__ (self):
        self.url="https://localhost:443/PLCAPI/"
	self.server=xmlrpclib.Server(self.url,allow_none=True)
        self.path=os.path.dirname(sys.argv[0])

###################3
    def auth_root (self):
	return {'Username':'root@onelab-test.inria.fr',
		'AuthMethod':'password',
		'AuthString':'test++',
                'Role' : 'root'
                }
    
##############check if the db version exsit
    def check_dir(self,dbname):

        config_file = "/plc/data/var/lib/pgsql/backups/"+dbname
        if (os.path.isfile (config_file)):
            print "==>dbversion found "
            return 1
        else:
            print "\n %s  non-existing Bdd version\n" % config_file
            return 0
            
##############restoring one db return list of host nodes
    def restore_db(self,db,display):
        try:
            list_host=[]
            ##stop httpd service
            os.system('chroot /plc/root  service httpd stop')
            ##droping
            os.system(' echo drop database planetlab4 |chroot /plc/root psql --user=pgsqluser template1')
            ##creating
            os.system('chroot /plc/root  createdb -U postgres --encoding=UNICODE --owner=pgsqluser planetlab4')
            ##populating
            os.system('chroot /plc/root psql -U pgsqluser planetlab4 -f /var/lib/pgsql/backups/'+db)
            ##starting httpd service
            os.system('chroot /plc/root  service httpd start')

            print 'db.restored'
            hosts=self.server.GetNodes(self.auth_root())
            for host in hosts:
                print host['hostname']
                list_host.append(host['hostname'])
                
            for l in list_host :
                print display
                os.system('DISPLAY=%s vmplayer %s/VirtualFile-%s/My_Virtual_Machine.vmx &'%(display,self.path,l))

        except Exception, e:
            print str(e)
###########################    




    def main (self):
        try:
            usage = """usage: %prog [options] BDDversion"""
            parser=OptionParser(usage=usage,version=self.subversion_id)
            # verbosity
            parser.add_option("-v","--verbose", action="store_true", dest="verbose", default=False, 
                              help="Run in verbose mode")
            #exporting Display
            parser.add_option("-d","--display", action="store", dest="Xdisplay", default='bellami:0.0',
                              help="export the display on the mentionneted one")
       
        
            (self.options, self.args) = parser.parse_args()
            
            hosts=[]
            i=0
            dirname =''
            display=''
           
            
            if (self.options.Xdisplay):
                display=self.options.Xdisplay
                print 'the display is', display
       
                
            if (len(self.args) == 0 ):
                parser.print_help()
                sys.exit(1)
            else:
                dirname=self.args[0]    
               
            if (not (self.check_dir(dirname))):
                 parser.print_help()
                 sys.exit(1)
                 
            self.restore_db(dirname,display)
            
        except Exception, e:
            print str(e)
            
if __name__ == "__main__":
    TestRestore().main()       
     
