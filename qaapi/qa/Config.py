import xmlrpclib
import os
import sys
import re
import socket
import utils
import copy
from PLCs import PLC, PLCs
from Sites import Site, Sites	
from Nodes import Node, Nodes
from Slices import Slice, Slices
from Persons import Person, Persons	

class Config:

    path = os.path.dirname(os.path.abspath(__file__))
    tests_path = path + os.sep + 'tests' + os.sep
    node_tests_path = tests_path + os.sep + 'node' + os.sep
    slice_tests_path = tests_path + os.sep + 'slice' + os.sep				
    vserver_scripts_path = path + os.sep + 'vserver' + os.sep

    def update_api(self, plc = None):
	# Set up API acccess
	# If plc is specified, find its configuration
	# and use its API
        if plc is not None:
	    protocol, host, path, port  = 'http', plc['host'], plc['api_path'], plc['port']
	    if port in ['443']:
		protocol = 'https'
	    api_server = "%(protocol)s://%(host)s:%(port)s/%(path)s" % locals()
	    self.api = xmlrpclib.Server(api_server, allow_none = 1)
	    self.api_type = 'xmlrpc'	
	else:

	    # Try importing the API shell for direct api access.
	    # If that fails fall back to using xmlrpm
	    try:
	        sys.path.append('/usr/share/plc_api')
	        from PLC.Shell import Shell
	        shell = Shell(globals = globals())
	    
	        # test it
	        shell.GetRoles()
	        self.api = shell
	        self.api_type = 'direct'
	    except:
	        self.api = xmlrpclib.Server('https://%s/PLCAPI/' % self.PLC_API_HOST, allow_none = 1)
	        self.api_type = 'xmlrpc'

    def __init__(self, config_file = path+os.sep+'qa_config'):
	# Load config file
	try:
            execfile(config_file, self.__dict__)
        except:
            raise "Could not find system config in %s" % config_file

	self.auth = {}
	self.auth['Username'] = self.PLC_ROOT_USER
	self.auth['AuthString'] = self.PLC_ROOT_PASSWORD
	self.auth['AuthMethod'] = 'password'
	self.verbose = self.VERBOSE	
	
	# try setting hostname and ip
        self.hostname = socket.gethostname()
        try:
	    (stdout, stderr) = utils.popen("/sbin/ifconfig eth0 | grep 'inet addr'")
            inet_addr = re.findall('inet addr:[0-9\.^\w]*', stdout[0])[0]
            parts = inet_addr.split(":")
            self.ip = parts[1]
	except:
	    self.ip = '127.0.0.1'
	
        api_host = self.__dict__.get("PLC_API_HOST",self.ip)
        self.PLC_API_HOST=api_host

        self.update_api()

	# Load list of node tests
	valid_node_test_files = lambda name: not name.startswith('__init__') \
					     and not name.endswith('pyc')
	node_test_files = os.listdir(self.node_tests_path)
	self.node_test_files = filter(valid_node_test_files, node_test_files) 

    def get_plc(self, plc_name):
	plc = PLC(self)
	if hasattr(self, 'plcs')  and plc_name in self.plcs.keys():
	    plc.update(self.plcs[plc_name])
	    plc.config.update_api(plc)
	return plc

    def get_node(self, hostname):
	node = Node(self)
	if hasattr(self, 'nodes') and hostname in self.nodes.keys():
	    node.update(self.nodes[hostname])
	return node			

    def load(self, conffile):
	
	confdata = {}
	try: execfile(conffile, confdata)
	except: raise 

	from Nodes import Nodes
	from PLCs import PLCs	
	loadables = ['plcs', 'sites', 'nodes', 'slices', 'persons']
	config = Config()
	for loadable in loadables:
	    if loadable in confdata and loadable in ['plcs']:
	        setattr(self, loadable, PLCs(config, confdata[loadable]).dict('name'))
	    elif loadable in confdata and loadable in ['nodes']:
		setattr(self, loadable, Nodes(config, confdata[loadable]).dict('hostname'))	
	    elif loadable in confdata and loadable in ['sites']:
		setattr(self, loadable, Sites(confdata[loadable]).dict('login_base'))
	    elif loadable in confdata and loadable in ['slices']:
		setattr(self, loadable, Slices(confdata[loadable]).dict('name'))
	    elif loadable in confdata and loadable in ['persons']:
		setattr(self, loadable, Persons(confdata[loadable]).dict('email')) 
	    
	
