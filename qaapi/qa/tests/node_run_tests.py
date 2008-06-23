#!/usr/bin/python
import os, sys
from Test import Test
from qa import utils
from qa.TestScripts import TestScript, TestScripts
from qa.logger import Logfile

class node_run_tests(Test):
    """
    Attempt to download and execute the specified test scripts onto a node 
    and execute them run them. If no test files are specified, 
    then all are used. 
    """

    def __init__(self, config = None, logfile = None):
        if not config: config = Config()
        if not logfile: logfile = Logfile(config.logfile.dir + 'testscript.log')
        Test.__init__(self, config, logfile)

    def call(self, hostname, plcname, test):

	node = self.config.get_node(hostname)
        plc = self.config.get_plc(plcname)
	node_tests = ['node_cpu_sched.py', 'pf2test.pl'] 
	node_tests_path = self.config.node_tests_path
	node_test_files = self.config.node_tests_path
	tests_dir = node['tests_dir']

	# Verify test files
	if test:
	    invalid_tests = set([test]).difference(node_tests)
	    if invalid_tests:
		raise Exception, "Invalid test(s) %s. File(s) not found in %s" % \
				(" ".join(list(invalid_tests)), node_tests_path)
		
	result = {}
	if self.config.verbose:
	    utils.header("Running %(test)s test on %(hostname)s" % locals(), logfile = self.logfile)
	script = self.config.get_node_test(test)
	    
	exe_pre, exe_script, exe_post = None, script['name'], None
	if script['pre']: exe_pre = script['exe_pre']
	if script['args']: exe_script = "%s %s" % (script['name'], script['args'])
	if script['post']: exe_post = script['exe_post']
 
	for command in [exe_pre, exe_script, exe_post]:
            if command:
	        command = "cd %(tests_dir)s/%(archive_dir)s && ./%(command)s" % locals()
	        print >> node.logfile,  command
	        print >> self.logfile, command
  
                # Execute script on node
	        (stdout, stderr) = node.popen(command, False)
	        print >> node.logfile, "".join(stdout) 	 
	        print >> logfile, "".join(stdout) 
	        if self.config.verbose:
	            utils.header(stdout, logfile = self.config.logfile)
	        results[test] = (stdout, stderr)
	
	return 1 

if  __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_remote_call()(*args)	 		
