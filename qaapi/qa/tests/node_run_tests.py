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

    def call(self, hostname, plcname, tests = None):
	
	node_tests = ['node_cpu_sched.py', 'pf2test.pl'] 
	node_tests_path = self.config.node_tests_path
	node_test_files = self.config.node_tests_path
	archive_name = 'tests.tar.gz'
	archive_path = '/tmp/'
	tests_path = '/usr/share/'
	tests_dir = 'tests/'

	node = self.config.get_node(hostname)
	plc = self.config.get_plc(plcname)
	plc_ip = plc.update_ip()

	print >> node.logfile, "Running Node Tests"
	
	# Create tests archive
	if self.config.verbose:
	    utils.header("Updating tests archive at %(archive_path)s" % locals())
	utils.commands("mkdir -p %(archive_path)s/%(tests_dir)s" % locals())
	utils.commands("cp -Rf %(node_tests_path)s/* %(archive_path)s/%(tests_dir)s" % locals())  
	tar_cmd = "cd %(archive_path)s && tar -czf /%(archive_path)s/%(archive_name)s %(tests_dir)s" % locals()
	print >> node.logfile, tar_cmd
	(status, output) = utils.commands(tar_cmd)

	# Copy tests archive to plc's webroot
	if self.config.verbose:
            utils.header("Copying tests archive onto %(plcname)s webroot" % locals())
	plc.scp_to("%(archive_path)s/%(archive_name)s" % locals(), "/var/www/html/")

	if self.config.verbose:
	    utils.header("Downloading tests archive onto %(hostname)s" % locals())
	cleanup_cmd = "rm -f %(tests_path)s/%(archive_name)s" % locals()
	print >> node.logfile, cleanup_cmd
	node.commands(cleanup_cmd, False)
	wget_cmd = "wget -nH -P %(tests_path)s http://%(plc_ip)s/%(archive_name)s" % locals()
	print >> node.logfile, wget_cmd
	# Download tests onto      
	node.commands(wget_cmd)
	
	# Extract tests archive
	tarx_cmd = "cd %(tests_path)s && tar -xzm -f %(archive_name)s" % locals()
	print >> node.logfile, tarx_cmd
	node.popen(tarx_cmd)
	
	# Make tests executable
	# XX Should find a better way to do this
	chmod_cmd = "cd %s/tests && chmod 755 %s " % (tests_path, " ".join(node_tests) )
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

	# Add full path to test files      
	test_files_abs = [node_tests_path + os.sep + file for file in tests]
	
	results = {}
	for test in tests:
	    if self.config.verbose:
		utils.header("Running %(test)s test on %(hostname)s" % locals())
	    command = "cd %(tests_path)s/tests && ./%(test)s" % locals()
	    print >> node.logfile,  command
	    (stdout, stderr) = node.popen(command, False)
	    print >> node.logfile, "".join(stdout) 	 
	    
	    if self.config.verbose:
	        if status == 0:
		    utils.header("%(test)s Susccessful " % locals())
		else:
	 	    utils.header("%(test)s Failed " % locals())
	    	utils.header(output)
	    results[test] = (stdout, stderr)
	
	return 1 

if  __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_remote_call()(*args)	 		
