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
	'rootkey': '/home/tmack/.ssh/plc-root' # path to root ssh key
	}

    def __init__(self, config, fields = {}):

	# XX Filter out fields not specified in fields
	dict.__init__(self, self.fields)
	
	# Merge defined fields with defaults
	self.update(fields)
	self.config = config	
    
    def create_boot_image(self):

	command = ""
	if self['host'] and self['host'] not in ['localhost']:
	    command += "ssh -i %s root@%s " % (self['rootkey'], self['host'])
	
    def create_disk_image(self, size = '10G'):
	diskimg_path = self['homedir'] + os.sep + self['hostname'] + os.sep + \
		  	'hda.img'
	command = ""
	command += " qemu-img create -f qcow2 %(diskimg_path)s %(size)s " % locals()

	#utils.header(command)
	(status, output) = self.commands(command, True)

    def boot(self):
	pass

    def scp(self):
	pass 

class Nodes(list, Table):

    def __init__(self, config, nodes):
    	nodelist = [Node(config, node) for node in nodes]
	list.__init__(self, nodelist)
	self.config = config
	
