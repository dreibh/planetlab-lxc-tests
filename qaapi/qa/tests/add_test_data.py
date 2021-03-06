#!/usr/bin/python
import os,sys
from Test import Test
from qa import utils
from qa.PLCs import PLC, PLCs
  
class add_test_data(Test):
    """
    Adds the test data found in config to the plc db
    """   
    def call(self, plc_name = None):

	# Determine which plc to talk to 
	plc = self.config.get_plc(plc_name)
        api = plc.config.api
        auth = plc.config.auth

	# Search config for objects that belong to this plc
	# Any object with 'plc' defined as this plc's name or with 
	# no 'plc' defined will be added
	this_plc = lambda object: 'plcs' not in object or \
				  'plcs' in object and plc['name'] in object['plcs'] or \
				  object['plcs'] == None   
     	
	sitelist, nodelist, slicelist, personlist, nodegrouplist = [], [], [], [], []
	
	if isinstance(self.config.sites, dict):
	    sitelist = filter(this_plc, self.config.sites.values())  	
	if isinstance(self.config.nodes, dict):
	    nodelist = filter(this_plc, self.config.nodes.values())
	if isinstance(self.config.slices, dict):
	    slicelist = filter(this_plc, self.config.slices.values())
	if isinstance(self.config.persons, dict):
	    personlist = filter(this_plc, self.config.persons.values()) 
	if isinstance(self.config.nodegroups, dict): 
	    nodegrouplist = filter(this_plc, self.config.nodegroups.values())

	# Add Test site
	for site in sitelist:
	    sites = api.GetSites(auth, [site['login_base']])
	    if not sites:
	        site_id = api.AddSite(auth, dict(site))
	        site['site_id'] = site_id
	        if self.config.verbose:
		    utils.header("Added site: %s" % site['name'], logfile = self.config.logfile)
	    else:
	        site.update(sites[0])
	        if self.config.verbose:
		    utils.header("Site %s found" % site['name'], logfile = self.config.logfile)
	
	# Add Nodegroups
	for nodegroup in nodegrouplist:
	    nodegroups = api.GetNodeGroups(auth, [nodegroup['name']])
	    if not nodegroups:
		nodegroup_id = api.AddNodeGroup(auth, dict(nodegroup))
		nodegroup['nodegroup_id'] = nodegroup_id
		if self.config.verbose:
		    utils.header("Added Nodegroup: %s " % nodegroup['name'], logfile = self.config.logfile)
		else:
		    nodegroup.update(nodegroups[0])
		    if self.config.verbose:
			utils.header("Nodegroup %s found" % nodegroup['name'], logfile = self.config.logfile)	 

	# Add Test nodes
	for node in nodelist:
    	    nodes = api.GetNodes(auth, [node['hostname']])
	    if not nodes:
		node_id = api.AddNode(auth, node['site'], dict(node))
		node['node_id'] = node_id
		if self.config.verbose:
		    utils.header("Added node: %s" % node['hostname'], logfile = self.config.logfile)
	    else:
	        node.update(nodes[0])
		if self.config.verbose:
		    utils.header("Node %s found" % node['hostname'], logfile = self.config.logfile)

	    # Add node network
	    if 'nodenetwork_ids' not in node or not node['nodenetwork_ids']:
		for nodenetwork in node['nodenetworks']:
		    nodenetwork_id = api.AddNodeNetwork(auth, node['hostname'], dict(nodenetwork))
		    if self.config.verbose:
		        utils.header("Added nodenetwork to %s" % node['hostname'], logfile = self.config.logfile)
	        else:
	            if self.config.verbose:
	                utils.header("Nodenetwork found on node %s" % node['hostname'], logfile = self.config.logfile)
	    # Add node to nodegroups
	    if 'nodegroups' in node:
		for nodegroup in node['nodegroups']:
		    api.AddNodeToNodeGroup(auth, node['hostname'], nodegroup)
		if self.config.verbose:
		    utils.header("Added %s to nodegroup %s" % (node['hostname'], node['nodegroups']))	 				
	
	# Add Test slice
	for slice in slicelist:
	    slices = api.GetSlices(auth, [slice['name']])
	    if not slices:
	        slice_id = api.AddSlice(auth, dict(slice))
	        slice['slice_id'] = slice_id
	        if self.config.verbose:
		    utils.header("Added slice: %s" % slice['name'], logfile = self.config.logfile)
	    else:
	        slice.update(slices[0])
	        if self.config.verbose:
		    utils.header("Slice %s found" % slice['name'], logfile = self.config.logfile)
	    
	    # Add slice to nodes
	    for node in slice['nodes']:
		api.AddSliceToNodes(auth, slice['name'], [node])	 	
	        if self.config.verbose:
		    utils.header("Added slice to %s" % node, logfile = self.config.logfile)
	
	# Add test person
	for person in personlist:
	    roles = person['roles']
	    persons = api.GetPersons(auth, [person['email']])
    	    if not persons:
	        person_id = api.AddPerson(auth, dict(person))
	        person['person_id'] = person_id
		api.UpdatePerson(auth, person_id, {'enabled': True})
	        if self.config.verbose:
		    utils.header("Added person: %s" % person['email'], logfile = self.config.logfile)
	    else:
	        person.update(persons[0])
	        if self.config.verbose:
		    utils.header("Person %s found" % person['email'], logfile = self.config.logfile)
	
	    # Add roles to person
	    for role in roles:
		api.AddRoleToPerson(auth, role, person['email'])
		if self.config.verbose:
		    utils.header("Added %s to %s" % (role, person['email']), logfile = self.config.logfile)
	    # Add person to site
	    for site in person['sites']:
	        api.AddPersonToSite(auth, person['email'], site)
	        if self.config.verbose:
		    utils.header("Added %s to %s" % (person['email'], site), logfile = self.config.logfile)

	    # Add person to slice
	    for slice in person['slices']:
                api.AddPersonToSlice(auth, person['email'], slice)
	        if self.config.verbose:
		    utils.header("Added %s to %s" % (person['email'], slice), logfile = self.config.logfile)
	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    add_test_data()(*args)
