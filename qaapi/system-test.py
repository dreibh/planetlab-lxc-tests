#!/usr/bin/python
import commands
import os
import sys
from optparse import OptionParser
from random import Random
from time import localtime
from qa.utils import commands
from qa import utils 
from qa.Config import Config 
from qa.tests.vserver_create import vserver_create
from qa.tests.vserver_delete import vserver_delete
from qa.tests.plc_configure import plc_configure
from qa.tests.plc_stop import plc_stop
from qa.tests.plc_start import plc_start
from qa.tests.add_test_data import add_test_data
from qa.tests.sync_person_key import sync_person_key
from qa.tests.boot_node import boot_node
from qa.tests.access_slice import access_slice

def run_system_tests(config, vserver_name, plc_name):
    # configure the plc in this vserver
    config.plcs[plc_name]['vserver'] = vserver_name
    config.plcs[plc_name]['host'] = config.hostname
    config.plcs[plc_name]['ip'] = config.ip
    config.plcs[plc_name].update_ip()
	
    plc_configure(config)(plc_name)
    options = {}
    for service in ['API', 'WWW', 'BOOT',' DB']:
        options['PLC_'+service+'_HOST'] = config.plcs[plc_name]['ip']
        options['PLC_'+service+'_IP'] = config.plcs[plc_name]['ip']
    plc_configure(config)(plc_name, options)
    plc_start(config)(plc_name)

    # Add test site, node, person and slice data
    # Adds slice to node and person to slice 
    add_test_data(config)(plc_name)
    plc_stop(config)(plc_name)
    plc_start(config)(plc_name)
    person_email = config.persons.values()[0]['email']
    sync_person_key(config)(person_email)

    # Boot test node and confirm boot state
    nodelist = ['vm1.paris.cs.princeton.edu']
    for node in nodelist:
        if not node in config.nodes.keys():
            continue
        node = config.nodes[node]
        node['vserver'] = config.plcs[plc_name]['vserver']
        boot_node(config)(plc_name, node['hostname'])

def create_vserver(vserver_name, vserver_home, mailto):
    # create vserver for this system test if it doesnt already exist
    if not os.path.isdir('%(vserver_home)s/%(vserver_name)s' % locals()):
        vserver_create(config)(vserver_name, distro, mailto)

def cleanup_vservers(max_vservers, vserver_home, vserver_basename):
    # only keep the newest MAX_VSERVERS 
    vservers = os.listdir("%(vserver_home)s" % locals())
    valid_vservers = lambda vserver: vserver.startswith(vserver_basename)
    vservers = filter(valid_vservers, vservers)
    vservers.sort()
    vservers.reverse()
    expired_vservers = vservers[5:]
    for vserver in expired_vservers:
        utils.header("Deleting vserver: %(vserver)s" % locals())
        #vserver_delete()(vserver)

usage="""
Usage: %prog [options]   
"""
parser = OptionParser(usage=usage,add_help_option = False)
parser.add_option("-v", "--vserver", help = "Vserver where tests should run")
parser.add_option("-d", "--distro", help = "Fedora distro to use")
parser.add_option("-p", "--plcname", help = "Which plc do we use (from config file)")
parser.add_option("-m", "--mailto", help = "Vserver build mailto address")

(options, args) = parser.parse_args()

# choose which distros to use 
if options.distro is not None:  distros = [options.distro]
else: distros = ['f7']
# did the user specify a vserver or plc
vserver_name = options.vserver
if options.plcname is not None: plc_name = options.plcname
else: plc_name = 'TestPLC' 
# who gets emailed
if options.mailto is not None: mailto = options.mailto
else: mailto = 'tmack@cs.princeton.edu'     

# Define globals
# Determine vserver name, distribution and mailto
# The distribution and current date will be part of of the vserver name  
MAX_VSERVERS =  5
VSERVER_HOME = '/vservers/'
VSERVER_BASENAME = 'plc'

# Setup configuration 
config = Config()
config.load("qa/qa_config.py")	

if vserver_name:
    # run tests in vserver specified by user
    create_vserver(vserver_name, VSERVER_HOME, mailto)	
    run_system_tests(config, vserver_name, plc_name)
else:
    
    # use todays date and defaults to determine which vservers to run tests in 
    year, month, day = localtime()[:3]
    YEAR, MONTH, DAY = [str(x) for x in [year,month,day]]
    DATE = ".".join([YEAR, MONTH, DAY])
    for distro in distros:
        vserver_name = "%(VSERVER_BASENAME)s-%(distro)s-%(DATE)s" % locals()
	create_vserver(vserver_name, VSERVER_HOME, mailto)	
        try: 	
	    run_system_tests(config, vserver_name, plc_name)
        except:
	    utils.header("ERROR %(vserver_name)s tests failed" % locals())	
            raise
	
# remove old vsevers
cleanup_vservers(MAX_VSERVERS, VSERVER_HOME, VSERVER_BASENAME)

