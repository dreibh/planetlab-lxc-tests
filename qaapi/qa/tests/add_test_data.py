#!/usr/bin/env /usr/share/plc_api/plcsh

import os,sys
from Test import Test
from qa import utils

class add_test_data(Test):
    """
    Adds the test data found in config to the plc db
    """   
    def call(self):

	# Make sure some required fields are in config
	required_fields = ['TEST_SITE_NAME', 'TEST_SITE_LOGIN_BASE', 'TEST_SLICE_NAME', 'TEST_PERSON_EMAIL']
	required_node_fields = ['TEST_NODE_TYPE', 'TEST_NODE_METHOD', 'TEST_NODE_HOSTNAME', 'TEST_NODE_IP',
				'TEST_NODE_GATEWAY', 'TEST_NODE_DNS', 'TEST_NODE_NETWORK', 'TEST_NODE_BROADCAST',
				'TEST_NODE_NETMASK']

	for field in required_fields:
	    if not hasattr(self.config, field) or \
		   len(getattr(self.config, field).strip()) < 1:
		raise Exception, "%(field)s must be set and cannot be blank" % locals()

	# Look for node configurations
	node_params = {}
        for attr in dir(self.config):
            if attr.find("NODE") > 0:
                parts = attr.split('_')
                node_prefix = parts[1] +"_"+ parts[3]
                name = "_".join(parts[:3])
                value = getattr(self.config, attr)
	         # start a new node dictionary
                if node_prefix not in node_params:
                    node_params[node_prefix] = {'prefix': node_prefix}
                node_params[node_prefix][name] = value

	node_configs = node_params.values()
	node_list = []

	# Make sure required node fields are preset for each node config
        for node_config in node_configs:
	    for field in required_node_fields:
	        if field not in node_config or len(node_config[field].strip()) < 1:
	    	    raise Exception, "%s must be set for %s and cannot be blank" % (field, node_config['prefix'])
	    node = {'type': node_config['TEST_NODE_TYPE'],
		    'method': node_config['TEST_NODE_METHOD'],
		    'hostname': node_config['TEST_NODE_HOSTNAME'],
		    'ip':  node_config['TEST_NODE_IP'],
		    'gateway': node_config['TEST_NODE_GATEWAY'],
		    'dns1': node_config['TEST_NODE_DNS'],
		    'broadcast': node_config['TEST_NODE_BROADCAST'], 
		    'network': node_config['TEST_NODE_NETWORK'],
		    'netmask': node_config['TEST_NODE_NETMASK'],
		    'slice_ids': [],
		    'nodenetwork_ids': []}
	    node_list.append(node)
	    
	    
	# Define test objects 
	site_fields = {'name': self.config.TEST_SITE_NAME, 'login_base': self.config.TEST_SITE_LOGIN_BASE, 
		       'url': 'http://google.com', 'enabled': True, 'max_slices': 1000, 
   		       'max_slivers': 1000, 'is_public': True, 'abbreviated_name': 'Test', 
		       'person_ids': []}

	slice_fields = {'name': self.config.TEST_SLICE_NAME, 'instantiation': 'plc-instantiated', 
			'max_nodes': 1000, 'description': 'blank', 'person_ids': [], 'node_ids': []}

	person_fields = {'first_name': 'fname', 'last_name': 'lname', 'password': 'password',
                 	 'email': self.config.TEST_PERSON_EMAIL, 'site_ids': [], 'slice_ids': []}


	# Add Test site
	#sites = api.GetSites(auth, {'login_base': site_fields['login_base']})
	sites = GetSites({'login_base': site_fields['login_base']})
	if not sites:
    	    #site_id =  api.AddSite(auth, site_fields)
	    site_id = AddSite(site_fields)
	    site_fields['site_id'] = site_id
	    site = site_fields
	    if self.config.verbose:
		utils.header("Added test site")
	else:
	    site = sites[0]
	    if self.config.verbose:
		utils.header("Test site found")

	# Add Test nodes
	for node_fields in node_list:
    	    #nodes = api.GetNodes(auth, [node_fields['hostname']])
    	    nodes = GetNodes([node_fields['hostname']])
	    if not nodes:
        	#node_id = api.AddNode(auth, site_fields['login_base'], node_fields)
		node_id = AddNode(site_fields['login_base'], node_fields)
		node_fields['node_id'] = node_id
		node = node_fields
		nodes.append(node_fields)
		if self.config.verbose:
		    utils.header("Added test node")
	    else:
	        node = nodes[0]
		if self.config.verbose:
		    utils.header("Test node found")

	    # Add node network
	    if not node['nodenetwork_ids']:
		#nodenetwork_id = api.AddNodeNetwork(auth, node_fields['hostname'], node_fields)
		nodenetwork_id = AddNodeNetwork(node_fields['hostname'], node_fields)
		if self.config.verbose:
		    utils.header("Added test nodenetwork")
	    else:
	        if self.config.verbose:
	            utils.header("Nodenetwork found")	
	
	# Add Test slice
	#slices = api.GetSlices(auth, [slice_fields['name']])
	slices = GetSlices([slice_fields['name']])
	if not slices:
	    #slice_id = api.AddSlice(auth, slice_fields)
	    slice_id = AddSlice(slice_fields)
	    slice_fields['slice_id'] = slice_id
	    slice = slice_fields
	    if self.config.verbose:
		utils.header("Added test slice")
	else:
	    slice = slices[0]
	    if self.config.verbose:
		utils.header("Test slice found")

	# Add slice to nodes
	node_ids = [n['node_id'] for n in nodes]
	node_ids = filter(lambda node_id: node_id not in slice['node_ids'], node_ids)
	if node_ids:
	    #api.AddSliceToNodes(auth, slice['name'], node_ids)
	    AddSliceToNodes(slice['name'], node_ids)
	    if self.config.verbose:
		utils.header("Added test slice to test nodes")
	else:
	    if self.config.verbose:
		utils.header("Test slice found on test nodes")

	# Add test person
	#persons = api.GetPersons(auth, [person_fields['email']])
	persons = GetPersons([person_fields['email']])
    	if not persons:
      	    #person_id = api.AddPerson(auth, person_fields)
	    person_id = AddPerson(person_fields)
	    person_fields['person_id'] = person_id
	    person = person_fields
	    if self.config.verbose:
		utils.header("Added test person")
	else:
	    person = persons[0]
	    if self.config.verbose:
		utils.header("Test person found")
	
	# Add roles to person
	#api.AddRoleToPerson(auth, 'user', person['email'])
	AddRoleToPerson('user', person['email'])
	# Add person to site
	if site['site_id'] not in person['site_ids']:	
	    #api.AddPersonToSite(auth, person['email'], site['login_base'])
	    AddPersonToSite(person['email'], site['login_base'])
	    if self.config.verbose:
		utils.header("Added test person to test site")
	else:
	    if self.config.verbose:
		utils.header("Test person found on test site")

	# Add person to slice
	if slice['slice_id'] not in person['slice_ids']:
            #api.AddPersonToSlice(auth, person_fields['email'], slice_fields['name'])
	    AddPersonToSlice(person_fields['email'], slice_fields['name'])
	    if self.config.verbose:
		utils.header("Added test person to slice")
	else:
	    if self.config.verbose:
		utils.header("Test person found on test slice")
	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    add_test_data()(*args)
