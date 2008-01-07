#!/usr/bin/python
#
# Test script example
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: Test.py,v 1.18 2007/01/09 16:22:49 mlhuang Exp $
#

from pprint import pprint
from string import letters, digits, punctuation
from traceback import print_exc
from optparse import OptionParser
import base64
import os
import socket
import xmlrpclib

from Config import Config
from logger import log
from random import Random
random = Random()

config = Config()
api = config.api
auth = api.auth

boot_states = api.GetBootStates(auth)
roles = [role['name'] for role in api.GetRoles(auth)]
methods = api.GetNetworkMethods(auth)
types = api.GetNetworkTypes(auth)

#ifrom PLC.Shell import Shell
#shell = Shell(globals())

def randfloat(min = 0.0, max = 1.0):
    return float(min) + (random.random() * (float(max) - float(min)))

def randint(min = 0, max = 1):
    return int(randfloat(min, max + 1))

# See "2.2 Characters" in the XML specification:
#
# #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD]
# avoiding
# [#x7F-#x84], [#x86-#x9F], [#xFDD0-#xFDDF]

ascii_xml_chars = map(unichr, [0x9, 0xA, 0xD])
ascii_xml_chars += map(unichr, xrange(0x20, 0x7F - 1))
low_xml_chars = list(ascii_xml_chars)
low_xml_chars += map(unichr, xrange(0x84 + 1, 0x86 - 1))
low_xml_chars += map(unichr, xrange(0x9F + 1, 0xFF))
valid_xml_chars = list(low_xml_chars)
valid_xml_chars += map(unichr, xrange(0xFF + 1, 0xD7FF))
valid_xml_chars += map(unichr, xrange(0xE000, 0xFDD0 - 1))
valid_xml_chars += map(unichr, xrange(0xFDDF + 1, 0xFFFD))


def randstr(length, pool = valid_xml_chars, encoding = "utf-8"):
    sample = random.sample(pool, min(length, len(pool)))
    while True:
        s = u''.join(sample)
        bytes = len(s.encode(encoding))
        if bytes > length:
            sample.pop()
        elif bytes < length:
            sample += random.sample(pool, min(length - bytes, len(pool)))
            random.shuffle(sample)
        else:
            break
    return s

def randhostname():
    # 1. Each part begins and ends with a letter or number.
    # 2. Each part except the last can contain letters, numbers, or hyphens.
    # 3. Each part is between 1 and 64 characters, including the trailing dot.
    # 4. At least two parts.
    # 5. Last part can only contain between 2 and 6 letters.
    hostname = 'a' + randstr(61, letters + digits + '-') + '1.' + \
               'b' + randstr(61, letters + digits + '-') + '2.' + \
               'c' + randstr(5, letters)
    return hostname

def randpath(length):
    parts = []
    for i in range(randint(1, 10)):
        parts.append(randstr(randint(1, 30), ascii_xml_chars))
    return os.sep.join(parts)[0:length]

def randemail():
    return (randstr(100, letters + digits) + "@" + randhostname()).lower()

def randkey(bits = 2048):
    key_types = ["ssh-dss", "ssh-rsa"]
    key_type = random.sample(key_types, 1)[0]
    return ' '.join([key_type,
                     base64.b64encode(''.join(randstr(bits / 8).encode("utf-8"))),
                     randemail()])

def random_site():
    return {
        'name': randstr(254),
        'abbreviated_name': randstr(50),
        'login_base': randstr(20, letters).lower(),
        'latitude': int(randfloat(-90.0, 90.0) * 1000) / 1000.0,
        'longitude': int(randfloat(-180.0, 180.0) * 1000) / 1000.0,
        }
            
def random_address_type():
    return {
        'name': randstr(20),
        'description': randstr(254),
        }

def random_address():
    return {
        'line1': randstr(254),
        'line2': randstr(254),
        'line3': randstr(254),
        'city': randstr(254),
        'state': randstr(254),
        'postalcode': randstr(64),
        'country': randstr(128),
        }

def random_person():
    return {
        'first_name': randstr(128),
        'last_name': randstr(128),
        'email': randemail(),
        'bio': randstr(254),
        # Accounts are disabled by default
        'enabled': False,
        'password': randstr(254),
        }

def random_key():
    return {
        'key_type': random.sample(key_types, 1)[0],
        'key': randkey()
        }

def random_slice():
    return {
        'name': site['login_base'] + "_" + randstr(11, letters).lower(),
        'url': "http://" + randhostname() + "/",
        'description': randstr(2048),
        }

def random_nodegroup():
    return {
        'name': randstr(50),
        'description': randstr(200),
        }

def random_node():
   return {
       'hostname': randhostname(),
       'boot_state': random.sample(boot_states, 1)[0],
       'model': randstr(255),
       'version': randstr(64),
       }

def random_nodenetwork():
    nodenetwork_fields = {
        'method': random.sample(methods, 1)[0],
        'type': random.sample(types, 1)[0],
        'bwlimit': randint(500000, 10000000),
        }

    if method != 'dhcp':
        ip = randint(0, 0xffffffff)
        netmask = (0xffffffff << randint(2, 31)) & 0xffffffff
        network = ip & netmask
        broadcast = ((ip & netmask) | ~netmask) & 0xffffffff
        gateway = randint(network + 1, broadcast - 1)
        dns1 = randint(0, 0xffffffff)

        for field in 'ip', 'netmask', 'network', 'broadcast', 'gateway', 'dns1':
            nodenetwork_fields[field] = socket.inet_ntoa(struct.pack('>L', locals()[field]))

    return nodenetwork_fields

def random_pcu():
    return {
        'hostname': randhostname(),
        'ip': socket.inet_ntoa(struct.pack('>L', randint(0, 0xffffffff))),
        'protocol': randstr(16),
        'username': randstr(254),
        'password': randstr(254),
        'notes': randstr(254),
        'model': randstr(32),
        }

def random_conf_file():
    return {
        'enabled': bool(randint()),
        'source': randpath(255),
        'dest': randpath(255),
        'file_permissions': "%#o" % randint(0, 512),
        'file_owner': randstr(32, letters + '_' + digits),
        'file_group': randstr(32, letters + '_' + digits),
        'preinstall_cmd': randpath(100),
        'postinstall_cmd': randpath(100),
        'error_cmd': randpath(100),
        'ignore_cmd_errors': bool(randint()),
        'always_update': bool(randint()),
        }

def random_attribute_type():
    return {
        'name': randstr(100),
        'description': randstr(254),
        'min_role_id': random.sample(roles.values(), 1)[0],
        }

def isequal(object_fields, expected_fields):
    for field in expected_fields:
	assert field in object_fields
	assert object_fields[field] == expected_fields[field]

def islistequal(list1, list2):
    assert set(list1) == set(list2) 

def isunique(id, id_list):
    assert id not in id_list

def get_methods(self, prefix):
    method_list = filter(lambda name: name.startswith(prefix), self.methods)



tests = [
    # test_type: (Method, arguments, method_result_holder, number_to_add) 	
    {'add': (api.AddSite, random_site(), site_ids, 3),
     'add_check': (isunique, 	 

    ]

class Entity:
    """
    Template class for testing Add methods
    """ 	
    def __init__(self, auth, add_method, update_method, get_method, delete_method, primary_key):    
	
	self.methods_tested = []
	for method in [add_method, update_method, get_method, delete_method]:
	    self.methods_tested.append(method._Method_name)
	
	self.auth = auth
	self.Add = log(add_method)
	self.Update = log(update_method)
	self.Get = log(get_method)
	self.Delete = log(delete_method)
	self.primary_key = primary_key
   	self.object_ids = []
	 
    def test(self, args_method, num):
	
	self.object_ids = []
	
	for i in range(num):  
	    # Add object
	    object_fields = args_method()
	    object_id = self.Add(self.auth, object_fields)
	    
	    # Should return a unique id
	    AddCheck = log(isunique, 'Unique Check')
	    AddCheck(object_id, object_ids)
	    self.object_ids.extend([object_id])

	    # Check object
	    object = slef.Get(self.auth, [object_id])[0]
	    CheckObject = log(isequal, 'Add Check')
	    CheckObject(object, object_fields)
	    
	    # Update object
	    object_fields = args_method()
	    self.Update(self.auth, object_id, object_fields)

	    # Check again
	    object = self.Get(self.auth, [object_id])[0]
	    CheckObject = log(isqeual, 'Update Check')  	
	    CheckSite(object, object_fields)

	# Check Get all sites
	objects = self.Get(self.auth, object_ids)
	CheckObjects = log(islistqual, 'Get Check')
	CheckObjects(object_ids, [object[self.primary_key] for object in objects])  	    
	    
	return self.object_ids

    def cleanup(self):
	# Delete objects
	for object_id in sefl.object_ids:
	    self.Delete(self.auth, object_id)
	    
	# Check if objects are deleted
	CheckObjects = log(islistequal, 'Delete Check')	
	ChecObjects(api.Get(auth, self.object_ids), [])	 	
	

	
class Test:
    def __init__(self, config, verbose = True):
	self.check = True
        self.verbose = verbose
	self.methods = set(api.system.listMethods())
	self.methods_tested = set()
	
	self.site_ids = []
        self.address_type_ids = []
        self.address_ids = []
        self.person_ids = []


    def run(self,
            sites = 1,
            address_types = 3,
            addresses = 2,
            persons = 1000,
            keys = 3):
        try:
            try:
                site_test = Entity(auth, api.AddSite, api.UpdateSite, api.GetSite, api.DeleteSite, 'site_id')		     site_test.test(random_site, sites)

                self.AddressTypes(address_types)
                self.AddAddresses(addresses)
                self.AddPersons(persons)
            except:
                print_exc()
        finally:
	    for method in set(self.methods).difference(self.methoods_tested):
		print >> test_log, "%(method)s [Not Tested]" % locals()	

    def cleanup(self):
        self.DeletePersons()
        self.DeleteAddresses()
        self.DeleteAddressTypes()
        self.DeleteSites()

    	

    def Sites(self, n = 1):
        """
        Add and Modify a random site.
        """

	for i in range(n):
            # Add site
            site_fields = random_site()
	    AddSite = log(api.AddSite)
            site_id = AddSite(auth, site_fields)
	    self.methods_tested.update(['AddSite'])		
            
	    # Should return a unique site_id
            CheckSite = log(isunique, 'Unique Check')
	    CheckSite(site_id, self.site_ids)
            self.site_ids.append(site_id)

            # Check site
	    GetSites = log(api.GetSites)
            site = GetSites(auth, [site_id])[0]
	    CheckSite = log(isequal, 'AddSite Check')
	    CheckSite(site, site_fields)
	    self.methods_tested.update(['GetSites'])	

            # Update site
            site_fields = random_site()
            # XXX Currently cannot change login_base
            del site_fields['login_base']
            site_fields['max_slices'] = randint(1, 10)
            UpdateSite = log(api.UpdateSite)
	    UpdateSite(auth, site_id, site_fields)
	    self.methods_tested.update(['UpdateSite'])

            # Check site again
            site = GetSites(auth, [site_id])[0]
	    CheckSite = log(isequal, 'UpdateSite Check')
	    CheckSite(site, site_fields)

         
	# Check Get all sites   
        sites = GetSites(auth, self.site_ids)
        CheckSite = log(islistequal, 'GetSites Check')
	CheckSite(self.site_ids, [site['site_id'] for site in sites])

        if self.verbose:
            print "Added sites", self.site_ids

    def DeleteSites(self):
        """
        Delete any random sites we may have added.
        """
	# Delete all sites
	DeleteSite = log(api.DeleteSite)
        for site_id in self.site_ids:
            DeleteSite(auth, site_id)
	self.methods_tested.update(['DeleteSite'])

	# Check if sites are deleted
	CheckSite = log(islistequal, 'DeleteSite Check')
	CheckSite(api.GetSites(auth, self.site_ids), [])

        if self.verbose:
            print "Deleted sites", self.site_ids

        self.site_ids = []

    def AddAddressTypes(self, n = 3):
        """
        Add a number of random address types.
        """
        
        for i in range(n):
            address_type_fields = random_address_type()
	    AddAddressType = log(api.AddAddressType)
            address_type_id = AddAddressType(auth, address_type_fields)
	    self.methods_tested.update(['AddAddressType'])

            # Should return a unique address_type_id
            CheckAddressType = log(isunique, 'Unique Check')
	    CheckAddressType(address_type_id, self.address_type_ids)
	    self.address_type_ids.append(address_type_id)

            # Check address type
	    GetAddressTypes = log(api.GetAddressTypes)
            address_type = GetAddressTypes(auth, [address_type_id])[0]
	    CheckAddressType = log(isequal, 'AddAddressType Check')
	    CheckAddressType(address_type, address_type_fields)

            # Update address type
            address_type_fields = random_address_type()
	    UpdateAddressType = log(api.UpdateAddressType)
            UpdateAddressType(auth, address_type_id, address_type_fields)
            
            # Check address type again
            address_type = GetAddressTypes([address_type_id])[0]
	    CheckAddressType = log(isequal, 'UpdateAddressType Check')
	    CheckAddressType(address_type, address_type_fields)
	    self.methods_tested.update(['UpdateAddressType'])

	# Check get all address types
        address_types = GetAddressTypes(auth, self.address_type_ids)
	CheckAddressType = log(islistequal, 'GetAddressType Check')
	CheckAddressType(self.address_type_ids, 
			 [address_type['address_type_id' for address_type in address_types])
	self.methods_tested.update(['GetAddressTypes'])

        if self.verbose:
            print "Added address types", self.address_type_ids

    def DeleteAddressTypes(self):
        """
        Delete any random address types we may have added.
        """

	DeleteAddressType = log(api.DeleteAddressType)
        for address_type_id in self.address_type_ids:
            DeleteAddressType(auth, address_type_id)
	self.methods_tested.update(['DeleteAddressType'])

	CheckAddressType = log(islistequal, 'DeleteAddressType Check')
	CheckAddressType(api.GetAddressTypes(auth, self.address_type_ids), [])

        if self.verbose:
            print "Deleted address types", self.address_type_ids

        self.address_type_ids = []

    def AddAddresses(self, n = 3):
        """
        Add a number of random addresses to each site.
        """

        for site_id in self.site_ids:
            for i in range(n):
                address_fields = random_address()
                address_id = AddSiteAddress(site_id, address_fields)

                # Should return a unique address_id
                assert address_id not in self.address_ids
                self.address_ids.append(address_id)

                if self.check:
                    # Check address
                    address = GetAddresses([address_id])[0]
                    for field in address_fields:
                        assert address[field] == address_fields[field]

                    # Update address
                    address_fields = random_address()
                    UpdateAddress(address_id, address_fields)

                    # Check address again
                    address = GetAddresses([address_id])[0]
                    for field in address_fields:
                        assert address[field] == address_fields[field]

                # Add address types
                for address_type_id in self.address_type_ids:
                    AddAddressTypeToAddress(address_type_id, address_id)

        if self.check:
            addresses = GetAddresses(self.address_ids)
            assert set(self.address_ids) == set([address['address_id'] for address in addresses])
            for address in addresses:
                assert set(self.address_type_ids) == set(address['address_type_ids'])

        if self.verbose:
            print "Added addresses", self.address_ids

    def DeleteAddresses(self):
        """
        Delete any random addresses we may have added.
        """

        # Delete site addresses
        for address_id in self.address_ids:
            # Remove address types
            for address_type_id in self.address_type_ids:
                DeleteAddressTypeFromAddress(address_type_id, address_id)

            if self.check:
                address = GetAddresses([address_id])[0]
                assert not address['address_type_ids']

            DeleteAddress(address_id)
            if self.check:
                assert not GetAddresses([address_id])

        if self.check:
            assert not GetAddresses(self.address_ids)

        if self.verbose:
            print "Deleted addresses", self.address_ids

        self.address_ids = []

    def AddPersons(self, n = 3):
        """
        Add a number of random users to each site.
        """

        roles = GetRoles()
        role_ids = [role['role_id'] for role in roles]
        roles = [role['name'] for role in roles]
        roles = dict(zip(roles, role_ids))

        for i in range(n):

            # Add account
            person_fields = random_person()
            person_id = AddPerson(person_fields)

            # Should return a unique person_id
            assert person_id not in self.person_ids
            self.person_ids.append(person_id)

            if self.check:
                # Check account
                person = GetPersons([person_id])[0]
                for field in person_fields:
                    if field != 'password':
                        assert person[field] == person_fields[field]

                # Update account
                person_fields = random_person()
                UpdatePerson(person_id, person_fields)

                # Check account again
                person = GetPersons([person_id])[0]
                for field in person_fields:
                    if field != 'password':
                        assert person[field] == person_fields[field]

            auth = {'AuthMethod': "password",
                    'Username': person_fields['email'],
                    'AuthString': person_fields['password']}

            if self.check:
                # Check that account is disabled
                try:
                    assert not AuthCheck(auth)
                except:
                    pass

            # Add random set of roles
            person_roles = random.sample(['user', 'pi', 'tech'], randint(1, 3))
            for person_role in person_roles:
                role_id = roles[person_role]
                AddRoleToPerson(role_id, person_id)

            if self.check:
                person = GetPersons([person_id])[0]
                assert set(person_roles) == set(person['roles'])

            # Enable account
            UpdatePerson(person_id, {'enabled': True})

            if self.check:
                # Check that account is enabled
                assert AuthCheck(auth)

            # Associate account with random set of sites
            person_site_ids = []
            for site_id in random.sample(self.site_ids, randint(1, len(self.site_ids))):
                AddPersonToSite(person_id, site_id)
                person_site_ids.append(site_id)

            if self.check:
                # Make sure it really did it
                person = GetPersons([person_id])[0]
                assert set(person_site_ids) == set(person['site_ids'])

            # Set a primary site
            primary_site_id = random.sample(person_site_ids, randint(1, len(person_site_ids)))[0]
            SetPersonPrimarySite(person_id, primary_site_id)

            if self.check:
                person = GetPersons([person_id])[0]
                assert person['site_ids'][0] == primary_site_id

        if self.verbose:
            print "Added users", self.person_ids

    def DeletePersons(self):
        # Delete users
        for person_id in self.person_ids:
            # Remove from each site
            for site_id in self.site_ids:
                DeletePersonFromSite(person_id, site_id)

            if self.check:
                person = GetPersons([person_id])[0]
                assert not person['site_ids']

            # Revoke roles
            person = GetPersons([person_id])[0]
            for role_id in person['role_ids']:
                DeleteRoleFromPerson(role_id, person_id)

            if self.check:
                person = GetPersons([person_id])[0]
                assert not person['role_ids']

            # Disable account
            UpdatePerson(person_id, {'enabled': False})

            if self.check:
                person = GetPersons([person_id])[0]
                assert not person['enabled']

            # Delete account
            DeletePerson(person_id)

            if self.check:
                assert not GetPersons([person_id])                         

        if self.check:
            assert not GetPersons(self.person_ids)

        if self.verbose:
            print "Deleted users", self.person_ids

        self.person_ids = []

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-c", "--check", action = "store_true", default = False, help = "Verify actions (default: %default)")
    parser.add_option("-q", "--quiet", action = "store_true", default = False, help = "Be quiet (default: %default)")
    parser.add_option("-p", "--populate", action = "store_true", default = False, help = "Do not cleanup (default: %default)")
    (options, args) = parser.parse_args()
    test = Test(check = options.check, verbose = not options.quiet)
    test.run()
    if not options.populate:
        test.cleanup()
