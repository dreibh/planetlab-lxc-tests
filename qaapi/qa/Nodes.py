import utils
import os
from Remote import Remote
from Table import Table


class Node(dict, Remote):

    fields = {
	'plcs': ['TestPLC'],
	'hostname': None, 		# Node Hostname
	'host': 'localhost',		# host where node lives
	'redir_port': None,		# Port on host where ssh is redirected to virtual node
	'vserver': None,		# vserver where this node lives
	'type': 'vm', 			# type of node
	'model': '/minhw',
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

    def host_popen(self, command, fatal = True):
        command = self.get_host_command(command)
        return utils.popen(command, fatal, self.config.verbose)

    def host_popen3(self, command):
        command = self.get_host_command(command)
        return utils.popen3(command, self.config.verbose)

    def host_commands(self, command, fatal = True):
        command = self.get_host_command(command)
        return utils.commands(command, fatal, self.config.verbose)    
	 
class Nodes(list, Table):

    def __init__(self, config, nodes):
    	nodelist = [Node(config, node) for node in nodes]
	list.__init__(self, nodelist)
	self.config = config
	
