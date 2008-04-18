import utils
import os
import re
import time
from time import sleep
from Remote import Remote
from Table import Table
from logger import Logfile


class Node(dict, Remote):

    fields = {
	'plcs': ['TestPLC'],
	'hostname': None, 			      # Node Hostname
	'host': 'localhost',			      # host where node lives
	'redir_ssh_port': '51022',		      # Port on host where ssh is redirected to virtual node
	'vserver': None,			      # vserver where this node lives
	'type': 'vm', 				      # type of node
	'model': '/minhw',
	'nodenetworks': [], 			      # node networks
	'homedir': '/var/VirtualMachines/',
	'rootkey': '/etc/planetlab/root_ssh_key.rsa', # path to root ssh key
	'host_rootkey': None
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
	    filename = '/var/log/%s.log' % self['hostname']
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

    def get_remote_command(self, command, user = 'root', key = None):
	if key is None and 'rootkey' in self:
	    key = self['rootkey']
	options = ""
	options += " -o StrictHostKeyChecking=no "
	if key:
	    options += " -i %(key)s" % locals()
	host = self['hostname']
	if 'type' in self and self['type'] in ['vm']:
	    if 'redir_ssh_port' in self and self['redir_ssh_port']:
		options += " -p %s " % self['redir_ssh_port']
	    host = self.get_host_ip() 
	command = "ssh %(options)s %(user)s@%(host)s \'%(command)s\'" % locals()
        return self.get_host_command(command)
 
    def get_scp_command(self, localfile, remotefile, direction, recursive = False, user = 'root', key = None):
	# scp options
	options = ""
	options += " -o StrictHostKeyChecking=no "
	if recursive:
	    options += " -r " 	
	if key:
	    options += " -i %(key)s "% locals()
	elif self['rootkey']:
	    options += " -i %s " % self['rootkey']
	
	# Are we copying to a real node or a virtual node hosted
	# at another machine 
	host = self['hostname']
	if 'type' in self and self['type'] in ['vm']:
	    if 'redir_ssh_port' in self and self['redir_ssh_port']:
		options += " -p %s " % self['redir_ssh_port']
	    host = self.get_host_ip()

	if direction in ['to']:
	    command = "scp %(options)s %(localfile)s %(user)s@%(host)s:/%(remotefile)s" % locals()
	elif direction in ['from']:
	    command = "scp %(options)s %(user)s$%(host)s:/%(remotefile)s %(localfile)s" % locals() 
        else:
	    raise Error, "Invalid direction, must be 'to' or 'from'."
	return command	    

    # Host remote commands
    def host_popen(self, command, fatal = True):
        command = self.get_host_command(command)
        return utils.popen(command, fatal, self.config.verbose)

    def host_popen3(self, command):
        command = self.get_host_command(command)
        return utils.popen3(command, self.config.verbose)

    def host_commands(self, command, fatal = True):
        command = self.get_host_command(command)
        return utils.commands(command, fatal, self.config.verbose)    

    # Slice remote commands
    def slice_popen(self, command, user = 'root', key = None, fatal = True):
	command = self.get_remote_command(command, user, key)
	return utils.popen(command, fatal)

    def slice_popen3(self, command, user = 'root', key = None, fatal = True):
	command = self.get_remote_command(command, user, key)
	return utils.popen3(command, fatal)

    def slice_commands(self, command, user = 'root', key = None, fatal = True):
	command = self.get_remote_command(command, user, key)
	return utils.commands(command, fatal)

    # Host scp 
    def scp_to_host(self, localfile, remotefile, recursive = False):
	command = self.get_host_scp_command(localfile, remotefile, 'to', recursive)
	return utils.commands(command)

    def scp_from_host(self, localfile, remotefile, recursive = False):
        command = self.get_host_scp_command(localfile, remotefile, 'from', recursive)
	return utils.commands(command)

    # Node scp
    def scp_to(self, localfile, remotefile, recursive = False, user = 'root', key = None):
	# if node is vm, we must scp file(s) to host machine first
	# then run scp from there
	if 'type' in self and self['type'] in ['vm']:
	    fileparts = localfile.split(os.sep)
	    filename = fileparts[-1:][0]
	    tempfile = '/tmp/%(filename)s' % locals()
	    self.scp_to_host(localfile, tempfile, recursive)
	    command = self.get_scp_command(tempfile, remotefile, 'to', recursive, user, key) 
	    return self.host_commands(command)
	else:
	    	
	    command = self.get_scp_command(localfile, remotefile, 'to', recursive, user, key) 
	    return utils.commands(command)	

    def scp_from(self, localfile, remotefile, recursive = False, user = 'root', key = None):
	# if node is vm, we must scp file(s) onto host machine first
        # then run scp from there
        if 'type' in self and self['type'] in ['vm']:
            fileparts = remotefile.split(os.sep)
            filename = fileparts[-1:]
            tempfile = '/tmp/%(filename)s' % locals()
            self.scp_from_host(remotefile, tempfile, recursive)
            command = self.get_scp_command(localfile, tempfile, 'from', recursive, user, key)  
            return self.host_commands(command)
        else:

            command = self.get_scp_command(localfile, remotefile, 'from', recursive, user, key) 
            return utils.commands(command)	

    def is_ready(self, timeout=10):
	# Node is considered ready when Node Manager has started avuseradd processes have stopped 
	class test:
	    def __init__(self, name, description, system, cmd, check, inverse = False):
	        self.system = system
		self.cmd = cmd
		self.check = check
		self.name = name
		self.description = description
		self.inverse = inverse
 
	    def run(self, verbose = True):
		if verbose:
		    utils.header(self.description)	
	        (status, output) = self.system(self.cmd)
		if self.inverse and output.find(self.check) == -1:
		    if verbose: utils.header("%s Passed Test" % self.name)
		    return True
		elif not self.inverse and output and output.find(self.check)  -1:		
		    if verbose: utils.header("%s Passed Test" % self.name)
		    return True
		
		if verbose: utils.header("%s Failed Test" % self.name)
	        return False

	ready = False
	start_time = time.time()
	end_time = start_time + 60 * timeout
	vcheck_cmd = "ps -elfy | grep vuseradd | grep -v grep"  
        grep_cmd = "grep 'Starting Node Manager' %s" % self.logfile.filename
	tests = {
	'1':  test("NodeManager", "Checking if NodeManager has started", utils.commands, grep_cmd, "OK"),
	'2':  test("vuseradd", "Checking if vuseradd is done", self.commands, vcheck_cmd, "vuseradd", True)      
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
	 
class Nodes(list, Table):

    def __init__(self, config, nodes):
    	nodelist = [Node(config, node) for node in nodes]
	list.__init__(self, nodelist)
	self.config = config
	
