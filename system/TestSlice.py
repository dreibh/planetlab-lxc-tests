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

    def owner_auth(self):
        owner_spec = self.test_site.locate_user(self.slice_spec['owner'])
        return TestUser(self,self.test_site,owner_spec).auth()

    def slice_name (self):
        return self.slice_spec['slice_fields']['name']

    # init slice with people, and then add nodes 
    def create_slice(self):
        auth = self.owner_auth()
        slice_fields = self.slice_spec['slice_fields']
        slice_name = slice_fields['name']
        utils.header("Creating slice %s"%slice_name)
        self.test_plc.apiserver.AddSlice(auth,slice_fields)
        for username in self.slice_spec['usernames']:
                user_spec=self.test_site.locate_user(username)
                test_user=TestUser(self,self.test_site,user_spec)
                self.test_plc.apiserver.AddPersonToSlice(auth, test_user.name(), slice_name)
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

        self.add_nodes()

    def check_vsys_defaults (self, options, *args, **kwds):
        "check vsys tags match PLC_VSYS_DEFAULTS"
        auth = self.owner_auth()
        slice_fields = self.slice_spec['slice_fields']
        slice_name = slice_fields['name']
        vsys_tags = self.test_plc.apiserver.GetSliceTags (auth,{'tagname':'vsys','name':slice_name})
        values=[ st['value'] for st in vsys_tags ]
        expected=self.test_plc.plc_spec['expected_vsys_tags']
        return set(values) == set(expected)

    # just add the nodes and handle tags
    def add_nodes (self):
        auth = self.owner_auth()
        slice_name = self.slice_name()
        hostnames=[]
        for nodename in self.slice_spec['nodenames']:
            node_spec=self.test_site.locate_node(nodename)
            test_node=TestNode(self,self.test_site,node_spec)
            hostnames += [test_node.name()]
        utils.header("Adding %r in %s"%(hostnames,slice_name))
        self.test_plc.apiserver.AddSliceToNodes(auth, slice_name, hostnames)
        
    # trash the slice altogether
    def delete_slice(self):
        auth = self.owner_auth()
        slice_name = self.slice_name()
        utils.header("Deleting slice %s"%slice_name)
        self.test_plc.apiserver.DeleteSlice(auth,slice_name)

    # keep the slice alive and just delete nodes
    def delete_nodes (self):
        auth = self.owner_auth()
        slice_name = self.slice_name()
        print 'retrieving slice %s'%slice_name
        slice=self.test_plc.apiserver.GetSlices(auth,slice_name)[0]
        node_ids=slice['node_ids']
        utils.header ("Deleting %d nodes from slice %s"%\
                          (len(node_ids),slice_name))
        self.test_plc.apiserver.DeleteSliceFromNodes (auth,slice_name, node_ids)

    def locate_private_key(self):
        key_names=[]
        for username in self.slice_spec['usernames']:
            user_spec=self.test_site.locate_user(username)
            key_names += user_spec['key_names']
        return self.test_plc.locate_private_key_from_key_names (key_names)

    # trying to reach the slice through ssh - expected to answer
    def ssh_slice (self, options, *args, **kwds):
        "tries to ssh-enter the slice with the user key, to ensure slice creation"
        return self.do_ssh_slice(options, expected=True, *args, **kwds)

    # when we expect the slice is not reachable
    def ssh_slice_off (self, options, *args, **kwds):
        "tries to ssh-enter the slice with the user key, expecting it to be unreachable"
        return self.do_ssh_slice(options, expected=False, *args, **kwds)

    def do_ssh_slice(self,options,expected=True,timeout_minutes=20,silent_minutes=10,period=15):
        timeout = datetime.datetime.now()+datetime.timedelta(minutes=timeout_minutes)
        graceout = datetime.datetime.now()+datetime.timedelta(minutes=silent_minutes)
        # locate a key
        private_key=self.locate_private_key()
        if not private_key :
            utils.header("WARNING: Cannot find a valid key for slice %s"%self.name())
            return False

        # convert nodenames to real hostnames
        slice_spec = self.slice_spec
        restarted=[]
        tocheck=[]
        for nodename in slice_spec['nodenames']:
            (site_spec,node_spec) = self.test_plc.locate_node(nodename)
            tocheck.append(node_spec['node_fields']['hostname'])

        if expected:    msg="ssh slice access enabled"
        else:           msg="ssh slice access disabled"
            
        utils.header("checking for %s -- slice %s on nodes %r"%(msg,self.name(),tocheck))
        utils.header("max timeout is %d minutes, silent for %d minutes (period is %s)"%\
                         (timeout_minutes,silent_minutes,period))
        while tocheck:
            for hostname in tocheck:
                (site_spec,node_spec) = self.test_plc.locate_hostname(hostname)
                date_test_ssh = TestSsh (hostname,key=private_key,username=self.name())
                command = date_test_ssh.actual_command("echo hostname ; hostname; echo id; id; echo uname -a ; uname -a")
                date = utils.system (command, silent=datetime.datetime.now() < graceout)
                if getattr(options,'dry_run',None): return True
                if expected:    success = date==0
                else:           success = date!=0
                    
                if success:
                    utils.header("OK %s - slice=%s@%s"%(msg,self.name(),hostname))
                    tocheck.remove(hostname)
                else:
                    # real nodes will have been checked once in case they're up - skip if not
                    if TestNode.is_real_model(node_spec['node_fields']['model']):
                        utils.header("WARNING : Checking slice %s on real node %s skipped"%(self.name(),hostname))
                        tocheck.remove(hostname)
                    # nm restart after first failure, if requested 
                    if options.forcenm and hostname not in restarted:
                        utils.header ("forcenm option : restarting nm on %s"%hostname)
                        restart_test_ssh=TestSsh(hostname,key="keys/key_admin.rsa")
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
                    utils.header("FAILED %s slice=%s@%s"%(msg,self.name(),hostname))
                return False
            # wait for the period
            time.sleep (period)
        # for an empty slice
        return True
