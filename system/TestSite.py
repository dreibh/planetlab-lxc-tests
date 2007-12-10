import os
import sys
import datetime
import time
import xmlrpclib

from TestConfig import *
import utils

class TestSite:

    def __init__ (self,test_plc,site_spec):
	self.test_plc=test_plc
	self.site_spec=site_spec
        self.sitename=site_spec['site_fields']['name']
        
    def create_site (self):
        try:
            print self.test_plc.auth_root()
            self.site_id = self.test_plc.server.AddSite(self.test_plc.auth_root(),
							self.site_spec['site_fields'])
	    self.test_plc.server.AddSiteAddress(self.test_plc.auth_root(),self.site_id,
				       self.site_spec['site_address'])
            
	    return self.site_id
        except Exception, e:
	    print str(e)
            
    def site_id(self):
	return self.site_id()

    def create_user (self, user_spec):
        try:
            i=0
            utils.header('Adding user %s'%user_spec['email'])
            self.person_id=self.test_plc.server.AddPerson(self.test_plc.auth_root(),
                                                          user_spec)
            self.test_plc.server.UpdatePerson(self.test_plc.auth_root(),
                                              self.person_id,{'enabled': True})
            for role in user_spec['roles']:
                self.test_plc.server.AddRoleToPerson(self.test_plc.auth_root(),
                                                     role,user_spec['email'])
            self.test_plc.server.AddPersonToSite(self.test_plc.auth_root(),
                                                 user_spec['email'],
                                                 self.site_spec['site_fields']['login_base'])
        except Exception,e:
            print str(e)
            
    def enable_user (self, user_spec):
        try:
            persones=self.test_plc.server.GetPersons(self.test_plc.auth_root())
            for person in persones:
                if (person['enabled']!="True"):
                    self.test_plc.server.UpdatePerson(self.test_plc.auth_root(),
                                                      person['person_id'],
                                                      {'enabled': True})
        except Exception,e:
            print str(e)
            
    def add_key_user(self,user_spec):
        try:
            auth=""
            for userspec in self.site_spec['users']:
                if(user_spec == userspec):
                    for role in userspec['roles']:
                        auth=auth+role
                    print auth
                    self.test_plc.server.AddPersonKey(self.anyuser_auth(auth),
                                                      user_spec['email'], key)
        except Exception, e:
            print str(e)
            
    def anyuser_auth (self,key):
        for person in self.site_spec['users']:
            if person['auth_meth']== key :
                return {'Username':person['email'],
                        'AuthMethod':'password',
                        'AuthString':person['password'],
                        'Role':person['roles'][0],
                        }

    def node_check_status(self,liste_nodes,bool):
        try:
            ret_value=True    
            filter=['boot_state']
            bt={'boot_state':'boot'}
            dbg={'boot_state':'dbg'}
            secondes=15
            start_time = datetime.datetime.now() ##geting the current time
            dead_time=datetime.datetime.now()+ datetime.timedelta(minutes=10)
            utils.header("Starting checking for nodes in site %s"%self.sitename)
            
            for l in liste_nodes :
                hostname=l['hostname']
                while (bool):
                    node_status=self.test_plc.server.GetNodes(self.test_plc.auth_root(),hostname, filter)
                    utils.header('Actual status for node %s is [%s]'%(hostname,node_status))
                    try:
                        if (node_status[0] == bt):
                            test_name='Test Installation Node hosted: '+hostname
                            self.test_plc.display_results(test_name, 'Successful', '')
                            break ##for existing and renaming virtual file to just installed
                        elif (node_status[0] ==dbg):
                            test_name='Test Installation Node hosted: '+hostname
                            self.test_plc.display_results(test_name, 'En Debug', '')
                            bool=False
                            break ##for existing and renaming virtual file to just installed
                        elif ( start_time  <= dead_time ) :
                            start_time=datetime.datetime.now()+ datetime.timedelta(minutes=2)
                            time.sleep(secondes)
                        else: bool=False
                    except OSError ,e :
                        bool=False
                        str(e)
                if (bool):
                    utils.header("Node %s correctly instaled and booted"%hostname)
                else :
                    utils.header("Node %s not fully booted"%hostname)
                    ret_value=False
                    test_name='Test Installation Node Hosted: ',hostname
                    self.test_plc.display_results(test_name, 'Failure', '')
            
            utils.header("End checking for nodes in site %s"%self.sitename)
            return ret_value
        except Exception, e:
            print str(e)
            utils.header("will kill vmware in 10 seconds")
            time.sleep(10)
            self.kill_all_vmwares()
            sys.exit(1)
            
    def kill_all_vmwares(self):
        utils.header('Killing any running vmware or vmplayer instance')
        os.system('pgrep vmware | xargs -r kill')
        os.system('pgrep vmplayer | xargs -r kill ')
        os.system('pgrep vmware | xargs -r kill -9')
        os.system('pgrep vmplayer | xargs -r kill -9')
        
    def run_vmware(self,node_specs,display):
        path=os.path.dirname(sys.argv[0])
        self.kill_all_vmwares()
        utils.header('Displaying vmplayer on DISPLAY=%s'%display)
        for spec in node_specs :
            hostname=spec['hostname']
            utils.header('Starting vmplayer for node %s -- see vmplayer.log'%hostname)
            os.system('set -x; cd %s/vmplayer-%s ; DISPLAY=%s vmplayer node.vmx < /dev/null 2>&1 >> vmplayer.log &'%(path,hostname,display))

    def delete_known_hosts(self):
        utils.header("Messing with known_hosts (cleaning hostnames starting with 'test'")
        sed_command="sed -i -e '/^test[0-9]/d' /root/.ssh/known_hosts"
        os.system("set -x ; " + sed_command)

    def slice_access(self):
        try:
            bool=True
            bool1=True
            secondes=15
            self.delete_known_hosts()
            start_time = datetime.datetime.now()
            dead_time=start_time + datetime.timedelta(minutes=3)##adding 3minutes
            for slice in slices_specs:
                for slicenode in slice['slice_nodes']:
                    hostname=slicenode['hostname']
                    slicename=slice['slice_spec']['name']
                    while(bool):
                        utils.header('restarting nm on %s'%hostname)
                        access=os.system('set -x; ssh -i /etc/planetlab/root_ssh_key.rsa  root@%s service nm restart'%hostname )
                        if (access==0):
                            utils.header('nm restarted on %s'%hostname)
                            while(bool1):
                                utils.header('trying to connect to %s@%s'%(slicename,hostname))
                                Date=os.system('set -x; ssh -i ~/.ssh/slices.rsa %s@%s date'%(slicename,hostname))
                                if (Date==0):
                                    break
                                elif ( start_time  <= dead_time ) :
                                    start_time=datetime.datetime.now()+ datetime.timedelta(seconds=30)
                                    time.sleep(secondes)
                                else:
                                    bool1=False
                            if(bool1):
                                utils.header('connected to %s@%s -->'%(slicename,hostname))
                            else:
                                utils.header('%s@%s : last chance - restarting nm on %s'%(slicename,hostname,hostname))
                                access=os.system('set -x; ssh -i /etc/planetlab/root_ssh_key.rsa  root@%s service nm restart'%hostname)
                                if (access==0):
                                    utils.header('trying to connect (2) to %s@%s'%(slicename,hostname))
                                    Date=os.system('set -x; ssh -i ~/.ssh/slices.rsa %s@%s date'%(slicename,hostname))
                                    if (Date==0):
                                        utils.header('connected to %s@%s -->'%(slicename,hostname))
                                    else:
                                        utils.header('giving up with to %s@%s -->'%(slicename,hostname))
                                        sys.exit(1)
                                else :
                                    utils.header('Last chance failed on %s@%s -->'%(slicename,hostname))
                            break
                        elif ( start_time  <= dead_time ) :
                            start_time=datetime.datetime.now()+ datetime.timedelta(minutes=1)
                            time.sleep(secondes)
                        else:
                            bool=False
                                
                    if (not bool):
                        print 'Node manager problems'
                        sys.exit(1)
                    
        except Exception, e:
            print str(e)
            sys.exit(1)
   
