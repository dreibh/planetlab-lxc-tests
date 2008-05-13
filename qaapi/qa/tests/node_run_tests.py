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

    def call(self, hostname, plcname, tests = None):

	node = self.config.get_node(hostname)
        plc = self.config.get_plc(plcname)
        plc_ip = plc.update_ip()
	node_tests = ['node_cpu_sched.py', 'pf2test.pl'] 
	node_tests_path = self.config.node_tests_path
	node_test_files = self.config.node_tests_path
	tests_dir = node['tests_dir']

	print >> node.logfile, "Running Node Tests"
	
	# Create tests archive
	(archive_filename, archive_filepath) = self.config.archive_node_tests()
	archive_dir = archive_filename.split('.tar')[0]

	# Copy tests archive to plc's webroot
	plc.scp_to_webroot("%(archive_filepath)s" % locals())

	# Download url onto node
	url = "http://%(plc_ip)s/%(archive_filename)s" % locals() 
	node.wget(url, tests_dir)
  
	# Extract tests archive
	tarx_cmd = "cd %(tests_dir)s && tar -xzm -f %(archive_filename)s" % locals()
	print >> node.logfile, tarx_cmd
	node.popen(tarx_cmd)
	
	# Make tests executable
	# XX Should find a better way to do this
	chmod_cmd = "cd %s/%s && chmod 755 %s " % (tests_dir, archive_dir, " ".join(node_tests) )
	print >> node.logfile, chmod_cmd
	node.popen(chmod_cmd) 
 
	# Verify test files
	if tests:
	    invalid_tests = set(tests).difference(node_tests)
	    if invalid_tests:
		raise Exception, "Invalid test(s) %s. File(s) not found in %s" % \
				(" ".join(list(invalid_tests)), node_tests_path)
	else:
	    tests = node_tests

	#tests = self.config.get_node_tests(tests)
	# Add full path to test files      
	#test_files_abs = [node_tests_path + os.sep + file for file in tests]
	
	results = {}
	for test in tests:
	    if self.config.verbose:
		utils.header("Running %(test)s test on %(hostname)s" % locals(), logfile = self.config.logfile)
	    script = self.config.get_node_test(test)
	    
	    exe_pre, exe_script, exe_post = None, script['name'], None
	    if script['pre']: exe_pre = script['exe_pre']
	    if script['args']: exe_script = "%s %s" % (script['name'], script['args'])
	    if script['post']: exe_post = script['exe_post']
 
	    # Create a separate logfile for this script
	    logfile = Logfile(self.config.logfile.dir + script['name'] + ".log")
	    for command in [exe_pre, exe_script, exe_post]:
		if command:
		    command = "cd %(tests_dir)s/%(archive_dir)s && ./%(command)s" % locals()
	    	    print >> node.logfile,  command
		    print >> logfile, command

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
