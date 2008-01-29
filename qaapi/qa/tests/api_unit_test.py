#!/usr/bin/env /usr/share/plc_api/plcsh
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

try: boot_states = GetBootStates()
except: boot_states = [u'boot', u'dbg', u'inst', u'new', u'rcnf', u'rins']

try: roles = [role['name'] for role in GetRoles()]
except: roles = [u'admin', u'pi', u'user', u'tech']

try: methods = GetNetworkMethods()
except: methods = [u'static', u'dhcp', u'proxy', u'tap', u'ipmi', u'unknown']

try: key_types = GetKeyTypes()
except: key_types = [u'ssh']

try:types = GetNetworkTypes()
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
	     boot_sates = 2,
	     conf_files = 3,
	     nodes = 4,
             address_types = 3,
             addresses = 2,
             persons = 4, 
	     keys = 3,
	     key_types = 3,	
	     slices = 4,
	     initscripts = 4,	
	    ):
	self.all_methods = set(system.listMethods()) 
	self.methods_tested = set()
	self.methods_failed = set()

	# Begin testing methods
	try:
	    try:
		#self.boot_state_ids = self.BootStates(boot_states)
	        self.site_ids = self.Sites(sites)
	 	#self.peer_ids = self.Peers(peers)
		self.address_type_ids = self.AddressTypes(address_types)
	        self.address_ids = self.Addresses(addresses)
        	#self.conf_files = self.ConfFiles(conf_files)
		#self.network_method_ids = self.NetworkMethods()
		#self.network_type_ids = self.NetworkTypes()
		#self.nodegroup_ids = self.NodeGroups()
		self.node_ids = self.Nodes(nodes)
		#self.node_network_ids = self.NodeNetworks(node_networks)
		#self.node_network_setting_type_ids = self.NodeNetworkSettingsTypes(node_network_settings_types)
		#self.node_network_setting_ids = self.NodeNetworkSettings(node_network_settings)
		#self.pcu_protocol_types_ids = self.PCUProtocolTypes(pcu_protocol_types)
		#self.pcus_ids = self.PCUs(pcus)
		#self.pcu_types_ids = self.PCUTypes(pcu_types)
		#self.role_ids = self.Roles(roles)
		#self.key_types = self.KeyTypes(key_types)
		#self.slice_attribute_type_ids = self.SliceAttributeTypes(slice_attribute_types)
		#self.slice_instantiation_ids = self.SliceInstantiations(slice_instantiations)
		self.slice_ids = self.Slices(slices)
		#self.slice_attribute_ids = self.SliceAttributes(slice_attributes)
		#self.initscript_ids = self.InitScripts(initscripts)
		self.person_ids = self.Persons(persons)
		self.key_ids = self.Keys(keys)
		# self.message_ids = self.Messages(messages)	
		#self.NotifPersons()
		# Test GetEventObject only 
		#self.event_object_ids = self.GetEventObjects()
		#self.event_ids = self.GetEvents() 
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
	     method_name = method.name

        self.methods_tested.update([method_name])
	def wrapper(*args, **kwds):
	    try:
	        return method(*args, **kwds)
	    except:
	        self.methods_failed.update([method_name])
		return None

	return wrapper
 
    def cleanup(self):
        if hasattr(self, 'initscript_ids'): self.DeleteInitScripts()
	if hasattr(self, 'slice_attribute_ids'): self.DeleteSliceAttributes()
	if hasattr(self, 'slice_ids'): self.DeleteSlices()
	if hasattr(self, 'slice_instantiation_ids'): self.DeleteSliceInstantiations()
	if hasattr(self, 'slice_attribute_type_ids'): self.DeleteSliceAttributeTypes()
	if hasattr(self, 'slice_attribute_ids'): self.DeleteSliceAttributes()
	if hasattr(self, 'key_type_ids'): self.DeleteKeyTypes()
	if hasattr(self, 'key_ids'): self.DeleteKeys()
	if hasattr(self, 'person_ids'): self.DeletePersons()
        if hasattr(self, 'role_ids'): self.DeleteRoles()
	if hasattr(self, 'pcu_type_ids'): self.DeletePCUTypes()
	if hasattr(self, 'pcu_ids'): self.DeletePCUs()
	if hasattr(self, 'pcu_protocol_type_ids'): self.DeleteProtocolTypes()		
	if hasattr(self, 'node_network_setting_ids'): self.DeleteNodeNetworkSettings()
	if hasattr(self, 'address_ids'): self.DeleteAddresses()
        if hasattr(self, 'attress_type_ids'): self.DeleteAddressTypes()
        if hasattr(self, 'node_ids'): self.DeleteNodes()
	if hasattr(self, 'site_ids'): self.DeleteSites()
	

    def Sites(self, n=4):
	site_ids = []
	for i in range(n):
	    # Add Site
	    site_fields = random_site()
	    AddSite = self.debug(shell.AddSite) 
	    site_id = AddSite(site_fields)
	    if site_id is None: continue

	    # Should return a unique id
	    self.isunique(site_id, site_ids, 'AddSite - isunique')
	    site_ids.append(site_id)
	    GetSites = self.debug(shell.GetSites)
	    sites = GetSites([site_id])
	    if sites is None: continue
	    site = sites[0]
	    self.isequal(site, site_fields, 'AddSite - isequal')
	
	    # Update site
	    site_fields = random_site()
	    UpdateSite = self.debug(shell.UpdateSite)
	    result = UpdateSite(site_id, site_fields)

	    # Check again
	    sites = GetSites([site_id])
	    if sites is None: continue
	    site = sites[0] 	 
	    self.isequal(site, site_fields, 'UpdateSite - isequal')
	    
	sites = GetSites(site_ids)
	if sites is not None: 
	    self.islistequal(site_ids, [site['site_id'] for site in sites], 'GetSites - isequal')
	
	if self.config.verbose:
	    utils.header("Added sites: %s" % site_ids)    	

	return site_ids


    def DeleteSites(self):
        # Delete all sites
        DeleteSite = self.debug(shell.DeleteSite)
        for site_id in self.site_ids:
            result = DeleteSite(site_id)

        # Check if sites are deleted
	GetSites = self.debug(shell.GetSites)
	sites = GetSites(self.site_ids) 
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
	    AddNode = self.debug(shell.AddNode)
	    node_id = AddNode(site_id, node_fields)
	    if node_id is None: continue
	    
	    # Should return a unique id
	    self.isunique(node_id, node_ids, 'AddNode - isunique')
	    node_ids.append(node_id)

	    # Check nodes
	    GetNodes = self.debug(shell.GetNodes)
	    nodes = GetNodes([node_id])
	    if nodes is None: continue
	    node = nodes[0]
	    self.isequal(node, node_fields, 'AddNode - isequal')
	
	    # Update node
	    node_fields = random_node()
	    UpdateNode = self.debug(shell.UpdateNode)
	    result = UpdateNode(node_id, node_fields)
	    
	    # Check again
	    nodes = GetNodes([node_id])
	    if nodes is None: continue
	    node = nodes[0]
	    self.isequal(node, node_fields, 'UpdateNode - isequal')
	
	nodes = GetNodes(node_ids)
	if nodes is not None:
	    self.islistequal(node_ids, [node['node_id'] for node in nodes], 'GetNodes - isequal')

	if self.config.verbose:
            utils.header("Added nodes: %s" % node_ids)
	
	return node_ids

    def DeleteNodes(self):
	DeleteNode = self.debug(shell.DeleteNode)
	for node_id in self.node_ids:
	    result = DeleteNode(node_id)

	# Check if nodes are deleted
	GetNodes = self.debug(shell.GetNodes)
	nodes = GetNodes(self.node_ids)
	self.islistequal(nodes, [], 'DeleteNode Check')

	if self.config.verbose:
	    utils.header("Deleted nodes: %s" % self.node_ids)
	
	self.node_ids = []
		 		 
    def AddressTypes(self, n = 3):
        address_type_ids = []
        for i in range(n):
            address_type_fields = random_address_type()
	    AddAddressType = self.debug(shell.AddAddressType)
            address_type_id = AddAddressType(address_type_fields)
	    if address_type_id is None: continue

            # Should return a unique address_type_id
	    self.isunique(address_type_id, address_type_ids, 'AddAddressType - isunique') 
	    address_type_ids.append(address_type_id)

            # Check address type
	    GetAddressTypes = self.debug(shell.GetAddressTypes)
            address_types = GetAddressTypes([address_type_id])
	    if address_types is None: continue
	    address_type = address_types[0]
	    self.isequal(address_type, address_type_fields, 'AddAddressType - isequal')

            # Update address type
            address_type_fields = random_address_type()
	    UpdateAddressType = self.debug(shell.UpdateAddressType)
            result = UpdateAddressType(address_type_id, address_type_fields)
	    if result is None: continue
            
            # Check address type again
            address_types = GetAddressTypes([address_type_id])
	    if address_types is None: continue
	    address_type = address_types[0]	
	    self.isequal(address_type, address_type_fields, 'UpdateAddressType - isequal') 	

	# Check get all address types
        address_types = GetAddressTypes(address_type_ids)
	if address_types is not None:
	    self.islistequal(address_type_ids, [address_type['address_type_id'] for address_type in address_types], 'GetAddressTypes - isequal')

        if self.config.verbose:
            utils.header("Added address types: %s " % address_type_ids)

	return address_type_ids

    def DeleteAddressTypes(self):

	DeleteAddressType = self.debug(shell.DeleteAddressType)
        for address_type_id in self.address_type_ids:
            DeleteAddressType(ddress_type_id)

	GetAddressTypes = self.debug(shell.GetAddressTypes)
	address_types = GetAddressTypes(self.address_type_ids)
	self.islistequal(address_types, [], 'DeleteAddressType - check')

        if self.config.verbose:
            utils.header("Deleted address types: " % self.address_type_ids)

        self.address_type_ids = []

    def Addresses(self, n = 3):
	address_ids = []
        for i in range(n):
            address_fields = random_address()
	    site_id = random.sample(self.site_ids, 1)[0]	
	    AddSiteAddress = self.debug(shell.AddSiteAddress)
            address_id = AddSiteAddress(site_id, address_fields)
	    if address_id is None: continue 
	
            # Should return a unique address_id
	    self.isunique(address_id, address_ids, 'AddSiteAddress - isunique')
	    address_ids.append(address_id)

	    # Check address
	    GetAddresses = self.debug(shell.GetAddresses)  
	    addresses = GetAddresses([address_id])
	    if addresses is None: continue
	    address = addresses[0]
	    self.isequal(address, address_fields, 'AddSiteAddress - isequal')
	    
	    # Update address
	    address_fields = random_address()
	    UpdateAddress = self.debug(shell.UpdateAddress)
	    result = UpdateAddress(address_id, address_fields)
	 	
	    # Check again
	    addresses = GetAddresses([address_id])
	    if addresses is None: continue
	    address = addresses[0]
	    self.isequal(address, address_fields, 'UpdateAddress - isequal')
	       
	addresses = GetAddresses(address_ids)
	if addresses is not None:  
	    self.islistequal(address_ids, [ad['address_id'] for ad in addresses], 'GetAddresses - isequal')     
        
	if self.config.verbose:
            utils.header("Added addresses: %s" % address_ids)

	return address_ids

    def DeleteAddresses(self):

	DeleteAddress = self.debug(shell.DeleteAddress)
        # Delete site addresses
        for address_id in self.address_ids:
	    result = DeleteAddress(address_id)
	
	# Check 
	GetAddresses = self.debug(shell.GetAddresses)
	addresses = GetAddresses(self.address_ids)
	self.islistequal(addresses, [], 'DeleteAddress - check')
        if self.config.verbose:
            utils.header("Deleted addresses: %s" % self.address_ids)

        self.address_ids = []

    def Slices(self, n = 3):
	slice_ids = []
        for i in range(n):
            # Add Site
            slice_fields = random_slice()
            AddSlice = self.debug(shell.Slice)
            slice_id = AddSlice(slice_fields)
            if slice_id is None: continue

            # Should return a unique id
            self.isunique(slice_id, slice_ids, 'AddSlicel - isunique')
            slice_ids.append(slice_id)
            GetSlices = self.debug(shell.GetSlices)
            slices = GetSlices([slice_id])
            if slices is None: continue
            slice = slices[0]
            self.isequal(slice, slice_fields, 'AddSlice - isequal')

            # Update slice
            slice_fields = random_slice()
            UpdateSite = self.debug(shell.UpdateSlice)
            result = UpdateSlice(slice_id, slice_fields)

            # Check again
            slices = GetSites([slice_id])
            if slices is None: continue
            slice = slices[0]
            self.isequal(slice, slice_fields, 'UpdateSlice - isequal')

	    # XX Add attribute

	    # XX Add node

        slices = GetSites(slice_ids)
        if slices is not None:
            self.islistequal(slice_ids, [slice['slice_id'] for slice in slices], 'GetSlices - isequal')

        if self.config.verbose:
            utils.header("Added slices: %s" % slice_ids)

        return slice_ids 

    def DeleteSlices(self):
	
	# XX manually delete attributes for first slice
	slices = GetSlices(self.slice_ids, ['slice_attribute_ids', 'node_ids'])


	DeleteSlice = self.debug(shell.DeleteSlice)
        # Have DeleteSlice automatically delete attriubtes for the rest 
        for slice_id in self.slice_ids:
            # Delete account
            DeleteSlice(slice_id)

        # Check if persons are deleted
        GetSlices = self.debug(shell.GetSlices)
        slices = GetSlices(self.slice_ids)
        self.islistequal(slices, [], 'DeleteSlice - check')

        if self.verbose:
            utils.header("Deleted slices: %s" % self.slice_ids)

        self.slice_ids = []


    def Persons(self, n = 3):

        person_ids = []
	for i in range(n):

            # Add account
            person_fields = random_person()
	    AddPerson = self.debug(shell.AddPerson)
            person_id = AddPerson(person_fields)
	    if person_id is None: continue
	
            # Should return a unique person_id
            self.isunique(person_id, person_ids, 'AddPerson - isunique')
	    person_ids.append(person_id)
	    GetPersons = self.debug(shell.GetPersons)
	    persons = GetPersons([person_id])
	    if persons is None: continue
	    person = persons[0]
	    self.isequal(person, person_fields, 'AddPerson - isequal')

            # Update account
            person_fields = random_person()
	    person_fields['enabled'] = True
	    UpdatePerson = self.debug(shell.UpdatePerson)
            result = UpdatePerson(person_id, person_fields)
	
            # Add random role 
	    AddRoleToPerson = self.debug(shell.AddRoleToPerson)	
            role = random.sample(roles, 1)[0]
            result = AddRoleToPerson(role, person_id)

	    # Add key to person
	    key = random_key()
	    key_id = AddPersonKey = self.debug(shell.AddPersonKey)
	    AddPersonKey(person_id, key)
	
	    # Add person to site
	    site_id = random.sample(self.site_ids, 1)[0]
	    AddPersonToSite = self.debug(shell.AddPersonToSite)
	    AddPersonToSite(person_id, site_id)  	 
	
	    # Add person to slice
	    slice_id = random.sample(self.slice_ids, 1)[0]
	    AddPersonToSlice = self.debug(self.AddPersonToSlice)
	    AddPersonToSlice(person_id, slice_id)

	    # check role, key, site, slice
	    persons = GetPersons([person_id], ['roles', 'key_ids', 'site_ids', 'slice_ids'])
	    if persons is None or not persons: continue
	    person = persons[0]
	    self.islistequal([role], person['roles'], 'AddRoleToPerson - check')
	    self.islistequal([key_id], person['key_ids'], 'AddPersonKey - check')
	    self.islistequal([site_id], person['site_ids'], 'AddPersonToSite - check')
	    self.islistequal([slice_id], person['slice_ids'], 'AddPersonToSlice - check')

	persons = GetPersons(person_ids)
	if persons is not None:
	    self.islistequal(person_ids, [p['person_id'] for p in persons], 'GetPersons - isequal')

        if self.verbose:
            utils.header("Added users: %s" % self.person_ids)

    def DeletePersons(self):
        
	# Delete attributes manually for first person
	persons = GetPersons(self.person_ids, ['person_id' , 'key_ids', 'site_ids', 'slice_ids'])
	if persons is None or not persons: return 0
	person = persons[0]
	  
	# Delete role
        DeleteRoleFromPerson = self.debug(shell.DeleteRoleFromPerson)
        DeleteRoleFromPerson(person['role'], person['person_id'])

        # Delete key
        DeleteKey = self.debug(shell.DeleteKey)
        DeleteKey(person['key_id'])

        # Remove person from site
        DeletePersonFromSite = self.debug(shell.DeletePersonFromSite)
        DeletePersonFromSite(person['person_id'], person['site_id'])

        # Remove person from slice
        DeletePersonFromSlice = self.debug(shell.DeletePersonFromSlice)
        DeletePersonFromSlice(person['person_id'], person['slice_id'])

        # check role, key, site, slice
        persons = GetPersons([person['person_id']], ['roles', 'key_ids', 'site_ids', 'slice_ids'])
        if persons is None or not persons: return 0
        person = persons[0]
        self.islistequal([], person['roles'], 'DeleteRoleFromPerson - check')
        self.islistequal([], person['key_ids'], 'DeleteKey - check')
        self.islistequal([], person['site_ids'], 'DeletePersonFromSite - check')
        self.islistequal([], person['slice_ids'], 'DeletePersonFromSlice - check')
	
	DeletePerson = self.debug(shell.DeletePerson)
        # Have DeletePeson automatically delete attriubtes for all other persons 
        for person_id in self.person_ids:
            # Delete account
            DeletePerson(person_id)

        # Check if persons are deleted
	GetPersons = self.debug(shell.GetPersons)
	persons = GetPersons(self.person_ids)
	self.islistequal(persons, [], 'DeletePerson - check')
 
	if self.verbose:
            utils.header("Deleted users: %s" % self.person_ids)

        self.person_ids = []


if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    api_unit_test()(*args)
