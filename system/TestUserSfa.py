# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import os, sys, time
import xmlrpclib

import utils

class TestUserSfa:

    def __init__ (self,test_auth_sfa, user_spec):
        self.test_auth_sfa=test_auth_sfa
        self.user_spec=user_spec
        # shortcuts
        self.test_plc=self.test_auth_sfa.test_plc
        self.login_base=self.test_auth_sfa.login_base

    def sfi_path(self): return self.test_auth_sfa.sfi_path()
    def qualified(self,name): return self.test_auth_sfa.qualified(name)
    def sfi_pi(self,*args,**kwds): return self.test_auth_sfa.sfi_pi(*args, **kwds)
    def sfi_user(self,*args,**kwds): return self.test_auth_sfa.sfi_user(*args, **kwds)

    # xxx todo - not the right place any longer - or is it ?
    def sfa_add_user (self,options):
        "add a regular user using sfi add"
        user_hrn = self.qualified(self.user_spec['name'])
        command="add"
        command += " --type user"
        command += " --xrn %s"%user_hrn
        command += " --email %s"%self.user_spec['email']
        command += " " + " ".join(self.user_spec['add_options'])
        # handle key separately because of embedded whitespace
        # hack - the user's pubkey is avail from his hrn
        command += " -k %s/%s.pub"%(self.sfi_path(),user_hrn)
	return self.test_plc.run_in_guest(self.sfi_pi(command))==0

    def sfa_update_user (self,options):
        "update a user record using sfi update"
        user_hrn = self.qualified(self.user_spec['name'])
        command="update"
        command += " --type user"
        command += " --xrn %s"%user_hrn
        command += " " + " ".join(self.user_spec['update_options'])
	return self.test_plc.run_in_guest(self.sfi_pi(command))==0

    def sfa_delete_user(self,options):
	"run sfi delete on user record"
        user_hrn = self.qualified(self.user_spec['name'])
        command="remove -t user %s"%user_hrn
	return \
            self.test_plc.run_in_guest(self.sfi_pi(command))==0
