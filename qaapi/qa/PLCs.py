import os
import copy
import qa.utils	
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

    def start_xmlrpc_server(self):
	"""
	PLCAPI comes with a SimpleServer script that allows you to run a 
	standalone http server that listens on the specified port.
	This is useful for running multiple api servers on the same machine.
	"""
	if 'host' in self and not 'host' in ['localhost', None]:
	    server_script = "/usr/share/plc_api/Server.py" 
	    self.commands("%s -p %s" % (server_script, self['port']))    
	    if self.config.verbose:
		utils.header("Starting api server at %s on listening on port %s" % (self['host'], self['port']))     

class PLCs(list, Table):

    def __init__(self, config, plcs):
	plclist = [PLC(config, plc) for plc in plcs]
	list.__init__(self, plclist)
