# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import os, sys, time
import xmlrpclib

import utils

class TestUserSfa:

    def __init__ (self,test_plc):
	self.test_plc=test_plc
        # shortcuts
        self.sfa_spec=test_plc.plc_spec['sfa']
        self.piuser=self.sfa_spec['piuser']
        self.regularuser=self.sfa_spec['regularuser']
        self.login_base=self.sfa_spec['login_base']

    def add_user (self):
	return self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ add person.xml")==0

    def update_user (self):
	return self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ update person.xml")==0

    def delete_user(self):
	auth=self.sfa_spec['SFA_REGISTRY_ROOT_AUTH']
	return \
            self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ remove -t user %s.%s.%s"%(auth,self.login_base,self.regularuser))==0

