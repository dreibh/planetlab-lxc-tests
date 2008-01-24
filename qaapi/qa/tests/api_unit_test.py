#!/usr/bin/python
#
# Test script example
#
# Copyright (C) 2006 The Trustees of Princeton University
#
#

from pprint import pprint
from string import letters, digits, punctuation
from traceback import print_exc
import base64
import os, sys
import socket
import xmlrpclib
import time

from Test import Test
from qa import utils
from qa.Config import Config
from qa.logger import Logfile, log
from random import Random

random = Random()

config = Config()
auth = config.auth

try: boot_states = config.api.GetBootStates(auth)
except: boot_states = [u'boot', u'dbg', u'inst', u'new', u'rcnf', u'rins']

try: roles = [role['name'] for role in config.api.GetRoles(auth)]
except: roles = [u'admin', u'pi', u'user', u'tech']

try: methods = config.api.GetNetworkMethods(auth)
except: methods = [u'static', u'dhcp', u'proxy', u'tap', u'ipmi', u'unknown']

try:types = config.api.GetNetworkTypes(auth)
except: types = [u'ipv4']

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
    try:	
        for field in expected_fields:
	    assert field in object_fields
	    assert object_fields[field] == expected_fields[field]
    except:
	return False
    return True

def islistequal(list1, list2):
    try: 
	assert set(list1) == set(list2) 
    except:
	return False
    return True
	
def isunique(id, id_list):
    try:
	assert id not in id_list
    except:
	return False
    return True
	
class api_unit_test(Test):
    
    def call(self,
	     sites = 2,
	     nodes = 4,
             address_types = 3,
             addresses = 2,
             persons = 10, 
	     keys = 3
	    ):
	self.api = self.config.api
	self.auth = self.config.auth
	self.all_methods = set(self.api.system.listMethods()) 
	self.methods_tested = set()
	self.methods_failed = set()

	try:
	    try:
	        self.site_ids = self.Sites(sites)
        	self.node_ids = self.Nodes(nodes)
	    except:
		print_exc()
	finally:
	    try:
		self.cleanup()
	    finally: 
		 
	        logfile = Logfile("api-unittest.log")
		methods_ok = list(self.methods_tested.difference(self.methods_failed))
		methods_failed = list(self.methods_failed)
		methods_untested = list(self.all_methods.difference(self.methods_tested))
		methods_ok.sort()
		methods_failed.sort()
		methods_untested.sort()
		print >> logfile, "\n".join([m+": [OK]" for m in  methods_ok])
	        print >> logfile, "\n".join([m+": [FAILED]" for m in methods_failed])
		print >> logfile, "\n".join([m+": [Not Tested]" for m in  methods_untested])
 
    def isequal(self, object_fields, expected_fields, method_name):
        try:
            for field in expected_fields:
                assert field in object_fields
                assert object_fields[field] == expected_fields[field]
        except:
	    self.methods_failed.update([method_name])	 
	    return False
        return True

    def islistequal(self, list1, list2, method_name):
        try: assert set(list1) == set(list2)
        except:
	    self.methods_failed.update([method_name]) 
	    return False
        return True

    def isunique(self, id, id_list, method_name):
        try: assert id not in id_list
        except:
	    self.methods_failed.update([method_name]) 	 
	    return False
        return True

    def debug(self, method, method_name=None):
	if method_name is None:
	     method_name = method._Method__name

        self.methods_tested.update([method_name])
	def wrapper(*args, **kwds):
	    try:
	        return method(*args, **kwds)
	    except:
	        self.methods_failed.update([method_name])
		return None

	return wrapper
 
    def cleanup(self):
        #if self.person_ids: self.DeletePersons()
        #if self.address_ids: self.DeleteAddresses()
        #if self.address_type_ids: self.DeleteAddressTypes()
        if hasattr(self, 'node_ids'): self.DeleteNodes()
	if hasattr(self, 'site_ids'): self.DeleteSites()
	

    def Sites(self, n=4):
	site_ids = []
	for i in range(n):
	    # Add Site
	    site_fields = random_site()
	    AddSite = self.debug(self.api.AddSite) 
	    site_id = AddSite(self.auth, site_fields)
	    if site_id is None: continue

	    # Should return a unique id
	    self.isunique(site_id, site_ids, 'AddSite - isunique')
	    site_ids.append(site_id)
	    GetSites = self.debug(self.api.GetSites)
	    sites = GetSites(self.auth, [site_id])
	    if sites is None: continue
	    site = sites[0]
	    self.isequal(site, site_fields, 'AddSite - isequal')
	
	    # Update site
	    site_fields = random_site()
	    UpdateSite = self.debug(self.api.UpdateSite)
	    result = UpdateSite(self.auth, site_id, site_fields)

	    # Check again
	    sites = GetSites(self.auth, [site_id])
	    if sites is None: continue
	    site = sites[0] 	 
	    self.isequal(site, site_fields, 'UpdateSite - isequal')
	    
	sites = GetSites(self.auth, site_ids)
	if sites is not None: 
	    self.islistequal(site_ids, [site['site_id'] for site in sites], 'GetSites - isequal')
	
	if self.config.verbose:
	    utils.header("Added sites: %s" % site_ids)    	

	return site_ids


    def DeleteSites(self):
        # Delete all sites
        DeleteSite = self.debug(self.api.DeleteSite)
        for site_id in self.site_ids:
            result = DeleteSite(self.auth, site_id)

        # Check if sites are deleted
	GetSites = self.debug(self.api.GetSites)
	sites = GetSites(self.auth, self.site_ids) 
        self.islistequal(sites, [], 'DeleteSite - check')	

        if self.config.verbose:
            utils.header("Deleted sites: %s" % self.site_ids)

        self.site_ids = []	 	 

    def Nodes(self, n=4):
	node_ids = []
	for i in range(n):
	    # Add Node
	    node_fields = random_node()
	    site_id = random.sample(self.site_ids, 1)[0]
	    AddNode = self.debug(self.api.AddNode)
	    node_id = AddNode(self.auth, site_id, node_fields)
	    if node_id is None: continue
	    
	    # Should return a unique id
	    self.isunique(node_id, node_ids, 'AddNode - isunique')
	    node_ids.append(node_id)

	    # Check nodes
	    GetNodes = self.debug(self.api.GetNodes)
	    nodes = GetNodes(self.auth, [node_id])
	    if nodes is None: continue
	    node = nodes[0]
	    self.isequal(node, node_fields, 'AddNode - isequal')
	
	    # Update node
	    node_fields = random_node()
	    UpdateNode = self.debug(self.api.UpdateNode)
	    result = UpdateNode(self.auth, node_id, node_fields)
	    
	    # Check again
	    nodes = GetNodes(self.auth, [node_id])
	    if nodes is None: continue
	    node = nodes[0]
	    self.isequal(node, node_fields, 'UpdateNode - isequal')
	
	nodes = GetNodes(self.auth, node_ids)
	if nodes is not None:
	    self.islistequal(node_ids, [node['node_id'] for node in nodes], 'GetNodes - isequal')

	if self.config.verbose:
            utils.header("Added nodes: %s" % node_ids)
	
	return node_ids

    def DeleteNodes(self):
	DeleteNode = self.debug(self.api.DeleteNode)
	for node_id in self.node_ids:
	    result = DeleteNode(self.auth, node_id)

	# Check if nodes are deleted
	GetNodes = self.debug(self.api.GetNodes)
	nodes = GetNodes(self.api, self.node_ids)
	self.islistequal(nodes, [], 'DeleteNode Check')

	if self.config.verbose:
	    utils.header("Deleted nodes: %s" % self.node_ids)
	
	self.node_ids = []
		 		 
    def AddressTypes(self, n = 3):
        address_type_ids = []
        for i in range(n):
            address_type_fields = random_address_type()
	    AddAddressType = self.debug(self.api.AddAddressType)
            address_type_id = AddAddressType(self.auth, address_type_fields)
	    if address_type_id is None: continue

            # Should return a unique address_type_id
	    self.isunique(address_type_id, address_type_ids, 'AddAddressType - isunique') 
	    address_type_ids.append(address_type_id)

            # Check address type
	    GetAddressTypes = self.debug(self.api.GetAddressTypes)
            address_types = GetAddressTypes(self.auth, [address_type_id])
	    if address_types is None: continue
	    address_type = address_types[0]
	    self.isequal(address_type, address_type_fields, 'AddAddressType - isequal')

            # Update address type
            address_type_fields = random_address_type()
	    UpdateAddressType = self.debug(self.api.UpdateAddressType)
            result = UpdateAddressType(self.auth, address_type_id, address_type_fields)
	    if result is None: continue
            
            # Check address type again
            address_types = GetAddressTypes(self.auth, [address_type_id])
	    if address_types is None: continue
	    address_type = address_types[0]	
	    self.isequal(address_type, address_type_fields, 'UpdateAddressType - isequal') 	

	# Check get all address types
        address_types = GetAddressTypes(self.auth, address_type_ids)
	if address_types is not None:
	    self.islistequal(address_type_ids, [address_type['address_type_id'] for address_type in address_types], 'GetAddressTypes - isequal')

        if self.config.verbose:
            print "Added address types", address_type_ids

	return address_type_ids

    def DeleteAddressTypes(self):

	DeleteAddressType = self.debug(self.api.DeleteAddressType)
        for address_type_id in self.address_type_ids:
            DeleteAddressType(auth, address_type_id)

	GetAddressTypes = self.debug(self.api.GetAddressTypes)
	address_types = GetAddressTypes(self.auth, self.address_type_ids)
	self.islistequal(address_types, [], 'DeleteAddressType - check')

        if self.config.verbose:
            utils.header("Deleted address types: " % self.address_type_ids)

        self.address_type_ids = []

    def Addresses(self, n = 3):
	address_ids = []
        for i in range(n):
            address_fields = random_address()
	    site_id = random.sample(self.site_ids, 1)[0]	
	    AddSiteAddress = self.debug(self.api.AddSiteAddress)
            address_id = AddSiteAddress(self.auth, site_id, address_fields)
	    if address_id is None: continue 
	
            # Should return a unique address_id
	    self.isunique(address_id, address_ids, 'AddSiteAddress - isunique')
	    address_ids.append(address_id)

	    # Check address
	    GetAddresses = self.debug(self.api.GetAddresses)  
	    addresses = GetAddresses(self.auth, [address_id])
	    if addresses is None: continue
	    address = addresses[0]
	    self.isequal(address, address_fields, 'AddSiteAddress - isequal')
	    
	    # Update address
	    address_fields = random_address()
	    UpdateAddress = self.debug(self.api.UpdateAddress)
	    result = UpdateAddress(self.auth, address_id, address_fields)
	 	
	    # Check again
	    addresses = GetAddresses(self.auth, [address_id])
	    if addresses is None: continue
	    address = addresses[0]
	    self.isequal(address, address_fields, 'UpdateAddress - isequal')
	       
	addresses = GetAddress(self.auth, address_ids)
	if addresses is not None:  
	    slef.islistequal(address_ids, [ad['address_id'] for ad in addresses], 'GetAddresses - isequal')     
        
	if self.config.verbose:
            utils.header("Added addresses: %s" % self.address_ids)

	return address_ids

    def DeleteAddresses(self):

	DeleteAddress = self.debug(self.api.DeleteAddress)
        # Delete site addresses
        for address_id in self.address_ids:
	    result = DeleteAddress(self.auth, address_id)
	
	# Check 
	GetAddresses = self.debug(self.api.GetAddresses)
	addresses = GetAddresses(self.api, self.address_ids)
	self.islistequal(addresses, [], 'DeleteAddress - check')
        if self.verbose:
            print "Deleted addresses", self.address_ids

        self.address_ids = []

    def AddPersons(self, n = 3):

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


if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    api_unit_test()(*args)
