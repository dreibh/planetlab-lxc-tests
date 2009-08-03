import os, sys, time
import xmlrpclib

import utils

class TestUserSfa:

    def __init__ (self,test_plc,plc_spec_sfa):
	self.test_plc=test_plc
	self.spec_sfa=plc_spec_sfa

    def name(self):
        return self.user_spec['user_fields']['email']

    def add_user (self):
	return \
        self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ add  person.xml")==0

    def update_user (self):
	return \
        self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ update  person.xml")==0

    def delete_user(self):
	auth=self.spec_sfa['SFA_REGISTRY_ROOT_AUTH']
	return \
	self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ remove -t user %s.main.sfafakeuser1"%auth)==0

