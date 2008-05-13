import utils
import os
import re
import time
from time import sleep
from Remote import Remote, VRemote
from Table import Table
from logger import Logfile


class Node(dict, VRemote):

    fields = {
	'plcs': ['TestPLC'],
	'hostname': None, 			      # Node Hostname
	'host': 'localhost',			      # host where node lives
	'redir_ssh_port': '51022',		      # Port on host where ssh is redirected to virtual node
	'vserver': None,			      # vserver where this node lives
	'type': 'vm', 				      # type of node
	'model': '/minhw',
	'nodegroups': [],
	'nodenetworks': [], 			      # node networks
	'homedir': '/var/VirtualMachines/',
	'rootkey': '/etc/planetlab/root_ssh_key.rsa', # path to root ssh key
	'host_rootkey': None,			      # path to host root ssh key
	'tests_dir': '/usr/share/tests/',
	'tests': []				      # which test to run. None or empty list means run all   		
	}

    def __init__(self, config, fields = {}):

	# XX Filter out fields not specified in fields
	dict.__init__(self, self.fields)
	
	# Merge defined fields with defaults
	self.update(fields)
	self.config = config
	self.__init_logfile__()
	
    get_host_command = Remote.get_remote_command
    get_host_scp_command = Remote.get_scp_command

    def __init_logfile__(self, filename = None):
	if not filename:
	    filename = '%s/%s.log' % (self.config.logdir, self['hostname'])
	self.logfile = Logfile(filename)

    def rotate_logfile(self):
	if os.path.isfile(self.logfile.filename):
	    (status, output) = utils.commands("ls %s*" % self.logfile.filename)
	    files = output.split("\n")
	    files.sort()
	    lastfile = files[-1:][0]
	    index = lastfile.split(self.logfile.filename)[1].replace(".", "")		  			
	    if not index:
		index = "1"
	    else:
		index = str(int(index) + 1)
	    utils.commands("mv %s %s.%s" % (self.logfile.filename, self.logfile.filename, index))
		
    def get_host_ip(self):
	self.__init_logfile__()

	# Used to get ip of this nodes host
	ip_command = "/sbin/ifconfig eth0 | grep -v inet6 | grep inet | awk '{print$2;}'" 
	(status, output) = self.host_commands(ip_command)            
 	ip = re.findall(r'[0-9\.]+', output)[0]	
	return ip

    def is_ready(self, timeout=30):
	# Node is considered ready when Node Manager has started avuseradd processes have stopped
	log = self.config.logfile 
	class test:
	    def __init__(self, name, description, system, cmd, check, inverse = False, logfile = log):
	        self.system = system
		self.cmd = cmd
		self.check = check
		self.name = name
		self.description = description
		self.inverse = inverse
		self.logfile = logfile
 
	    def run(self, logfile, verbose = True):
		if verbose:
		    utils.header(self.description, logfile =  self.logfile)	
	        (status, output) = self.system(self.cmd)
		if self.inverse and output.find(self.check) == -1:
		    if verbose: utils.header("%s Passed Test" % self.name, logfile = self.logfile)
		    return True
		elif not self.inverse and output and output.find(self.check)  -1:		
		    if verbose: utils.header("%s Passed Test" % self.name, logfile = self.logfile)
		    return True
		
		if verbose: utils.header("%s Failed Test" % self.name, logfile = self.logfile)
	        return False

	ready = False
	start_time = time.time()
	end_time = start_time + 60 * timeout
	vcheck_cmd = "ps -elfy | grep vuseradd | grep -v grep"  
        grep_cmd = "grep 'Starting Node Manager' %s" % self.logfile.filename
	tests = {
	'1':  test("NodeManager", "Checking if NodeManager has started", utils.commands, grep_cmd, "OK", logfile = self.config.logfile),
	'2':  test("vuseradd", "Checking if vuseradd is done", self.commands, vcheck_cmd, "vuseradd", True, logfile = self.config.logfile)      
	}
	
	while time.time() < end_time and ready == False:
	    # Run tests in order
	    steps = tests.keys()
	    steps.sort()
	    results = {}
	    for step in steps:
		test = tests[step]
		results[step] = result = test.run(self.config.verbose)
		if not result: break
		        	   	 	
	    # Check results. We are ready if all passed 		
	    if not set(results.values()).intersection([False, None]):
		ready = True
	    else:
		if self.config.verbose:
		    utils.header("%s not ready. Waiting 30 seconds. %s seconds left" % \
				 (self['hostname'], int(end_time - time.time())) )
		time.sleep(30)   			

	return ready  
	 
class Nodes(Table):

    def __init__(self, config, nodes):
    	nodelist = [Node(config, node) for node in nodes]
	Table.__init__(self, nodelist)
	self.config = config
	
