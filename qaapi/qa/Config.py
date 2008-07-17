import xmlrpclib
import os
import sys
import re
import socket
import utils
import copy
from logger import logfile, Logfile
from Table import Table
from PLCs import PLC, PLCs
from Sites import Site, Sites	
from Nodes import Node, Nodes
from Slices import Slice, Slices
from Persons import Person, Persons	
from TestScripts import TestScript

path = os.path.dirname(os.path.abspath(__file__))

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

    def __init__(self, config_file = path+os.sep+'qa_config', logdir = "/var/log"):
	# Load config file
	try:
            execfile(config_file, self.__dict__)
        except:
            raise "Could not find system config in %s" % config_file
	
	self.logdir = logdir	
	log_filename = logdir + os.sep + "qaapi.log"
 	self.update_logfile(log_filename)
	self.auth = {}
	self.auth['Username'] = self.PLC_ROOT_USER
	self.auth['AuthString'] = self.PLC_ROOT_PASSWORD
	self.auth['AuthMethod'] = 'password'
	self.verbose = self.VERBOSE

	attributes = ['plcs', 'sites', 'slices', 'nodes', 'persons', 'nodegroups']
	for attribute in attributes:
	    setattr(self, attribute, [])	
	
	# try setting hostname and ip
        self.hostname = socket.gethostname()
        try:
            command = "/sbin/ifconfig eth0 | grep -v inet6 | grep inet | awk '{print$2;}'"
            (status, output) = utils.commands(command, logfile = self.logfile)            
	    self.ip = re.findall(r'[0-9\.]+', output)[0]
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

    def update_logfile(self, filename):
	self.logfile = Logfile(filename)
	filename_parts = self.logfile.filename.split(os.sep)
	self.logdir = os.sep + os.sep.join(filename_parts[:-1]) + os.sep

    def get_plc(self, plc_name):
	plc = PLC(self)
	if hasattr(self, 'plcs')  and plc_name in self.plcs.keys():
	    plc.update(self.plcs[plc_name])
	    plc.update_api()
	return plc

    def get_node(self, hostname):
	node = Node(self)
	if hasattr(self, 'nodes') and hostname in self.nodes.keys():
	    node.update(self.nodes[hostname])
	    node.__init_logfile__()
	return node			

    def get_node_test(self, testscript):
	script = TestScript({'name': testscript})
	if hasattr(self, 'node_tests') and testscript in self.node_tests.keys():
	    script.update(self.node_tests[testscript])
	return script

    def get_slice_test(self, testscript):
	script = TestScript()
	if hasattr(self, 'slice_tests') and testscript in self.slice_tests.keys():
	    script.update(self.slice_tests[testscript])
	return script  
	 
    
    def load(self, conffile):
	
	confdata = {}
	try: execfile(conffile, confdata)
	except: raise 

	from Nodes import Nodes
	from PLCs import PLCs	
	loadables = ['plcs', 'sites', 'nodes', 'nodegroups', 'slices', 'persons']
	config = Config(logdir = self.logdir)
	for element in confdata.keys():
	    if element in ['plcs'] and confdata.has_key(element):
	        setattr(self, element, PLCs(config, confdata[element]).dict('name'))
		setattr(config, element, PLCs(config, confdata[element]).dict('name'))
	    elif element in ['nodes'] and confdata.has_key(element):
		setattr(self, element, Nodes(config, confdata[element]).dict('hostname'))
		setattr(config, element, Nodes(config, confdata[element]).dict('hostname'))
	    elif element in ['nodegroups'] and confdata.has_key(element):
		setattr(self, element, Table(confdata[element]).dict('name'))	
		setattr(config, element, Table(confdata[element]).dict('name'))
	    elif element in ['sites'] and confdata.has_key(element):
		setattr(self, element, Sites(confdata[element]).dict('login_base'))
		setattr(config, element, Sites(confdata[element]).dict('login_base'))
	    elif element in ['slices'] and confdata.has_key(element):
		setattr(self, element, Slices(config, confdata[element]).dict('name'))
		setattr(config, element, Slices(config, confdata[element]).dict('name'))
	    elif element in ['persons'] and confdata.has_key(element):
		setattr(self, element, Persons(confdata[element]).dict('email'))
		setattr(config, element, Persons(confdata[element]).dict('email'))
	    elif element in ['node_tests'] and confdata.has_key(element):
		setattr(self, element, TestScripts(confdata[element]).dict('name')) 
		setattr(config, element, TestScripts(confdata[element]).dict('name'))
	    elif element in ['slice_tests'] and confdata.has_key(element):
	 	setattr(self, element, TestScripts(confdata[element]).dict('name'))
		setattr(config, element, TestScripts(confdata[element]).dict('name'))

    def archive_scripts(self, prefix):
	valid_prefix = ['slice', 'node'] 
	if prefix not in valid_prefix:
	    raise "Error. Invalid prefix %s. Must be in %s" %  (prefix, valid_prefix)

	scripts_dir = self.path + os.sep + 'tests' +os.sep + prefix + os.sep
	workdir = '/tmp' + os.sep	
	archive_path = workdir + os.sep + prefix + os.sep
	archive_filename = prefix + ".tar.gz"
  
	if self.verbose:
	    utils.header("Creating/Updating %s archive %s" % (prefix, archive_path + archive_filename), logfile = self.logfile)
	utils.commands("mkdir -p %(archive_path)s" % locals(), logfile = self.logfile) 	
	utils.commands("cp -Rf %(scripts_dir)s* %(archive_path)s" % locals(), logfile = self.logfile)
	tar_cmd = "cd %(workdir)s && tar -czf %(workdir)s/%(archive_filename)s %(prefix)s" % locals() 
	utils.commands(tar_cmd, logfile = self.logfile)
	return (archive_filename, workdir+archive_filename) 

    def archive_slice_tests(self): 
	return self.archive_scripts('slice')
    
    def archive_node_tests(self):
	return self.archive_scripts('node')		
