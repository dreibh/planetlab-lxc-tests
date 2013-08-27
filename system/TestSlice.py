# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import utils
import os, os.path
from datetime import datetime, timedelta
import time

from TestKey import TestKey
from TestUser import TestUser
from TestNode import TestNode
from TestSsh import TestSsh
from Completer import Completer, CompleterTask

class CompleterTaskSshSlice (CompleterTask):

    def __init__ (self, test_plc, hostname, slicename, private_key,command, expected, dry_run):
        self.test_plc=test_plc
        self.hostname=hostname
        self.slicename=slicename
        self.private_key=private_key
        self.command=command
        self.dry_run=dry_run
        self.expected=expected
    def run (self, silent): 
        (site_spec,node_spec) = self.test_plc.locate_hostname(self.hostname)
        test_ssh = TestSsh (self.hostname,key=self.private_key,username=self.slicename)
        full_command = test_ssh.actual_command(self.command)
        retcod = utils.system (full_command, silent=silent)
        if self.dry_run: return True
        if self.expected:       return retcod==0
        else:                   return retcod!=0
    def failure_message (self):
        if self.expected:
            return "Could not ssh into sliver %s@%s"%(self.slicename,self.hostname)
        else:
            return "Could still ssh into sliver%s@%s (that was expected to be down)"%(self.slicename,self.hostname)

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
        if 'omf-friendly' in self.slice_spec:
            utils.header("Making slice %s OMF-friendly"%slice_name)
            self.test_plc.apiserver.AddSliceTag(self.test_plc.auth_root(), slice_name,'vref','omf')
            self.test_plc.apiserver.AddSliceTag(self.test_plc.auth_root(), slice_name,'omf_control','yes')
# setting vref directly like this was useful for multi-arch tests long ago - see wifilab
# however this should rather use other tags by now, so we drop this for now
#        if self.slice_spec.has_key ('vref'):
#            vref_value=self.slice_spec['vref']
#            self.test_plc.apiserver.AddSliceTag(self.test_plc.auth_root(), slice_name,'vref',vref_value)
        # epilogue
        self.add_nodes()

    def check_vsys_defaults (self, options, *args, **kwds):
        "check vsys tags match PLC_VSYS_DEFAULTS"
        auth = self.owner_auth()
        slice_fields = self.slice_spec['slice_fields']
        slice_name = slice_fields['name']
        vsys_tags = self.test_plc.apiserver.GetSliceTags (auth,{'tagname':'vsys','name':slice_name})
        values=[ st['value'] for st in vsys_tags ]
        expected=self.test_plc.plc_spec['expected_vsys_tags']
        result = set(values) == set(expected)
        if not result:
            print 'Check vsys defaults with slice %s'%slice_name
            print 'Expected %s'%expected
            print 'Got %s'%values
        return result

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
        "tries to ssh-enter the slice with the user key, to check for slice creation"
        return self.do_ssh_slice(options, expected=True, *args, **kwds)

    # when we expect the slice is not reachable
    def ssh_slice_off (self, options, *args, **kwds):
        "tries to ssh-enter the slice with the user key, expecting it to be unreachable"
        return self.do_ssh_slice(options, expected=False, *args, **kwds)

    def do_ssh_slice(self,options,expected=True,
                     timeout_minutes=20,silent_minutes=10,period_seconds=15,command=None):
        "tries to enter a slice"

        timeout  = timedelta(minutes=timeout_minutes)
        graceout = timedelta(minutes=silent_minutes)
        period   = timedelta(seconds=period_seconds)
        if not command:
            command="echo hostname ; hostname; echo id; id; echo uname -a ; uname -a"
        # locate a key
        private_key=self.locate_private_key()
        if not private_key :
            utils.header("WARNING: Cannot find a valid key for slice %s"%self.name())
            return False

        # convert nodenames to real hostnames
        if expected:    msg="ssh slice access enabled"
        else:           msg="ssh slice access disabled"
        utils.header("checking for %s -- slice %s"%(msg,self.name()))

        tasks=[]
        slicename=self.name()
        dry_run = getattr(options,'dry_run',False)
        for nodename in self.slice_spec['nodenames']:
            (site_spec,node_spec) = self.test_plc.locate_node(nodename)
            tasks.append( CompleterTaskSshSlice(self.test_plc,node_spec['node_fields']['hostname'],
                                                slicename,private_key,command,expected,dry_run))
        return Completer (tasks).run (timeout, graceout, period)

    def ssh_slice_basics (self, options, *args, **kwds):
        "the slice is expected to be UP and we just check a few simple sanity commands, including 'ps' to check for /proc"
        overall=True
        if not self.do_ssh_slice_once(options,expected=True,  command='true'): overall=False
        if not self.do_ssh_slice_once(options,expected=False, command='false'): overall=False
        if not self.do_ssh_slice_once(options,expected=False, command='someimprobablecommandname'): overall=False
        if not self.do_ssh_slice_once(options,expected=True,  command='ps'): overall=False
        return overall

    # pick just one nodename and runs the ssh command once
    def do_ssh_slice_once(self,options,command,expected):
        # locate a key
        private_key=self.locate_private_key()
        if not private_key :
            utils.header("WARNING: Cannot find a valid key for slice %s"%self.name())
            return False

        # convert nodenames to real hostnames
        slice_spec = self.slice_spec
        nodename=slice_spec['nodenames'][0]
        (site_spec,node_spec) = self.test_plc.locate_node(nodename)
        hostname=node_spec['node_fields']['hostname']

        if expected:    msg="%s to return TRUE from ssh"%command
        else:           msg="%s to return FALSE from ssh"%command
            
        utils.header("checking %s -- slice %s on node %s"%(msg,self.name(),hostname))
        (site_spec,node_spec) = self.test_plc.locate_hostname(hostname)
        test_ssh = TestSsh (hostname,key=private_key,username=self.name())
        full_command = test_ssh.actual_command(command)
        retcod = utils.system (full_command,silent=True)
        if getattr(options,'dry_run',None): return True
        if expected:    success = retcod==0
        else:           success = retcod!=0
        if not success: utils.header ("WRONG RESULT for %s"%msg)
        return success
