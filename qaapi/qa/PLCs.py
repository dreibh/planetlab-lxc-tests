import os
import copy	
from Remote import Remote
from Table import Table

class PLC(dict, Remote):
    fields = {
	'name': 'TestPLC', 				# PLC Name			
	'host': 'localhost',				# Node Hostname
	'ip':	'127.0.0.1',				# IP
	'chroot': None,
	'vserver': None, 				# Vserver where this PLC lives
	'rootkey': '/home/tmack/.ssh/plc-root', 	# Root Key
	'api_path': '/PLCAPI/', 				# PLCAPI path 
	'port': '443' 					# PLCAPI port
	
	}

    def __init__(self, config, fields = {}):
	# XX Filter out fields not specified in fields
	dict.__init__(self, self.fields)
	
	# Merge defined fields with defaults
	self.update(fields)
	
	# init config
	self.config = config
	self.config.update_api(self)

class PLCs(list, Table):

    def __init__(self, config, plcs):
	plclist = [PLC(config, plc) for plc in plcs]
	list.__init__(self, plclist)
