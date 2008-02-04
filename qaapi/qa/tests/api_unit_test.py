#!/usr/bin/env /usr/share/plc_api/plcsh
#
# Test script example
#
# Copyright (C) 2006 The Trustees of Princeton University
#
#

from pprint import pprint
from string import letters, digits, punctuation
import traceback
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
api = config.api
auth = api.auth  

try: boot_states = api.GetBootStates(auth)
except: boot_states = [u'boot', u'dbg', u'inst', u'new', u'rcnf', u'rins']

try: roles = [role['name'] for role in api.GetRoles(auth)]
except: roles = [u'admin', u'pi', u'user', u'tech']

try: methods = api.GetNetworkMethods(auth)
except: methods = [u'static', u'dhcp', u'proxy', u'tap', u'ipmi', u'unknown']

try: key_types = api.GetKeyTypes(auth)
except: key_types = [u'ssh']

try:types = api.GetNetworkTypes(auth)
except: types = [u'ipv4']

try:
    sites = api.GetSites(auth, None, ['login_base'])
    login_bases = [site['login_base'] for site in sites]
except: 
    login_bases = ['pl']


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
	'max_slices': 10
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
        'name': random.sample(login_bases, 1)[0] + "_" + randstr(11, letters).lower(),
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
   
    error_log = Logfile('api-unittest-error.log')
    
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
	self.all_methods = set(api.system.listMethods()) 
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
		utils.header("writing api_unitest.log") 
	        logfile = Logfile("api-unittest-summary.log")
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
	        print >> self.error_log, "%s: %s\n" % (method_name, traceback.format_exc()) 
		return None

	return wrapper
 
    def cleanup(self):
	if hasattr(self, 'key_type_ids'): self.DeleteKeyTypes()
	if hasattr(self, 'key_ids'): self.DeleteKeys()
	if hasattr(self, 'person_ids'): self.DeletePersons()
        if hasattr(self, 'initscript_ids'): self.DeleteInitScripts()
	if hasattr(self, 'slice_attribute_ids'): self.DeleteSliceAttributes()
	if hasattr(self, 'slice_ids'): self.DeleteSlices()
	if hasattr(self, 'slice_instantiation_ids'): self.DeleteSliceInstantiations()
	if hasattr(self, 'slice_attribute_type_ids'): self.DeleteSliceAttributeTypes()
	if hasattr(self, 'slice_attribute_ids'): self.DeleteSliceAttributes()
        if hasattr(self, 'role_ids'): self.DeleteRoles()
	if hasattr(self, 'pcu_type_ids'): self.DeletePCUTypes()
	if hasattr(self, 'pcu_ids'): self.DeletePCUs()
	if hasattr(self, 'pcu_protocol_type_ids'): self.DeleteProtocolTypes()		
	if hasattr(self, 'node_network_setting_ids'): self.DeleteNodeNetworkSettings()
	if hasattr(self, 'address_ids'): self.DeleteAddresses()
        if hasattr(self, 'address_type_ids'): self.DeleteAddressTypes()
        if hasattr(self, 'node_ids'): self.DeleteNodes()
	if hasattr(self, 'site_ids'): self.DeleteSites()
	

    def Sites(self, n=4):
	site_ids = []
	for i in range(n):
	    # Add Site
	    site_fields = random_site()
	    AddSite = self.debug(api.AddSite) 
	    site_id = AddSite(auth, site_fields)
	    if site_id is None: continue

	    # Should return a unique id
	    self.isunique(site_id, site_ids, 'AddSite - isunique')
	    site_ids.append(site_id)
	    GetSites = self.debug(api.GetSites)
	    sites = GetSites(auth, [site_id])
	    if sites is None: continue
	    site = sites[0]
	    self.isequal(site, site_fields, 'AddSite - isequal')
	
	    # Update site
	    site_fields = random_site()
	    UpdateSite = self.debug(api.UpdateSite)
	    result = UpdateSite(auth, site_id, site_fields)

	    # Check again
	    sites = GetSites(auth, [site_id])
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
        DeleteSite = self.debug(api.DeleteSite)
        for site_id in self.site_ids:
            result = DeleteSite(site_id)

        # Check if sites are deleted
	GetSites = self.debug(api.GetSites)
	sites = GetSites(auth, self.site_ids) 
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
	    AddNode = self.debug(api.AddNode)
	    node_id = AddNode(auth, site_id, node_fields)
	    if node_id is None: continue
	    
	    # Should return a unique id
	    self.isunique(node_id, node_ids, 'AddNode - isunique')
	    node_ids.append(node_id)

	    # Check nodes
	    GetNodes = self.debug(api.GetNodes)
	    nodes = GetNodes(auth, [node_id])
	    if nodes is None: continue
	    node = nodes[0]
	    self.isequal(node, node_fields, 'AddNode - isequal')
	
	    # Update node
	    node_fields = random_node()
	    UpdateNode = self.debug(api.UpdateNode)
	    result = UpdateNode(auth, node_id, node_fields)
	    
	    # Check again
	    nodes = GetNodes(auth, [node_id])
	    if nodes is None: continue
	    node = nodes[0]
	    self.isequal(node, node_fields, 'UpdateNode - isequal')
	
	nodes = GetNodes(auth, node_ids)
	if nodes is not None:
	    self.islistequal(node_ids, [node['node_id'] for node in nodes], 'GetNodes - isequal')

	if self.config.verbose:
            utils.header("Added nodes: %s" % node_ids)
	
	return node_ids

    def DeleteNodes(self):
	DeleteNode = self.debug(api.DeleteNode)
	for node_id in self.node_ids:
	    result = DeleteNode(auth, node_id)

	# Check if nodes are deleted
	GetNodes = self.debug(api.GetNodes)
	nodes = GetNodes(auth, self.node_ids)
	self.islistequal(nodes, [], 'DeleteNode Check')

	if self.config.verbose:
	    utils.header("Deleted nodes: %s" % self.node_ids)
	
	self.node_ids = []
		 		 
    def AddressTypes(self, n = 3):
        address_type_ids = []
        for i in range(n):
            address_type_fields = random_address_type()
	    AddAddressType = self.debug(api.AddAddressType)
            address_type_id = AddAddressType(auth, address_type_fields)
	    if address_type_id is None: continue

            # Should return a unique address_type_id
	    self.isunique(address_type_id, address_type_ids, 'AddAddressType - isunique') 
	    address_type_ids.append(address_type_id)

            # Check address type
	    GetAddressTypes = self.debug(api.GetAddressTypes)
            address_types = GetAddressTypes(auth, [address_type_id])
	    if address_types is None: continue
	    address_type = address_types[0]
	    self.isequal(address_type, address_type_fields, 'AddAddressType - isequal')

            # Update address type
            address_type_fields = random_address_type()
	    UpdateAddressType = self.debug(api.UpdateAddressType)
            result = UpdateAddressType(auth, address_type_id, address_type_fields)
	    if result is None: continue
            
            # Check address type again
            address_types = GetAddressTypes(auth, [address_type_id])
	    if address_types is None: continue
	    address_type = address_types[0]	
	    self.isequal(address_type, address_type_fields, 'UpdateAddressType - isequal') 	

	# Check get all address types
        address_types = GetAddressTypes(auth, address_type_ids)
	if address_types is not None:
	    self.islistequal(address_type_ids, [address_type['address_type_id'] for address_type in address_types], 'GetAddressTypes - isequal')

        if self.config.verbose:
            utils.header("Added address types: %s " % address_type_ids)

	return address_type_ids

    def DeleteAddressTypes(self):

	DeleteAddressType = self.debug(api.DeleteAddressType)
        for address_type_id in self.address_type_ids:
            DeleteAddressType(auth, address_type_id)

	GetAddressTypes = self.debug(api.GetAddressTypes)
	address_types = GetAddressTypes(auth, self.address_type_ids)
	self.islistequal(address_types, [], 'DeleteAddressType - check')

        if self.config.verbose:
            utils.header("Deleted address types: " % self.address_type_ids)

        self.address_type_ids = []

    def Addresses(self, n = 3):
	address_ids = []
        for i in range(n):
            address_fields = random_address()
	    site_id = random.sample(self.site_ids, 1)[0]	
	    AddSiteAddress = self.debug(api.AddSiteAddress)
            address_id = AddSiteAddress(auth, site_id, address_fields)
	    if address_id is None: continue 
	
            # Should return a unique address_id
	    self.isunique(address_id, address_ids, 'AddSiteAddress - isunique')
	    address_ids.append(address_id)

	    # Check address
	    GetAddresses = self.debug(api.GetAddresses)  
	    addresses = GetAddresses(auth, [address_id])
	    if addresses is None: continue
	    address = addresses[0]
	    self.isequal(address, address_fields, 'AddSiteAddress - isequal')
	    
	    # Update address
	    address_fields = random_address()
	    UpdateAddress = self.debug(api.UpdateAddress)
	    result = UpdateAddress(auth, address_id, address_fields)
	 	
	    # Check again
	    addresses = GetAddresses(auth, [address_id])
	    if addresses is None: continue
	    address = addresses[0]
	    self.isequal(address, address_fields, 'UpdateAddress - isequal')
	       
	addresses = GetAddresses(auth, address_ids)
	if addresses is not None:  
	    self.islistequal(address_ids, [ad['address_id'] for ad in addresses], 'GetAddresses - isequal')     
        
	if self.config.verbose:
            utils.header("Added addresses: %s" % address_ids)

	return address_ids

    def DeleteAddresses(self):

	DeleteAddress = self.debug(api.DeleteAddress)
        # Delete site addresses
        for address_id in self.address_ids:
	    result = DeleteAddress(auth, address_id)
	
	# Check 
	GetAddresses = self.debug(api.GetAddresses)
	addresses = GetAddresses(auth, self.address_ids)
	self.islistequal(addresses, [], 'DeleteAddress - check')
        if self.config.verbose:
            utils.header("Deleted addresses: %s" % self.address_ids)

        self.address_ids = []

    def Slices(self, n = 3):
	slice_ids = []
        for i in range(n):
            # Add Site
            slice_fields = random_slice()
            AddSlice = self.debug(api.AddSlice)
            slice_id = AddSlice(auth, slice_fields)
            if slice_id is None: continue

            # Should return a unique id
            self.isunique(slice_id, slice_ids, 'AddSlicel - isunique')
            slice_ids.append(slice_id)
            GetSlices = self.debug(api.GetSlices)
            slices = GetSlices(auth, [slice_id])
            if slices is None: continue
            slice = slices[0]
            self.isequal(slice, slice_fields, 'AddSlice - isequal')

            # Update slice
            slice_fields = random_slice()
            UpdateSlice = self.debug(api.UpdateSlice)
            result = UpdateSlice(auth, slice_id, slice_fields)

            # Check again
            slices = GetSlices(auth, [slice_id])
            if slices is None: continue
            slice = slices[0]
            self.isequal(slice, slice_fields, 'UpdateSlice - isequal')

	    # XX Add attribute

	    # XX Add node

        slices = GetSlices(auth, slice_ids)
        if slices is not None:
            self.islistequal(slice_ids, [slice['slice_id'] for slice in slices], 'GetSlices - isequal')

        if self.config.verbose:
            utils.header("Added slices: %s" % slice_ids)

        return slice_ids 

    def DeleteSlices(self):
	
	# XX manually delete attributes for first slice
	GetSlices = self.debug(api.GetSlices)
	slices = GetSlices(auth, self.slice_ids, ['slice_attribute_ids', 'node_ids'])

        # Have DeleteSlice automatically delete attriubtes for the rest 
	DeleteSlice = self.debug(api.DeleteSlice)
        for slice_id in self.slice_ids:
            # Delete account
            DeleteSlice(auth, slice_id)

        # Check if slices are deleted
        GetSlices = self.debug(api.GetSlices)
        slices = GetSlices(auth, self.slice_ids)
        self.islistequal(slices, [], 'DeleteSlice - check')

        if self.config.verbose:
            utils.header("Deleted slices: %s" % self.slice_ids)

        self.slice_ids = []

    def Persons(self, n = 3):

        person_ids = []
	for i in range(n):

            # Add account
            person_fields = random_person()
	    AddPerson = self.debug(api.AddPerson)
            person_id = AddPerson(auth, person_fields)
	    if person_id is None: continue
	
            # Should return a unique person_id
            self.isunique(person_id, person_ids, 'AddPerson - isunique')
	    person_ids.append(person_id)
	    GetPersons = self.debug(api.GetPersons)
	    persons = GetPersons(auth, [person_id])
	    if persons is None: continue
	    person = persons[0]
	    self.isequal(person, person_fields, 'AddPerson - isequal')

            # Update account
            person_fields = random_person()
	    person_fields['enabled'] = True
	    UpdatePerson = self.debug(api.UpdatePerson)
            result = UpdatePerson(auth, person_id, person_fields)
	
            # Add random role 
	    AddRoleToPerson = self.debug(api.AddRoleToPerson)	
            role = random.sample(roles, 1)[0]
            result = AddRoleToPerson(auth, role, person_id)

	    # Add key to person
	    key = random_key()
	    key_id = AddPersonKey = self.debug(api.AddPersonKey)
	    AddPersonKey(auth, person_id, key)
	
	    # Add person to site
	    site_id = random.sample(self.site_ids, 1)[0]
	    AddPersonToSite = self.debug(api.AddPersonToSite)
	    AddPersonToSite(auth, person_id, site_id)  	 
	
	    # Add person to slice
	    slice_id = random.sample(self.slice_ids, 1)[0]
	    AddPersonToSlice = self.debug(api.AddPersonToSlice)
	    AddPersonToSlice(auth, person_id, slice_id)

	    # check role, key, site, slice
	    persons = GetPersons(auth, [person_id], ['roles', 'key_ids', 'site_ids', 'slice_ids'])
	    if persons is None or not persons: continue
	    person = persons[0]
	    self.islistequal([role], person['roles'], 'AddRoleToPerson - check')
	    self.islistequal([key_id], person['key_ids'], 'AddPersonKey - check')
	    self.islistequal([site_id], person['site_ids'], 'AddPersonToSite - check')
	    self.islistequal([slice_id], person['slice_ids'], 'AddPersonToSlice - check')

	persons = GetPersons(auth, person_ids)
	if persons is not None:
	    self.islistequal(person_ids, [p['person_id'] for p in persons], 'GetPersons - isequal')

        if self.config.verbose:
            utils.header("Added users: %s" % person_ids)

	return person_ids

    def DeletePersons(self):
        
	# Delete attributes manually for first person
	GetPersons = self.debug(api.GetPersons)
	persons = GetPersons(auth, self.person_ids, ['person_id' , 'key_ids', 'site_ids', 'slice_ids', 'roles'])
	if persons is None or not persons: return 0
	person = persons[0]

 	if person['roles']:	   
	    # Delete role
 	    role = random.sample(person['roles'], 1)[0]
            DeleteRoleFromPerson = self.debug(api.DeleteRoleFromPerson)
            DeleteRoleFromPerson(auth, role, person['person_id'])

	if person['key_ids']:
            # Delete key
	    key_id = random.sample(person['key_ids'], 1)[0] 
            DeleteKey = self.debug(api.DeleteKey)
            DeleteKey(auth, key_id)
	
	if person['site_ids']:
            # Remove person from site
	    site_id = random.sample(person['site_ids'], 1)[0]
            DeletePersonFromSite = self.debug(api.DeletePersonFromSite)
            DeletePersonFromSite(auth, person['person_id'], site_id)

	if person['slice_ids']:
            # Remove person from slice
	    slice_id = random.sample(person['slice_ids'], 1)[0]
            DeletePersonFromSlice = self.debug(api.DeletePersonFromSlice)
            DeletePersonFromSlice(auth, person['person_id'], slice_id)

        # check role, key, site, slice
        persons = GetPersons(auth, [person['person_id']], ['roles', 'key_ids', 'site_ids', 'slice_ids'])
        if persons is None or not persons: return 0
        person = persons[0]
        self.islistequal([], person['roles'], 'DeleteRoleFromPerson - check')
        self.islistequal([], person['key_ids'], 'DeleteKey - check')
        self.islistequal([], person['site_ids'], 'DeletePersonFromSite - check')
        self.islistequal([], person['slice_ids'], 'DeletePersonFromSlice - check')
	
	DeletePerson = self.debug(api.DeletePerson)
        # Have DeletePeson automatically delete attriubtes for all other persons 
        for person_id in self.person_ids:
            # Delete account
            DeletePerson(auth, person_id)

        # Check if persons are deleted
	GetPersons = self.debug(api.GetPersons)
	persons = GetPersons(auth, self.person_ids)
	self.islistequal(persons, [], 'DeletePerson - check')
 
	if self.config.verbose:
            utils.header("Deleted users: %s" % self.person_ids)

        self.person_ids = []


    def Keys(self, n = 3):
	key_ids = []
	for i in range(n):
	    # Add a key to an account
	    key_fields = random_key()
	    person_id = random.sample(self.person_ids, 1)[0]
	    AddPersonKey = self.debug(api.AddPersonKey)
	    key_id = AddPersonKey(auth, person_id, key_fields)   
	    if key_id is None: continue
	     	
	    # Should return a unique key_id
	    self.isunique(key_id, key_ids, 'AddPersonKey - isunique')
	    key_ids.append(key_id)
	    GetKeys = self.debug(api.GetKeys)
	    keys = GetKeys(auth, [key_id])
	    if keys is None: continue
	    key = keys[0]
	    self.isequal(key, key_fields, 'AddPersonKey - isequal')
	    
	    # Update Key
	    key_fields = random_key()
	    UpdateKey = self.debug(api.UpdateKey)
	    result = UpdateKey(auth, key_id, key_fields)
	    
	    keys = GetKeys(auth, [key_id])
	    if keys is None or not keys: continue	 	 
	    key = keys[0]
	    self.isequal(key, key_fields, 'UpdatePersonKey - isequal')
	    
	keys = GetKeys(auth, key_ids)
	if keys is not None:
	    self.islistequal(key_ids, [key['key_id'] for key in keys], 'GetKeys - isequal')
	
	if self.config.verbose:
	    utils.header("Added keys: %s" % key_ids)
	return key_ids


    def DeleteKeys(self):
	
	# Blacklist first key, Delete rest
	GetKeys = self.debug(api.GetKeys)
	keys = GetKeys(auth, self.key_ids)
	if keys is None or not keys: return 0
	key = keys[0]
	
	BlacklistKey = self.debug(api.BlacklistKey)
	BlacklistKey(auth, key['key_id'])  
	
	keys = GetKeys(auth, [key['key_id']])
	self.islistequal(keys, [], 'BlacklistKey - check')
	
	if self.config.verbose:
	    utils.header("Blacklisted key: %s" % key['key_id'])

	DeleteKey = self.debug(api.DeleteKey)
	for key_id in self.key_ids:
	    DeleteKey(auth, key_id)
	
	keys = GetKeys(auth, self.key_ids)
	self.islistequal(keys, [], 'DeleteKey - check')
	
	if self.config.verbose:
	    utils.header("Deleted keys: %s" % self.key_ids)  
	     
	self.key_ids = []
	
if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    api_unit_test()(*args)
