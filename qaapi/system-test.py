#!/usr/bin/python
import commands
import os
import sys
from random import Random
from time import localtime
from qa.utils import commands 
from qa.Config import Config 
from qa.tests.vserver_create import vserver_create
from qa.tests.vserver_delete import vserver_delete
from qa.tests.plc_configure import plc_configure
from qa.tests.plc_start import plc_start
from qa.tests.add_test_data import add_test_data
from qa.tests.sync_person_key import sync_person_key
from qa.tests.boot_node import boot_node
from qa.tests.get_boot_state import get_boot_state
from qa.tests.node_remote_call import node_remote_call
from qa.tests.access_slice import access_slice
random = Random()

def randint(min = 0.0, max = 1.0):
    return float(min) + (random.random() * (float(max) - float(min))) 

# Determine vserver name, distribution and mailto
# The distribution and current date will be part of of the vserver name  
MAX_VSERVERS =  5
VSERVER_HOME = '/vservers/'
VSERVER_BASENAME = 'plc'
WORKDIR = '/tmp/'
SVNPATH='http://svn.planet-lab.org/svn/tests/trunk/'
TEST_MODULE = 'qaapi'
YEAR, MONTH, DAY = [str(x) for x in localtime()[:3]]
DATE = ".".join([YEAR, MONTH, DAY])
FCDISTRO = 'f8'  
TEST_VSERVER = VSERVER_BASENAME + "-"+ FCDISTRO + "-" + DATE
VSERVER_PATH = VSERVER_HOME +os.sep+ TEST_VSERVER
MAILTO = 'tmack@cs.princeton.edu'
PLCNAME = 'TestPLC'


# Setup configuration 
config = Config()
config.load("qa/config.py")	
config.plcs[PLCNAME]['vserver'] = TEST_VSERVER
config.plcs[PLCNAME]['ip'] = config.ip
config.plcs[PLCNAME]['api_path'] = ""
config.plcs[PLCNAME]['port'] = str(randint(49152, 65535))
config.plcs[PLCNAME].config.update_api(config.plcs[PLCNAME])

# create a vserer for this system test
vserver_create(config)(TEST_VSERVER, FCDISTRO, MAILTO)

# configure the plc in this vserver
plc_configure(config)(PLCNAME)
plc_start(config)(PLCNAME)

# Add test site, node, person and slice data
# Adds slice to node and person to slice 
add_test_data(config)(PLCNAME)
person_email = config.persons.values()[0]['email']
sync_person_key(config)(person_email)

# Boot test node and confirm boot state
node_hostname = config.nodes.values()[0]['hostname'] 
boot_node(config)(node_hostname)

# remove old vsevers
# only keep the newest MAX_VSERVERS 
vserver_basepath = "%(VSERVER_HOME)s/%(VSERVER_BASENAME)s" 
vservers = os.listdir("%(vserver_basepath)s*" % locals())
vservers.sort()
vservers.reverse()
deleted_vservers = vservers[5:]
for vserver in deleted_vservers:
    utils.header("Deleting vserver: %(vserver)s" % locals())	
    #vserver_delete()(vserver)
 
