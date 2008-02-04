import utils
import os, os.path
import datetime
import time

from TestKey import TestKey
from TestUser import TestUser
from TestNode import TestNode

class TestSlice:

    def __init__ (self,test_plc,test_site,slice_spec):
	self.test_plc=test_plc
        self.test_site=test_site
	self.slice_spec=slice_spec

    def name(self):
        return self.slice_spec['slice_fields']['name']

    def delete_slice(self):
        owner_spec = self.test_site.locate_user(self.slice_spec['owner'])
        auth = TestUser(self,self.test_site,owner_spec).auth()
        slice_fields = self.slice_spec['slice_fields']
        slice_name = slice_fields['name']
        self.test_plc.server.DeleteSlice(auth,slice_fields['name'])
        utils.header("Deleted slice %s"%slice_fields['name'])

    
    def create_slice(self):
        owner_spec = self.test_site.locate_user(self.slice_spec['owner'])
        auth = TestUser(self,self.test_site,owner_spec).auth()
        slice_fields = self.slice_spec['slice_fields']
        slice_name = slice_fields['name']

        self.test_plc.server.AddSlice(auth,slice_fields)
        for username in self.slice_spec['usernames']:
                user_spec=self.test_site.locate_user(username)
                test_user=TestUser(self,self.test_site,user_spec)
                self.test_plc.server.AddPersonToSlice(auth, test_user.name(), slice_name)

        hostnames=[]
        for nodename in self.slice_spec['nodenames']:
            node_spec=self.test_site.locate_node(nodename)
            test_node=TestNode(self,self.test_site,node_spec)
            hostnames += [test_node.name()]
        utils.header("Adding %r in %s"%(hostnames,slice_name))
        self.test_plc.server.AddSliceToNodes(auth, slice_name, hostnames)
        if self.slice_spec.has_key('initscriptname'):
            isname=self.slice_spec['initscriptname']
            utils.header("Adding initscript %s in %s"%(isname,slice_name))
            self.test_plc.server.AddSliceAttribute(self.test_plc.auth_root(), slice_name,'initscript',isname)
        
    def clear_known_hosts (self):
        utils.header("Messing with known_hosts for slice %s"%self.name())
        # scan nodenames
        for nodename in self.slice_spec['nodenames']:
            self.test_plc.run_in_guest("sed -i -e '/^%s/d' /root/.ssh/known_hosts"%nodename)

    ###the logic is quit wrong, must be rewritten
    def do_check_slices(self):
        # Do not wait here, as this step can be run directly in which case you don't want to wait
        # just add the 5 minutes to the overall timeout
        #utils.header("Waiting for the nodes to fully boot")
        #time.sleep(300)
        bool=bool1=True
        secondes=15
        self.test_plc.clear_ssh_config()
        self.clear_known_hosts()
        start_time = datetime.datetime.now()
        dead_time=start_time + datetime.timedelta(minutes=11)
        for slice_spec in self.test_plc.plc_spec['slices']:
            for hostname in slice_spec['nodenames']:
                slicename=slice_spec['slice_fields']['name']
                # locate the first avail. key
                found=False
                for username in slice_spec['usernames']:
                    user_spec=self.test_site.locate_user(username)
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
                    access=self.test_plc.run_in_guest('ssh -i /etc/planetlab/root_ssh_key.rsa root@%s service nm restart'%hostname )
                    if (access==0):
                        utils.header('nm restarted on %s'%hostname)
                        while(bool1):
                            utils.header('trying to connect to %s@%s'%(slicename,hostname))
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
                            time.sleep(240)##temoprally adding some delay due to the network slowness 
                            if (access==0):
                                utils.header('trying to connect (2) to %s@%s'%(slicename,hostname))
                                Date=utils.system('ssh -i %s %s@%s date'%(privatekey,slicename,hostname))
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
        
