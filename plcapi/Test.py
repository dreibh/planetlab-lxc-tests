#!/usr/bin/python
#
# Test script utility class
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id$
#

from pprint import pprint
from string import letters, digits, punctuation
from traceback import print_exc
from optparse import OptionParser
import socket
import base64
import struct
import os
import xmlrpclib

from PLC.Shell import Shell

from random import Random
random = Random()

def randfloat(min = 0.0, max = 1.0):
    return float(min) + (random.random() * (float(max) - float(min)))

def randint(min = 0, max = 1):
    return int(randfloat(min, max + 1))

# See "2.2 Characters" in the XML specification:
#
# #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD]
# avoiding
# [#x7F-#x84], [#x86-#x9F], [#xFDD0-#xFDDF]
#

ascii_xml_chars = map(unichr, [0x9, 0xA])
# xmlrpclib uses xml.parsers.expat, which always converts either '\r'
# (#xD) or '\n' (#xA) to '\n'. So avoid using '\r', too, if this is
# still the case.
if xmlrpclib.loads(xmlrpclib.dumps(('\r',)))[0][0] == '\r':
    ascii_xml_chars.append('\r')
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
    return u'/'.join(parts)[0:length]

def randemail():
    return (randstr(100, letters + digits) + "@" + randhostname()).lower()

def randkey(bits = 2048):
    ssh_key_types = ["ssh-dss", "ssh-rsa"]
    key_type = random.sample(ssh_key_types, 1)[0]
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

def random_key(key_types):
    return {
        'key_type': random.sample(key_types, 1)[0],
        'key': randkey()
        }

def random_nodegroup():
    return {
        'groupname': randstr(50),
#        'description': randstr(200),
        }

def random_node(boot_states):
    return {
        'hostname': randhostname(),
        'boot_state': random.sample(boot_states, 1)[0],
        'model': randstr(255),
        'version': randstr(64),
        }

def random_interface(method, type):
    interface_fields = {
        'method': method,
        'type': type,
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
            interface_fields[field] = socket.inet_ntoa(struct.pack('>L', locals()[field]))

    return interface_fields

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

def random_attribute_type(role_ids):
    return {
        'name': randstr(100),
        'description': randstr(254),
        'min_role_id': random.sample(role_ids, 1)[0],
        }

def random_slice(login_base):
    return {
        'name': login_base + "_" + randstr(11, letters).lower(),
        'url': "http://" + randhostname() + "/",
        'description': randstr(2048),
        }

class Test:
    tiny = {
        'sites': 1,
        'address_types': 1,
        'addresses_per_site': 1,
        'persons_per_site': 1,
        'keys_per_person': 1,
        'nodegroups': 1,
        'nodes_per_site': 1,
        'interfaces_per_node': 1,
        'pcus_per_site': 1,
        'conf_files': 1,
        'attribute_types': 1,
        'slices_per_site': 1,
        'attributes_per_slice': 1,
        }

    default = {
        'sites': 10,
        'address_types': 2,
        'addresses_per_site': 2,
        'persons_per_site': 10,
        'keys_per_person': 2,
        'nodegroups': 10,
        'nodes_per_site': 2,
        'interfaces_per_node': 1,
        'pcus_per_site': 1,
        'conf_files': 10,
        'attribute_types': 10,
        'slices_per_site': 10,
        'attributes_per_slice': 2,
        }

    def __init__(self, api, check = True, verbose = True):
        self.api = api
        self.check = check
        self.verbose = verbose
        
        self.site_ids = []
        self.address_type_ids = []
        self.address_ids = []
        self.person_ids = []
        self.key_ids = []
        self.nodegroup_ids = []
        self.node_ids = []
        self.interface_ids = []
        self.pcu_ids = []
        self.conf_file_ids = []
        self.attribute_type_ids = []
        self.slice_ids = []
        self.slice_attribute_ids = []

    def Run(self, **kwds):
        """
        Run a complete database and API consistency test. Populates
        the database with a set of random entities, updates them, then
        deletes them. Examples:

        test.Run() # Defaults
        test.Run(**Test.default) # Defaults
        test.Run(**Test.tiny) # Tiny set
        test.Run(sites = 123, slices_per_site = 4) # Defaults with overrides
        """

        try:
            self.Add(**kwds)
            self.Update()
        finally:
            self.Delete()

    def Add(self, **kwds):
        """
        Populate the database with a set of random entities. Examples:

        test.populate() # Defaults
        test.populate(Test.tiny) # Tiny set
        test.populate(sites = 123, slices_per_site = 4) # Defaults with overrides
        """

        params = self.default.copy()
        params.update(kwds)

        self.AddSites(params['sites'])
        self.AddAddressTypes(params['address_types'])
        self.AddAddresses(params['addresses_per_site'])
        self.AddPersons(params['persons_per_site'])
        self.AddKeys(params['keys_per_person'])
        self.AddNodeGroups(params['nodegroups'])
        self.AddNodes(params['nodes_per_site'])
        self.AddInterfaces(params['interfaces_per_node'])
        self.AddPCUs(params['pcus_per_site'])
        self.AddConfFiles(params['conf_files'])
        self.AddSliceAttributeTypes(params['attribute_types'])
        self.AddSlices(params['slices_per_site'])
        self.AddSliceAttributes(params['attributes_per_slice'])

    def Update(self):
        self.UpdateSites()
        self.UpdateAddressTypes()
        self.UpdateAddresses()
        self.UpdatePersons()
        self.UpdateKeys()
        self.UpdateNodeGroups()
        self.UpdateNodes()
        self.UpdateInterfaces()
        self.UpdatePCUs()
        self.UpdateConfFiles()
        self.UpdateSliceAttributeTypes()
        self.UpdateSlices()
        self.UpdateSliceAttributes()

    def Delete(self):
        self.DeleteSliceAttributes()
        self.DeleteSlices()
        self.DeleteSliceAttributeTypes()
        self.DeleteKeys()
        self.DeleteConfFiles()
        self.DeletePCUs()
        self.DeleteInterfaces()
        self.DeleteNodes()
        self.DeletePersons()
        self.DeleteNodeGroups()
        self.DeleteAddresses()
        self.DeleteAddressTypes()
        self.DeleteSites()

    def AddSites(self, n = 10):
        """
        Add a number of random sites.
        """

        for i in range(n):
            # Add site
            site_fields = random_site()
            site_id = self.api.AddSite(site_fields)

            # Should return a unique site_id
            assert site_id not in self.site_ids
            self.site_ids.append(site_id)

            # Enable slice creation
            site_fields['max_slices'] = randint(1, 10)
            self.api.UpdateSite(site_id, site_fields)

            if self.check:
                # Check site
                site = self.api.GetSites([site_id])[0]
                for field in site_fields:
                    assert site[field] == site_fields[field]

            if self.verbose:
                print "Added site", site_id

    def UpdateSites(self):
        """
        Make random changes to any sites we may have added.
        """

        for site_id in self.site_ids:
            # Update site
            site_fields = random_site()
            # Do not change login_base
	    if 'login_base' in site_fields:
		del site_fields['login_base']
            self.api.UpdateSite(site_id, site_fields)

            if self.check:
                # Check site
                site = self.api.GetSites([site_id])[0]
                for field in site_fields:
                    assert site[field] == site_fields[field]

            if self.verbose:
                print "Updated site", site_id

    def DeleteSites(self):
        """
        Delete any random sites we may have added.
        """

        for site_id in self.site_ids:
            self.api.DeleteSite(site_id)

            if self.check:
                assert not self.api.GetSites([site_id])

            if self.verbose:
                print "Deleted site", site_id

        if self.check:
            assert not self.api.GetSites(self.site_ids)

        self.site_ids = []

    def AddAddressTypes(self, n = 2):
        """
        Add a number of random address types.
        """

        for i in range(n):
            address_type_fields = random_address_type()
            address_type_id = self.api.AddAddressType(address_type_fields)

            # Should return a unique address_type_id
            assert address_type_id not in self.address_type_ids
            self.address_type_ids.append(address_type_id)

            if self.check:
                # Check address type
                address_type = self.api.GetAddressTypes([address_type_id])[0]
                for field in address_type_fields:
                    assert address_type[field] == address_type_fields[field]

            if self.verbose:
                print "Added address type", address_type_id

    def UpdateAddressTypes(self):
        """
        Make random changes to any address types we may have added.
        """

        for address_type_id in self.address_type_ids:
            # Update address_type
            address_type_fields = random_address_type()
            self.api.UpdateAddressType(address_type_id, address_type_fields)

            if self.check:
                # Check address type
                address_type = self.api.GetAddressTypes([address_type_id])[0]
                for field in address_type_fields:
                    assert address_type[field] == address_type_fields[field]

            if self.verbose:
                print "Updated address_type", address_type_id

    def DeleteAddressTypes(self):
        """
        Delete any random address types we may have added.
        """

        for address_type_id in self.address_type_ids:
            self.api.DeleteAddressType(address_type_id)

            if self.check:
                assert not self.api.GetAddressTypes([address_type_id])

            if self.verbose:
                print "Deleted address type", address_type_id

        if self.check:
            assert not self.api.GetAddressTypes(self.address_type_ids)

        self.address_type_ids = []

    def AddAddresses(self, per_site = 2):
        """
        Add a number of random addresses to each site.
        """

        for site_id in self.site_ids:
            for i in range(per_site):
                address_fields = random_address()
                address_id = self.api.AddSiteAddress(site_id, address_fields)

                # Should return a unique address_id
                assert address_id not in self.address_ids
                self.address_ids.append(address_id)

                # Add random address type
                if self.address_type_ids:
                    for address_type_id in random.sample(self.address_type_ids, 1):
                        self.api.AddAddressTypeToAddress(address_type_id, address_id)

                if self.check:
                    # Check address
                    address = self.api.GetAddresses([address_id])[0]
                    for field in address_fields:
                        assert address[field] == address_fields[field]

                if self.verbose:
                    print "Added address", address_id, "to site", site_id

    def UpdateAddresses(self):
        """
        Make random changes to any addresses we may have added.
        """

        for address_id in self.address_ids:
            # Update address
            address_fields = random_address()
            self.api.UpdateAddress(address_id, address_fields)

            if self.check:
                # Check address
                address = self.api.GetAddresses([address_id])[0]
                for field in address_fields:
                    assert address[field] == address_fields[field]

            if self.verbose:
                print "Updated address", address_id

    def DeleteAddresses(self):
        """
        Delete any random addresses we may have added.
        """

        for address_id in self.address_ids:
            # Remove address types
            address = self.api.GetAddresses([address_id])[0]
            for address_type_id in address['address_type_ids']:
                self.api.DeleteAddressTypeFromAddress(address_type_id, address_id)

            if self.check:
                address = self.api.GetAddresses([address_id])[0]
                assert not address['address_type_ids']

            self.api.DeleteAddress(address_id)

            if self.check:
                assert not self.api.GetAddresses([address_id])

            if self.verbose:
                print "Deleted address", address_id

        if self.check:
            assert not self.api.GetAddresses(self.address_ids)

        self.address_ids = []

    def AddPersons(self, per_site = 10):
        """
        Add a number of random users to each site.
        """

        for site_id in self.site_ids:
            for i in range(per_site):
                # Add user
                person_fields = random_person()
                person_id = self.api.AddPerson(person_fields)

                # Should return a unique person_id
                assert person_id not in self.person_ids
                self.person_ids.append(person_id)

                if self.check:
                    # Check user
                    person = self.api.GetPersons([person_id])[0]
                    for field in person_fields:
                        if field != 'password':
                            assert person[field] == person_fields[field]

                auth = {'AuthMethod': "password",
                        'Username': person_fields['email'],
                        'AuthString': person_fields['password']}

                if self.check:
                    # Check that user is disabled
                    try:
                        assert not self.api.AuthCheck(auth)
                    except:
                        pass

                # Add random set of roles
                role_ids = random.sample([20, 30, 40], randint(1, 3))
                for role_id in role_ids:
                    self.api.AddRoleToPerson(role_id, person_id)

                if self.check:
                    person = self.api.GetPersons([person_id])[0]
                    assert set(role_ids) == set(person['role_ids'])

                # Enable user
                self.api.UpdatePerson(person_id, {'enabled': True})

                if self.check:
                    # Check that user is enabled
                    assert self.api.AuthCheck(auth)

                # Associate user with site
                self.api.AddPersonToSite(person_id, site_id)
                self.api.SetPersonPrimarySite(person_id, site_id)

                if self.check:
                    person = self.api.GetPersons([person_id])[0]
                    assert person['site_ids'][0] == site_id

                if self.verbose:
                    print "Added user", person_id, "to site", site_id

    def UpdatePersons(self):
        """
        Make random changes to any users we may have added.
        """

        for person_id in self.person_ids:
            # Update user
            person_fields = random_person()
            # Keep them enabled
            person_fields['enabled'] = True
            self.api.UpdatePerson(person_id, person_fields)

            if self.check:
                # Check user
                person = self.api.GetPersons([person_id])[0]
                for field in person_fields:
                    if field != 'password':
                        assert person[field] == person_fields[field]

            if self.verbose:
                print "Updated person", person_id

            person = self.api.GetPersons([person_id])[0]

            # Associate user with a random set of sites
            site_ids = random.sample(self.site_ids, randint(0, len(self.site_ids)))
            for site_id in (set(site_ids) - set(person['site_ids'])):
                self.api.AddPersonToSite(person_id, site_id)
            for site_id in (set(person['site_ids']) - set(site_ids)):
                self.api.DeletePersonFromSite(person_id, site_id)

            if site_ids:
                self.api.SetPersonPrimarySite(person_id, site_ids[0])

            if self.check:
                person = self.api.GetPersons([person_id])[0]
                assert set(site_ids) == set(person['site_ids'])

            if self.verbose:
                print "Updated person", person_id, "to sites", site_ids

    def DeletePersons(self):
        """
        Delete any random users we may have added.
        """

        for person_id in self.person_ids:
            # Remove from site
            person = self.api.GetPersons([person_id])[0]
            for site_id in person['site_ids']:
                self.api.DeletePersonFromSite(person_id, site_id)

            if self.check:
                person = self.api.GetPersons([person_id])[0]
                assert not person['site_ids']

            # Revoke roles
            for role_id in person['role_ids']:
                self.api.DeleteRoleFromPerson(role_id, person_id)

            if self.check:
                person = self.api.GetPersons([person_id])[0]
                assert not person['role_ids']

            # Disable account
            self.api.UpdatePerson(person_id, {'enabled': False})

            if self.check:
                person = self.api.GetPersons([person_id])[0]
                assert not person['enabled']

            # Delete account
            self.api.DeletePerson(person_id)

            if self.check:
                assert not self.api.GetPersons([person_id])                         

            if self.verbose:
                print "Deleted user", person_id

        if self.check:
            assert not self.api.GetPersons(self.person_ids)

        self.person_ids = []

    def AddKeys(self, per_person = 2):
        """
        Add a number of random keys to each user.
        """

        key_types = self.api.GetKeyTypes()
        if not key_types:
            raise Exception, "No key types"

        for person_id in self.person_ids:
            for i in range(per_person):
                # Add key
                key_fields = random_key(key_types)
                key_id = self.api.AddPersonKey(person_id, key_fields)

                # Should return a unique key_id
                assert key_id not in self.key_ids
                self.key_ids.append(key_id)

                if self.check:
                    # Check key
                    key = self.api.GetKeys([key_id])[0]
                    for field in key_fields:
                        assert key[field] == key_fields[field]

                    # Add and immediately blacklist a key
                    key_fields = random_key(key_types)
                    key_id = self.api.AddPersonKey(person_id, key_fields)

                    self.api.BlacklistKey(key_id)

                    # Is effectively deleted
                    assert not self.api.GetKeys([key_id])

                    # Cannot be added again
                    try:
                        key_id = self.api.AddPersonKey(person_id, key_fields)
                        assert False
                    except Exception, e:
                        pass

                if self.verbose:
                    print "Added key", key_id, "to user", person_id

    def UpdateKeys(self):
        """
        Make random changes to any keys we may have added.
        """

        key_types = self.api.GetKeyTypes()
        if not key_types:
            raise Exception, "No key types"

        for key_id in self.key_ids:
            # Update key
            key_fields = random_key(key_types)
            self.api.UpdateKey(key_id, key_fields)

            if self.check:
                # Check key
                key = self.api.GetKeys([key_id])[0]
                for field in key_fields:
                    assert key[field] == key_fields[field]

            if self.verbose:
                print "Updated key", key_id

    def DeleteKeys(self):
        """
        Delete any random keys we may have added.
        """

        for key_id in self.key_ids:
            self.api.DeleteKey(key_id)

            if self.check:
                assert not self.api.GetKeys([key_id])

            if self.verbose:
                print "Deleted key", key_id

        if self.check:
            assert not self.api.GetKeys(self.key_ids)

        self.key_ids = []

    def AddNodeGroups(self, n = 10):
        """
        Add a number of random node groups.
        """

        for i in range(n):
            # Add node group
            nodegroup_fields = random_nodegroup()
            nodegroup_id = self.api.AddNodeGroup(nodegroup_fields)

            # Should return a unique nodegroup_id
            assert nodegroup_id not in self.nodegroup_ids
            self.nodegroup_ids.append(nodegroup_id)

            if self.check:
                # Check node group
                nodegroup = self.api.GetNodeGroups([nodegroup_id])[0]
                for field in nodegroup_fields:
                    assert nodegroup[field] == nodegroup_fields[field]

            if self.verbose:
                print "Added node group", nodegroup_id

    def UpdateNodeGroups(self):
        """
        Make random changes to any node groups we may have added.
        """

        for nodegroup_id in self.nodegroup_ids:
            # Update nodegroup
            nodegroup_fields = random_nodegroup()
            self.api.UpdateNodeGroup(nodegroup_id, nodegroup_fields)

            if self.check:
                # Check nodegroup
                nodegroup = self.api.GetNodeGroups([nodegroup_id])[0]
                for field in nodegroup_fields:
                    assert nodegroup[field] == nodegroup_fields[field]

            if self.verbose:
                print "Updated node group", nodegroup_id

    def DeleteNodeGroups(self):
        """
        Delete any random node groups we may have added.
        """

        for nodegroup_id in self.nodegroup_ids:
            self.api.DeleteNodeGroup(nodegroup_id)

            if self.check:
                assert not self.api.GetNodeGroups([nodegroup_id])

            if self.verbose:
                print "Deleted node group", nodegroup_id

        if self.check:
            assert not self.api.GetNodeGroups(self.nodegroup_ids)

        self.nodegroup_ids = []

    def AddNodes(self, per_site = 2):
        """
        Add a number of random nodes to each site. Each node will also
        be added to a random node group if AddNodeGroups() was
        previously run.
        """
        
        boot_states = self.api.GetBootStates()
        if not boot_states:
            raise Exception, "No boot states"

        for site_id in self.site_ids:
            for i in range(per_site):
                # Add node
                node_fields = random_node(boot_states)
                node_id = self.api.AddNode(site_id, node_fields)

                # Should return a unique node_id
                assert node_id not in self.node_ids
                self.node_ids.append(node_id)

                # Add to a random set of node groups
                nodegroup_ids = random.sample(self.nodegroup_ids, randint(0, len(self.nodegroup_ids)))
                for nodegroup_id in nodegroup_ids:
                    self.api.AddNodeToNodeGroup(node_id, nodegroup_id)

                if self.check:
                    # Check node
                    node = self.api.GetNodes([node_id])[0]
                    for field in node_fields:
                        assert node[field] == node_fields[field]

                if self.verbose:
                    print "Added node", node_id

    def UpdateNodes(self):
        """
        Make random changes to any nodes we may have added.
        """

        boot_states = self.api.GetBootStates()
        if not boot_states:
            raise Exception, "No boot states"

        for node_id in self.node_ids:
            # Update node
            node_fields = random_node(boot_states)
            self.api.UpdateNode(node_id, node_fields)

            node = self.api.GetNodes([node_id])[0]

            # Add to a random set of node groups
            nodegroup_ids = random.sample(self.nodegroup_ids, randint(0, len(self.nodegroup_ids)))
            for nodegroup_id in (set(nodegroup_ids) - set(node['nodegroup_ids'])):
                self.api.AddNodeToNodeGroup(node_id, nodegroup_id)
            for nodegroup_id in (set(node['nodegroup_ids']) - set(nodegroup_ids)):
                self.api.DeleteNodeFromNodeGroup(node_id, nodegroup_id)

            if self.check:
                # Check node
                node = self.api.GetNodes([node_id])[0]
                for field in node_fields:
                    assert node[field] == node_fields[field]
                assert set(nodegroup_ids) == set(node['nodegroup_ids'])

            if self.verbose:
                print "Updated node", node_id
                print "Added node", node_id, "to node groups", nodegroup_ids

    def DeleteNodes(self):
        """
        Delete any random nodes we may have added.
        """

        for node_id in self.node_ids:
            # Remove from node groups
            node = self.api.GetNodes([node_id])[0]
            for nodegroup_id in node['nodegroup_ids']:
                self.api.DeleteNodeFromNodeGroup(node_id, nodegroup_id)

            if self.check:
                node = self.api.GetNodes([node_id])[0]
                assert not node['nodegroup_ids']

            self.api.DeleteNode(node_id)

            if self.check:
                assert not self.api.GetNodes([node_id])

            if self.verbose:
                print "Deleted node", node_id

        if self.check:
            assert not self.api.GetNodes(self.node_ids)

        self.node_ids = []

    def AddInterfaces(self, per_node = 1):
        """
        Add a number of random network interfaces to each node.
        """

        network_methods = self.api.GetNetworkMethods()
        if not network_methods:
            raise Exception, "No network methods"
        
        network_types = self.api.GetNetworkTypes()
        if not network_types:
            raise Exception, "No network types"

        for node_id in self.node_ids:
            for i in range(per_node):
                method = random.sample(network_methods, 1)[0]
                type = random.sample(network_types, 1)[0]

                # Add node network
                interface_fields = random_interface(method, type)
                interface_id = self.api.AddInterface(node_id, interface_fields)

                # Should return a unique interface_id
                assert interface_id not in self.interface_ids
                self.interface_ids.append(interface_id)

                if self.check:
                    # Check node network
                    interface = self.api.GetInterfaces([interface_id])[0]
                    for field in interface_fields:
                        assert interface[field] == interface_fields[field]

                if self.verbose:
                    print "Added node network", interface_id, "to node", node_id

    def UpdateInterfaces(self):
        """
        Make random changes to any network interfaces we may have added.
        """

        network_methods = self.api.GetNetworkMethods()
        if not network_methods:
            raise Exception, "No network methods"
        
        network_types = self.api.GetNetworkTypes()
        if not network_types:
            raise Exception, "No network types"

        for interface_id in self.interface_ids:
            method = random.sample(network_methods, 1)[0]
            type = random.sample(network_types, 1)[0]

            # Update interface
            interface_fields = random_interface(method, type)
            self.api.UpdateInterface(interface_id, interface_fields)

            if self.check:
                # Check interface
                interface = self.api.GetInterfaces([interface_id])[0]
                for field in interface_fields:
                    assert interface[field] == interface_fields[field]

            if self.verbose:
                print "Updated node network", interface_id

    def DeleteInterfaces(self):
        """
        Delete any random network interfaces we may have added.
        """

        for interface_id in self.interface_ids:
            self.api.DeleteInterface(interface_id)

            if self.check:
                assert not self.api.GetInterfaces([interface_id])

            if self.verbose:
                print "Deleted node network", interface_id

        if self.check:
            assert not self.api.GetInterfaces(self.interface_ids)

        self.interface_ids = []

    def AddPCUs(self, per_site = 1):
        """
        Add a number of random PCUs to each site. Each node at the
        site will be added to a port on the PCU if AddNodes() was
        previously run.
        """

        for site_id in self.site_ids:
            for i in range(per_site):
                # Add PCU
                pcu_fields = random_pcu()
                pcu_id = self.api.AddPCU(site_id, pcu_fields)

                # Should return a unique pcu_id
                assert pcu_id not in self.pcu_ids
                self.pcu_ids.append(pcu_id)

                # Add each node at this site to a different port on this PCU
                site = self.api.GetSites([site_id])[0]
                port = randint(1, 10)
                for node_id in site['node_ids']:
                    self.api.AddNodeToPCU(node_id, pcu_id, port)
                    port += 1

                if self.check:
                    # Check PCU
                    pcu = self.api.GetPCUs([pcu_id])[0]
                    for field in pcu_fields:
                        assert pcu[field] == pcu_fields[field]

                if self.verbose:
                    print "Added PCU", pcu_id, "to site", site_id

    def UpdatePCUs(self):
        """
        Make random changes to any PCUs we may have added.
        """

        for pcu_id in self.pcu_ids:
            # Update PCU
            pcu_fields = random_pcu()
            self.api.UpdatePCU(pcu_id, pcu_fields)

            if self.check:
                # Check PCU
                pcu = self.api.GetPCUs([pcu_id])[0]
                for field in pcu_fields:
                    assert pcu[field] == pcu_fields[field]

            if self.verbose:
                print "Updated PCU", pcu_id

    def DeletePCUs(self):
        """
        Delete any random nodes we may have added.
        """

        for pcu_id in self.pcu_ids:
            # Remove nodes from PCU
            pcu = self.api.GetPCUs([pcu_id])[0]
            for node_id in pcu['node_ids']:
                self.api.DeleteNodeFromPCU(node_id, pcu_id)

            if self.check:
                pcu = self.api.GetPCUs([pcu_id])[0]
                assert not pcu['node_ids']

            self.api.DeletePCU(pcu_id)

            if self.check:
                assert not self.api.GetPCUs([pcu_id])

            if self.verbose:
                print "Deleted PCU", pcu_id

        if self.check:
            assert not self.api.GetPCUs(self.pcu_ids)

        self.pcu_ids = []

    def AddConfFiles(self, n = 10):
        """
        Add a number of random global configuration files.
        """

        conf_files = []

        for i in range(n):
            # Add a random configuration file
            conf_files.append(random_conf_file())

        if n:
            # Add a nodegroup override file
            nodegroup_conf_file = conf_files[0].copy()
            nodegroup_conf_file['source'] = randpath(255)
            conf_files.append(nodegroup_conf_file)

            # Add a node override file
            node_conf_file = conf_files[0].copy()
            node_conf_file['source'] = randpath(255)
            conf_files.append(node_conf_file)

        for conf_file_fields in conf_files:
            conf_file_id = self.api.AddConfFile(conf_file_fields)

            # Should return a unique conf_file_id
            assert conf_file_id not in self.conf_file_ids
            self.conf_file_ids.append(conf_file_id)

            # Add to nodegroup
            if conf_file_fields == nodegroup_conf_file and self.nodegroup_ids:
                nodegroup_id = random.sample(self.nodegroup_ids, 1)[0]
                self.api.AddConfFileToNodeGroup(conf_file_id, nodegroup_id)
            else:
                nodegroup_id = None

            # Add to node
            if conf_file_fields == node_conf_file and self.node_ids:
                node_id = random.sample(self.node_ids, 1)[0]
                self.api.AddConfFileToNode(conf_file_id, node_id)
            else:
                node_id = None

            if self.check:
                # Check configuration file
                conf_file = self.api.GetConfFiles([conf_file_id])[0]
                for field in conf_file_fields:
                    assert conf_file[field] == conf_file_fields[field]

            if self.verbose:
                print "Added configuration file", conf_file_id,
                if nodegroup_id is not None:
                    print "to node group", nodegroup_id,
                elif node_id is not None:
                    print "to node", node_id,
                print

    def UpdateConfFiles(self):
        """
        Make random changes to any configuration files we may have added.
        """

        for conf_file_id in self.conf_file_ids:
            # Update configuration file
            conf_file_fields = random_conf_file()
            # Do not update dest so that it remains an override if set
	    if 'dest' in conf_file_fields:
		del conf_file_fields['dest']
            self.api.UpdateConfFile(conf_file_id, conf_file_fields)

            if self.check:
                # Check configuration file
                conf_file = self.api.GetConfFiles([conf_file_id])[0]
                for field in conf_file_fields:
                    assert conf_file[field] == conf_file_fields[field]

            if self.verbose:
                print "Updated configuration file", conf_file_id

    def DeleteConfFiles(self):
        """
        Delete any random configuration files we may have added.
        """

        for conf_file_id in self.conf_file_ids:
            self.api.DeleteConfFile(conf_file_id)

            if self.check:
                assert not self.api.GetConfFiles([conf_file_id])

            if self.verbose:
                print "Deleted configuration file", conf_file_id

        if self.check:
            assert not self.api.GetConfFiles(self.conf_file_ids)

        self.conf_file_ids = []

    def AddSliceAttributeTypes(self, n = 10):
        """
        Add a number of random slice attribute types.
        """

        roles = self.api.GetRoles()
        if not roles:
            raise Exception, "No roles"
        role_ids = [role['role_id'] for role in roles]

        for i in range(n):
            attribute_type_fields = random_attribute_type(role_ids)
            attribute_type_id = self.api.AddSliceAttributeType(attribute_type_fields)

            # Should return a unique attribute_type_id
            assert attribute_type_id not in self.attribute_type_ids
            self.attribute_type_ids.append(attribute_type_id)

            if self.check:
                # Check slice attribute type
                attribute_type = self.api.GetSliceAttributeTypes([attribute_type_id])[0]
                for field in attribute_type_fields:
                    assert attribute_type[field] == attribute_type_fields[field]

            if self.verbose:
                print "Added slice attribute type", attribute_type_id

    def UpdateSliceAttributeTypes(self):
        """
        Make random changes to any slice attribute types we may have added.
        """

        roles = self.api.GetRoles()
        if not roles:
            raise Exception, "No roles"
        role_ids = [role['role_id'] for role in roles]

        for attribute_type_id in self.attribute_type_ids:
            # Update slice attribute type
            attribute_type_fields = random_attribute_type(role_ids)
            self.api.UpdateSliceAttributeType(attribute_type_id, attribute_type_fields)

            if self.check:
                # Check slice attribute type
                attribute_type = self.api.GetSliceAttributeTypes([attribute_type_id])[0]
                for field in attribute_type_fields:
                    assert attribute_type[field] == attribute_type_fields[field]

            if self.verbose:
                print "Updated slice attribute type", attribute_type_id

    def DeleteSliceAttributeTypes(self):
        """
        Delete any random slice attribute types we may have added.
        """

        for attribute_type_id in self.attribute_type_ids:
            self.api.DeleteSliceAttributeType(attribute_type_id)

            if self.check:
                assert not self.api.GetSliceAttributeTypes([attribute_type_id])

            if self.verbose:
                print "Deleted slice attribute type", attribute_type_id

        if self.check:
            assert not self.api.GetSliceAttributeTypes(self.attribute_type_ids)

        self.attribute_type_ids = []

    def AddSlices(self, per_site = 10):
        """
        Add a number of random slices per site.
        """

        for site in self.api.GetSites(self.site_ids):
            for i in range(min(per_site, site['max_slices'])):
                # Add slice
                slice_fields = random_slice(site['login_base'])
                slice_id = self.api.AddSlice(slice_fields)

                # Should return a unique slice_id
                assert slice_id not in self.slice_ids
                self.slice_ids.append(slice_id)

                # Add slice to a random set of nodes
                node_ids = random.sample(self.node_ids, randint(0, len(self.node_ids)))
                if node_ids:
                    self.api.AddSliceToNodes(slice_id, node_ids)

                # Add random set of site users to slice
                person_ids = random.sample(site['person_ids'], randint(0, len(site['person_ids'])))
                for person_id in person_ids:
                    self.api.AddPersonToSlice(person_id, slice_id)

                if self.check:
                    # Check slice
                    slice = self.api.GetSlices([slice_id])[0]
                    for field in slice_fields:
                        assert slice[field] == slice_fields[field]

                    assert set(node_ids) == set(slice['node_ids'])
                    assert set(person_ids) == set(slice['person_ids'])

                if self.verbose:
                    print "Added slice", slice_id, "to site", site['site_id'],
                    if node_ids:
                        print "and nodes", node_ids,
                    print
                    if person_ids:
                        print "Added users", site['person_ids'], "to slice", slice_id

    def UpdateSlices(self):
        """
        Make random changes to any slices we may have added.
        """

        for slice_id in self.slice_ids:
            # Update slice
            slice_fields = random_slice("unused")
            # Cannot change slice name
	    if 'name' in slice_fields:
		del slice_fields['name']
            self.api.UpdateSlice(slice_id, slice_fields)

            slice = self.api.GetSlices([slice_id])[0]

            # Add slice to a random set of nodes
            node_ids = random.sample(self.node_ids, randint(0, len(self.node_ids)))
            self.api.AddSliceToNodes(slice_id, list(set(node_ids) - set(slice['node_ids'])))
            self.api.DeleteSliceFromNodes(slice_id, list(set(slice['node_ids']) - set(node_ids)))

            # Add random set of users to slice
            person_ids = random.sample(self.person_ids, randint(0, len(self.person_ids)))
            for person_id in (set(person_ids) - set(slice['person_ids'])):
                self.api.AddPersonToSlice(person_id, slice_id)
            for person_id in (set(slice['person_ids']) - set(person_ids)):
                self.api.DeletePersonFromSlice(person_id, slice_id)

            if self.check:
                slice = self.api.GetSlices([slice_id])[0]
                for field in slice_fields:
                    assert slice[field] == slice_fields[field]
                assert set(node_ids) == set(slice['node_ids'])
                assert set(person_ids) == set(slice['person_ids'])

            if self.verbose:
                print "Updated slice", slice_id
                print "Added nodes", node_ids, "to slice", slice_id
                print "Added persons", person_ids, "to slice", slice_id

    def DeleteSlices(self):
        """
        Delete any random slices we may have added.
        """

        for slice_id in self.slice_ids:
            self.api.DeleteSlice(slice_id)

            if self.check:
                assert not self.api.GetSlices([slice_id])

            if self.verbose:
                print "Deleted slice", slice_id

        if self.check:
            assert not self.api.GetSlices(self.slice_ids)

        self.slice_ids = []

    def AddSliceAttributes(self, per_slice = 2):
        """
        Add a number of random slices per site.
        """

        if not self.attribute_type_ids:
            return

        for slice_id in self.slice_ids:
            slice = self.api.GetSlices([slice_id])[0]

            for i in range(per_slice):
                # Set a random slice/sliver attribute
                for attribute_type_id in random.sample(self.attribute_type_ids, 1):
                    value = randstr(16, letters + '_' + digits)
                    # Make it a sliver attribute with 50% probability
                    if slice['node_ids']:
                        node_id = random.sample(slice['node_ids'] + [None] * len(slice['node_ids']), 1)[0]
                    else:
                        node_id = None

                    # Add slice attribute
                    if node_id is None:
                        slice_attribute_id = self.api.AddSliceAttribute(slice_id, attribute_type_id, value)
                    else:
                        slice_attribute_id = self.api.AddSliceAttribute(slice_id, attribute_type_id, value, node_id)

                    # Should return a unique slice_attribute_id
                    assert slice_attribute_id not in self.slice_attribute_ids
                    self.slice_attribute_ids.append(slice_attribute_id)

                    if self.check:
                        # Check slice attribute
                        slice_attribute = self.api.GetSliceAttributes([slice_attribute_id])[0]
                        for field in 'attribute_type_id', 'slice_id', 'node_id', 'slice_attribute_id', 'value':
                            assert slice_attribute[field] == locals()[field]

                    if self.verbose:
                        print "Added slice attribute", slice_attribute_id, "of type", attribute_type_id,
                        if node_id is not None:
                            print "to node", node_id,
                        print
                        
    def UpdateSliceAttributes(self):
        """
        Make random changes to any slice attributes we may have added.
        """

        for slice_attribute_id in self.slice_attribute_ids:
            # Update slice attribute
            value = randstr(16, letters + '_' + digits)
            self.api.UpdateSliceAttribute(slice_attribute_id, value)

            # Check slice attribute again
            slice_attribute = self.api.GetSliceAttributes([slice_attribute_id])[0]
            assert slice_attribute['value'] == value

            if self.verbose:
                print "Updated slice attribute", slice_attribute_id

    def DeleteSliceAttributes(self):
        """
        Delete any random slice attributes we may have added.
        """

        for slice_attribute_id in self.slice_attribute_ids:
            self.api.DeleteSliceAttribute(slice_attribute_id)

            if self.check:
                assert not self.api.GetSliceAttributes([slice_attribute_id])

            if self.verbose:
                print "Deleted slice attribute", slice_attribute_id

        if self.check:
            assert not self.api.GetSliceAttributes(self.slice_attribute_ids)

        self.slice_attribute_ids = []

def main():
    parser = OptionParser()
    parser.add_option("-c", "--check", action = "store_true", default = False, help = "Check most actions (default: %default)")
    parser.add_option("-q", "--quiet", action = "store_true", default = False, help = "Be quiet (default: %default)")
    parser.add_option("-t", "--tiny", action = "store_true", default = False, help = "Run a tiny test (default: %default)")
    (options, args) = parser.parse_args()

    test = Test(api = Shell(),
                check = options.check,
                verbose = not options.quiet)

    if options.tiny:
        params = Test.tiny
    else:
        params = Test.default

    test.Run(**params)

if __name__ == "__main__":
    main()
