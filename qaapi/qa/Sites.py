import os
from Table import Table

class Site(dict):

     fields = {
	'plcs': ['TestPLC'],
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

class Sites(Table):
    def __init__(self, sites):
	sitelist = [Site(site) for site in sites]
	Table.__init__(self, sitelist)				 	  			 	 	
