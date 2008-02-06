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
            self.test_plc.run_in_guest("sed -i -e /^%s/d /root/.ssh/known_hosts"%nodename)
        #scan public key and update the known_host file in the root image
        self.test_plc.scan_publicKeys(self.slice_spec['nodenames'])
        
    def locate_key(self,slice_spec):
        # locate the first avail. key
        found=False
        for username in slice_spec['usernames']:
            user_spec=self.test_site.locate_user(username)
            for keyname in user_spec['keynames']:
                key_spec=self.test_plc.locate_key(keyname)
                test_key=TestKey(self.test_plc,key_spec)
                publickey=test_key.publicpath()
                privatekey=test_key.privatepath()
                keyname=test_key.name()
                if os.path.isfile(publickey) and os.path.isfile(privatekey):
                    found=True
        #create dir in plc root image
        remote_privatekey="/root/keys/%s.rsa"%keyname
        if not os.path.isdir("/plc/root/data/root/keys"):
            self.test_plc.run_in_guest("mkdir  /root/keys" )
            self.test_plc.copy_in_guest(privatekey,remote_privatekey,True)

        return (found,remote_privatekey)

    def do_check_slices(self,options):
        bool=True
        self.clear_known_hosts()
        start_time = datetime.datetime.now()
        dead_time=start_time + datetime.timedelta(minutes=15)
        for slice_spec in self.test_plc.plc_spec['slices']:
            for hostname in slice_spec['nodenames']:
                slicename=slice_spec['slice_fields']['name']
                (found,remote_privatekey)=self.locate_key(slice_spec)
                if( not found):
                    raise Exception,"Cannot find a valid key for slice %s"%slicename
                    break 
                while(bool):
                    utils.header('trying to connect to %s@%s'%(slicename,hostname))
                    Date=self.test_plc.run_in_guest('ssh -i %s %s@%s date'%(remote_privatekey,slicename,hostname))
                    if (Date==0):
                        break
                    elif ( start_time  <= dead_time ) :
                        start_time=datetime.datetime.now()+ datetime.timedelta(seconds=45)
                        time.sleep(45)
                    elif (options.forcenm):
                        utils.header('%s@%s : restarting nm in case is in option on %s'%(slicename,hostname,hostname))
                        access=self.test_plc.run_in_guest('ssh -i /etc/planetlab/root_ssh_key.rsa  root@%s service nm restart'%hostname)
                        if (access==0):
                            utils.header('nm restarted on %s'%hostname)
                        else:
                            utils.header('%s@%s : Failed to restart the NM on %s'%(slicename,hostname,hostname))
                        utils.header('Try to reconnect to  %s@%s after the tentative of restarting NM'%(slicename,hostname))
                        connect=self.test_plc.run_in_guest('ssh -i %s %s@%s date'%(remote_privatekey,slicename,hostname))
                        if (not connect):
                            utils.header('connected to %s@%s -->'%(slicename,hostname))
                            break
                        else:
                            utils.header('giving up with to %s@%s -->'%(slicename,hostname))
                            bool=False
                            break
                    else:
                        bool=False
                        break
        return bool

         

