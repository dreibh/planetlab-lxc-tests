#!/usr/bin/python
#
# Sample myplc testing script that makes use of 
# qaapi modules. 
import sys
from pprint import pprint
from qa.Config import Config
from qa.tests.plc_configure import plc_configure
from qa.tests.plc_start import plc_start
from qa.tests.add_test_data import add_test_data
from qa.tests.sync_person_key import sync_person_key
from qa.tests.boot_node import boot_node
from qa.tests.get_boot_state import get_boot_state
from qa.tests.node_remote_call import node_remote_call
from qa.tests.access_slice import access_slice

config = Config()
node = config.TEST_NODE_HOSTNAME_1
person = config.TEST_PERSON_EMAIL

#plc_configure()()
#plc_start()()

# Add test site, node, person and slice data
# Adds slice to node and person to slice 
add_test_data()()

# Update plc with tests user's current public key
sync_person_key()(person)

# exit for now untill we get node booted with correct network
sys.exit(0)
# Boot test node and confirm boot state
boot_node()(node)
if get_boot_state()(node) not in ['boot']:
    raise Exception, "%(node)s not fully booted" % locals()

# Restart node manager on the node
priv_key_path = "/etc/planetlab/root_ssh_key.rsa" % locals() 
restart_nm = 'service nm restart'	
node_remote_call(priv_key_path, node, restart_nm)

# Try to access the test  slice on the test node
email = config.TEST_PERSON_EMAIL
slice = config.TEST_SLICE_NAME
access_slice(email, slice, node)
   
