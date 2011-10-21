# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import os, sys, time
import xmlrpclib

import utils

class TestUserSfa:

    def __init__ (self,test_plc,sfa_slice_spec,test_slice_sfa):
	self.test_plc=test_plc
        self.sfa_slice_spec=sfa_slice_spec
        self.test_slice_sfa=test_slice_sfa
        # shortcuts
        self.sfa_spec=test_plc.plc_spec['sfa']
        self.piuser=self.sfa_slice_spec['piuser']
        self.regularuser=self.sfa_slice_spec['regularuser']
        self.login_base=self.sfa_slice_spec['login_base']

    def sfi_path(self): return self.test_slice_sfa.sfi_path()
    def addpersonfile(self): return self.test_slice_sfa.addpersonfile()

    # xxx todo - not the right place any longer - or is it ?
    def add_user (self):
	return self.test_plc.run_in_guest("sfi.py -d %s add %s"%
                                              (self.sfi_path(),self.addpersonfile()))==0

    def update_user (self):
	return self.test_plc.run_in_guest("sfi.py -d %s update %s"%
                                          (self.sfi_path(),self.addpersonfile()))==0

    def delete_user(self):
	auth=self.sfa_spec['SFA_REGISTRY_ROOT_AUTH']
	return \
            self.test_plc.run_in_guest("sfi.py -d %s remove -t user %s.%s.%s"%(
                self.sfi_path(),auth,self.login_base,self.regularuser))==0

