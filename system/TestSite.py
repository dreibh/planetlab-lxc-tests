import os.path
import datetime
import time
import traceback

import utils
from TestNode import TestNode
from TestUser import TestUser
from TestKey import TestKey

class TestSite:

    def __init__ (self,test_plc,site_spec):
	self.test_plc=test_plc
	self.site_spec=site_spec
        
    def name(self):
        return self.site_spec['site_fields']['login_base']

    def create_site (self):
        print self.test_plc.auth_root()
        self.test_plc.apiserver.AddSite(self.test_plc.auth_root(),
                                                    self.site_spec['site_fields'])
        self.test_plc.apiserver.AddSiteAddress(self.test_plc.auth_root(),self.name(),
                                            self.site_spec['address_fields'])
            
    def create_users (self):
        for user_spec in self.site_spec['users']:
            test_user=TestUser(self.test_plc,self,user_spec)
            test_user.create_user()
            test_user.add_keys()            

    def delete_site (self):
        print self.test_plc.auth_root()
        self.test_plc.apiserver.DeleteSite(self.test_plc.auth_root(),self.name())
        return True
            
    def delete_users(self):
        for user_spec in self.site_spec['users']:
            test_user=TestUser(self.test_plc,self,user_spec)
            test_user.delete_user()

    def locate_user (self,username):
        for user in self.site_spec['users']:
            if user['name'] == username:
                return user
            if user['user_fields']['email'] == username:
                return user
        raise Exception,"Cannot locate user %s"%username
        
    def locate_node (self,nodename):
        for node in self.site_spec['nodes']:
            if node['name'] == nodename:
                return node
        raise Exception,"Cannot locate node %s"%nodename
        
           
    
