# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import utils
import os, os.path
import datetime
import time

from TestKey import TestKey
from TestUser import TestUser
from TestNode import TestNode
from TestSsh import TestSsh

class TestSlice:

    def __init__ (self,test_plc,test_site,slice_spec):
	self.test_plc=test_plc
        self.test_site=test_site
	self.slice_spec=slice_spec
        self.test_ssh=TestSsh(self.test_plc.test_ssh)
        
    def name(self):
        return self.slice_spec['slice_fields']['name']
    
    def get_slice(self,slice_name):
        for slice_spec in self.test_plc.plc_spec['slices']:
            if(slice_spec['slice_fields']['name']== slice_name):
                return slice_spec

    def delete_slice(self):
        owner_spec = self.test_site.locate_user(self.slice_spec['owner'])
        auth = TestUser(self,self.test_site,owner_spec).auth()
        slice_fields = self.slice_spec['slice_fields']
        slice_name = slice_fields['name']
        self.test_plc.apiserver.DeleteSlice(auth,slice_fields['name'])
        utils.header("Deleted slice %s"%slice_fields['name'])

    
    def create_slice(self):
        owner_spec = self.test_site.locate_user(self.slice_spec['owner'])
        auth = TestUser(self,self.test_site,owner_spec).auth()
        slice_fields = self.slice_spec['slice_fields']
        slice_name = slice_fields['name']

        self.test_plc.apiserver.AddSlice(auth,slice_fields)
        for username in self.slice_spec['usernames']:
                user_spec=self.test_site.locate_user(username)
                test_user=TestUser(self,self.test_site,user_spec)
                self.test_plc.apiserver.AddPersonToSlice(auth, test_user.name(), slice_name)

        hostnames=[]
        for nodename in self.slice_spec['nodenames']:
            node_spec=self.test_site.locate_node(nodename)
            test_node=TestNode(self,self.test_site,node_spec)
            hostnames += [test_node.name()]
        utils.header("Adding %r in %s"%(hostnames,slice_name))
        self.test_plc.apiserver.AddSliceToNodes(auth, slice_name, hostnames)
        # add initscript code or name as appropriate
        if self.slice_spec.has_key('initscriptcode'):
            iscode=self.slice_spec['initscriptcode']
            utils.header("Adding initscript code %s in %s"%(iscode,slice_name))
            self.test_plc.apiserver.AddSliceTag(self.test_plc.auth_root(), slice_name,'initscript_code',iscode)
        elif self.slice_spec.has_key('initscriptname'):
            isname=self.slice_spec['initscriptname']
            utils.header("Adding initscript name %s in %s"%(isname,slice_name))
            self.test_plc.apiserver.AddSliceTag(self.test_plc.auth_root(), slice_name,'initscript',isname)
        if self.slice_spec.has_key ('vref'):
            vref_value=self.slice_spec['vref']
            self.test_plc.apiserver.AddSliceTag(self.test_plc.auth_root(), slice_name,'vref',vref_value)
        
    def locate_key(self):
        # locate the first avail. key
        found=False
        for username in self.slice_spec['usernames']:
            user_spec=self.test_site.locate_user(username)
            for keyname in user_spec['keynames']:
                key_spec=self.test_plc.locate_key(keyname)
                test_key=TestKey(self.test_plc,key_spec)
                publickey=test_key.publicpath()
                privatekey=test_key.privatepath()
                keyname=test_key.name()
                if os.path.isfile(publickey) and os.path.isfile(privatekey):
                    found=True
        return (found,privatekey)

    def ssh_slice(self,options,timeout_minutes=20,silent_minutes=10,period=15):
        timeout = datetime.datetime.now()+datetime.timedelta(minutes=timeout_minutes)
        graceout = datetime.datetime.now()+datetime.timedelta(minutes=silent_minutes)
        # locate a key
        (found,remote_privatekey)=self.locate_key()
        if not found :
            utils.header("WARNING: Cannot find a valid key for slice %s"%self.name())
            return False

        # convert nodenames to real hostnames
        slice_spec = self.slice_spec
        restarted=[]
        tocheck=[]
        for nodename in slice_spec['nodenames']:
            (site_spec,node_spec) = self.test_plc.locate_node(nodename)
            tocheck.append(node_spec['node_fields']['hostname'])

        utils.header("checking ssh access into slice %s on nodes %r"%(self.name(),tocheck))
        utils.header("max timeout is %d minutes, silent for %d minutes (period is %s)"%\
                         (timeout_minutes,silent_minutes,period))
        while tocheck:
            for hostname in tocheck:
                (site_spec,node_spec) = self.test_plc.locate_hostname(hostname)
                date_test_ssh = TestSsh (hostname,key=remote_privatekey,username=self.name())
                command = date_test_ssh.actual_command("echo hostname ; hostname; echo id; id; echo uname -a ; uname -a")
                date = utils.system (command, silent=datetime.datetime.now() < graceout)
                if date==0:
                    utils.header("Successfuly entered slice %s on %s"%(self.name(),hostname))
                    tocheck.remove(hostname)
                else:
                    # real nodes will have been checked once in case they're up - skip if not
                    if TestNode.is_real_model(node_spec['node_fields']['model']):
                        utils.header("WARNING : Checking slice %s on real node %s skipped"%(self.name(),hostname))
                        tocheck.remove(hostname)
                    # nm restart after first failure, if requested 
                    if options.forcenm and hostname not in restarted:
                        utils.header ("forcenm option : restarting nm on %s"%hostname)
                        restart_test_ssh=TestSsh(hostname,key="keys/key1.rsa")
                        access=restart_test_ssh.actual_command('service nm restart')
                        if (access==0):
                            utils.header('nm restarted on %s'%hostname)
                        else:
                            utils.header('Failed to restart nm on %s'%(hostname))
                        restarted.append(hostname)
            if not tocheck:
                # we're done
                return True
            if datetime.datetime.now() > timeout:
                for hostname in tocheck:
                    utils.header("FAILURE to ssh into %s@%s"%(self.name(),hostname))
                return False
            # wait for the period
            time.sleep (period)
        # for an empty slice
        return True
