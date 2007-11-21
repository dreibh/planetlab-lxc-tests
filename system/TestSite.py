import os
import sys
import datetime
import time
from TestConfig import *
import xmlrpclib

class TestSite:

    def __init__ (self,test_plc,site_spec):
	self.test_plc=test_plc
	self.site_spec=site_spec
        self.timset=time.strftime("%H:%M:%S", time.localtime())
        
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
            print '========>Adding user at '+self.timset+ ': ',user_spec
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
            dead_time=datetime.datetime.now()+ datetime.timedelta(minutes=10)##adding 10minutes
            start=time.strftime("%H:%M:%S", time.localtime())
            print "time in the begining  is :",start
            
            for l in liste_nodes :
                while (bool):
                    node_status=self.test_plc.server.GetNodes(self.test_plc.auth_root(),
                                                              l['hostname'], filter)
                    timset=time.strftime("%H:%M:%S", time.localtime())
                    print 'the actual status for the node '+l['hostname']+' at '+str(timset)+' is :',node_status
                    try:
                        if (node_status[0] == bt):
                            test_name='\nTest Installation Node hosted: '+l['hostname']
                            self.test_plc.affiche_results(test_name, 'Successful', '')##printing out the result
                            break ##for exsiting and renaming virtual file to just installed
                        elif (node_status[0] ==dbg):
                            test_name='\nTest Installation Node hosted: '+l['hostname']
                            self.test_plc.affiche_results(test_name, 'En Debug', '')##printing out the result
                            bool=False
                            break ##for exsiting and renaming virtual file to just installed
                        elif ( start_time  <= dead_time ) :
                            start_time=datetime.datetime.now()+ datetime.timedelta(minutes=2)
                            time.sleep(secondes)
                        else: bool=False
                    except OSError ,e :
                        bool=False
                        str(e)
                if (bool):
                    print "Node correctly instaled and booted "
                else :
                    print "Node not fully booted "##cheek if configuration file already exist
                    ret_value=False
                    test_name='\nTest Installation Node Hosted: ',l['hostname']
                    self.test_plc.affiche_results(test_name, 'Failure', '')##printing out the result
            
            end=time.strftime("%H:%M:%S", time.localtime())
            print "time at the end is :",end  ##converting time to secondes
            return ret_value
        except Exception, e:
            print str(e)
            print "vmware killed if problems occur  "
            time.sleep(10)
            self.kill_all_vmwares()
            sys.exit(1)
            
    def kill_all_vmwares(self):
        os.system('pgrep vmware | xargs -r kill')
        os.system('pgrep vmplayer | xargs -r kill ')
        os.system('pgrep vmware | xargs -r kill -9')
        os.system('pgrep vmplayer | xargs -r kill -9')
        
    def run_vmware(self,liste_nodes,display):
        path=os.path.dirname(sys.argv[0])
        print path
        print " kill last vmware before any new  installation  "
        self.kill_all_vmwares()
        print 'i will be displayed here========>', display
        arg='< /dev/null &>/dev/null &'
        for l in liste_nodes :
            #os.system('set -x; vmplayer  VirtualFile-%s/My_Virtual_Machine.vmx  %s '%(l['hostname'],arg))
            os.system('set -x; DISPLAY=%s vmplayer %s/VirtualFile-%s/My_Virtual_Machine.vmx %s '%(display,path,l['hostname'],arg))

    def delete_known_hosts(self):
        try:
            file1=open('/root/.ssh/known_hosts','r')
            file2=open('/root/.ssh/known_hosts_temp','w')
            while 1:
                txt = file1.readline()
                if txt=='':
                    file1.close()
                    file2.close()
                    break
                if txt[0:4]!='test' :
                    file2.write(txt)
            
                
            os.system('mv -f /root/.ssh/known_hosts_temp  /root/.ssh/known_hosts')
        except Exception, e:
            print str(e)

    def slice_access(self,liste_nodes):
        try:
            bool=True
            bool1=True
            secondes=15
            self.delete_known_hosts()
            start_time = datetime.datetime.now()
            dead_time=start_time + datetime.timedelta(minutes=3)##adding 3minutes
            for slice in slices_specs:
                for slicenode in slice['slice_nodes']:
                    timset=time.strftime("%H:%M:%S", time.localtime())
                    while(bool):
                        print '=========>Try to Restart the Node Manager on %s at %s:'%(slicenode['hostname'],str(timset))
                        access=os.system('set -x; ssh -i /etc/planetlab/root_ssh_key.rsa  root@%s service nm restart'%slicenode['hostname'] )
                        if (access==0):
                            print '=========>Node Manager Restarted on %s at %s:'%(slicenode['hostname'] ,str(timset))
                            while(bool1):
                                print '=========>Try to connect to the %s@%s at %s '%(slice['slice_spec']['name'],slicenode['hostname'],str(time.strftime("%H:%M:%S", time.localtime())))
                                Date=os.system('set -x; ssh -i ~/.ssh/slices.rsa %s@%s echo "The Actual Time here is;" date'%(slice['slice_spec']['name'],slicenode['hostname']))
                                if (Date==0):
                                    break
                                elif ( start_time  <= dead_time ) :
                                    start_time=datetime.datetime.now()+ datetime.timedelta(seconds=30)
                                    time.sleep(secondes)
                                else:
                                    bool1=False
                            if(bool1):
                                print '=========>connected to the '+slice['slice_spec']['name']+'@'+slicenode['hostname'] +'--->'
                            else:
                                print '=========>access to one slice is denied but last chance'
                                print '=========>Retry to Restart the Node Manager on %s at %s:'%(slicenode['hostname'],str(timset))
                                access=os.system('set -x; ssh -i /etc/planetlab/root_ssh_key.rsa  root@%s service nm restart'%slicenode['hostname'] )
                                if (access==0):
                                    print '=========>Retry to connect to the %s@%s at %s '%(slice['slice_spec']['name'],slicenode['hostname'],str(time.strftime("%H:%M:%S", time.localtime())))
                                    Date=os.system('set -x; ssh -i ~/.ssh/slices.rsa %s@%s echo "The Actual Time here is;" date'%(slice['slice_spec']['name'],slicenode['hostname'] ))
                                    if (Date==0):
                                        print '=========>connected to the '+slice['slice_spec']['name']+'@'+slicenode['hostname']+'--->'
                                    else:
                                        print '=========>the Access is finaly denied'
                                        sys.exit(1)
                                else :"=========>Last try failed"
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
   
