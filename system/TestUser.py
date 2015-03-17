# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import os, sys, time
import xmlrpclib

import utils

class TestUser:

    def __init__ (self, test_plc, test_site, user_spec):
	self.test_plc = test_plc
	self.test_site = test_site
	self.user_spec = user_spec

    def name(self):
        return self.user_spec['user_fields']['email']

    def auth (self):
        person = self.user_spec['user_fields']
        return {'Username'   : person['email'],
                'AuthMethod' : 'password',
                'AuthString' : person['password'],
                'Role'       : self.user_spec['roles'][0],
                }

    def create_user (self):
        user_spec = self.user_spec
        fields = user_spec['user_fields']
        auth = self.test_plc.auth_root()
        utils.header('Adding user {} - roles {}'.format(fields['email'], user_spec['roles']))
        self.test_plc.apiserver.AddPerson(auth, fields)
        self.test_plc.apiserver.UpdatePerson(auth, fields['email'], {'enabled': True})
        for role in user_spec['roles']:
            self.test_plc.apiserver.AddRoleToPerson(auth,role,fields['email'])
        self.test_plc.apiserver.AddPersonToSite(auth,
                                                self.name(),
                                                self.test_site.name())

    def delete_user(self):
        auth = self.test_plc.auth_root()
        self.test_plc.apiserver.DeletePerson(auth,self.name())

    def add_keys (self):
        user_spec = self.user_spec
        for key_name in user_spec['key_names']:
            key_spec = self.test_plc.locate_key(key_name)
            auth = self.auth()
            self.test_plc.apiserver.AddPersonKey(auth,self.name(), key_spec['key_fields'])
