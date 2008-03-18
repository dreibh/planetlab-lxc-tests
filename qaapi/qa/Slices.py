import os
from Table import Table

class Slice(dict):

     fields = {
	'plc': None,
	'name': None,
	'instantiation': 'plc-instantiated',
	'max_nodes': 1000,
	'description': 'blank',
	'url': None
	}

     def __init__(self, fields = {}):

	dict.__init__(self, self.fields)
	
	self.update(fields)

class Slices(list, Table):
    def __init__(self, slices):
	slicelist = [Slice(slice) for slice in slices]
	list.__init__(self, slicelist)				 	  			 	 	
