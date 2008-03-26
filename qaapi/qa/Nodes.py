import utils
import os
from Remote import Remote
from Table import Table


class Node(dict, Remote):

    fields = {
	'plc': None,
	'hostname': None, 		# Node Hostname
	'host': 'localhost',		# host where node lives
	'vserver': None,		# vserver where this node lives
	'type': 'virtual', 		# type of node
	'nodenetworks': [], 		# node networks
	'homedir': '/var/VirtualMachines/',
	'rootkey': None			 # path to root ssh key
	}

    def __init__(self, config, fields = {}):

	# XX Filter out fields not specified in fields
	dict.__init__(self, self.fields)
	
	# Merge defined fields with defaults
	self.update(fields)
	self.config = config	
    
class Nodes(list, Table):

    def __init__(self, config, nodes):
    	nodelist = [Node(config, node) for node in nodes]
	list.__init__(self, nodelist)
	self.config = config
	
