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
import struct
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

try:attribute_types = api.GetSliceAttributeTypes(auth)
except: attribute_types = range(20) 

try:
    sites = api.GetSites(auth, None, ['login_base'])
    login_bases = [site['login_base'] for site in sites]
except: 
    login_bases = ['pl']


def randfloat(min = 0.0, max = 1.0):
    return float(min) + (random.random() * (float(max) - float(min)))

def randint(min = 0, max = 1):
    return int(randfloat(min, max + 1))

def randbool():
    return random.sample([True, False], 1)[0]	
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

def random_peer():
    bits = 2048	
    return {
	'peername': randstr(254),
	'peer_url': "https://" + randhostname() + "/",
	'key': base64.b64encode(''.join(randstr(bits / 8).encode("utf-8"))),
	'cacert': base64.b64encode(''.join(randstr(bits / 8).encode("utf-8")))
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

def random_pcu_type():
    return {
	'model': randstr(254),
	'name': randstr(254),
	}

def random_pcu_protocol_type():
    return { 
	'port': randint(0, 65535),
	'protocol': randstr(254),
	'supported': randbool()
	}

def random_slice_instantiation():
    return {
	'instantiation': randstr(10)
	}
def random_slice_attribute():
    return {
	'attribute_type_id': random.sample(attribute_types, 1)[0],
	'name': randstr(50),
	'description': randstr(100),
	'min_role_id': random.sample([10,20,30,40], 1)[0],
	'value': randstr(20)
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

    logfile = Logfile("api-unittest-summary.log")
   
    def call(self,
	     boot_states = 2,
	     sites = 2,
	     peers = 2,
             address_types = 3,
             addresses = 2,
	     pcu_types = 2,
	     pcu_protocol_types = 2,
	     pcus = 2,
	     network_methods = 2,
	     network_types = 2,
	     nodegroups = 3,
	     nodes = 4,
	     conf_files = 3,
	     nodenetworks = 4,
	     nodenetworksetting_types = 2,
	     nodenetworksettings = 2,
	     slice_attribute_types = 2,
	     slice_instantiations = 2,
	     slices = 4,
	     slice_attributes = 4,	     
	     initscripts = 4,	
             roles = 2,
	     persons = 4, 
	     key_types = 3,	
	     keys = 3,
	     messages = 2
	    ):
	# Filter out deprecated (Adm) and boot Methods
	current_methods = lambda method: not method.startswith('Adm') or \
				         not method.startswith('Slice') or \
					 not method.startswith('Boot') or \
					 not method.startswith('system')
	self.all_methods = set(api.system.listMethods()) 
	self.methods_tested = set()
	self.methods_failed = set()

	# Begin testing methods
	try:
	    try:
		if hasattr(self, 'BootStates'): self.boot_states = self.BootStates(boot_states)
	        if hasattr(self, 'Sites'): self.site_ids = self.Sites(sites)
	 	if hasattr(self, 'Peers'): self.peer_ids = self.Peers(peers)
		if hasattr(self, 'AddressTypes'): self.address_type_ids = self.AddressTypes(address_types)
	        if hasattr(self, 'Addresses'): self.address_ids = self.Addresses(addresses)
		if hasattr(self, 'PCUTypes'): self.pcu_type_ids = self.PCUTypes(pcu_types)
		if hasattr(self, 'PCUProtocolTypes'): self.pcu_protocol_type_ids = self.PCUProtocolTypes(pcu_protocol_types)
                if hasattr(self, 'PCUs'): self.pcu_ids = self.PCUs(pcus)                
		if hasattr(self, 'NetworkMethods'): self.network_methods = self.NetworkMethods()
		if hasattr(self, 'NetworkTypes'): self.network_types = self.NetworkTypes()
		if hasattr(self, 'NodeGroups'): self.nodegroup_ids = self.NodeGroups()
		if hasattr(self, 'Nodes'): self.node_ids = self.Nodes(nodes)
		if hasattr(self, 'ConfFiles'): self.conf_file_ids = self.ConfFiles(conf_files)
		if hasattr(self, 'NodeNetworks'): self.node_network_ids = self.NodeNetworks(node_networks)
		if hasattr(self, 'NodeNetworkSettingsTypes'): self.node_network_setting_type_ids = self.NodeNetworkSettingsTypes(node_network_settings_types)
		if hasattr(self, 'NodeNetworkSettings'): self.node_network_setting_ids = self.NodeNetworkSettings(node_network_settings)
		if hasattr(self, 'SliceAttributeTypes'): self.slice_attribute_types = self.SliceAttributeTypes(slice_attribute_types)
		if hasattr(self, 'SliceInstantiations'): self.slice_instantiations = self.SliceInstantiations(slice_instantiations)
		if hasattr(self, 'Slices'): self.slice_ids = self.Slices(slices)
		if hasattr(self, 'SliceAttributes'): self.slice_attribute_ids = self.SliceAttributes(slice_attributes)
		if hasattr(self, 'InitScripts'): self.initscript_ids = self.InitScripts(initscripts)
		if hasattr(self, 'Roles'): self.role_ids = self.Roles(roles)
		if hasattr(self, 'Persons'): self.person_ids = self.Persons(persons)
		if hasattr(self, 'KeyTypes'): self.key_types = self.KeyTypes(key_types)
		if hasattr(self, 'Keys'): self.key_ids = self.Keys(keys)
		if hasattr(self, 'Messages'):  self.message_ids = self.Messages(messages)	
		if hasattr(self, 'NotifyPersons'): self.NotifPersons()
		# Test GetEventObject only 
		if hasattr(self, 'GetEventObject'): self.event_object_ids = self.GetEventObjects()
		if hasattr(self, 'GetEvents'): self.event_ids = self.GetEvents() 
	    except:
		print_exc()
	finally:
	    try:
		self.cleanup()
	    finally: 
		utils.header("writing api-unittest-summary.log") 
		methods_ok = list(self.methods_tested.difference(self.methods_failed))
		methods_failed = list(self.methods_failed)
		methods_untested = list(self.all_methods.difference(self.methods_tested))
		methods_ok.sort()
		methods_failed.sort()
		methods_untested.sort()
		print >> self.logfile, "\n".join([m+": [OK]" for m in  methods_ok])
	        print >> self.logfile, "\n".join([m+": [FAILED]" for m in methods_failed])
		print >> self.logfile, "\n".join([m+": [Not Tested]" for m in  methods_untested])
 
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
	        print >> self.logfile, "%s: %s\n" % (method_name, traceback.format_exc()) 
		return None

	return wrapper
 
    def cleanup(self):
	if hasattr(self, 'key_type_ids'): self.DeleteKeyTypes()
	if hasattr(self, 'key_ids'): self.DeleteKeys()
	if hasattr(self, 'person_ids'): self.DeletePersons()
	if hasattr(self, 'role_ids'): self.DeleteRoles()
        if hasattr(self, 'initscript_ids'): self.DeleteInitScripts()
	if hasattr(self, 'slice_attribute_ids'): self.DeleteSliceAttributes()
	if hasattr(self, 'slice_ids'): self.DeleteSlices()
	if hasattr(self, 'slice_instantiations'): self.DeleteSliceInstantiations()
	if hasattr(self, 'slice_attribute_type_ids'): self.DeleteSliceAttributeTypes()
	if hasattr(self, 'nodenetwork_setting_ids'): self.DeleteNodeNetworkSettings()
	if hasattr(self, 'nodenetwork_setting_type_ids'): self.DeleteNodeNetworkSettingTypes()
	if hasattr(self, 'nodenetwork_ids'): self.DeleteNodeNetworks()
	if hasattr(self, 'conffile_ids'): self.DeleteConfFiles()
        if hasattr(self, 'node_ids'): self.DeleteNodes()
	if hasattr(self, 'nodegroups_ids'): self.DeleteNodeGroups()
	if hasattr(self, 'network_types'): self.DeleteNetworkTypes()
	if hasattr(self, 'network_methods'): self.DeleteNetworkMethods()
	if hasattr(self, 'pcu_ids'): self.DeletePCUs()
	if hasattr(self, 'pcu_protocol_type_ids'): self.DeletePCUProtocolTypes()		
	if hasattr(self, 'pcu_type_ids'): self.DeletePCUTypes()
	if hasattr(self, 'address_ids'): self.DeleteAddresses()
        if hasattr(self, 'address_type_ids'): self.DeleteAddressTypes()
	if hasattr(self, 'peer_ids'): self.DeletePeers()
	if hasattr(self, 'site_ids'): self.DeleteSites()
	if hasattr(self, 'boot_state_ids'): self.DeleteBootStates()
	

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
	    
	sites = GetSites(auth, site_ids)
	if sites is not None: 
	    self.islistequal(site_ids, [site['site_id'] for site in sites], 'GetSites - isequal')
	
	if self.config.verbose:
	    utils.header("Added sites: %s" % site_ids)    	

	return site_ids


    def DeleteSites(self):
        # Delete all sites
        DeleteSite = self.debug(api.DeleteSite)
        for site_id in self.site_ids:
            result = DeleteSite(auth, site_id)

        # Check if sites are deleted
	GetSites = self.debug(api.GetSites)
	sites = GetSites(auth, self.site_ids) 
        self.islistequal(sites, [], 'DeleteSite - check')	

        if self.config.verbose:
            utils.header("Deleted sites: %s" % self.site_ids)

        self.site_ids = []

    def NetworkMethods(self, n=2):
        methods = []
	AddNetworkMethod = self.debug(api.AddNetworkMethod)
	GetNetworkMethods = self.debug(api.GetNetworkMethods)
 
        for i in range(n):
            # Add Network Method
            net_method = randstr(10)
            AddNetworkMethod(auth, net_method)
            if net_method is None: continue

            # Should return a unique id
            self.isunique(net_method, methods, 'AddNetworkMethod - isunique')
            methods.append(net_method)
            net_methods = GetNetworkMethods(auth)
            if net_methods is None: continue
	    net_methods = filter(lambda x: x in [net_method], net_methods) 
            method = net_methods[0]
            self.isequal(method, net_method, 'AddNetworkMethod - isequal')


        net_methods = GetNetworkMethods(auth)
        if net_methods is not None:
	    net_methods = filter(lambda x: x in methods, net_methods)
            self.islistequal(methods, net_methods, 'GetNetworkMethods - isequal')

        if self.config.verbose:
            utils.header("Added network methods: %s" % methods)

        return methods

    def DeleteNetworkMethods(self):
	DeleteNetworkMethod = self.debug(api.DeleteNetworkMethod)
	GetNetworkMethods = self.debug(api.GetNetworkMethods)	
	for method in self.network_methods:
	    DeleteNetworkMethod(auth, method)

	# check 
	network_methods = GetNetworkMethods(auth, self.network_methods)
	self.islistequal(network_methods, [], 'DeleteNetworkMethods - check')

	if self.config.verbose:
	    utils.header("Deleted network methods: %s" % self.network_methods)
	self.network_methods = []    

    def NetworkTypes(self, n=2):
	net_types = []
        AddNetworkType = self.debug(api.AddNetworkType)
        GetNetworkTypes = self.debug(api.GetNetworkTypes)
         
        for i in range(n):
            # Add Network Type 
            type = randstr(10)
            AddNetworkType(auth, type)
      
            # Should return a unique id
            self.isunique(type, net_types, 'AddNetworkType - isunique')
            net_types.append(type)
            types = GetNetworkTypes(auth)
            if types is None: continue
	    types = filter(lambda x: x in [type], types)
            if types is None: continue
            net_type = types[0]
            self.isequal(net_type, type, 'AddNetworkType - isequal')
    
        types = GetNetworkTypes(auth, net_types)
        if types is not None:
	    types = filter(lambda x: x in net_types, types)
            self.islistequal(types, net_types, 'GetNetworkTypes - isequal')

        if self.config.verbose:
            utils.header("Added network types: %s" % net_types)

        return net_types	

    def DeleteNetworkTypes(self):	
        DeleteNetworkType = self.debug(api.DeleteNetworkType)
        GetNetworkTypes = self.debug(api.GetNetworkTypes)
        for type in self.network_types:
            DeleteNetworkType(auth, type)

        # check 
        network_types = GetNetworkTypes(auth, self.network_types)
        self.islistequal(network_types, [], 'DeleteNetworkTypes - check')

        if self.config.verbose:
            utils.header("Deleted network types: %s" % self.network_types)
        self.network_types = []	


    def NodeGroups(self, n = 4):
	nodegroup_ids = []
	AddNodeGroup = self.debug(api.AddNodeGroup)
	UpdateNodeGroup = self.debug(api.UpdateNodeGroup)
	GetNodeGroups = self.debug(api.GetNodeGroups)

	for i in range(n):
	    # Add Nodegroups
	    nodegroup_fields = random_nodegroup()
	    nodegroup_id = AddNodeGroup(auth, nodegroup_fields)
	    if nodegroup_id is None: continue
 	
	    # Should return a unique id
	    self.isunique(nodegroup_id, nodegroup_ids, 'AddNodeGroup - isunique')
	    nodegroup_ids.append(nodegroup_id)
	    nodegroups = GetNodeGroups(auth, [nodegroup_id])
	    if nodegroups is None: continue
	    nodegroup = nodegroups[0]
	    self.isequal(nodegroup, nodegroup_fields, 'AddNodeGroup - isequal')
	
	    # Update NodeGroups
	    nodegroup_fields = random_nodegroup()
	    UpdateNodeGroup(auth, nodegroup_id, nodegroup_fields)

	    # Check again
	    nodegroups = GetNodeGroups(auth, [nodegroup_id])
	    if nodegroups is None: continue
	    nodegroup = nodegroups[0]
	    self.isequal(nodegroup, nodegroup_fields, 'UpdateNodeGroup - isequal')

  	nodegroups = GetNodeGroups(auth, nodegroup_ids)
	if nodegroups is not None:
	    self.islistequal(nodegroup_ids, [n['nodegroup_id'] for n in nodegroups], 'GetNodeGroups - isequal')
	if self.config.verbose:
	    utils.header("Added nodegroups: %s" % nodegroup_ids)
	
	return nodegroup_ids

    def DeleteNodeGroups(self):
	# Delete all NodeGroups
	GetNodeGroups = self.debug(api.GetNodeGroups)
	DeleteNodeGroup = self.debug(api.DeleteNodeGroup)
	
	for nodegroup_id in self.nodegroup_ids:
	    result = DeleteNodeGroup(auth, nodegroup_id)
	
	# Check is nodegroups are deleted
	nodegroups = GetNodeGroups(auth, self.nodegroup_ids)
	self.islisteqeual(nodegroups, [], 'DeleteNodeGroup - check')
	
	if self.config.verbose:
	    utils.header("Deleted nodegroups: %s" % self.nodegroup_ids)
	
	self.nodegroup_ids = []    

    def PCUTypes(self, n=2):
        pcu_type_ids = []
	AddPCUType = self.debug(api.AddPCUType)
	UpdatePCUType = self.debug(api.UpdatePCUType)
	GetPCUTypes = self.debug(api.GetPCUTypes)
 
	for i in range(n):
	    # Add PCUType
	    pcu_type_fields = random_pcu_type()
	    pcu_type_id = AddPCUType(auth, pcu_type_fields)
	    if pcu_type_id is None: continue
	
	    # Should return a unique id
	    self.isunique(pcu_type_id, pcu_type_ids, 'AddPCUType - isunique')
	    pcu_type_ids.append(pcu_type_id)
	   
	    # Check pcu type
	    pcu_types = GetPCUTypes(auth, [pcu_type_id])  
	    if pcu_types is None: continue
	    pcu_type = pcu_types[0]
	    self.isequal(pcu_type, pcu_type_fields, 'AddPCUType - isequal')

	    # Update PCUType
	    pcu_type_fields = random_pcu_type()
            pcu_type_id = UpdatePCUType(auth, pcu_type_id, pcu_type_fields)

	    # Check again
	    pcu_types = GetPCUTypes(auth, [pcu_type_id])
	    if pcu_types is None: continue
            pcu_type = pcu_types[0]
            self.isequal(pcu_type, pcu_type_fields, 'UpdatePCUType - isequal')

	pcu_types = GetPCUTypes(auth, pcu_type_ids)
	if pcu_types is not None:
	    self.islistequal(pcu_type_ids, [p['pcu_type_id'] for p in pcu_types], 'GetPCUTypes - check')

	if self.config.verbose:
	    utils.header("Added pcu_types: %s " % pcu_type_ids)
	return pcu_type_ids
	  
    def DeletePCUTypes(self):
	GetPCUTypes = self.debug(api.GetPCUTypes)
	DeletePCUType = self.debug(api.DeletePCUType)
	
	for pcu_type_id in self.pcu_type_ids:
	    DeletePCUType(auth, pcu_type_id)
	
	pcu_types = GetPCUTypes(auth, self.pcu_type_ids)
	self.islistequal(pcu_types, [], 'DeletePCUType - check')  

    def PCUProtocolTypes(self, n=2):
	protocol_type_ids = []
	AddPCUProtocolType = self.debug(api.AddPCUProtocolType)
	UpdatePCUProtocolType = self.debug(api.UpdatePCUProtocolType)
	GetPCUProtocolTypes = self.debug(api.GetPCUProtocolTypes)
	
	for i in range(n):
	    # Add PCUProtocolType
	    protocol_type_fields = random_pcu_protocol_type()
	    pcu_type_id = random.sample(self.pcu_type_ids, 1)[0]
	    protocol_type_id = AddPCUProtocolType(auth, pcu_type_id, protocol_type_fields)	    
	    if protocol_type_id is None: continue
	    
	    # Should return a unique id
	    self.isunique(protocol_type_id, protocol_type_ids, 'AddPCUProtocolType - isunique')
	    protocol_type_ids.append(protocol_type_id)

	    # Check protocol type
    	    protocol_types = GetPCUProtocolTypes(auth, [protocol_type_id])
	    if protocol_types is None: continue
	    protocol_type = protocol_types[0]
	    self.isequal(protocol_type, protocol_type_fields, 'AddPCUProtocolType - isequal')
	 	
	    # Update protocol type
	    protocol_type_fields = random_pcu_protocol_type()
	    UpdatePCUProtocolType(auth, protocol_type_id, protocol_type_fields)
	    
	    # Check again
	    protocol_types = GetPCUProtocolTypes(auth, [protocol_type_id])
            if protocol_types is None: continue
            protocol_type = protocol_types[0]
            self.isequal(protocol_type, protocol_type_fields, 'UpdatePCUProtocolType - isequal')

	protocol_types = GetPCUProtocolTypes(auth, protocol_type_ids)
	if protocol_types is not None: 
	    pt_ids = [p['pcu_protocol_type_id'] for p in protocol_types]
	    self.islistequal(protocol_type_ids, pt_ids, 'GetPCUProtocolTypes - isequal')
	
	if self.config.verbose:
	    utils.header('Added pcu_protocol_types: %s' % protocol_type_ids)

	return protocol_type_ids	 	

    def DeletePCUProtocolTypes(self):
	GetPCUProtocolTypes = self.debug(api.GetPCUProtocolTypes)
	DeletePCUProtocolType = self.debug(api.DeletePCUProtocolType)
	
	for protocol_type_id in self.pcu_protocol_type_ids:
	    DeletePCUProtocolType(auth, protocol_type_id)
	
	# check 
	protocol_types = GetPCUProtocolTypes(auth, self.pcu_protocol_type_ids)
	self.islistequal(protocol_types, [], 'DeletePCUProtocolType - check')
	
	if self.config.verbose:
	    utils.header("Deleted pcu_protocol_types: %s" % self.pcu_protocol_type_ids)
	self.pcu_protocol_type_ids = []

    def PCUs(self, n = 4):
	pcu_ids = []
	AddPCU = self.debug(api.AddPCU)
	UpdatePCU = self.debug(api.UpdatePCU)
	GetPCUs = self.debug(api.GetPCUs)

	for i in range(n):
	    # Add PCU		
	    pcu_fields = random_pcu()
	    site_id = random.sample(self.site_ids, 1)[0] 
	    pcu_id = AddPCU(auth, site_id, pcu_fields)
	    if pcu_id is None: continue

	    # Should return a unique id
	    self.isunique(pcu_id, pcu_ids, 'AddPCU - isunique')
	    pcu_ids.append(pcu_id)

	    # check PCU
	    pcus = GetPCUs(auth, [pcu_id])
	    if pcus is None: continue
	    pcu = pcus[0]
	    self.isequal(pcu, pcu_fields, 'AddPCU - isequal')
	
	    # Update PCU
	    pcu_fields = random_pcu()
	    UpdatePCU(auth, pcu_id, pcu_fields)
	
	    # Check again
	    pcus = GetPCUs(auth, [pcu_id])
            if pcus is None: continue
            pcu = pcus[0]
            self.isequal(pcu, pcu_fields, 'UpdatePCU - isequal')

	pcus = GetPCUs(auth, pcu_ids)
	if pcus is not None:
	    self.islistequal(pcu_ids, [p['pcu_id'] for p in pcus], 'GetPCUs - isequal')

	if self.config.verbose:
	    utils.header('Added pcus: %s' % pcu_ids)

	return pcu_ids
	
    def DeletePCUs(self):
	GetPCUs = self.debug(api.GetPCUs)
	DeletePCU = self.debug(api.DeletePCU)

	for pcu_id in self.pcu_ids:
	    DeletePCU(auth, pcu_id)

	# check 
	pcus = GetPCUs(auth, self.pcu_ids)
	self.islistequal(pcus, [], 'DeletePCU - check')
	
	if self.config.verbose:
	    utils.header("Deleted pcus: %s " % self.pcu_ids)
	self.pcu_ids = []	      	 
 
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

	    # Add node to nodegroup
	    nodegroup_id = random.sample(self.nodegroup_ids, 1)[0]
	    AddNodeToNodeGroup = self.debug(api.AddNodeToNodeGroup)
	    AddNodeToNodeGroup(auth, node_id, nodegroup_id)

	    # Add node to PCU
	    pcu_id = random.sample(self.pcu_ids, 1)[0]
	    AddNodeToPCU = self.debug(api.AddNodeToPCU)
	    AddNodeToPCU(auth, node_id, nodegroup_id)

	    # check nodegroup, pcu
	    nodes = GetNodes(auth, [node_id], ['nodegroup_ids', 'pcu_ids'])
	    if nodes is None or not nodes: continue
	    node = nodes[0]
	    self.islistequal([nodegroup_id], node['nodegroup_ids'], 'AddNodeToNodeGroup - check')
	    self.islistequal([pcu_id], node['pcu_ids'], 'AddNodeToPCU - check') 			
	
	nodes = GetNodes(auth, node_ids)
	if nodes is not None:
	    self.islistequal(node_ids, [node['node_id'] for node in nodes], 'GetNodes - isequal')

	if self.config.verbose:
            utils.header("Added nodes: %s" % node_ids)
	
	return node_ids

    def DeleteNodes(self):

	# Delete attributes manually for first node
	GetNodes = self.debug(api.GetNodes)
	nodes = GetNodes(auth, self.node_ids)
	if nodes is None or not nodes: return 0
	node = nodes[0]

	if node['nodegroup_ids']:
	    # Delete NodeGroup
	    nodegroup_id = random.sample(node['nodegroup_ids'], 1)[0]
	    DeleteNodeFromNodeGroup = self.debug(api.DeleteNodeFromNodeGroup)
	    DeleteNodeFromNodeGroup(auth, node['node_id'], nodegroup_id)

	if node['pcu_ids']:
	    # Delete PCU
	    pcu_id = random.sample(node['pcu_ids'], 1)[0]
	    DeleteNodeFromPCU = self.debug(api.DeleteNodeFromPCU)
	    DeleteNodeFromPCU(auth, node['node_id'], pcu_id)

	# check nodegroup, pcu
	nodes = GetNodes(auth, [node['node_id']])
	if nodes is None or not nodes: return 0
	self.islistequal([], node['nodegroup_ids'], 'DeleteNodeGromNodeGroup - check')
	self.islistequal([], node['pcu_ids'], 'DeleteNodeFromPCU - check')

	# Delete rest of nodes  
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

    def SliceAttributeTypes(self, n = 2):
        attribute_type_ids = []
	AddSliceAttributeType = self.debug(api.AddSliceAttribute)
	GetSliceAttributeTypes = self.debug(api.GetSliceAttributes)
	UpdateSliceAttributeType = self.debug(api.UpdateSliceAttribute)
        
	for i in range(n):
            attribute_type_fields = random_attribute_type()
            attribute_type_id = AddSliceAttributeType(auth, attribute_type_fields)
            if attribute_type_id is None: continue

            # Should return a unique slice_attribute_type_id
            self.isunique(attribute_type_id, attribute_type_ids, 'AddSliceAttributeType - isunique')
            attribute_type_ids.append(attribute_type_id)

            # Check slice_attribute_type
            attribute_types = GeddtSliceAttribute_types(auth, [attribute_type_id])
            if attribute_types is None: continue
            attribute_type = attribute_types[0]
            self.isequal(attribute_type, attribute_types_fields, 'AddSliceAttributeType - isequal')

            # Update slice_attribute_type
            attribute_type_fields = random_attribute_type()
            result = UpdateSliceAttributeType(auth, attribute_type_id, attribute_type_fields)

            # Check again
            attribute_types = GetSliceAttributeTypes(auth, [attribute_type_id])
            if attribute_types is None: continue
            attribute_type = attribute_types[0]
            self.isequal(attribute_type, attribute_type_fields, 'UpdateSliceAttributeType - isequal')

        attribute_types = GetSliceAttributeType(auth, attribute_type_ids)
        if attribute_types is not None:
	    at_ids = [at['attribute_type_id'] for at in attribute_types] 
            self.islistequal(attribute_type_ids, at_ids, 'GetSliceAttributeTypes - isequal')

        if self.config.verbose:
            utils.header("Added slice_attribute_types: %s" % attribute_type_ids)

        return attribute_type_ids

    def DeleteSliceAttributeTypes(self):
	DeleteSliceAttributeType = self.debug(api.DeleteSliceAttributeType)
	GetSliceAttributeTypes = self.debug(api.GetSliceAtttributeTypes)

        # Delete slice_attribute_type
        for slice_attribute_type_id in self.slice_attribute_types_ids:
            result = DeleteSliceAttributeType(auth, slice_attribute_type_id)

        # Check 
        slice_attribute_type_ids = GetSliceAttributeTypes(auth, self.slice_attribute_type_id)
        self.islistequal(slice_attribute_type_ids, [], 'DeleteSliceAttributeTypes - check')
        if self.config.verbose:
            utils.header("Deleted slice_attributes: %s" % self.slice_attribute_type_ids)

        self.slice_attribute_type_ids = []

    def SliceInstantiations(self, n = 2):
	insts = []
        AddSliceInstantiation= self.debug(api.AddSliceInstantiation)
        GetSliceInstantiations = self.debug(api.GetSliceInstantiaton)

        for i in range(n):
            instantiation_fields = random_instantiation()
            result = AddSliceInstantiation(auth, instantiation_fields)
            if result is None: continue
	    instantiation = instantiation_fields['instantiation']
	    insts.append(instantiation)		

            # Check slice instantiaton
            instantiations = GetSliceInstantiation(auth, ['instantiation'])
            if instantiations is None: continue
            instantiation = instantiations[0]
            self.isequal(instantiation, instantiation_fields, 'AddSliceInstantiation - isequal')

	
        instantiations = GetSliceInstantiations(auth, insts)
        if instantiations is not None:
            inst_list = [i['instantiaion'] for i in instantiations]
            self.islistequal(insts, inst_list, 'GetSliceInstantiations - isequal')

        if self.config.verbose:
            utils.header("Added slice instantiations: %s" % insts)

        return insts
	
    def DeleteSliceInstantiations(self):
	DeleteSliceInstantiation = self.debug(api.DeleteSliceInstantiation)
	GetSliceInstantiations = self.debug(api.GetSliceInstantiations)
        # Delete slice instantiation
        for instantiation  in self.slice_instantiations:
            result = DeleteSliceInstantiation(auth, instantiation)

        # Check 
        instantiations = GetSliceInstnatiations(auth, self.slice_instantiations)
        self.islistequal(instantiations, [], 'DeleteSliceInstantiation - check')
        if self.config.verbose:
            utils.header("Deleted slice instantiations" % self.slice_instantiations)

        self.slice_instantiations = []	

    def Slices(self, n = 3):
	slice_ids = []
        AddSlice = self.debug(api.AddSlice)
        GetSlices = self.debug(api.GetSlices)
        UpdateSlice = self.debug(api.UpdateSlice)
	AddSliceToNode = self.debug(api.AddSliceToNode)
        for i in range(n):
            # Add Site
            slice_fields = random_slice()
            slice_id = AddSlice(auth, slice_fields)
            if slice_id is None: continue

            # Should return a unique id
            self.isunique(slice_id, slice_ids, 'AddSlicel - isunique')
            slice_ids.append(slice_id)
            slices = GetSlices(auth, [slice_id])
            if slices is None: continue
            slice = slices[0]
            self.isequal(slice, slice_fields, 'AddSlice - isequal')

            # Update slice
            slice_fields = random_slice()
            result = UpdateSlice(auth, slice_id, slice_fields)

            # Check again
            slices = GetSlices(auth, [slice_id])
            if slices is None: continue
            slice = slices[0]
            self.isequal(slice, slice_fields, 'UpdateSlice - isequal')

	    # Add node
	    node_id = random.sample(self.node_ids, 1)[0]
	    AddSliceToNode(auth, slice_id, node_id)
	
	    # check node
	    slices = GetSlices(auth, [slice_id], ['node_ids'])
	    if slices is None or not slices: continue
	    slice = slices[0]
	    self.islistequal([node_id], slice['node_ids'], 'AddSliceToNode - check')		

        slices = GetSlices(auth, slice_ids)
        if slices is not None:
            self.islistequal(slice_ids, [slice['slice_id'] for slice in slices], 'GetSlices - isequal')

        if self.config.verbose:
            utils.header("Added slices: %s" % slice_ids)

        return slice_ids 

    def DeleteSlices(self):
	
	GetSlices = self.debug(api.GetSlices)
	DeleteSlice = self.debug(api.DeleteSlice)
	DeleteSliceFromNodes = self.debug(api.DeleteSliceFromNodes)	

	# manually delete attributes for first slice
	slices = GetSlices(auth, self.slice_ids, ['slice_id', 'node_ids'])
	if slices is None or not slices: return 0
	slice = slices[0]
	
	if slice['node_ids']:
	    # Delete node from slice
	    node_id = random.sample(slice['node_ids'], 1)[0]
	    DeleteSliceFromNodes(slice['slice_id'], [node_id])
	
	# Check node_ids
	slices = GetSlices(auth, [slice['slice_id']], ['node_ids'])
	if slices is None or not slices: return 0
	slice = slices[0]
	self.islistequal([], slice['node_ids'], 'DeleteSliceFromNode - check')   

        # Have DeleteSlice automatically delete attriubtes for the rest 
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

    def SliceAttributes(self, n = 4):
	attribute_ids = []
	AddSliceAttribute = self.debug(api.AddSliceAttribute)
	GetSliceAttributes = self.debug(api.GetSliceAttributes)
	UpdateSliceAttribute = self.debug(api.UpdateSliceAttribute)

        for i in range(n):
            # Add slice attribute
            attribute_fields = random_slice_attribute()
            slice_id = random.sample(self.slice_ids, 1)[0]
            attribute_id = AddSliceAttribute(auth, slice_id, attribute_fields)
            if attribute_id is None: continue

            # Should return a unique id
            self.isunique(attribute_id, attribute_ids, 'AddSliceAttribute - isunique')
            attribute_ids.append(attribute_id)

            # Check attribute
            attributes = GetSliceAttributes(auth, [attribute_id])
            if attributes is None: continue
            attribute = attributes[0]
            self.isequal(attribute, attribute_fields, 'AddSliceAttribute - isequal')

            # Update attribute
            attribute_fields = random_attribute()
            result = UpdateSliceAttribute(auth, attribute_id, attribute_fields)

            # Check again
            attributes = GetSliceAttributes(auth, [attribute_id])
            if attributes is None: continue
            attribute = attributes[0]
            self.isequal(attribute, attribute_fields, 'UpdateSliceAttribute - isequal')

	attributes = GetSliceAttributes(auth, attribute_ids)
	if attributes is not None:
	    attr_ids = [a['attribute_id'] for a in attributes]
	    self.islistequal(attribute_ids, attr_ids, 'GetSliceAttributes - isequal')
	if self.config.verbose:
	    utils.header("Added slice attributes: %s" % attribute_ids)

	return attribute_ids 

    def DeleteSliceAttributes(self):
	DeleteSliceAttribute = self.debug(api.DeleteSliceAttribute)
        GetSliceAttributes = self.debug(api.GetSliceAttributes)

        for attribute_id in self.slice_attribute_ids:
            DeleteSliceAttribute(auth, attribute_id)

        attributes = GetSliceAttributes(auth, self.slice_attribute_ids)
        self.islistequal(attributes, [], 'DeleteSliceAttribute - check')

        if self.config.verbose:
            utils.header("Deleted slice attributes: %s" % self.slice_attribute_ids)

        self.slice_attribute_ids = []	

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

    def BootStates(self, n = 3):
	boot_states = []
	AddBootState = self.debug(api.AddBootState)
	GetBootStates = self.debug(api.GetBootStates)
	for i in range(n):
	    # Add boot state
	    bootstate_fields = randstr(10)
	    result = AddBootState(auth, bootstate_fields)
	    if result is None: continue
	
	    # Check boot states
	    boot_states.append(bootstate_fields)      
	    bootstates = GetBootStates(auth)
	    if not bootstates: continue
	    bootstates = filter(lambda x: x in [bootstate_fields], bootstates)
	    if not bootstates: continue
	    bootstate = bootstates[0]
	    self.isequal(bootstate, bootstate_fields, 'AddBootState - isequal')
  	    	
	# Check all
	bs = GetBootStates(auth)
	if bs is not None:
	    bs = filter(lambda x: x in [boot_states], bs)
	    self.islistequal(boot_states, bs, 'GetBootStates - isequal')

	if self.config.verbose:
	    utils.header("Added boot_states: %s" % boot_states)

	return boot_states

    def DeleteBootStates(self):
	DeleteBootState = self.debug(api.DeleteBootState)
	GetBootStates = self.debug(api.GetBootStates)
	for boot_state in self.boot_states:
	    result = DeleteBootState(auth, boot_state)
	
	# Check if bootsates are deleted
	boot_states = GetBootStates(auth, self.boot_states)
	self.islistequa(boot_states, [], 'DeleteBootState check')
	
	if self.config.verbose:
	    utils.header("Deleted boot_states: %s" % self.boot_states)

	self.boot_states = []
	    
	 
    def Peers(self, n = 2):
	peer_ids = []
	for i in range(n):
	    # Add Peer
	    peer_fields = random_peer()
	    AddPeer = self.debug(api.AddPeer)
	    peer_id = AddPeer(auth, peer_fields)
	
	    # Should return a unique id
	    self.isunique(peer_id, peer_ids, 'AddPeer - isunique')
	    peer_ids.append(peer_id)
	    GetPeers = self.debug(api.GetPeers)
	    peers = GetPeers(auth, [peer_id])
	    if peers is None: continue
	    peer = peers[0]
	    self.isequal(peer, peer_fields, 'AddPeer - isequal')
	    
	    # Update Peer
	    peer_fields = random_peer()
	    UpdatePeer = self.debug(api.UpdatePeer)
	    result = UpdatePeer(auth, peer_id, peer_fields)
	    
	    # Check again
	    peers = GetPeers(auth, [peer_id])
	    if peers is None: continue
	    peer = peers[0]
	    self.isequal(peer, peer_fields, 'UpdatePeer - isequal')

	peers = GetPeers(auth, peer_ids)
	if peers is not None:
	    self.islistequal(peer_ids, [peer['peer_id'] for peer in peers], 'GetPeers -isequal')
	
	if self.config.verbose:
	    utils.header("Added peers: %s" % peer_ids)
	
	return peer_ids


    def DeletePeers(self):
	# Delete all peers
	DeletePeer = self.debug(api.DeletePeer)
	for peer_id in self.peer_ids:
	    result = DeletePeer(auth, peer_id)
	
	# Check if peers are deleted
	GetPeers = self.debug(api.GetPeers)
	peers = GetPeers(auth, self.peer_ids)
	self.islistequal(peers, [], 'DeletePeer - check' % self.peer_ids)
	
	if self.config.verbose:
	    utils.header("Deleted sites: %s" % self.peer_ids)
	self.peer_ids =[] 
		
    def ConfFiles(self, n = 2):
	conf_file_ids = []
	for i in range(n):
	    # Add ConfFile
	    conf_file_fields = random_conf_file()
	    AddConfFile = self.debug(api.AddConfFile)
	    conf_file_id = AddConfFile(auth, conf_file_fields)
	    if conf_file_id is None: continue
	
	    # Should return a unique id
	    self.isunique(conf_file_id, conf_file_ids, 'AddConfFile - isunique')
	    conf_file_ids.append(conf_file_id)
	    
	    # Get ConfFiles
	    GetConfFiles = self.debug(api.GetConfFiles)
	    conf_files = GetConfFiles(auth, [conf_file_id])
	    if conf_files is None: continue
	    conf_file = conf_files[0]
	    self.isequal(conf_file, conf_file_fields, 'AddConfFile - isunique')
	    
	    # Update ConfFile
	    conf_file_fields = random_conf_file()
	    UpdateConfFile = self.debug(api.UpdateConfFile)
	    result = UpdateConfFile(auth, conf_file_id, conf_file_fields)
	   
	    # Check again
	    conf_files = GetConfFiles(auth, [conf_file_id])
            if conf_files is None: continue
            conf_file = conf_files[0]
            self.isequal(conf_file, conf_file_fields, 'UpdateConfFile - isunique')


	    # Add this conf file to a random node
	    node_id = random.sample(self.node_ids, 1)[0]
	    AddConfFileToNode = self.debug(api.AddConfFileToNode)
	    AddConfFileToNode(auth, conf_file_id, node_id)

	    # Add this conf file to a random node group
	    nodegroup_id = random.sample(self.nodegroup_ids, 1)[0]
	    AddConfFileToNodeGroup = self.debug(api.AddConfFileToNodeGroup)
	    AddConfFileToNodeGroup(auth, conf_file_id, nodegroup_id)

	    # Check node, nodegroup
	    conf_files = GetConfFiles(auth, [conf_file_id], ['node_ids', 'nodegroup_ids'])
	    if conf_files is None or not conf_files: continue
	    conf_file = conf_files[0]
	    self.islistequal([node_id], conf_file['node_ids'], 'AddConfFileToNode - check')
	    self.islistequal([nodegroup_id], conf_file['nodegroup_ids'], 'AddConfFileToNodeGroup - check')
	


	conf_files = GetConfFiles(auth, conf_file_ids)
	if conf_files is not None:
	    self.islistequal(conf_file_ids, [c['conf_file_id'] for c in conf_files], 'GetConfFiles - isequal')
	if self.config.verbose:
	    utils.header("Added conf_files: %s" % conf_file_ids)	

	return conf_file_ids

	def DeleteConfFiles(self):
	
	    GetConfFiles = self.debug(api.GetConfFiles)
	    conf_files = GetConfFiles(auth, self.conf_file_ids)
	    if conf_fiels is None or not conf_files: return 0		
	    conf_file = conf_files[0]
	    
	    if conf_file['node_ids']:
		node_id = random.sample(conf_file['node_ids'], 1)[0]
	        DeleteConfFileFromNode = self.debug(api.DeleteConfFileFromNode)
		DeleteConfFileFromNode(auth, conf_file['conf_file_id'], node_id)

	    if conf_file['nodegroup_ids']:
                nodegroup_id = random.sample(conf_file['nodegroup_ids'], 1)[0]
                DeleteConfFileFromNodeGroup = self.debug(api.DeleteConfFileFromNodeGroup)
                DeleteConfFileFromNode(auth, conf_file['conf_file_id'], nodegroup_id)

	    # check
	    conf_files = GetConfFiles(auth, conf_file['conf_file_id'], ['node_ids', 'nodegroup_ids'])
            if conf_files is None or not conf_files: return 0 
            conf_file = conf_files[0]
            self.islistequal([], conf_file['node_ids'], 'AddConfFileToNode - check')
            self.islistequal([], conf_file['nodegroup_ids'], 'AddConfFileToNodeGroup - check')

	    DeleteConfFile = self.debug(api.DeleteConfFile)
	    for conf_file_id in self.conf_file_ids:
	        DeleteConfFile(auth, conf_file_id)

	    # check 
	    conf_files = GetConfFiles(auth, self.conf_file_ids)
	    self.islistequal(conf_files, [], 'DeleteConfFile - check')
	    
	    if self.config.verbose:
	        utils.header("Deleted conf_files: %s" % self.conf_file_ids)

	    self.conf_file_ids = []
	
	
if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    api_unit_test()(*args)
