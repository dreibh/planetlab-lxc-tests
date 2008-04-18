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
	options = " -q "
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
	options = " -q "
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

    def is_ready(self, timeout=8):
	# Node is considered ready when vuseradd processes have stopped 
	ready = False
	start_time = time.time()
	end_time = start_time + 60 * timeout
	while time.time() < end_time and ready == False:
	    command = "ps -elfy | grep vuseradd | grep -v grep"	
	    (output, errors) = self.popen(command, False) 
	    if output and output.find('vuseradd') or errors:
		if self.config.verbose:
                    utils.header('%s is not ready. waiting 30 seconds' %  self['hostname'])
                sleep(20)
	    else:
		ready = True
		if self.config.verbose:
		    utils.header('%s is ready' % self['hostname'])

	return ready  
	 
class Nodes(list, Table):

    def __init__(self, config, nodes):
    	nodelist = [Node(config, node) for node in nodes]
	list.__init__(self, nodelist)
	self.config = config
	
