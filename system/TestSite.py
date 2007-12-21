import os.path
import datetime
import time
import traceback

import utils
from TestNode import TestNode
from TestUser import TestUser
from TestKey import TestKey

class TestSite:

    def __init__ (self,test_plc,site_spec):
	self.test_plc=test_plc
	self.site_spec=site_spec
        
    def name(self):
        return self.site_spec['site_fields']['login_base']

    def create_site (self):
        print self.test_plc.auth_root()
        self.test_plc.server.AddSite(self.test_plc.auth_root(),
                                                    self.site_spec['site_fields'])
        self.test_plc.server.AddSiteAddress(self.test_plc.auth_root(),self.name(),
                                            self.site_spec['address_fields'])
            
    def create_users (self):
        for user_spec in self.site_spec['users']:
            test_user=TestUser(self.test_plc,self,user_spec)
            test_user.create_user()
            test_user.add_keys()            

    def delete_site (self):
        print self.test_plc.auth_root()
        self.test_plc.server.DeleteSite(self.test_plc.auth_root(),self.name())
        return True
            
    def delete_users(self):
        for user_spec in self.site_spec['users']:
            test_user=TestUser(self.test_plc,self,user_spec)
            test_user.delete_user()

    def locate_user (self,username):
        for user in self.site_spec['users']:
            if user['name'] == username:
                return user
            if user['user_fields']['email'] == username:
                return user
        raise Exception,"Cannot locate user %s"%username
        
    def locate_node (self,nodename):
        for node in self.site_spec['nodes']:
            if node['node_fields']['hostname'] == nodename:
                return node
        raise Exception,"Cannot locate node %s"%nodename
        
    # left as-is, i.e. crappy
    def check_nodes(self):
        # should filter out nodes not under vmware not qemu
        node_specs=self.site_spec['nodes']
        bool=True
        try:
            ret_value=True    
            filter=['boot_state']
            bt={'boot_state':'boot'}
            dbg={'boot_state':'dbg'}
            secondes=15
            start_time = datetime.datetime.now() ##geting the current time
            dead_time=datetime.datetime.now()+ datetime.timedelta(minutes=5)
            utils.header("Starting checking for nodes in site %s"%self.name())
            
            for node_spec in node_specs :
                hostname=node_spec['node_fields']['hostname']
                while (bool):
                    node_status=self.test_plc.server.GetNodes(self.test_plc.auth_root(),hostname, filter)
                    utils.header('Actual status for node %s is [%s]'%(hostname,node_status))
                    try:
                        if (node_status[0] == bt):
                            utils.header('%s has reached boot state'%hostname)
                            break 
                        elif (node_status[0] ==dbg):
                            utils.header('%s has reached debug state'%hostname)
                            bool=False
                            break 
                        elif ( start_time  <= dead_time ) :
                            start_time=datetime.datetime.now()+ datetime.timedelta(minutes=2)
                            time.sleep(secondes)
                        else: bool=False
                    except OSError ,e :
                        bool=False
                        str(e)
                if (bool):
                    utils.header("Node %s correctly installed and booted"%hostname)
                else :
                    utils.header("Node %s not fully booted"%hostname)
                    ret_value=False
            
            utils.header("End checking for nodes in site %s"%self.name())
            return ret_value
        except Exception, e:
            traceback.print_exc()
            utils.header("will kill vmware in 10 seconds")
            time.sleep(5)
            self.tst_plc.kill_all_vmwares()
            raise 
            
    def start_nodes (self,options):
        for node_spec in self.site_spec['nodes']:
            TestNode(self.test_plc, self, node_spec).start_node(options)
        return True
           
    def delete_known_hosts(self):
        utils.header("Messing with known_hosts (cleaning hostnames starting with 'test[0-9]')")
        sed_command="sed -i -e '/^test[0-9]/d' /root/.ssh/known_hosts"
        utils.system(sed_command)

    # xxx should be attached to TestPlc
    def check_slices(self):
        
        bool=True
        bool1=True
        secondes=15
        self.delete_known_hosts()
        start_time = datetime.datetime.now()
        dead_time=start_time + datetime.timedelta(minutes=3)##adding 3minutes
        for slice_spec in self.test_plc.plc_spec['slices']:
            for hostname in slice_spec['nodenames']:
                slicename=slice_spec['slice_fields']['name']
                # locate the first avail. key
                found=False
                for username in slice_spec['usernames']:
                    user_spec=self.locate_user(username)
                    for keyname in user_spec['keynames']:
                        key_spec=self.test_plc.locate_key(keyname)
                        publickey=TestKey(self.test_plc,key_spec).publicpath()
                        privatekey=TestKey(self.test_plc,key_spec).privatepath()
                        if os.path.isfile(publickey) and os.path.isfile(privatekey):
                            found=True
                            break
                if not found:
                    raise Exception,"Cannot find a valid key for slice %s"%slicename

                while(bool):
                    utils.header('restarting nm on %s'%hostname)
                    access=utils.system('ssh -i /etc/planetlab/root_ssh_key.rsa root@%s service nm restart'%hostname )
                    if (access==0):
                        utils.header('nm restarted on %s'%hostname)
                        while(bool1):
                            utils.header('trying to connect to %s@%s'%(slicename,hostname))
                            ### should use saved keys instead of this hard-coded stuff
                            Date=utils.system('ssh -i %s %s@%s date'%(privatekey,slicename,hostname))
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
                            access=utils.system('ssh -i /etc/planetlab/root_ssh_key.rsa  root@%s service nm restart'%hostname)
                            if (access==0):
                                utils.header('trying to connect (2) to %s@%s'%(slicename,hostname))
                                Date=utils.system('ssh -i ~/.ssh/slices.rsa %s@%s date'%(slicename,hostname))
                                if (Date==0):
                                    utils.header('connected to %s@%s -->'%(slicename,hostname))
                                else:
                                    utils.header('giving up with to %s@%s -->'%(slicename,hostname))
                                    return False
                            else :
                                utils.header('Last chance failed on %s@%s -->'%(slicename,hostname))
                        break
                    elif ( start_time  <= dead_time ) :
                        start_time=datetime.datetime.now()+ datetime.timedelta(minutes=1)
                        time.sleep(secondes)
                    else:
                        bool=False
                            
        return bool
