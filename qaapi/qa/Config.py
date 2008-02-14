import xmlrpclib
import os
import sys
import re
import socket
import utils

class Config:

    path = os.path.dirname(os.path.abspath(__file__))
    tests_path = path + os.sep + 'tests'
    node_tests_path = tests_path + os.sep + 'node'
    slice_tests_path = tests_path + os.sep + 'slice'				

    def update_api(self):
	# Set up API acccess
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
        (stdout, stderr) = utils.popen("/sbin/ifconfig eth0 | grep 'inet addr'")
        inet_addr = re.findall('inet addr:[0-9\.^\w]*', stdout[0])[0]
        parts = inet_addr.split(":")
        self.ip = parts[1]
	
        api_host = self.__dict__.get("PLC_API_HOST",self.ip)
        self.PLC_API_HOST=api_host

        self.update_api()

	# Load list of node tests
	valid_node_test_files = lambda name: not name.startswith('__init__') \
					     and not name.endswith('pyc')
	node_test_files = os.listdir(self.node_tests_path)
	self.node_test_files = filter(valid_node_test_files, node_test_files) 

