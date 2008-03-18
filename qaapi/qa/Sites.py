import os
from Table import Table

class Site(dict):

     fields = {
	'plc': 'TestPLC',
	'name': None,
	'login_base': None,
	'enabled': True,
	'abbreviated_name': None,
	'max_slices': 100,
	'is_public': True,
	'url': None
	}

     def __init__(self, fields = {}):

	dict.__init__(self, self.fields)
	
	self.update(fields)

class Sites(list, Table):
    def __init__(self, sites):
	sitelist = [Site(site) for site in sites]
	list.__init__(self, sitelist)				 	  			 	 	
