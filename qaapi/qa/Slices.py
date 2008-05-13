import os
from Remote import Remote
from Table import Table

class Slice(dict, Remote):

     fields = {
	'plcs': ['TestPLC'],		     # which plc does this slice belong to	
	'name': None,
	'instantiation': 'plc-instantiated',
	'max_nodes': 1000,
	'description': 'blank',
	'url': None,
	'key': None,			     # any valid ssh key
	'nodes': [],			     # nodes where this slice runs
	'tests_path': '/usr/share/tests/',   	
	'tests': []                          # which test to run. None or empty list means run all
	}

     def __init__(self, fields = {}):

	dict.__init__(self, self.fields)
	
	self.update(fields)

class Slices(Table):
    def __init__(self, slices):
	slicelist = [Slice(slice) for slice in slices]
	Table.__init__(self, slicelist)				 	  			 	 	
