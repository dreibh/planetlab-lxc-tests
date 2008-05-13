#!/usr/bin/python

import os, sys
from Test import Test
from qa import utils
from qa.PLCs import PLC, PLCs

class delete_test_data(Test):
    """
    Removes the test data found in config from the plc db
    """

    def call(self, plc_name = None):

	# Determine which plc to talk to 
	plc = self.config.get_plc(plc_name)
        api = plc.config.api
        auth = plc.config.auth
	
	# Search config for objects that belong to this plc
        # Any object with 'plc' defined as this plc's name or with 
        # no 'plc' defined will be added
        this_plc = lambda object: 'plc' not in object or \
                                  'plc' in object and object['plc'] == plc['name'] or \
                                  object['plc'] == None

	sitelist = filter(this_plc, self.config.sites.values())
	nodegrouplist = filter(this_plc, self.config.nodegroups.values())
		
	# Deleting the site should delete everything associated with it
	# including nodes, persons
	for site in sitelist:
	    try:
	        api.DeleteSite(auth, site['login_base'])
	        if self.config.verbose:
	            utils.header("Test data deleted", logfile = self.config.logfile)
	    except:
		if self.config.verbose:
		    utils.header("Error	deleting %s" % site['login_base'], logfile = self.config.logfile)		
	# Delete nodegroups
	for nodegroup in nodegrouplist:
	    try:
		api.DeleteNodeGroup(auth, nodegroup['name'])
		if self.config.verbose:
		    utils.header("NodeGroups deleted", logfile = self.config.logfile)
	    except:
		if self.config.verbose:
		    utils.header("Error deleting %s" % nodegroup['name'], logfile = self.config.logfile)	
	return 1 
	
if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    delete_test_data()(*args)		
