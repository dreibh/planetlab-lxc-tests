# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#

import time
from datetime import datetime, timedelta

import utils
from TestNode import TestNode
from TestUser import TestUser
from TestBoxQemu import TestBoxQemu
from TestSsh import TestSsh

from Completer import Completer, CompleterTask
from TestSlice import CompleterTaskSshSlice

class TestSliceSfa:

    def __init__ (self, test_auth_sfa, slice_spec):
        self.test_auth_sfa=test_auth_sfa
        self.slice_spec=slice_spec
        # shortcuts
        self.test_plc=self.test_auth_sfa.test_plc

    def hrn (self): 
        return self.test_auth_sfa.obj_hrn(self.slice_spec['name'])
    def sfi_path (self):
        return self.test_auth_sfa.sfi_path()

    # send back up to the TestAuthSfa
    def rspec_style (self): return self.test_auth_sfa.rspec_style()
    def sfi_pi(self,*args,**kwds): return self.test_auth_sfa.sfi_pi(*args, **kwds)
    def sfi_user(self,*args,**kwds): return self.test_auth_sfa.sfi_user(*args, **kwds)

    def discover_option(self):
        if self.rspec_style()=='pg': return "-r GENI"
        else:                        return "-r sfa"

    # those are step names exposed as methods of TestPlc, hence the _sfa

    # needs to be run as pi
    def sfa_register_slice(self,options):
        "run sfi register (on Registry)"
        sfi_command="register"
        sfi_command += " --type slice"
        sfi_command += " --xrn %s"%self.hrn()
        for opt in self.slice_spec['register_options']:
            sfi_command += " %s"%(opt)
	return self.test_plc.run_in_guest(self.sfi_pi(sfi_command))==0

    def sfa_renew_slice(self, options):
        "run sfi renew (on Aggregates)"
        too_late =  datetime.now() + timedelta(weeks=52)
        one_month = datetime.now() + timedelta(weeks=4)
        # we expect this to fail on too long term attemps, but to succeed otherwise
        overall=True
        for ( renew_until, expected) in [ (too_late, False), (one_month, True) ] :
            sfi_command="renew"
            sfi_command += " %s"%self.hrn()
            sfi_command += " %s"%renew_until.strftime("%Y-%m-%d")
            succeeded = self.test_plc.run_in_guest(self.sfi_user(sfi_command))==0
            if succeeded!=expected:
                utils.header ("Expecting success=%s, got %s"%(expected,succeeded))
                # however it turns out sfi renew always returns fine....
                #overall=False
            # so for helping manual checks:
            sfi_command="show -k hrn -k expires %s"%self.hrn()
            self.test_plc.run_in_guest(self.sfi_user(sfi_command))
        return overall

    # helper - filename to store a given result
    def _resname (self,name,ext): return "%s.%s"%(name,ext)
    def adfile (self): return self._resname("ad","rspec")
    def reqfile (self): return self._resname("req","rspec")
    def nodefile (self): return self._resname("nodes","txt")
    
    # run as user
    def sfa_discover(self,options):
        "discover resources into resouces_in.rspec"
        return self.test_plc.run_in_guest(self.sfi_user(\
                "resources %s -o %s/%s"% (self.discover_option(),self.sfi_path(),self.adfile())))==0

    # run sfi create as a regular user
    def sfa_create_slice(self,options):
        "run sfi create (on SM) - 1st time"
        commands=[
            "sfiListNodes.py -i %s/%s -o %s/%s"%(self.sfi_path(),self.adfile(),self.sfi_path(),self.nodefile()),
            "sfiAddSliver.py -i %s/%s -n %s/%s -o %s/%s"%\
                (self.sfi_path(),self.adfile(),self.sfi_path(),self.nodefile(),self.sfi_path(),self.reqfile()),
            self.sfi_user("allocate %s %s"%(self.hrn(),self.reqfile())),
            self.sfi_user("provision %s"%(self.hrn())),
            ]
        for command in commands:
            if self.test_plc.run_in_guest(command)!=0: return False
        return True

    def plc_name (self):
        return "%s_%s"%(self.test_auth_sfa.login_base,self.slice_spec['name'])

    # all local nodes in slice ?
    def sfa_check_slice_plc (self,options):
        "check sfa_create_slice at the plcs - all local nodes should be in slice"
        slice=self.test_plc.apiserver.GetSlices(self.test_plc.auth_root(), self.plc_name())[0]
        nodes=self.test_plc.apiserver.GetNodes(self.test_plc.auth_root(), {'peer_id':None})
        result=True
        for node in nodes: 
            if node['node_id'] in slice['node_ids']:
                utils.header("local node %s found in slice %s"%(node['hostname'],slice['name']))
            else:
                utils.header("ERROR - local node %s NOT FOUND in slice %s"%(node['hostname'],slice['name']))
                result=False
        return result

    # actually the same for now
    def sfa_update_slice(self,options):
        "run sfi create (on SM) on existing object"
        return self.sfa_create_slice(options)

    # run as pi
    def sfa_delete_slice(self,options):
	"run sfi delete"
	self.test_plc.run_in_guest(self.sfi_pi("delete %s"%(self.hrn(),)))
	return self.test_plc.run_in_guest(self.sfi_pi("remove -t slice %s"%(self.hrn(),)))==0

    def locate_private_key(self):
        return self.test_plc.locate_private_key_from_key_names ( [ self.slice_spec['key_name'] ] )

    # check the resulting sliver
    def ssh_slice_sfa(self,options,timeout_minutes=40,silent_minutes=0,period_seconds=15):
	"tries to ssh-enter the SFA slice"
        timeout  = timedelta(minutes=timeout_minutes)
        graceout = timedelta(minutes=silent_minutes)
        period   = timedelta(seconds=period_seconds)
        # locate a key
        private_key=self.locate_private_key()
        if not private_key :
            utils.header("WARNING: Cannot find a valid key for slice %s"%self.name())
            return False
        command="echo hostname ; hostname; echo id; id; echo uname -a ; uname -a"
        
        tasks=[]
        slicename=self.plc_name()
        dry_run = getattr(options,'dry_run',False)
        for nodename in self.slice_spec['nodenames']:
            (site_spec,node_spec) = self.test_plc.locate_node(nodename)
            tasks.append( CompleterTaskSshSlice(self.test_plc,node_spec['node_fields']['hostname'],
                                                slicename,private_key,command,expected=True,dry_run=dry_run))
        return Completer (tasks).run (timeout, graceout, period)
