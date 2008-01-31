#!/usr/bin/python
import os, sys
from Test import Test
from qa import utils

class node_run_tests(Test):
    """
    Attempt to copy the specified node test files onto a node using 
    the plc root key and execute them. If no test files are specified, 
    then all are used. 
    """

    def call(self, hostname, tests = None, root_key_path = "/etc/planetlab/root_ssh_key.rsa"):
	
	# Verify root key exists
	if not os.path.isfile(root_key_path):
	    raise Exception, "no such private key file %(root_key_path)s" % locals()
	
	node_tests_path = self.config.node_tests_path
	node_test_files = self.config.node_tests_path
	# Verify test files
	if tests:
	    invalid_tests = set(tests).difference(node_test_files)
	    if invalid_tests:
		raise Exception, "Invalid test(s) %s. File(s) not found in %s" % \
				(" ".join(list(invalid_tests)), node_tests_path)
	else:
	    tests = test_files

	# Add full path to test files      
	test_files_abs = [node_tests_path + os.sep + file for file in tests]
	
	# Copy files onto node
	copy_command = "scp -i %s %s root@%s:/tmp/ " % (root_key_path, " ".join(test_files_abs), hostname)
	if self.config.verbose:
	    utils.header(copy_command)
	(status, output) = utils.commands(copy_command)

	# execute each file individually
	results = {}
	exe_command = "ssh -i %(root_key_path)s root@%(hostname)s /tmp/%(file)s" 
	for file in test_files:
	    command = exe_command % locals()
	    if self.config.verbose:
		utils.header(command)
	    (status, output) = utils.commands(command, False)
	    results[file] = (status, output)
	
	return 1 

if  __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_remote_call()(*args)	 		
