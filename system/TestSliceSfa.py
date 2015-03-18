# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#

import os.path
import time
from datetime import datetime, timedelta
import json
import traceback

import utils
from TestNode import TestNode
from TestUser import TestUser
from TestBoxQemu import TestBoxQemu

from Completer import Completer, CompleterTask
from TestSlice import CompleterTaskSliceSsh

class TestSliceSfa:

    def __init__ (self, test_auth_sfa, slice_spec):
        self.test_auth_sfa = test_auth_sfa
        self.slice_spec = slice_spec
        # shortcuts
        self.test_plc = self.test_auth_sfa.test_plc

    def hrn (self): 
        return self.test_auth_sfa.obj_hrn(self.slice_spec['name'])
    def sfi_path (self):
        return self.test_auth_sfa.sfi_path()

    # send back up to the TestAuthSfa
    def sfi_path (self): return self.test_auth_sfa.sfi_path()
    def rspec_style (self): return self.test_auth_sfa.rspec_style()
    def sfi_pi(self,*args,**kwds): return self.test_auth_sfa.sfi_pi(*args, **kwds)
    def sfi_user(self,*args,**kwds): return self.test_auth_sfa.sfi_user(*args, **kwds)

    def discover_option(self):
        if self.rspec_style() == 'pg':
            return "-r GENI"
        else:
            return "-r sfa"

    # those are step names exposed as methods of TestPlc, hence the _sfa

    # needs to be run as pi
    def sfa_register_slice(self,options):
        "run sfi register (on Registry)"
        sfi_command  = "register"
        sfi_command += " --type slice"
        sfi_command += " --xrn {}".format(self.hrn())
        for opt in self.slice_spec['register_options']:
            sfi_command += " {}".format(opt)
        return self.test_plc.run_in_guest(self.sfi_pi(sfi_command))==0

    def sfa_renew_slice(self, options):
        "run sfi renew (on Aggregates)"
#        too_late =  (datetime.now() + timedelta(weeks=52)).strftime("%Y-%m-%d")
        one_month = (datetime.now() + timedelta(weeks=4)).strftime("%Y-%m-%d")
        too_late =  "+12m"
#        one_month = "+4w"
        # we expect this to fail on too long term attemps, but to succeed otherwise
        overall=True
        for ( renew_until, expected) in [ (too_late, False), (one_month, True) ] :
            sfi_command = "renew"
            sfi_command += " {}".format(self.hrn())
            sfi_command += " {}".format(renew_until)
            succeeded = self.test_plc.run_in_guest(self.sfi_user(sfi_command))==0
            if succeeded != expected:
                utils.header ("Expecting success={}, got {}".format(expected, succeeded))
                # however it turns out sfi renew always returns fine....
                #overall=False
            # so for helping manual checks:
            # xxx this should use sfa_get_expires below and actually check the expected result
            sfi_command = "show -k hrn -k expires {}".format(self.hrn())
            self.test_plc.run_in_guest(self.sfi_user(sfi_command))
        return overall

    def sfa_get_expires (self, options):
        filename = "{}.json".format(self.hrn())
        # /root/sfi/pg/<>
        inplc_filename = os.path.join(self.sfi_path(),filename)
        # /vservers/<>/root/sfi/... - cannot use os.path 
        inbox_filename = "{}{}".format(self.test_plc.vm_root_in_host(), inplc_filename)
        sfi_command  = ""
        sfi_command += "-R {} --rawformat json".format(inplc_filename)
        sfi_command += " status"
        sfi_command += " {}".format(self.hrn())
        # cannot find it if sfi status returns an error
        if self.test_plc.run_in_guest (self.sfi_user(sfi_command)) !=0: return
        if self.test_plc.test_ssh.fetch(inbox_filename,filename)!=0: return 
        try:
            with open(filename) as f:
                status = json.loads(f.read())
            value = status['value']
            sliver = value['geni_slivers'][0]
            expires = sliver['geni_expires']
            print(" * expiration for {} (first sliver) -> {}".format(self.hrn(), expires))
            return expires
        except:
            traceback.print_exc()

    # helper - filename to store a given result
    def _resname (self,name,ext): return "{}.{}".format(name, ext)
    def adfile (self): return self._resname("ad","rspec")
    def reqfile (self): return self._resname("req","rspec")
    def empty_reqfile (self): return "empty-rspec.xml"
    def nodefile (self): return self._resname("nodes","txt")
    
    # run as user
    def sfa_discover(self,options):
        "discover resources into resouces_in.rspec"
        return self.test_plc.run_in_guest(self.sfi_user(\
                "resources {} -o {}/{}"\
                    .format(self.discover_option(),self.sfi_path(),self.adfile()))) == 0

    def sfa_rspec(self,options):
        "invoke sfiListNodes and sfiAddSlivers to prepare a rspec"
        commands = [
            "sfiListNodes.py -i {}/{} -o {}/{}".format(self.sfi_path(), self.adfile(),
                                                       self.sfi_path(), self.nodefile()),
            "sfiAddSliver.py -i {}/{} -n {}/{} -o {}/{}".format(self.sfi_path(), self.adfile(),
                                                                self.sfi_path(), self.nodefile(),
                                                                self.sfi_path(), self.reqfile()),
            ]
        for command in commands:
            if self.test_plc.run_in_guest(command) != 0: return False
        return True

    def _sfa_allocate(self,file,options):
        command = self.sfi_user("allocate {} {}".format(self.hrn(), file))
        return self.test_plc.run_in_guest(command) == 0

    def sfa_allocate(self,options):
        "invoke run sfi allocate (on SM)"
        return self._sfa_allocate(self.reqfile(),options)
    def sfa_allocate_empty(self,options):
        "invoke run sfi allocate (on SM) with an empty rspec"
        return self._sfa_allocate(self.empty_reqfile(),options)

    def sfa_provision(self,options):
        "invoke run sfi provision (on SM)"
        command = self.sfi_user("provision {}".format(self.hrn()))
        return self.test_plc.run_in_guest(command) == 0
    # just a synonym
    sfa_provision_empty = sfa_provision

    def plc_name (self):
        return "{}_{}".format(self.test_auth_sfa.login_base, self.slice_spec['name'])

    # all local nodes in slice ?
    def sfa_check_slice_plc (self,options):
        "check the slice has been created at the plc - all local nodes should be in slice"
        slice = self.test_plc.apiserver.GetSlices(self.test_plc.auth_root(), self.plc_name())[0]
        nodes = self.test_plc.apiserver.GetNodes(self.test_plc.auth_root(), {'peer_id':None})
        result = True
        for node in nodes: 
            if node['node_id'] in slice['node_ids']:
                utils.header("local node {} found in slice {}".format(node['hostname'], slice['name']))
            else:
                utils.header("ERROR - local node {} NOT FOUND in slice {}"\
                             .format(node['hostname'], slice['name']))
                result = False
        return result

    # no node left in slice ?
    def sfa_check_slice_plc_empty (self,options):
        "check the slice have been emptied at the plcs - no node should be in slice"
        slices = self.test_plc.apiserver.GetSlices(self.test_plc.auth_root(), 
                                                 self.plc_name(),
                                                 ['node_ids'])
        return not slices[0]['node_ids']

    # xxx historically this used to do the same as sfa-create-slice
    # which was later on split into 3 distinct steps, 
    # and we can ignore the first that is about setting up the rspec
    def sfa_update_slice(self,options):
        "re-run sfi allocate and provision (on SM) on existing object"
        return self.sfa_allocate(options) and self.sfa_provision(options)

    # run as pi
    def sfa_delete_slice(self,options):
        "run sfi delete"
        self.test_plc.run_in_guest(self.sfi_pi("delete {}".format(self.hrn())))
        return self.test_plc.run_in_guest(self.sfi_pi("remove -t slice {}".format(self.hrn()))) == 0

    def locate_private_key(self):
        return self.test_plc.locate_private_key_from_key_names ( [ self.slice_spec['key_name'] ] )

    # check the resulting sliver
    def ssh_slice_sfa(self, options, timeout_minutes=40, silent_minutes=0, period_seconds=15):
        "tries to ssh-enter the SFA slice"
        timeout  = timedelta(minutes=timeout_minutes)
        graceout = timedelta(minutes=silent_minutes)
        period   = timedelta(seconds=period_seconds)
        # locate a key
        private_key=self.locate_private_key()
        if not private_key :
            utils.header("WARNING: Cannot find a valid key for slice {}".format(self.name()))
            return False
        command="echo hostname ; hostname; echo id; id; echo uname -a ; uname -a"
        
        tasks=[]
        slicename=self.plc_name()
        dry_run = getattr(options,'dry_run',False)
        for nodename in self.slice_spec['nodenames']:
            (site_spec,node_spec) = self.test_plc.locate_node(nodename)
            tasks.append( CompleterTaskSliceSsh(self.test_plc, node_spec['node_fields']['hostname'],
                                                slicename, private_key, command,
                                                expected=True, dry_run=dry_run))
        return Completer (tasks, message='ssh_slice_sfa').run(timeout, graceout, period)
