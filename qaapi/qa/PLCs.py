import os
import re
import utils
import xmlrpclib	
from Remote import Remote
from Table import Table
from logger import Logfile

class PLC(dict, Remote):
    fields = {
	'name': 'TestPLC', 				# PLC Name			
	'host': 'localhost',				# Node Hostname
	'ip':	'127.0.0.1',				# IP
	'chroot': None,					# Path to the chroot
	'vserver': None, 				# Vserver where this PLC lives
	'host_rootkey': None,			 	# Root Key
	'api_path': '/PLCAPI/', 			# PLCAPI path 
	'port': '443' 					# PLCAPI port
	
	}

    def __init__(self, config, fields = {}):
	# XX Filter out fields not specified in fields
	dict.__init__(self, self.fields)
	
	# Merge defined fields with defaults
	self.update(fields)
	
	# init config
	self.config = config
	self.__init_logfile__()

    def __init_logfile__(self, filename = None):
        if not filename:
            filename = '%s/qaapi.log' % (self.config.logdir)
        self.logfile = Logfile(filename)

    def update_ip(self):
	try: 	
	    command = "/sbin/ifconfig eth0 | grep -v inet6 | grep inet | awk '{print$2;}'"
	    (status, output) = self.commands(command)
	    ip = re.findall(r'[0-9\.]+', output)[0]  	
	except:
	    ip = "127.0.0.1"
	self['ip'] = ip.strip() 
	return self['ip']	

    def update_api(self):
	# Set up API acccess
        # If plc is specified, find its configuration
        # and use its API
	self.update_ip()
	name, ip, port, path = self['name'], self['ip'], self['port'], self['api_path']
	if self.config.verbose:
	    utils.header("Updating %(name)s's api to https://%(ip)s:%(port)s/%(path)s" % locals(), logfile = self.config.logfile)   
	api_server = "https://%(ip)s:%(port)s/%(path)s" % locals()
	self.config.api = xmlrpclib.Server(api_server, allow_none = 1)
        self.config.api_type = 'xmlrpc'	

    def update_node_images(self):
	pass

    def scp_to_webroot(self, localfiles, recursive = False):
	if self.config.verbose:
	    utils.header("Copying %s to %s webroot" % (localfiles, self['name']), logfile = self.config.logfile)
	self.scp_to("%(localfiles)s" % locals(), "/var/www/html/")
	url = 'http://%s/%s' % (self['ip'], localfiles)	
	
	return url 

class PLCs(Table):

    def __init__(self, config, plcs):
	plclist = [PLC(config, plc) for plc in plcs]
	Table.__init__(self, plclist)
