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
boot_states = [u'boot', u'dbg', u'inst', u'new', u'rcnf', u'rins']
roles = [10,20,30,40]
methods = [u'static', u'dhcp', u'proxy', u'tap', u'ipmi', u'unknown']
key_types = [u'ssh']
types = [u'ipv4']
attribute_types = range(6,20)
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
       'session': randstr(20) 	
       }

def random_nodenetwork():
    nodenetwork_fields = {
        'method': random.sample(methods, 1)[0],
        'type': random.sample(types, 1)[0],
        'bwlimit': randint(500000, 10000000),
        }

    if nodenetwork_fields['method'] != 'dhcp':
        ip = randint(0, 0xffffffff)
        netmask = (0xffffffff << randint(2, 31)) & 0xffffffff
        network = ip & netmask
        broadcast = ((ip & netmask) | ~netmask) & 0xffffffff
        gateway = randint(network + 1, broadcast - 1)
        dns1 = randint(0, 0xffffffff)

        for field in 'ip', 'netmask', 'network', 'broadcast', 'gateway', 'dns1':
            nodenetwork_fields[field] = socket.inet_ntoa(struct.pack('>L', locals()[field]))

    return nodenetwork_fields

def random_nodenetwork_setting():
    return {
	'value': randstr(20)
	}

def random_nodenetwork_setting_type(): 
    return {
	'name': randstr(20),
	'description': randstr(50),
	'category': randstr(20),
	'min_role_id': random.sample(roles, 1)[0]
	}

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
        'min_role_id': int(random.sample(roles, 1)[0]),
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
	'value': randstr(20)
	}

def random_initscript():
    return {
	'name': randstr(20),
	'enabled': randbool(),
	'script': randstr(200)
	}

def random_role():
    return {
	'role_id': randint(1000),
	'name': randstr(50)
	}

def random_message():
    return {
	'message_id': randstr(10),
	'subject': randstr(100),
	'template': randstr(254),
	}

class api_unit_test(Test):

    def call(self,
	     plc_name = None,
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
	     nodenetwork_setting_types = 2,
	     nodenetwork_settings = 2,
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
	plc = self.config.get_plc(plc_name)
        self.api = plc.config.api
        self.auth = plc.config.auth
        self.logfile = Logfile(self.config.logfile.dir + 'api-unittest.log')

	# Filter out deprecated (Adm) and boot Methods
	current_methods = lambda method: not method.startswith('Adm') and \
				         not method.startswith('Slice') and \
					 not method.startswith('Boot') and \
					 not method.startswith('Anon') and \
					 not method.startswith('system')
	self.all_methods = set(filter(current_methods, self.api.system.listMethods())) 
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
		if hasattr(self, 'NodeNetworks'): self.nodenetwork_ids = self.NodeNetworks(nodenetworks)
		if hasattr(self, 'NodeNetworkSettingTypes'): self.nodenetwork_setting_type_ids = self.NodeNetworkSettingTypes(nodenetwork_setting_types)
		if hasattr(self, 'NodeNetworkSettings'): self.nodenetwork_setting_ids = self.NodeNetworkSettings(nodenetwork_settings)
		if hasattr(self, 'SliceAttributeTypes'): self.slice_attribute_type_ids = self.SliceAttributeTypes(slice_attribute_types)
		if hasattr(self, 'SliceInstantiations'): self.slice_instantiations = self.SliceInstantiations(slice_instantiations)
		if hasattr(self, 'Slices'): self.slice_ids = self.Slices(slices)
		if hasattr(self, 'SliceAttributes'): self.slice_attribute_ids = self.SliceAttributes(slice_attributes)
		if hasattr(self, 'InitScripts'): self.initscript_ids = self.InitScripts(initscripts)
		if hasattr(self, 'Roles'): self.role_ids = self.Roles(roles)
		if hasattr(self, 'Persons'): self.person_ids = self.Persons(persons)
		if hasattr(self, 'KeyTypes'): self.key_types = self.KeyTypes(key_types)
		if hasattr(self, 'Keys'): self.key_ids = self.Keys(keys)
	 	if hasattr(self, 'Messages'):  self.message_ids = self.Messages(messages)	
		if hasattr(self, 'Sessions'): self.session_ids = self.Sessions()
		
		# Test misc Get calls
	        if hasattr(self, 'GenerateNodeConfFile'): self.GenerateNodeConfFile()
		if hasattr(self, 'GetBootMedium'): self.GetBootMedium() 
		if hasattr(self, 'GetEventObjects'): self.event_object_ids = self.GetEventObjects()
		if hasattr(self, 'GetEvents'): self.event_ids = self.GetEvents()
		if hasattr(self, 'GetPeerData'): self.GetPeerData()
	  	if hasattr(self, 'GetPeerName'): self.GetPeerName()
		if hasattr(self, 'GetPlcRelease'): self.GetPlcRelease()
		if hasattr(self, 'GetSliceKeys'): self.GetSliceKeys()
		if hasattr(self, 'GetSliceTicket'): self.GetSliceTicket()
		if hasattr(self, 'GetSlicesMD5'): self.GetSlicesMD5()
		if hasattr(self, 'GetSlivers'): self.GetSlivers()
		if hasattr(self, 'GetWhitelist'): self.GetWhitelist()

		# Test various administrative methods
		if hasattr(self, 'NotifyPersons'): self.NotifyPersons()
		if hasattr(self, 'NotifySupport'): self.NotifySupport()
		if hasattr(self, 'RebootNode'): self.RebootNode()
		if hasattr(self, 'RefrestPeer'): self.RefreshPeer()
		if hasattr(self, 'ResetPassword'): self.ResetPassword()
		if hasattr(self, 'SetPersonPrimarySite'): self.SetPersonPrimarySite()
		if hasattr(self, 'VerifyPerson'): self.VerifyPerson()
		
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
    
    def isinlist(self, item, item_list, method_name):
	try: assert item in item_list
	except:
	    self.methods_failed.update([method_name])
	    return False
	return True
 
    def debug(self, method, method_name=None):
	if method_name is None:
	    try: 
	        method_name = method.name
	        self.methods_tested.update([method_name])
	    except:
	        method_name = method._Method__name
	        self.methods_tested.update([method_name])
		
	def wrapper(*args, **kwds):
	    try:
	        return method(*args, **kwds)
	    except:
	        self.methods_failed.update([method_name])
	        print >> self.logfile, "%s%s: %s\n" % (method_name, tuple(args[1:]), traceback.format_exc()) 
		return None

	return wrapper
 
    def cleanup(self):
	if hasattr(self, 'session_ids'): self.DeleteSessions()
	if hasattr(self, 'message_ids'): self.DeleteMessages()
	if hasattr(self, 'key_types'): self.DeleteKeyTypes()
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
	if hasattr(self, 'conf_file_ids'): self.DeleteConfFiles()
        if hasattr(self, 'node_ids'): self.DeleteNodes()
	if hasattr(self, 'nodegroup_ids'): self.DeleteNodeGroups()
	if hasattr(self, 'network_types'): self.DeleteNetworkTypes()
	if hasattr(self, 'network_methods'): self.DeleteNetworkMethods()
	if hasattr(self, 'pcu_ids'): self.DeletePCUs()
	if hasattr(self, 'pcu_protocol_type_ids'): self.DeletePCUProtocolTypes()		
	if hasattr(self, 'pcu_type_ids'): self.DeletePCUTypes()
	if hasattr(self, 'address_ids'): self.DeleteAddresses()
        if hasattr(self, 'address_type_ids'): self.DeleteAddressTypes()
	if hasattr(self, 'peer_ids'): self.DeletePeers()
	if hasattr(self, 'site_ids'): self.DeleteSites()
	if hasattr(self, 'boot_states'): self.DeleteBootStates()
		

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

    def NetworkMethods(self, n=2):
        methods = []
	AddNetworkMethod = self.debug(self.api.AddNetworkMethod)
	GetNetworkMethods = self.debug(self.api.GetNetworkMethods)
 
        for i in range(n):
            # Add Network Method
            net_method = randstr(10)
            AddNetworkMethod(self.auth, net_method)
            if net_method is None: continue

            # Should return a unique id
            self.isunique(net_method, methods, 'AddNetworkMethod - isunique')
            methods.append(net_method)
            net_methods = GetNetworkMethods(self.auth)
            if net_methods is None: continue
	    net_methods = filter(lambda x: x in [net_method], net_methods) 
            method = net_methods[0]
            self.isequal(method, net_method, 'AddNetworkMethod - isequal')


        net_methods = GetNetworkMethods(self.auth)
        if net_methods is not None:
	    net_methods = filter(lambda x: x in methods, net_methods)
            self.islistequal(methods, net_methods, 'GetNetworkMethods - isequal')

        if self.config.verbose:
            utils.header("Added network methods: %s" % methods)

        return methods

    def DeleteNetworkMethods(self):
	DeleteNetworkMethod = self.debug(self.api.DeleteNetworkMethod)
	GetNetworkMethods = self.debug(self.api.GetNetworkMethods)	
	for method in self.network_methods:
	    DeleteNetworkMethod(self.auth, method)

	# check 
	network_methods = GetNetworkMethods(self.auth)
	network_methods = filter(lambda x: x in self.network_methods, network_methods)
	self.islistequal(network_methods, [], 'DeleteNetworkMethods - check')

	if self.config.verbose:
	    utils.header("Deleted network methods: %s" % self.network_methods)
	self.network_methods = []    

    def NetworkTypes(self, n=2):
	net_types = []
        AddNetworkType = self.debug(self.api.AddNetworkType)
        GetNetworkTypes = self.debug(self.api.GetNetworkTypes)
         
        for i in range(n):
            # Add Network Type 
            type = randstr(10)
            AddNetworkType(self.auth, type)
      
            # Should return a unique id
            self.isunique(type, net_types, 'AddNetworkType - isunique')
            net_types.append(type)
            types = GetNetworkTypes(self.auth)
            if types is None: continue
	    types = filter(lambda x: x in [type], types)
            if types is None: continue
            net_type = types[0]
            self.isequal(net_type, type, 'AddNetworkType - isequal')
    
        types = GetNetworkTypes(self.auth)
        if types is not None:
	    types = filter(lambda x: x in net_types, types)
            self.islistequal(types, net_types, 'GetNetworkTypes - isequal')

        if self.config.verbose:
            utils.header("Added network types: %s" % net_types)

        return net_types	

    def DeleteNetworkTypes(self):	
        DeleteNetworkType = self.debug(self.api.DeleteNetworkType)
        GetNetworkTypes = self.debug(self.api.GetNetworkTypes)
        for type in self.network_types:
            DeleteNetworkType(self.auth, type)

        # check 
        network_types = GetNetworkTypes(self.auth)
	network_types = filter(lambda x: x in self.network_types, network_types)
        self.islistequal(network_types, [], 'DeleteNetworkTypes - check')

        if self.config.verbose:
            utils.header("Deleted network types: %s" % self.network_types)
        self.network_types = []	


    def NodeGroups(self, n = 4):
	nodegroup_ids = []
	AddNodeGroup = self.debug(self.api.AddNodeGroup)
	UpdateNodeGroup = self.debug(self.api.UpdateNodeGroup)
	GetNodeGroups = self.debug(self.api.GetNodeGroups)

	for i in range(n):
	    # Add Nodegroups
	    nodegroup_fields = random_nodegroup()
	    nodegroup_id = AddNodeGroup(self.auth, nodegroup_fields)
	    if nodegroup_id is None: continue
 	
	    # Should return a unique id
	    self.isunique(nodegroup_id, nodegroup_ids, 'AddNodeGroup - isunique')
	    nodegroup_ids.append(nodegroup_id)
	    nodegroups = GetNodeGroups(self.auth, [nodegroup_id])
	    if nodegroups is None: continue
	    nodegroup = nodegroups[0]
	    self.isequal(nodegroup, nodegroup_fields, 'AddNodeGroup - isequal')
	
	    # Update NodeGroups
	    nodegroup_fields = random_nodegroup()
	    UpdateNodeGroup(self.auth, nodegroup_id, nodegroup_fields)

	    # Check again
	    nodegroups = GetNodeGroups(self.auth, [nodegroup_id])
	    if nodegroups is None: continue
	    nodegroup = nodegroups[0]
	    self.isequal(nodegroup, nodegroup_fields, 'UpdateNodeGroup - isequal')

  	nodegroups = GetNodeGroups(self.auth, nodegroup_ids)
	if nodegroups is not None:
	    self.islistequal(nodegroup_ids, [n['nodegroup_id'] for n in nodegroups], 'GetNodeGroups - isequal')
	if self.config.verbose:
	    utils.header("Added nodegroups: %s" % nodegroup_ids)
	
	return nodegroup_ids

    def DeleteNodeGroups(self):
	# Delete all NodeGroups
	GetNodeGroups = self.debug(self.api.GetNodeGroups)
	DeleteNodeGroup = self.debug(self.api.DeleteNodeGroup)
	
	for nodegroup_id in self.nodegroup_ids:
	    result = DeleteNodeGroup(self.auth, nodegroup_id)
	
	# Check is nodegroups are deleted
	nodegroups = GetNodeGroups(self.auth, self.nodegroup_ids)
	self.islistequal(nodegroups, [], 'DeleteNodeGroup - check')
	
	if self.config.verbose:
	    utils.header("Deleted nodegroups: %s" % self.nodegroup_ids)
	
	self.nodegroup_ids = []    

    def PCUTypes(self, n=2):
        pcu_type_ids = []
	AddPCUType = self.debug(self.api.AddPCUType)
	UpdatePCUType = self.debug(self.api.UpdatePCUType)
	GetPCUTypes = self.debug(self.api.GetPCUTypes)
 
	for i in range(n):
	    # Add PCUType
	    pcu_type_fields = random_pcu_type()
	    pcu_type_id = AddPCUType(self.auth, pcu_type_fields)
	    if pcu_type_id is None: continue
	    # Should return a unique id
	    self.isunique(pcu_type_id, pcu_type_ids, 'AddPCUType - isunique')
	    pcu_type_ids.append(pcu_type_id)
	   
	    # Check pcu type
	    pcu_types = GetPCUTypes(self.auth, [pcu_type_id])
	    if pcu_types is None: continue
	    pcu_type = pcu_types[0]
	    self.isequal(pcu_type, pcu_type_fields, 'AddPCUType - isequal')

	    # Update PCUType
	    pcu_type_fields = random_pcu_type()
            UpdatePCUType(self.auth, pcu_type_id, pcu_type_fields)

	    # Check again
	    pcu_types = GetPCUTypes(self.auth, [pcu_type_id])
	    if pcu_types is None: continue
            pcu_type = pcu_types[0]
            self.isequal(pcu_type, pcu_type_fields, 'UpdatePCUType - isequal')

	pcu_types = GetPCUTypes(self.auth, pcu_type_ids)
	if pcu_types is not None:
	    self.islistequal(pcu_type_ids, [p['pcu_type_id'] for p in pcu_types], 'GetPCUTypes - check')

	if self.config.verbose:
	    utils.header("Added pcu_types: %s " % pcu_type_ids)
	return pcu_type_ids
	  
    def DeletePCUTypes(self):
	GetPCUTypes = self.debug(self.api.GetPCUTypes)
	DeletePCUType = self.debug(self.api.DeletePCUType)
	
	for pcu_type_id in self.pcu_type_ids:
	    DeletePCUType(self.auth, pcu_type_id)
	
	pcu_types = GetPCUTypes(self.auth, self.pcu_type_ids)
	self.islistequal(pcu_types, [], 'DeletePCUType - check')  

    def PCUProtocolTypes(self, n=2):
	protocol_type_ids = []
	AddPCUProtocolType = self.debug(self.api.AddPCUProtocolType)
	UpdatePCUProtocolType = self.debug(self.api.UpdatePCUProtocolType)
	GetPCUProtocolTypes = self.debug(self.api.GetPCUProtocolTypes)
	
	for i in range(n):
	    # Add PCUProtocolType
	    protocol_type_fields = random_pcu_protocol_type()
	    pcu_type_id = random.sample(self.pcu_type_ids, 1)[0]
	    protocol_type_id = AddPCUProtocolType(self.auth, pcu_type_id, protocol_type_fields)	    
	    if protocol_type_id is None: continue
	    
	    # Should return a unique id
	    self.isunique(protocol_type_id, protocol_type_ids, 'AddPCUProtocolType - isunique')
	    protocol_type_ids.append(protocol_type_id)

	    # Check protocol type
    	    protocol_types = GetPCUProtocolTypes(self.auth, [protocol_type_id])
	    if protocol_types is None: continue
	    protocol_type = protocol_types[0]
	    self.isequal(protocol_type, protocol_type_fields, 'AddPCUProtocolType - isequal')
	 	
	    # Update protocol type
	    protocol_type_fields = random_pcu_protocol_type()
	    UpdatePCUProtocolType(self.auth, protocol_type_id, protocol_type_fields)
	    
	    # Check again
	    protocol_types = GetPCUProtocolTypes(self.auth, [protocol_type_id])
            if protocol_types is None: continue
            protocol_type = protocol_types[0]
            self.isequal(protocol_type, protocol_type_fields, 'UpdatePCUProtocolType - isequal')

	protocol_types = GetPCUProtocolTypes(self.auth, protocol_type_ids)
	if protocol_types is not None: 
	    pt_ids = [p['pcu_protocol_type_id'] for p in protocol_types]
	    self.islistequal(protocol_type_ids, pt_ids, 'GetPCUProtocolTypes - isequal')
	
	if self.config.verbose:
	    utils.header('Added pcu_protocol_types: %s' % protocol_type_ids)

	return protocol_type_ids	 	

    def DeletePCUProtocolTypes(self):
	GetPCUProtocolTypes = self.debug(self.api.GetPCUProtocolTypes)
	DeletePCUProtocolType = self.debug(self.api.DeletePCUProtocolType)
	
	for protocol_type_id in self.pcu_protocol_type_ids:
	    DeletePCUProtocolType(self.auth, protocol_type_id)
	
	# check 
	protocol_types = GetPCUProtocolTypes(self.auth, self.pcu_protocol_type_ids)
	self.islistequal(protocol_types, [], 'DeletePCUProtocolType - check')
	
	if self.config.verbose:
	    utils.header("Deleted pcu_protocol_types: %s" % self.pcu_protocol_type_ids)
	self.pcu_protocol_type_ids = []

    def PCUs(self, n = 4):
	pcu_ids = []
	AddPCU = self.debug(self.api.AddPCU)
	UpdatePCU = self.debug(self.api.UpdatePCU)
	GetPCUs = self.debug(self.api.GetPCUs)

	for site_id in self.site_ids:
	    # Add PCU		
	    pcu_fields = random_pcu()
	    pcu_id = AddPCU(self.auth, site_id, pcu_fields)
	    if pcu_id is None: continue

	    # Should return a unique id
	    self.isunique(pcu_id, pcu_ids, 'AddPCU - isunique')
	    pcu_ids.append(pcu_id)

	    # check PCU
	    pcus = GetPCUs(self.auth, [pcu_id])
	    if pcus is None: continue
	    pcu = pcus[0]
	    self.isequal(pcu, pcu_fields, 'AddPCU - isequal')
	
	    # Update PCU
	    pcu_fields = random_pcu()
	    UpdatePCU(self.auth, pcu_id, pcu_fields)
	
	    # Check again
	    pcus = GetPCUs(self.auth, [pcu_id])
            if pcus is None: continue
            pcu = pcus[0]
            self.isequal(pcu, pcu_fields, 'UpdatePCU - isequal')

	pcus = GetPCUs(self.auth, pcu_ids)
	if pcus is not None:
	    self.islistequal(pcu_ids, [p['pcu_id'] for p in pcus], 'GetPCUs - isequal')

	if self.config.verbose:
	    utils.header('Added pcus: %s' % pcu_ids)

	return pcu_ids
	
    def DeletePCUs(self):
	GetPCUs = self.debug(self.api.GetPCUs)
	DeletePCU = self.debug(self.api.DeletePCU)

	for pcu_id in self.pcu_ids:
	    DeletePCU(self.auth, pcu_id)

	# check 
	pcus = GetPCUs(self.auth, self.pcu_ids)
	self.islistequal(pcus, [], 'DeletePCU - check')
	
	if self.config.verbose:
	    utils.header("Deleted pcus: %s " % self.pcu_ids)
	self.pcu_ids = []	      	 
 
    def Nodes(self, n=4):
	node_ids = []
	AddNode = self.debug(self.api.AddNode)
	GetNodes = self.debug(self.api.GetNodes)
	UpdateNode = self.debug(self.api.UpdateNode)
	for i in range(n):
	    # Add Node
	    node_fields = random_node()
	    site_id = random.sample(self.site_ids, 1)[0]
	    node_id = AddNode(self.auth, site_id, node_fields)
	    if node_id is None: continue
	    
	    # Should return a unique id
	    self.isunique(node_id, node_ids, 'AddNode - isunique')
	    node_ids.append(node_id)

	    # Check nodes
	    nodes = GetNodes(self.auth, [node_id])
	    if nodes is None: continue
	    node = nodes[0]
	    self.isequal(node, node_fields, 'AddNode - isequal')
	
	    # Update node
	    node_fields = random_node()
	    result = UpdateNode(self.auth, node_id, node_fields)
	    
	    # Check again
	    nodes = GetNodes(self.auth, [node_id])
	    if nodes is None: continue
	    node = nodes[0]
	    self.isequal(node, node_fields, 'UpdateNode - isequal')

	    # Add node to nodegroup
	    nodegroup_id = random.sample(self.nodegroup_ids, 1)[0]
	    AddNodeToNodeGroup = self.debug(self.api.AddNodeToNodeGroup)
	    AddNodeToNodeGroup(self.auth, node_id, nodegroup_id)

	    # Add node to PCU
	    sites = self.api.GetSites(self.auth, [node['site_id']], ['pcu_ids'])
	    if not sites: continue
	    site = sites[0]   
	    pcu_id = random.sample(site['pcu_ids'], 1)[0]
	    port = random.sample(range(65535), 1)[0] 
	    AddNodeToPCU = self.debug(self.api.AddNodeToPCU)
	    AddNodeToPCU(self.auth, node_id, pcu_id, port)

	    # check nodegroup, pcu
	    nodes = GetNodes(self.auth, [node_id], ['nodegroup_ids', 'pcu_ids'])
	    if nodes is None or not nodes: continue
	    node = nodes[0]
	    self.islistequal([nodegroup_id], node['nodegroup_ids'], 'AddNodeToNodeGroup - check')
	    self.islistequal([pcu_id], node['pcu_ids'], 'AddNodeToPCU - check') 			
	
	nodes = GetNodes(self.auth, node_ids)
	if nodes is not None:
	    self.islistequal(node_ids, [node['node_id'] for node in nodes], 'GetNodes - isequal')

	if self.config.verbose:
            utils.header("Added nodes: %s" % node_ids)
	
	return node_ids

    def DeleteNodes(self):

	# Delete attributes manually for first node
	GetNodes = self.debug(self.api.GetNodes)
	nodes = GetNodes(self.auth, self.node_ids)
	if nodes is None or not nodes: return 0
	node = nodes[0]

	if node['nodegroup_ids']:
	    # Delete NodeGroup
	    nodegroup_id = random.sample(node['nodegroup_ids'], 1)[0]
	    DeleteNodeFromNodeGroup = self.debug(self.api.DeleteNodeFromNodeGroup)
	    DeleteNodeFromNodeGroup(self.auth, node['node_id'], nodegroup_id)

	if node['pcu_ids']:
	    # Delete PCU
	    pcu_id = random.sample(node['pcu_ids'], 1)[0]
	    DeleteNodeFromPCU = self.debug(self.api.DeleteNodeFromPCU)
	    DeleteNodeFromPCU(self.auth, node['node_id'], pcu_id)

	# check nodegroup, pcu
	nodes = GetNodes(self.auth, [node['node_id']])
	if nodes is None or not nodes: return 0
	self.islistequal([], node['nodegroup_ids'], 'DeleteNodeGromNodeGroup - check')
	self.islistequal([], node['pcu_ids'], 'DeleteNodeFromPCU - check')

	# Delete rest of nodes  
	DeleteNode = self.debug(self.api.DeleteNode)
	for node_id in self.node_ids:
	    result = DeleteNode(self.auth, node_id)

	# Check if nodes are deleted
	GetNodes = self.debug(self.api.GetNodes)
	nodes = GetNodes(self.auth, self.node_ids)
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
            utils.header("Added address types: %s " % address_type_ids)

	return address_type_ids

    def DeleteAddressTypes(self):

	DeleteAddressType = self.debug(self.api.DeleteAddressType)
        for address_type_id in self.address_type_ids:
            DeleteAddressType(self.auth, address_type_id)

	GetAddressTypes = self.debug(self.api.GetAddressTypes)
	address_types = GetAddressTypes(self.auth, self.address_type_ids)
	self.islistequal(address_types, [], 'DeleteAddressType - check')

        if self.config.verbose:
            utils.header("Deleted address types: %s" % self.address_type_ids)

        self.address_type_ids = []

    def Addresses(self, n = 3):
	address_ids = []
	AddSiteAddress = self.debug(self.api.AddSiteAddress)
	GetAddresses = self.debug(self.api.GetAddresses)  
	UpdateAddress = self.debug(self.api.UpdateAddress)
        AddAddressTypeToAddress = self.debug(self.api.AddAddressTypeToAddress)
	for i in range(n):
            address_fields = random_address()
	    site_id = random.sample(self.site_ids, 1)[0]	
            address_id = AddSiteAddress(self.auth, site_id, address_fields)
	    if address_id is None: continue 
	
            # Should return a unique address_id
	    self.isunique(address_id, address_ids, 'AddSiteAddress - isunique')
	    address_ids.append(address_id)

	    # Check address
	    addresses = GetAddresses(self.auth, [address_id])
	    if addresses is None: continue
	    address = addresses[0]
	    self.isequal(address, address_fields, 'AddSiteAddress - isequal')
	    
	    # Update address
	    address_fields = random_address()
	    result = UpdateAddress(self.auth, address_id, address_fields)
	 	
	    # Check again
	    addresses = GetAddresses(self.auth, [address_id])
	    if addresses is None: continue
	    address = addresses[0]
	    self.isequal(address, address_fields, 'UpdateAddress - isequal')
	      
	    # Add Address Type
	    address_type_id = random.sample(self.address_type_ids, 1)[0]
	    AddAddressTypeToAddress(self.auth, address_type_id, address_id)
	    
	    # check adress type
	    addresses = GetAddresses(self.auth, [address_id], ['address_type_ids'])
	    if addresses is None or not addresses: continue
	    address = addresses[0]
	    self.islistequal([address_type_id], address['address_type_ids'], 'AddAddressTypeToAddress - check')		
	 
	addresses = GetAddresses(self.auth, address_ids)
	if addresses is not None:  
	    self.islistequal(address_ids, [ad['address_id'] for ad in addresses], 'GetAddresses - isequal')     
        
	if self.config.verbose:
            utils.header("Added addresses: %s" % address_ids)

	return address_ids

    def DeleteAddresses(self):

	DeleteAddress = self.debug(self.api.DeleteAddress)
	DeleteAddressTypeFromAddress = self.debug(self.api.DeleteAddressTypeFromAddress)
	GetAddresses = self.debug(self.api.GetAddresses)
        
	# Delete attributes mananually first
	addresses = GetAddresses(self.auth, self.address_ids, ['address_id', 'address_type_ids'])
	if addresses is None or not addresses: return 0
	address = addresses[0]

	if address['address_type_ids']:
	    address_type_id = random.sample(address['address_type_ids'], 1)[0]
	    DeleteAddressTypeFromAddress(self.auth, address_type_id, address['address_id'])  

	# check address_type_ids
	addresses = GetAddresses(self.auth, [address['address_id']], ['address_type_ids'])
	if addresses is None or not addresses: return 0
	address = addresses[0]
	self.islistequal([], address['address_type_ids'], 'DeleteAddressTypeFromAddress - check') 

	# Delete site addresses
        for address_id in self.address_ids:
	    result = DeleteAddress(self.auth, address_id)
	
	# Check 
	addresses = GetAddresses(self.auth, self.address_ids)
	self.islistequal(addresses, [], 'DeleteAddress - check')
        if self.config.verbose:
            utils.header("Deleted addresses: %s" % self.address_ids)

        self.address_ids = []

    def SliceAttributeTypes(self, n = 2):
        attribute_type_ids = []
	AddSliceAttributeType = self.debug(self.api.AddSliceAttributeType)
	GetSliceAttributeTypes = self.debug(self.api.GetSliceAttributeTypes)
	UpdateSliceAttributeType = self.debug(self.api.UpdateSliceAttributeType)
        
	for i in range(n):
            attribute_type_fields = random_attribute_type()
            attribute_type_id = AddSliceAttributeType(self.auth, attribute_type_fields)
            if attribute_type_id is None: continue

            # Should return a unique slice_attribute_type_id
            self.isunique(attribute_type_id, attribute_type_ids, 'AddSliceAttributeType - isunique')
            attribute_type_ids.append(attribute_type_id)

            # Check slice_attribute_type
            attribute_types = GetSliceAttributeTypes(self.auth, [attribute_type_id])
            if attribute_types is None: continue
            attribute_type = attribute_types[0]
            self.isequal(attribute_type, attribute_type_fields, 'AddSliceAttributeType - isequal')

            # Update slice_attribute_type
            attribute_type_fields = random_attribute_type()
            result = UpdateSliceAttributeType(self.auth, attribute_type_id, attribute_type_fields)

            # Check again
            attribute_types = GetSliceAttributeTypes(self.auth, [attribute_type_id])
            if attribute_types is None: continue
            attribute_type = attribute_types[0]
            self.isequal(attribute_type, attribute_type_fields, 'UpdateSliceAttributeType - isequal')

        attribute_types = GetSliceAttributeTypes(self.auth, attribute_type_ids)
        if attribute_types is not None:
	    at_ids = [at['attribute_type_id'] for at in attribute_types] 
            self.islistequal(attribute_type_ids, at_ids, 'GetSliceAttributeTypes - isequal')

        if self.config.verbose:
            utils.header("Added slice_attribute_types: %s" % attribute_type_ids)

        return attribute_type_ids

    def DeleteSliceAttributeTypes(self):
	DeleteSliceAttributeType = self.debug(self.api.DeleteSliceAttributeType)
	GetSliceAttributeTypes = self.debug(self.api.GetSliceAttributeTypes)

        # Delete slice_attribute_type
        for slice_attribute_type_id in self.slice_attribute_type_ids:
            result = DeleteSliceAttributeType(self.auth, slice_attribute_type_id)

        # Check 
        slice_attribute_types = GetSliceAttributeTypes(self.auth, self.slice_attribute_type_ids)
        self.islistequal(slice_attribute_types, [], 'DeleteSliceAttributeTypes - check')
        if self.config.verbose:
            utils.header("Deleted slice_attributes: %s" % self.slice_attribute_type_ids)

        self.slice_attribute_type_ids = []

    def SliceInstantiations(self, n = 2):
	insts = []
        AddSliceInstantiation= self.debug(self.api.AddSliceInstantiation)
        GetSliceInstantiations = self.debug(self.api.GetSliceInstantiations)

        for i in range(n):
            inst = randstr(10)
            result = AddSliceInstantiation(self.auth, inst)
            if result is None: continue
	    insts.append(inst)		

            # Check slice instantiaton
            instantiations = GetSliceInstantiations(self.auth)
            if instantiations is None: continue
	    instantiations = filter(lambda x: x in [inst], instantiations)
            instantiation = instantiations[0]
            self.isequal(instantiation, inst, 'AddSliceInstantiation - isequal')

	
        instantiations = GetSliceInstantiations(self.auth)
        if instantiations is not None:
	    instantiations = filter(lambda x: x in insts, instantiations)
            self.islistequal(insts, instantiations, 'GetSliceInstantiations - isequal')

        if self.config.verbose:
            utils.header("Added slice instantiations: %s" % insts)

        return insts
	
    def DeleteSliceInstantiations(self):
	DeleteSliceInstantiation = self.debug(self.api.DeleteSliceInstantiation)
	GetSliceInstantiations = self.debug(self.api.GetSliceInstantiations)
        # Delete slice instantiation
        for instantiation  in self.slice_instantiations:
            result = DeleteSliceInstantiation(self.auth, instantiation)

        # Check 
        instantiations = GetSliceInstantiations(self.auth)
	instantiations = filter(lambda x: x in self.slice_instantiations, instantiations)
        self.islistequal(instantiations, [], 'DeleteSliceInstantiation - check')
        if self.config.verbose:
            utils.header("Deleted slice instantiations: %s" % self.slice_instantiations)

        self.slice_instantiations = []	

    def Slices(self, n = 3):
	slice_ids = []
        AddSlice = self.debug(self.api.AddSlice)
        GetSlices = self.debug(self.api.GetSlices)
        UpdateSlice = self.debug(self.api.UpdateSlice)
	AddSliceToNodes = self.debug(self.api.AddSliceToNodes)
        for i in range(n):
            # Add Site
            slice_fields = random_slice()
            slice_id = AddSlice(self.auth, slice_fields)
            if slice_id is None: continue

            # Should return a unique id
            self.isunique(slice_id, slice_ids, 'AddSlicel - isunique')
            slice_ids.append(slice_id)
            slices = GetSlices(self.auth, [slice_id])
            if slices is None: continue
            slice = slices[0]
            self.isequal(slice, slice_fields, 'AddSlice - isequal')

            # Update slice
            slice_fields = random_slice()
            result = UpdateSlice(self.auth, slice_id, slice_fields)

            # Check again
            slices = GetSlices(self.auth, [slice_id])
            if slices is None: continue
            slice = slices[0]
            self.isequal(slice, slice_fields, 'UpdateSlice - isequal')

	    # Add node
	    node_id = random.sample(self.node_ids, 1)[0]
	    AddSliceToNodes(self.auth, slice_id, [node_id])
	
	    # check node
	    slices = GetSlices(self.auth, [slice_id], ['node_ids'])
	    if slices is None or not slices: continue
	    slice = slices[0]
	    self.islistequal([node_id], slice['node_ids'], 'AddSliceToNode - check')		

        slices = GetSlices(self.auth, slice_ids)
        if slices is not None:
            self.islistequal(slice_ids, [slice['slice_id'] for slice in slices], 'GetSlices - isequal')

        if self.config.verbose:
            utils.header("Added slices: %s" % slice_ids)

        return slice_ids 

    def DeleteSlices(self):
	
	GetSlices = self.debug(self.api.GetSlices)
	DeleteSlice = self.debug(self.api.DeleteSlice)
	DeleteSliceFromNodes = self.debug(self.api.DeleteSliceFromNodes)	

	# manually delete attributes for first slice
	slices = GetSlices(self.auth, self.slice_ids, ['slice_id', 'node_ids'])
	if slices is None or not slices: return 0
	slice = slices[0]
	
	if slice['node_ids']:
	    # Delete node from slice
	    node_id = random.sample(slice['node_ids'], 1)[0]
	    DeleteSliceFromNodes(self.auth, slice['slice_id'], [node_id])
	
	# Check node_ids
	slices = GetSlices(self.auth, [slice['slice_id']], ['node_ids'])
	if slices is None or not slices: return 0
	slice = slices[0]
	self.islistequal([], slice['node_ids'], 'DeleteSliceFromNode - check')   

        # Have DeleteSlice automatically delete attriubtes for the rest 
        for slice_id in self.slice_ids:
            # Delete account
            DeleteSlice(self.auth, slice_id)

        # Check if slices are deleted
        GetSlices = self.debug(self.api.GetSlices)
        slices = GetSlices(self.auth, self.slice_ids)
        self.islistequal(slices, [], 'DeleteSlice - check')

        if self.config.verbose:
            utils.header("Deleted slices: %s" % self.slice_ids)

        self.slice_ids = []

    def SliceAttributes(self, n = 4):
	attribute_ids = []
	AddSliceAttribute = self.debug(self.api.AddSliceAttribute)
	GetSliceAttributes = self.debug(self.api.GetSliceAttributes)
	UpdateSliceAttribute = self.debug(self.api.UpdateSliceAttribute)

        for i in range(n):
            # Add slice attribute
            attribute_fields = random_slice_attribute()
            slice_id = random.sample(self.slice_ids, 1)[0]
	    type = attribute_fields['attribute_type_id']
	    value = attribute_fields['value']	
            attribute_id = AddSliceAttribute(self.auth, slice_id, type, value)
            if attribute_id is None: continue

            # Should return a unique id
            self.isunique(attribute_id, attribute_ids, 'AddSliceAttribute - isunique')
            attribute_ids.append(attribute_id)

            # Check attribute
            attributes = GetSliceAttributes(self.auth, [attribute_id])
            if attributes is None: continue
            attribute = attributes[0]
            self.isequal(attribute, attribute_fields, 'AddSliceAttribute - isequal')

            # Update attribute
            attribute_fields = random_slice_attribute()
	    type = attribute_fields['attribute_type_id']
            value = attribute_fields['value']	
            result = UpdateSliceAttribute(self.auth, attribute_id, value)

            # Check again
            attributes = GetSliceAttributes(self.auth, [attribute_id])
            if attributes is None: continue
            attribute = attributes[0]
            self.isequal(attribute, attribute_fields, 'UpdateSliceAttribute - isequal')

	attributes = GetSliceAttributes(self.auth, attribute_ids)
	if attributes is not None:
	    attr_ids = [a['slice_attribute_id'] for a in attributes]
	    self.islistequal(attribute_ids, attr_ids, 'GetSliceAttributes - isequal')
	if self.config.verbose:
	    utils.header("Added slice attributes: %s" % attribute_ids)

	return attribute_ids 

    def DeleteSliceAttributes(self):
	DeleteSliceAttribute = self.debug(self.api.DeleteSliceAttribute)
        GetSliceAttributes = self.debug(self.api.GetSliceAttributes)

        for attribute_id in self.slice_attribute_ids:
            DeleteSliceAttribute(self.auth, attribute_id)

        attributes = GetSliceAttributes(self.auth, self.slice_attribute_ids)
        self.islistequal(attributes, [], 'DeleteSliceAttribute - check')

        if self.config.verbose:
            utils.header("Deleted slice attributes: %s" % self.slice_attribute_ids)

        self.slice_attribute_ids = []	

    def InitScripts(self, n = 2):
        initscript_ids = []
        AddInitScript = self.debug(self.api.AddInitScript)
        GetInitScripts = self.debug(self.api.GetInitScripts)
        UpdateInitScript = self.debug(self.api.UpdateInitScript)
        for i in range(n):
            # Add Peer
            initscript_fields = random_initscript()
            initscript_id = AddInitScript(self.auth, initscript_fields)

            # Should return a unique id
            self.isunique(initscript_id, initscript_ids, 'AddInitScript - isunique')
            initscript_ids.append(initscript_id)
            initscripts = GetInitScripts(self.auth, [initscript_id])
            if initscripts is None: continue
            initscript = initscripts[0]
            self.isequal(initscript, initscript_fields, 'AddInitScript - isequal')

            # Update Peer
            initscript_fields = random_initscript()
            result = UpdateInitScript(self.auth, initscript_id, initscript_fields)

            # Check again
            initscripts = GetInitScripts(self.auth, [initscript_id])
            if initscripts is None: continue
            initscript = initscripts[0]
            self.isequal(initscript, initscript_fields, 'UpdateInitScript - isequal')

        initscripts = GetInitScripts(self.auth, initscript_ids)
        if initscripts is not None:
            self.islistequal(initscript_ids, [i['initscript_id'] for i in initscripts], 'GetInitScripts -isequal')

        if self.config.verbose:
            utils.header("Added initscripts: %s" % initscript_ids)

        return initscript_ids

    def DeleteInitScripts(self):
	# Delete all initscripts
        DeleteInitScript = self.debug(self.api.DeleteInitScript)
        GetInitScripts = self.debug(self.api.GetInitScripts)
        for initscript_id in self.initscript_ids:
            result = DeleteInitScript(self.auth, initscript_id)

        # Check if peers are deleted
        initscripts = GetInitScripts(self.auth, self.initscript_ids)
        self.islistequal(initscripts, [], 'DeletInitScript - check')

        if self.config.verbose:
            utils.header("Deleted initscripts: %s" % self.initscript_ids)
        self.initscript_ids =[]

    def Roles(self, n = 2):
	role_ids = []
        AddRole = self.debug(self.api.AddRole)
        GetRoles = self.debug(self.api.GetRoles)
        for i in range(n):
            # Add Role
            role_fields = random_role()
	    role_id = role_fields['role_id']
	    name = role_fields['name']
            AddRole(self.auth, role_id, name)

            # Should return a unique id
            self.isunique(role_id, role_ids, 'AddRole - isunique')
            role_ids.append(role_id)
            roles = GetRoles(self.auth)
            if roles is None: continue
            roles = filter(lambda x: x['role_id'] in [role_id], roles)
	    role = roles[0]
            self.isequal(role, role_fields, 'AddRole - isequal')

        roles = GetRoles(self.auth)
        if roles is not None:
	    roles = filter(lambda x: x['role_id'] in role_ids, roles) 
            self.islistequal(role_ids, [r['role_id'] for r in roles], 'GetRoles - isequal')

        if self.config.verbose:
            utils.header("Added roles: %s" % role_ids)

        return role_ids

    def DeleteRoles(self):
	# Delete all roles
        DeleteRole = self.debug(self.api.DeleteRole)
        GetRoles = self.debug(self.api.GetRoles)
        for role_id in self.role_ids:
            result = DeleteRole(self.auth, role_id)

        # Check if peers are deleted
        roles = GetRoles(self.auth)
	roles = filter(lambda x: x['role_id'] in self.role_ids, roles) 
        self.islistequal(roles, [], 'DeleteRole - check' % self.role_ids)

        if self.config.verbose:
            utils.header("Deleted roles: %s" % self.role_ids)
        self.role_ids =[]

    def Persons(self, n = 3):

        person_ids = []
	for i in range(n):

            # Add account
            person_fields = random_person()
	    AddPerson = self.debug(self.api.AddPerson)
            person_id = AddPerson(self.auth, person_fields)
	    if person_id is None: continue
	
            # Should return a unique person_id
            self.isunique(person_id, person_ids, 'AddPerson - isunique')
	    person_ids.append(person_id)
	    GetPersons = self.debug(self.api.GetPersons)
	    persons = GetPersons(self.auth, [person_id])
	    if persons is None: continue
	    person = persons[0]
	    self.isequal(person, person_fields, 'AddPerson - isequal')

            # Update account
            person_fields = random_person()
	    person_fields['enabled'] = True
	    UpdatePerson = self.debug(self.api.UpdatePerson)
            result = UpdatePerson(self.auth, person_id, person_fields)
	
            # Add random role 
	    AddRoleToPerson = self.debug(self.api.AddRoleToPerson)	
            role = random.sample(roles, 1)[0]
            result = AddRoleToPerson(self.auth, role, person_id)

	    # Add key to person
	    key = random_key()
	    key_id = AddPersonKey = self.debug(self.api.AddPersonKey)
	    AddPersonKey(self.auth, person_id, key)
	
	    # Add person to site
	    site_id = random.sample(self.site_ids, 1)[0]
	    AddPersonToSite = self.debug(self.api.AddPersonToSite)
	    AddPersonToSite(self.auth, person_id, site_id)  	 
	
	    # Add person to slice
	    slice_id = random.sample(self.slice_ids, 1)[0]
	    AddPersonToSlice = self.debug(self.api.AddPersonToSlice)
	    AddPersonToSlice(self.auth, person_id, slice_id)

	    # check role, key, site, slice
	    persons = GetPersons(self.auth, [person_id], ['roles', 'key_ids', 'site_ids', 'slice_ids'])
	    if persons is None or not persons: continue
	    person = persons[0]
	    self.islistequal([role], person['roles'], 'AddRoleToPerson - check')
	    self.islistequal([key_id], person['key_ids'], 'AddPersonKey - check')
	    self.islistequal([site_id], person['site_ids'], 'AddPersonToSite - check')
	    self.islistequal([slice_id], person['slice_ids'], 'AddPersonToSlice - check')

	persons = GetPersons(self.auth, person_ids)
	if persons is not None:
	    self.islistequal(person_ids, [p['person_id'] for p in persons], 'GetPersons - isequal')

        if self.config.verbose:
            utils.header("Added users: %s" % person_ids)

	return person_ids

    def DeletePersons(self):
        
	# Delete attributes manually for first person
	GetPersons = self.debug(self.api.GetPersons)
	persons = GetPersons(self.auth, self.person_ids, ['person_id' , 'key_ids', 'site_ids', 'slice_ids', 'roles'])
	if persons is None or not persons: return 0
	person = persons[0]

 	if person['roles']:	   
	    # Delete role
 	    role = random.sample(person['roles'], 1)[0]
            DeleteRoleFromPerson = self.debug(self.api.DeleteRoleFromPerson)
            DeleteRoleFromPerson(self.auth, role, person['person_id'])

	if person['key_ids']:
            # Delete key
	    key_id = random.sample(person['key_ids'], 1)[0] 
            DeleteKey = self.debug(self.api.DeleteKey)
            DeleteKey(self.auth, key_id)
	
	if person['site_ids']:
            # Remove person from site
	    site_id = random.sample(person['site_ids'], 1)[0]
            DeletePersonFromSite = self.debug(self.api.DeletePersonFromSite)
            DeletePersonFromSite(self.auth, person['person_id'], site_id)

	if person['slice_ids']:
            # Remove person from slice
	    slice_id = random.sample(person['slice_ids'], 1)[0]
            DeletePersonFromSlice = self.debug(self.api.DeletePersonFromSlice)
            DeletePersonFromSlice(self.auth, person['person_id'], slice_id)

        # check role, key, site, slice
        persons = GetPersons(self.auth, [person['person_id']], ['roles', 'key_ids', 'site_ids', 'slice_ids'])
        if persons is None or not persons: return 0
        person = persons[0]
        self.islistequal([], person['roles'], 'DeleteRoleFromPerson - check')
        self.islistequal([], person['key_ids'], 'DeleteKey - check')
        self.islistequal([], person['site_ids'], 'DeletePersonFromSite - check')
        self.islistequal([], person['slice_ids'], 'DeletePersonFromSlice - check')
	
	DeletePerson = self.debug(self.api.DeletePerson)
        # Have DeletePeson automatically delete attriubtes for all other persons 
        for person_id in self.person_ids:
            # Delete account
            DeletePerson(self.auth, person_id)

        # Check if persons are deleted
	GetPersons = self.debug(self.api.GetPersons)
	persons = GetPersons(self.auth, self.person_ids)
	self.islistequal(persons, [], 'DeletePerson - check')
 
	if self.config.verbose:
            utils.header("Deleted users: %s" % self.person_ids)

        self.person_ids = []

    def KeyTypes(self, n = 2):
	key_types = []
        AddKeyType = self.debug(self.api.AddKeyType)
        GetKeyTypes = self.debug(self.api.GetKeyTypes)
        for i in range(n):
            # Add key type
            keytype = randstr(10)
            result = AddKeyType(self.auth, keytype)
            if result is None: continue

            # Check key types
            key_types.append(keytype)
            keytypes  = GetKeyTypes(self.auth)
            if not keytypes: continue
            keytypes = filter(lambda x: x in [keytype], keytypes)
            if not keytypes: continue
            self.isequal(keytype, keytypes[0], 'AddKeyType - isequal')

        # Check all
        keytypes = GetKeyTypes(self.auth)
        if keytypes is not None:
            keytypes = filter(lambda x: x in key_types, keytypes)
            self.islistequal(key_types, keytypes, 'GetKeyTypes - isequal')

        if self.config.verbose:
            utils.header("Added key types: %s" % key_types)

        return key_types

    def DeleteKeyTypes(self):
	DeleteKeyType = self.debug(self.api.DeleteKeyType)
        GetKeyTypes = self.debug(self.api.GetKeyTypes)
        for key_type in self.key_types:
            result = DeleteKeyType(self.auth, key_type)

        # Check if key types are deleted
        key_types = GetKeyTypes(self.auth)
	key_types = filter(lambda x: x in self.key_types, key_types)
        self.islistequal(key_types, [], 'DeleteKeyType - check')

        if self.config.verbose:
            utils.header("Deleted key types %s" % self.key_types)

        self.key_types = []	

    def Keys(self, n = 3):
	key_ids = []
	for i in range(n):
	    # Add a key to an account
	    key_fields = random_key()
	    person_id = random.sample(self.person_ids, 1)[0]
	    AddPersonKey = self.debug(self.api.AddPersonKey)
	    key_id = AddPersonKey(self.auth, person_id, key_fields)   
	    if key_id is None: continue
	     	
	    # Should return a unique key_id
	    self.isunique(key_id, key_ids, 'AddPersonKey - isunique')
	    key_ids.append(key_id)
	    GetKeys = self.debug(self.api.GetKeys)
	    keys = GetKeys(self.auth, [key_id])
	    if keys is None: continue
	    key = keys[0]
	    self.isequal(key, key_fields, 'AddPersonKey - isequal')
	    
	    # Update Key
	    key_fields = random_key()
	    UpdateKey = self.debug(self.api.UpdateKey)
	    result = UpdateKey(self.auth, key_id, key_fields)
	    
	    keys = GetKeys(self.auth, [key_id])
	    if keys is None or not keys: continue	 	 
	    key = keys[0]
	    self.isequal(key, key_fields, 'UpdatePersonKey - isequal')
	    
	keys = GetKeys(self.auth, key_ids)
	if keys is not None:
	    self.islistequal(key_ids, [key['key_id'] for key in keys], 'GetKeys - isequal')
	
	if self.config.verbose:
	    utils.header("Added keys: %s" % key_ids)
	return key_ids


    def DeleteKeys(self):
	
	# Blacklist first key, Delete rest
	GetKeys = self.debug(self.api.GetKeys)
	DeleteKey = self.debug(self.api.DeleteKey)
	BlacklistKey = self.debug(self.api.BlacklistKey)
	
	key_id = self.key_ids.pop()
	BlacklistKey(self.auth, key_id)  
	keys = GetKeys(self.auth, [key_id])
	self.islistequal(keys, [], 'BlacklistKey - check')
	
	if self.config.verbose:
	    utils.header("Blacklisted key: %s" % key_id)

	for key_id in self.key_ids:
	    DeleteKey(self.auth, key_id)
	
	keys = GetKeys(self.auth, self.key_ids)
	self.islistequal(keys, [], 'DeleteKey - check')
	
	if self.config.verbose:
	    utils.header("Deleted keys: %s" % self.key_ids)  
	     
	self.key_ids = []

    def BootStates(self, n = 3):
	boot_states = []
	AddBootState = self.debug(self.api.AddBootState)
	GetBootStates = self.debug(self.api.GetBootStates)
	for i in range(n):
	    # Add boot state
	    bootstate_fields = randstr(10)
	    result = AddBootState(self.auth, bootstate_fields)
	    if result is None: continue
	
	    # Check boot states
	    boot_states.append(bootstate_fields)      
	    bootstates = GetBootStates(self.auth)
	    if not bootstates: continue
	    bootstates = filter(lambda x: x in [bootstate_fields], bootstates)
	    if not bootstates: continue
	    bootstate = bootstates[0]
	    self.isequal(bootstate, bootstate_fields, 'AddBootState - isequal')
  	    	
	# Check all
	bs = GetBootStates(self.auth)
	if bs is not None:
	    bs = filter(lambda x: x in [boot_states], bs)
	    self.islistequal(boot_states, bs, 'GetBootStates - isequal')

	if self.config.verbose:
	    utils.header("Added boot_states: %s" % boot_states)

	return boot_states

    def DeleteBootStates(self):
	DeleteBootState = self.debug(self.api.DeleteBootState)
	GetBootStates = self.debug(self.api.GetBootStates)
	for boot_state in self.boot_states:
	    result = DeleteBootState(self.auth, boot_state)
	
	# Check if bootsates are deleted
	boot_states = GetBootStates(self.auth)
	boot_states = filter(lambda x: x in self.boot_states, boot_states)
	self.islistequal(boot_states, [], 'DeleteBootState check')
	
	if self.config.verbose:
	    utils.header("Deleted boot_states: %s" % self.boot_states)

	self.boot_states = []
	    
	 
    def Peers(self, n = 2):
	peer_ids = []
	AddPeer = self.debug(self.api.AddPeer)
	GetPeers = self.debug(self.api.GetPeers)
	UpdatePeer = self.debug(self.api.UpdatePeer)
	for i in range(n):
	    # Add Peer
	    peer_fields = random_peer()
	    peer_id = AddPeer(self.auth, peer_fields)
	
	    # Should return a unique id
	    self.isunique(peer_id, peer_ids, 'AddPeer - isunique')
	    peer_ids.append(peer_id)
	    peers = GetPeers(self.auth, [peer_id])
	    if peers is None: continue
	    peer = peers[0]
	    self.isequal(peer, peer_fields, 'AddPeer - isequal')
	    
	    # Update Peer
	    peer_fields = random_peer()
	    result = UpdatePeer(self.auth, peer_id, peer_fields)
	    
	    # Check again
	    peers = GetPeers(self.auth, [peer_id])
	    if peers is None: continue
	    peer = peers[0]
	    self.isequal(peer, peer_fields, 'UpdatePeer - isequal')

	peers = GetPeers(self.auth, peer_ids)
	if peers is not None:
	    self.islistequal(peer_ids, [peer['peer_id'] for peer in peers], 'GetPeers -isequal')
	
	if self.config.verbose:
	    utils.header("Added peers: %s" % peer_ids)
	
	return peer_ids


    def DeletePeers(self):
	# Delete all peers
	DeletePeer = self.debug(self.api.DeletePeer)
	GetPeers = self.debug(self.api.GetPeers)
	for peer_id in self.peer_ids:
	    result = DeletePeer(self.auth, peer_id)
	
	# Check if peers are deleted
	peers = GetPeers(self.auth, self.peer_ids)
	self.islistequal(peers, [], 'DeletePeer - check' % self.peer_ids)
	
	if self.config.verbose:
	    utils.header("Deleted peers: %s" % self.peer_ids)
	self.peer_ids =[] 
		
    def ConfFiles(self, n = 2):
	conf_file_ids = []
	for i in range(n):
	    # Add ConfFile
	    conf_file_fields = random_conf_file()
	    AddConfFile = self.debug(self.api.AddConfFile)
	    conf_file_id = AddConfFile(self.auth, conf_file_fields)
	    if conf_file_id is None: continue
	
	    # Should return a unique id
	    self.isunique(conf_file_id, conf_file_ids, 'AddConfFile - isunique')
	    conf_file_ids.append(conf_file_id)
	    
	    # Get ConfFiles
	    GetConfFiles = self.debug(self.api.GetConfFiles)
	    conf_files = GetConfFiles(self.auth, [conf_file_id])
	    if conf_files is None: continue
	    conf_file = conf_files[0]
	    self.isequal(conf_file, conf_file_fields, 'AddConfFile - isunique')
	    
	    # Update ConfFile
	    conf_file_fields = random_conf_file()
	    UpdateConfFile = self.debug(self.api.UpdateConfFile)
	    result = UpdateConfFile(self.auth, conf_file_id, conf_file_fields)
	   
	    # Check again
	    conf_files = GetConfFiles(self.auth, [conf_file_id])
            if conf_files is None: continue
            conf_file = conf_files[0]
            self.isequal(conf_file, conf_file_fields, 'UpdateConfFile - isunique')


	    # Add this conf file to a random node
	    node_id = random.sample(self.node_ids, 1)[0]
	    AddConfFileToNode = self.debug(self.api.AddConfFileToNode)
	    AddConfFileToNode(self.auth, conf_file_id, node_id)

	    # Add this conf file to a random node group
	    nodegroup_id = random.sample(self.nodegroup_ids, 1)[0]
	    AddConfFileToNodeGroup = self.debug(self.api.AddConfFileToNodeGroup)
	    AddConfFileToNodeGroup(self.auth, conf_file_id, nodegroup_id)

	    # Check node, nodegroup
	    conf_files = GetConfFiles(self.auth, [conf_file_id], ['node_ids', 'nodegroup_ids'])
	    if conf_files is None or not conf_files: continue
	    conf_file = conf_files[0]
	    self.islistequal([node_id], conf_file['node_ids'], 'AddConfFileToNode - check')
	    self.islistequal([nodegroup_id], conf_file['nodegroup_ids'], 'AddConfFileToNodeGroup - check')
	


	conf_files = GetConfFiles(self.auth, conf_file_ids)
	if conf_files is not None:
	    self.islistequal(conf_file_ids, [c['conf_file_id'] for c in conf_files], 'GetConfFiles - isequal')
	if self.config.verbose:
	    utils.header("Added conf_files: %s" % conf_file_ids)	

	return conf_file_ids

    def DeleteConfFiles(self):
	
	    GetConfFiles = self.debug(self.api.GetConfFiles)
	    DeleteConfFile = self.debug(self.api.DeleteConfFile)
	    DeleteConfFileFromNode = self.debug(self.api.DeleteConfFileFromNode)
            DeleteConfFileFromNodeGroup = self.debug(self.api.DeleteConfFileFromNodeGroup)

	    conf_files = GetConfFiles(self.auth, self.conf_file_ids)
	    if conf_files is None or not conf_files: return 0		
	    conf_file = conf_files[0]
	    if conf_file['node_ids']:
		node_id = random.sample(conf_file['node_ids'], 1)[0]
		DeleteConfFileFromNode(self.auth, conf_file['conf_file_id'], node_id)
	    if conf_file['nodegroup_ids']:
                nodegroup_id = random.sample(conf_file['nodegroup_ids'], 1)[0]
                DeleteConfFileFromNodeGroup(self.auth, conf_file['conf_file_id'], nodegroup_id)

	    # check
	    conf_files = GetConfFiles(self.auth, [conf_file['conf_file_id']], ['node_ids', 'nodegroup_ids'])
            if conf_files is None or not conf_files: return 0 
            conf_file = conf_files[0]
            self.islistequal([], conf_file['node_ids'], 'AddConfFileToNode - check')
            self.islistequal([], conf_file['nodegroup_ids'], 'AddConfFileToNodeGroup - check')

	    for conf_file_id in self.conf_file_ids:
	        DeleteConfFile(self.auth, conf_file_id)

	    # check 
	    conf_files = GetConfFiles(self.auth, self.conf_file_ids)
	    self.islistequal(conf_files, [], 'DeleteConfFile - check')
	    
	    if self.config.verbose:
	        utils.header("Deleted conf_files: %s" % self.conf_file_ids)

	    self.conf_file_ids = []
    
    def NodeNetworks(self, n = 4):
	nodenetwork_ids = []
        AddNodeNetwork = self.debug(self.api.AddNodeNetwork)
        UpdateNodeNetwork = self.debug(self.api.UpdateNodeNetwork)
        GetNodeNetworks = self.debug(self.api.GetNodeNetworks)

        for i in range(n):
            # Add Node Network          
            nodenetwork_fields = random_nodenetwork()
	    node_id = random.sample(self.node_ids, 1)[0]
            nodenetwork_id = AddNodeNetwork(self.auth, node_id, nodenetwork_fields)
            if nodenetwork_id is None: continue

            # Should return a unique id
            self.isunique(nodenetwork_ids, nodenetwork_ids, 'AddNodeNetwork - isunique')
            nodenetwork_ids.append(nodenetwork_id)

            # check Node Network
            nodenetworks = GetNodeNetworks(self.auth, [nodenetwork_id])
            if nodenetworks is None: continue
            nodenetwork = nodenetworks[0]
            self.isequal(nodenetwork, nodenetwork_fields, 'AddNodeNetwork - isequal')
        
            # Update NodeNetwork
            nodenetwork_fields = random_nodenetwork()
            UpdateNodeNetwork(self.auth, nodenetwork_id, nodenetwork_fields)

            # Check again
            nodenetworks = GetNodeNetworks(self.auth, [nodenetwork_id])
            if nodenetworks is None: continue
            nodenetwork = nodenetworks[0]
            self.isequal(nodenetwork,  nodenetwork_fields, 'UpdateNodeNetwork - isequal')

        nodenetworks = GetNodeNetworks(self.auth, nodenetwork_ids)
        if nodenetworks is not None:
            self.islistequal(nodenetwork_ids, [n['nodenetwork_id'] for n in nodenetworks], 'GetNodeNetworks - isequal')

        if self.config.verbose:
            utils.header('Added nodenetworks: %s' % nodenetwork_ids)

        return nodenetwork_ids

    def DeleteNodeNetworks(self):
	GetNodeNetworks = self.debug(self.api.GetNodeNetworks)
        DeleteNodeNetwork = self.debug(self.api.DeleteNodeNetwork)

        for nodenetwork_id in self.nodenetwork_ids:
            DeleteNodeNetwork(self.auth, nodenetwork_id)

        # check 
        nodenetworks = GetNodeNetworks(self.auth, self.nodenetwork_ids)
        self.islistequal(nodenetworks, [], 'DeleteNodeNetwork - check')

        if self.config.verbose:
            utils.header("Deleted nodenetworks: %s " % self.nodenetwork_ids)
        self.nodenetwork_ids = []			
	
    def NodeNetworkSettings(self, n=2):
	nodenetwork_setting_ids = []
        AddNodeNetworkSetting = self.debug(self.api.AddNodeNetworkSetting)
        UpdateNodeNetworkSetting = self.debug(self.api.UpdateNodeNetworkSetting)
        GetNodeNetworkSettings = self.debug(self.api.GetNodeNetworkSettings)

        for nodenetwork_id in self.nodenetwork_ids:
            # Add Node Network          
            nodenetwork_setting_fields = random_nodenetwork_setting()
            #nodenetwork_id = random.sample(self.nodenetwork_ids, 1)[0]
	    nodenetwork_setting_type_id = random.sample(self.nodenetwork_setting_type_ids, 1)[0]
	    value = nodenetwork_setting_fields['value']
            nodenetwork_setting_id = AddNodeNetworkSetting(self.auth, nodenetwork_id, nodenetwork_setting_type_id, value)
            if nodenetwork_setting_id is None: continue

            # Should return a unique id
            self.isunique(nodenetwork_setting_ids, nodenetwork_setting_ids, 'AddNodeNetworkSetting - isunique')
            nodenetwork_setting_ids.append(nodenetwork_setting_id)

            # check Node Network
            nodenetwork_settings = GetNodeNetworkSettings(self.auth, [nodenetwork_setting_id])
            if nodenetwork_settings is None: continue
            nodenetwork_setting = nodenetwork_settings[0]
            self.isequal(nodenetwork_setting, nodenetwork_setting_fields, 'AddNodeNetworkSetting - isequal')

            # Update NodeNetworkSetting
            nodenetwork_setting_fields = random_nodenetwork_setting()
	    value = nodenetwork_setting_fields['value'] 
            UpdateNodeNetworkSetting(self.auth, nodenetwork_setting_id, value)

            # Check again
            nodenetwork_settings = GetNodeNetworkSettings(self.auth, [nodenetwork_setting_id])
            if nodenetwork_settings is None: continue
            nodenetwork_setting = nodenetwork_settings[0]
            self.isequal(nodenetwork_setting,  nodenetwork_setting_fields, 'UpdateNodeNetworkSetting - isequal')

        nodenetwork_settings = GetNodeNetworkSettings(self.auth, nodenetwork_setting_ids)
        if nodenetwork_settings is not None:
            self.islistequal(nodenetwork_setting_ids, [n['nodenetwork_setting_id'] for n in nodenetwork_settings], 'GetNodeNetworkSettings - isequal')

        if self.config.verbose:
            utils.header('Added nodenetwork_settings: %s' % nodenetwork_setting_ids)

        return nodenetwork_setting_ids

    def DeleteNodeNetworkSettings(self):
	GetNodeNetworkSettings = self.debug(self.api.GetNodeNetworkSettings)
        DeleteNodeNetworkSetting = self.debug(self.api.DeleteNodeNetworkSetting)

        for nodenetwork_setting_id in self.nodenetwork_setting_ids:
            DeleteNodeNetworkSetting(self.auth, nodenetwork_setting_id)

        # check 
        nodenetwork_settings = GetNodeNetworkSettings(self.auth, self.nodenetwork_setting_ids)
        self.islistequal(nodenetwork_settings, [], 'DeleteNodeNetworkSetting - check')

        if self.config.verbose:
            utils.header("Deleted nodenetwork settings: %s " % self.nodenetwork_setting_ids)
        self.nodenetwork_setting_ids = []	
	
    def NodeNetworkSettingTypes(self, n = 2):
	nodenetwork_setting_type_ids = []
	AddNodeNetworkSettingType = self.debug(self.api.AddNodeNetworkSettingType)
        UpdateNodeNetworkSettingType = self.debug(self.api.UpdateNodeNetworkSettingType)
        GetNodeNetworkSettingTypes = self.debug(self.api.GetNodeNetworkSettingTypes)

        for i in range(n):
            # Add Node Network Settings Type         
            nodenetwork_setting_type_fields = random_nodenetwork_setting_type()
            nodenetwork_setting_type_id = AddNodeNetworkSettingType(self.auth, nodenetwork_setting_type_fields)
            if nodenetwork_setting_type_id is None: continue

            # Should return a unique id
            self.isunique(nodenetwork_setting_type_ids, nodenetwork_setting_type_ids, 'AddNodeNetworkSettingType - isunique')
            nodenetwork_setting_type_ids.append(nodenetwork_setting_type_id)

            # check Node Network Settings Type
            nodenetwork_setting_types = GetNodeNetworkSettingTypes(self.auth, [nodenetwork_setting_type_id])
            if nodenetwork_setting_types is None: continue
            nodenetwork_setting_type = nodenetwork_setting_types[0]
            self.isequal(nodenetwork_setting_type, nodenetwork_setting_type_fields, 'AddNodeNetworkSettingType - isequal')

            # Update NodeNetworkSetting
            nodenetwork_setting_type_fields = random_nodenetwork_setting_type()
            UpdateNodeNetworkSettingType(self.auth, nodenetwork_setting_type_id, nodenetwork_setting_type_fields)

            # Check again
            nodenetwork_setting_types = GetNodeNetworkSettingTypes(self.auth, [nodenetwork_setting_type_id])
            if nodenetwork_setting_types is None: continue
            nodenetwork_setting_type = nodenetwork_setting_types[0]
            self.isequal(nodenetwork_setting_type,  nodenetwork_setting_type_fields, 'UpdateNodeNetworkSettingType - isequal')

        nodenetwork_setting_types = GetNodeNetworkSettingTypes(self.auth, nodenetwork_setting_type_ids)
        if nodenetwork_setting_types is not None:
            self.islistequal(nodenetwork_setting_type_ids, [n['nodenetwork_setting_type_id'] for n in nodenetwork_setting_types], 'GetNodeNetworkSettingTypes - isequal')

        if self.config.verbose:
            utils.header('Added nodenetwork_setting_types: %s' % nodenetwork_setting_type_ids)

        return nodenetwork_setting_type_ids

    def DeleteNodeNetworkSettingTypes(self):
	GetNodeNetworkSettingTypes = self.debug(self.api.GetNodeNetworkSettingTypes)
        DeleteNodeNetworkSettingType = self.debug(self.api.DeleteNodeNetworkSettingType)

        for nodenetwork_setting_type_id in self.nodenetwork_setting_type_ids:
            DeleteNodeNetworkSettingType(self.auth, nodenetwork_setting_type_id)

        # check 
        nodenetwork_setting_types = GetNodeNetworkSettingTypes(self.auth, self.nodenetwork_setting_type_ids)
        self.islistequal(nodenetwork_setting_types, [], 'DeleteNodeNetworkSettingType - check')

        if self.config.verbose:
            utils.header("Deleted nodenetwork setting types: %s " % self.nodenetwork_setting_type_ids)
        self.nodenetwork_setting_type_ids = []	

    def Messages(self, n = 2):
	message_ids = []
        AddMessage = self.debug(self.api.AddMessage)
        GetMessages = self.debug(self.api.GetMessages)
        UpdateMessage = self.debug(self.api.UpdateMessage)
        for i in range(n):
            # Add Message
            message_fields = random_message()
            message_id = message_fields['message_id']
	    AddMessage(self.auth, message_fields)
            if message_id is None: continue

            # Should return a unique id
            self.isunique(message_id, message_ids, 'AddMessage - isunique')
            message_ids.append(message_id)
            messages = GetMessages(self.auth, [message_id])
            if messages is None: continue
            message = messages[0]
            self.isequal(message, message_fields, 'AddMessage - isequal')

            # Update message
            message_fields = random_message()
            result = UpdateMessage(self.auth, message_id, message_fields)

            # Check again
            messages = GetMessages(self.auth, [message_id])
            if messages is None: continue
            message = messages[0]
            self.isequal(message, message_fields, 'UpdateMessage - isequal')

        messages = GetMessages(self.auth, message_ids)
        if messages is not None:
            self.islistequal(message_ids, [m['message_id'] for m in messages], 'GetMessages - isequal')

        if self.config.verbose:
            utils.header("Added messages: %s" % message_ids)

        return message_ids

    def DeleteMessages(self):
	# Delete all messages
        DeleteMessage = self.debug(self.api.DeleteMessage)
        GetMessages = self.debug(self.api.GetMessages)
        for message_id in self.message_ids:
            result = DeleteMessage(self.auth, message_id)

        # Check if messages are deleted
        messages = GetMessages(self.auth, self.message_ids)
        self.islistequal(messages, [], 'DeleteMessage - check')

        if self.config.verbose:
            utils.header("Deleted messages: %s" % self.message_ids)

        self.message_ids = []

    def Sessions(self, n = 2):
	session_ids = []
        AddSession = self.debug(self.api.AddSession)
        GetSession = self.debug(self.api.GetSession)
	GetSessions = self.debug(self.api.GetSessions)
        for i in range(n):
            # Add session
            person_id = random.sample(self.person_ids, 1)[0]
            session_id = AddSession(self.auth, person_id)
            if session_id is None: continue
            session_ids.append(session_id)
 	
            # Check session 
            sessions = GetSessions(self.auth, [person_id])
            if not sessions: continue
            session = sessions[0]
	    sess_id = session['session_id']
            self.islistequal([sess_id], [session_id], 'AddSession - isequal')

	    # GetSession creates session_id based on auth, so we must use the current auth
	    session_id = GetSession(self.auth)
	    if session_id is None: continue
	    session_ids.append(session_id)
	    
	    # Check session
	    sessions = GetSessions(self.auth, [self.auth['Username']])
	    if not sessions: continue
	    session = sessions[0]
	    sess_id = session['session_id']
	    self.islistequal([sess_id], [session_id], 'GetSession - isequal') 	  
                
        # Check all
        sessions = GetSessions(self.auth, session_ids)
        if sessions is not None:
	    sess_ids = [s['session_id'] for s in sessions]	
            self.islistequal(sess_ids, session_ids, 'GetSessions - isequal')

        if self.config.verbose:
            utils.header("Added sessions: %s" % session_ids)

        return session_ids		

    def DeleteSessions(self):
	DeleteSession = self.debug(self.api.DeleteSession)
        GetSessions = self.debug(self.api.GetSessions)

	# DeleteSession deletes based on auth, so we must create auths for the sessions we delete
        for session_id  in self.session_ids:
	    sessions = GetSessions(self.auth, [session_id])
	    if not sessions: continue
	    session = sessions[0]
	    tmpauth = { 
		'session': session['session_id'],
		'AuthMethod': 'session'
	   	}
	   
            DeleteSession(tmpauth)

        # Check if sessions are deleted
        sessions = GetSessions(self.auth, self.session_ids)
        self.islistequal(sessions, [], 'DeleteBootState check')

        if self.config.verbose:
            utils.header("Deleted sessions: %s" % self.session_ids)

        self.session_ids = []	

    def GenerateNodeConfFile(self):
	GetNodes = self.debug(self.api.GetNodes)
	GetNodeNetworks = self.debug(self.api.GetNodeNetworks)
	GenerateNodeConfFile = self.debug(self.api.GenerateNodeConfFile)
 
	nodes = GetNodes(self.auth, self.node_ids)
	nodes = filter(lambda n: n['nodenetwork_ids'], nodes)
	if not nodes: return 0
	node = nodes[0]
 	nodenetworks = GetNodeNetworks(self.auth, node['nodenetwork_ids'])
	nodenetwork = nodenetworks[0]
	parts = node['hostname'].split(".", 1)
	host = parts[0]
	domain = parts[1]
	node_config = {
		'NODE_ID': node['node_id'],
		'NODE_KEY': node['key'],
		'IP_METHOD': nodenetwork['method'],
	 	'IP_ADDRESS': nodenetwork['ip'],
		'IP_GATEWAY': nodenetwork['gateway'],
		'IP_NETMASK': nodenetwork['netmask'],
		'IP_NETADDR': nodenetwork['network'],
		'IP_BROADCASTADDR': nodenetwork['broadcast'],
		'IP_DNS1': nodenetwork['dns1'],
		'IP_DNS2': nodenetwork['dns2'],
		'HOSTNAME': host,
		'DOMAIN_NAME': domain
		}
	node_config_file = GenerateNodeConfFile(self.auth, node['node_id'])
	self.isequal(node_config_file, node_config, 'GenerateNodeConfFile - isequal') 
	
	if self.config.verbose:
	    utils.header("GenerateNodeConfFile") 	 

    def GetBootMedium(self):
	pass


    def GetEventObjects(self):
	GetEventObjects = self.debug(self.api.GetEventObjects)
	GetEventObjects(self.auth)
	
	if self.config.verbose:
	    utils.header("GetEventObjects")

    def GetEvents(self):
	GetEvents = self.debug(self.api.GetEvents)
	GetEvents(self.auth)
	
	if self.config.verbose:
	    utils.header("GetEvents")

    def GetPeerData(self):
	GetPeers = self.debug(self.api.GetPeers)
	GetPeerData = self.debug(self.api.GetPeerData)
	
	peers = GetPeers(self.auth)
	if peers is None or not peers: return 0
	peer = peers[0]
	peer_data = GetPeerData(self.auth)

	# Manuall construt peer data

	if self.config.verbose:
	    utils.header("GetPeerData")

    def GetPeerName(self):
	# GetPeerName should return the same as api.config.PLC_NAME 
	GetPeerName = self.debug(self.api.GetPeerName)	  	
 	peer_name = GetPeerName(self.auth)
	self.islistequal([peer_name], [self.api.config.PLC_NAME], 'GetPeerName - isequal')
	
	if self.config.verbose:
	    utils.header("GetPeerName") 
 
    def GetPlcRelease(self):
	GetPlcRelease = self.debug(self.api.GetPlcRelease)
	plc_release = GetPlcRelease(self.auth)

	if self.config.verbose:
	    utils.header("GetPlcRelease")

    def GetSliceKeys(self):
	GetSliceKeys = self.debug(self.api.GetSliceKeys)
	GetSlices = self.debug(self.api.GetSlices)

	slices = GetSlices(self.auth, self.slice_ids)
	if not slices: return 0
	slices = filter(lambda s: s['person_ids'], slices)
	if not slices: return 0
	slice = slices[0]
	
	slice_keys = GetSliceKeys(self.auth, [slice['slice_id']])
	# XX Manually construct slice_keys for this slice and compare
	
	if self.config.verbose:
	    utils.header("GetSliceKeys(%s)" % [slice['slice_id']])

    def GetSliceTicket(self):
	GetSliceTicket = self.debug(self.api.GetSliceTicket)

	slice_id = random.sample(self.slice_ids, 1)[0] 
	slice_ticket = GetSliceTicket(self.auth, slice_id)

	if self.config.verbose:
	    utils.header("GetSliceTicket(%s)" % slice_id)

    def GetSlicesMD5(self):
	GetSlicesMD5 = self.debug(self.api.GetSlicesMD5)

	slices_md5 = GetSlicesMD5(self.auth)

	if self.config.verbose:
	    utils.header("GetSlicesMD5")

    def GetSlivers(self):
	GetSlivers = self.debug(self.api.GetSlivers)
	GetNodes = self.debug(self.api.GetNodes)
	nodes = GetNodes(self.auth, self.node_ids)
	if nodes is None or not nodes: return 0
	nodes = filter(lambda n: n['slice_ids'], nodes)
	if not nodes: return 0
	node = nodes[0]

	slivers = GetSlivers(self.auth, node['node_id'])
	
	# XX manually create slivers object and compare

	if self.config.verbose:
	    utils.header("GetSlivers(%s)" % node['node_id'])

    def GetWhitelist(self):
	GetWhitelist = self.debug(self.api.GetWhitelist)
	GetNodes = self.debug(self.api.GetNodes)

	whitelists = GetWhitelist(self.auth, self.node_ids)
	nodes = GetNodes(self.auth, self.node_ids)
	if nodes is None or not nodes: return 0
	nodes = filter(lambda n: n['slice_ids_whitelist'], nodes)
 	self.islistequal(whitelists, nodes, 'GetWhitelist - isequal')

	if self.config.verbose:
	    utils.header("GetWhitelist")

    def NotifyPersons(self):
	NotifyPersons = self.debug(self.api.NotifyPersons)
	person_id = random.sample(self.person_ids, 1)[0]

	NotifyPersons(self.auth, [person_id], 'QA Test', 'Welcome')

	if self.config.verbose:
	    utils.header('NotifyPersons(%s)' % [person_id])		
	 
    def NotifySupport(self):
	NotifySupport = self.debug(self.api.NotifySupport)
	NotifySupport(self.auth, 'QA Test', 'Support Request')
	
	if self.config.verbose:
	    utils.header('NotifSupport')

    def RebootNode(self):
	RebootNode = self.debug(self.api.RebootNode)
	node_id = random.sample(self.node_ids, 1)[0]
	RebootNode(self.auth, node_id)
	
	if self.config.verbose:
	    utils.header('RebootNode(%s)' % node_id)

    def ResetPassword(self):
	ResetPassword = self.debug(self.api.ResetPassword)
	person_id = random.sample(self.person_ids, 1)[0]
	ResetPassword(self.auth, person_id)

	if self.config.verbose:
	    utils.header('ResetPassword(%s)' % person_id)

    def SetPersonPrimarySite(self):
	SetPersonPrimarySite = self.debug(self.api.SetPersonPrimarySite)
	GetPersons = self.debug(self.api.GetPersons)
	person_id = random.sample(self.person_ids, 1)[0]
	persons = GetPersons(self.auth, person_id)
	if not persons: return 0
	person = persons[0] 
	site_id = random.sample(person['site_ids'], 1)[0]
	SetPersonPrimarySite(self.auth, person_id, site_id)

	if self.config.verbose:
	    utils.header('SetPersonPrimarySite(%s, %s)' % (person_id, site_id))

    def VerifyPerson(self):
	VerifyPerson = self.debug(self.api.VerifyPerson)
	UpdatePerson = self.debug(self.api.UpdatePerson)
	GetPersons = self.debug(self.api.GetPersons)

	# can only verify new (disabled) accounts 
	person_id = random.sample(self.person_ids, 1)[0]
	persons = GetPersons(self.auth, [person_id])
	if persons is None or not persons: return 0
	person = persons[0]
	UpdatePerson(self.auth, person['person_id'], {'enabled': False})
	VerifyPerson(self.auth, person['person_id'])

	if self.config.verbose:
	    utils.header('VerifyPerson(%s)' % person_id) 		
	    	 
if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    api_unit_test()(*args)
