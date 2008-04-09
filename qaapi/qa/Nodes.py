import utils
import os
import re
from Remote import Remote
from Table import Table


class Node(dict, Remote):

    fields = {
	'plcs': ['TestPLC'],
	'hostname': None, 		# Node Hostname
	'host': 'localhost',		# host where node lives
	'redir_ssh_port': '51022',	# Port on host where ssh is redirected to virtual node
	'vserver': None,		# vserver where this node lives
	'type': 'vm', 			# type of node
	'model': '/minhw',
	'nodenetworks': [], 		# node networks
	'homedir': '/var/VirtualMachines/',
	'rootkey': None,		 # path to root ssh key
	'host_rootkey': None
	}

    def __init__(self, config, fields = {}):

	# XX Filter out fields not specified in fields
	dict.__init__(self, self.fields)
	
	# Merge defined fields with defaults
	self.update(fields)
	self.config = config

    get_host_command = Remote.get_remote_command

    def get_remote_command(self, command, user = 'root', key = None):
	if key is None:
	    key = self['rootkey']
	options = " -q "
	options += " -o StrictHostKeyChecking=no "
	options += " -i %(key)s" % locals() 
	host = self['hostname']
	if 'type' in self and self['type'] in ['vm']:
	    if 'redir_ssh_port' in self and self['redir_ssh_port']:
		options += " -p %s " % self['redir_ssh_port']
	    ip_command = "/sbin/ifconfig eth0 | grep -v inet6 | grep inet | awk '{print$2;}'"
	    (status, output) = self.host_commands(ip_command)
	    host = re.findall(r'[0-9\.]+', output)[0]
	     
	command = "ssh %(options)s %(user)s@%(host)s \'%(command)s\'" % locals()
        return self.get_host_command(command)

    
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
	
