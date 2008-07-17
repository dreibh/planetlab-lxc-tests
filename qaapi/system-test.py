#!/usr/bin/python
import commands
import os
import sys
import traceback
from optparse import OptionParser
from random import Random
from time import localtime
from qa.sendmail import sendmail
from qa.utils import commands
from qa.logger import Logfile
from qa import utils 
from qa.Config import Config 
from qa.Step import Step
from qa.tests.vserver_create import vserver_create
from qa.tests.vserver_delete import vserver_delete
from qa.tests.plc_configure import plc_configure
from qa.tests.plc_stop import plc_stop
from qa.tests.plc_start import plc_start
from qa.tests.add_test_data import add_test_data
from qa.tests.api_unit_test import api_unit_test
from qa.tests.sync_person_key import sync_person_key
from qa.tests.boot_node import boot_node
from qa.tests.node_run_tests import node_run_tests

def create_vserver(vserver_name, vserver_home, mailto):
    # create vserver for this system test if it doesnt already exist
    if not os.path.isdir('%(vserver_home)s/%(vserver_name)s' % locals()):
        vserver_create(config)(vserver_name, distro, mailto)

def stop_vservers(prefix = 'plc', exempt = []):
   	
    # stop all running vservers
    vserver_stat = "vserver-stat | grep %(prefix)s | awk '{print$8}'" % locals()
    (stdin, stdout, stderr) = os.popen3(vserver_stat)
    vservers = [line.strip() for line in stdout.readlines()]
    vservers = filter(lambda x: x not in exempt, vservers)  		
    for vserver in vservers:
	try: 
	    utils.header("Stopping %(vserver)s " % locals())
	    stop_cmd = "vserver %(vserver)s stop" % locals()
	    (status, output) = commands("vserver %(vserver)s stop" % locals())		
	except: 
	    print "Failed to stop %(vserver)s" % locals()
	    utils.header("%s" % traceback.format_exc())

def cleanup_vservers(max_vservers, vserver_home, vserver_basename):
    # only keep the newest MAX_VSERVERS 
    vservers = os.listdir("%(vserver_home)s" % locals())
    valid_vservers = lambda vserver: vserver.startswith(vserver_basename) and os.path.isdir(vserver)
    vservers = filter(valid_vservers, vservers)
    vservers.sort()
    vservers.reverse()
    expired_vservers = vservers[max_vservers:]
    for vserver in expired_vservers:
        utils.header("Deleting vserver: %(vserver)s" % locals(), logfile = config.logfile)
        #vserver_delete()(vserver)

usage="""
Usage: %prog [options]   
"""
parser = OptionParser(usage=usage,add_help_option = False)
parser.add_option("-v", "--vserver", help = "Vserver where tests should run")
parser.add_option("-d", "--distro", help = "Fedora distro to use")
parser.add_option("-p", "--plcname", help = "Which plc do we use (from config file)")
parser.add_option("-m", "--mailto", help = "Vserver build mailto address")

# Define globals
# Determine vserver name, distribution and mailto
# The distribution and current date will be part of of the vserver name  
MAX_VSERVERS =  3
VSERVER_HOME = '/vservers/'
VSERVER_BASENAME = 'plc'
distro = 'f8' 
# use todays date and defaults to determine which vservers to run tests in 
year, month, day = localtime()[:3]
YEAR, MONTH, DAY = [str(x) for x in [year,month,day]]
DATE = ".".join([YEAR, MONTH, DAY])
vserver_name = "%(VSERVER_BASENAME)s-%(distro)s-%(DATE)s" % locals()

(options, args) = parser.parse_args()
# choose which distros to use 
if options.distro is not None:  distros = [options.distro]
else: distros = ['f8']

# did the user specify a vserver or plc
vserver_names = []
if options.vserver is not None: 
    vserver_name = options.vserver
    vserver_names.append(vserver_name)
	  
if options.plcname is not None: plc_name = options.plcname
else: plc_name = 'TestPLC' 

# who gets emailed
if options.mailto is not None: mailto = options.mailto
else: mailto = 'tmack@cs.princeton.edu'     

if not options.vserver:
    for distro in distros:
        vserver_names.append("%(VSERVER_BASENAME)s-%(distro)s-%(DATE)s" % locals())
	
stop_vservers(exempt = vserver_names)

for vserver_name in vserver_names:
    try: 	
	# Setup configuration 
	logfile_dir = "/var/log/qaapi/%(vserver_name)s" % locals()
	config = Config(logdir = logfile_dir)
	config.load("qa/qa_config.py")	
	
        config.plcs[plc_name]['vserver'] = vserver_name
	config.plcs[plc_name]['host'] = config.hostname
	config.plcs[plc_name]['ip'] = config.ip
	config.plcs[plc_name].update_ip()
	person_email = config.persons.values()[0]['email']

	# Set plc configuration options
	config_options = {}
	for service in ['API', 'WWW', 'BOOT',' DB']:
	    config_options['PLC_'+service+'_HOST'] = config.plcs[plc_name]['ip']
            config_options['PLC_'+service+'_IP'] = config.plcs[plc_name]['ip']	
	config_options['PLC_ROOT_USER'] = 'root@localhost.localdomain'
	config_options['PLC_ROOT_PASSWORD'] = 'root'
	
	# Set node configuration options
	nodelist = ['vm1.paris.cs.princeton.edu']
	node_tests = ['node_cpu_sched.py', 'pf2test.pl' ]
	slice = config.slices['ts_slice1']
	
        steps = {}
	steps[1] = Step("Create vserver %s" % vserver_name, create_vserver, 
			(vserver_name, VSERVER_HOME, mailto), config.logfile.filename)
	steps[2] = Step("Mount plc %s " % plc_name,  config.plcs[plc_name].commands, 
			("/sbin/service plc mount",), config.logfile.filename)
	steps[3] = Step("Configure plc %s" % plc_name, plc_configure(config), (plc_name, config_options,),
			config.logfile.filename)
	steps[4] = Step("Start plc %s " % plc_name, plc_start(config), (plc_name,),
			config.logfile.filename)
	steps[5] = Step("Add test data", add_test_data(config), (plc_name,), config.logfile.filename)
	steps[6] = Step("Sync person public key", sync_person_key(config), (person_email,),
			config.logfile.filename, False)
	# XX fix logfile parameter
	step_method = api_unit_test(config) 
	#steps[7] = Step("API unit test", step_method, (plc_name,), step_method.logfile.filename, False)

	for node in nodelist:
	    if not node in config.nodes.keys(): continue
	    node = config.nodes[node] 	
	    node['vserver'] = vserver_name 
	    step_num = max(steps.keys()) + 1

	    # Boot node
      	    steps[step_num] = Step("Boot node %s" % node['hostname'], boot_node(config),
				   (plc_name, node['hostname']), node.logfile.filename)
	    
	    # Check if node is fully booted
	    ready_step = Step("Check %s is ready" % node['hostname'], node.is_ready, (), node.logfile.filename)
	    steps[step_num].next_steps.append(ready_step)

	    # Download test scripts
	    download_scripts = Step("Download test scripts onto %s" % node['hostname'], node.download_testscripts,
			       	    (), config.logfile.filename)
	    steps[step_num].next_steps.append(download_scripts)

 		 
	    # XX fix logfile parameter
	    # XX node_run_tests should only run the test, download test on node before calling node_run_test
	    for test in node_tests:
		# Create a separate logfile for this script
        	log_filename = "%s/%s-%s.log" % (config.logfile.dir, test, node['hostname'])
		test_logfile = Logfile(log_filename)
	        step_method = node_run_tests(config, test_logfile) 
		test_step = Step("%s test on node %s" % (test, node['hostname']), 
				 step_method, (node['hostname'], plc_name, test), 
				 step_method.logfile.filename, False)
	        steps[step_num].next_steps.append(test_step)  	

	    # enter test slice
	    step_num = step_num + 1
	    steps[step_num] = Step("Enter slice %s on %s" % (slice['name'], node['hostname']),
				   node.slice_commands, ("echo `whoami`@`hostname`", slice['name']),
				   node.logfile.filename, False)
	   	     
	    # Copy contents of /var/log
	    step_num = step_num + 1
	    steps[step_num] = Step("Get %s logs" % node['hostname'], node.get_logs, (),
	                           node.logfile.filename, False)
	      
	# Now that all the steps are defined, run them
	order = steps.keys()
	order.sort()
	results = {}
	for num in order:
	    steps[num].run()
	    steps[num].notify_contacts()
	    if steps[num].fatal and not steps[num].passed:
		break	
	
	# Generate summary email
	to = ["qa@planet-lab.org"]
	subject = "PLC - %(distro)s - %(DATE)s QA summary" % locals()
	body = """
	The following are the results of QA tests for %(DATE)s %(distro)s MyPLC.\n\n""" % locals()
	
	utils.header("Sending summary email")
	# add results to summary body
	for num in order:
	    step = steps[num]
	    body += step.get_results()
	 
	sendmail(to, subject, body) 	
	sendmail(['tmack@cs.princeton.edu'], subject, body) 
    except:
        utils.header("ERROR %(vserver_name)s tests failed" % locals(), logfile = config.logfile)	
        utils.header("%s" % traceback.format_exc(), logfile = config.logfile)

