#!/usr/bin/env ./qash
#
# Sample myplc testing script that makes use of 
# qaapi modules. 

from pprint import pprint
from qa.Config import Config

config = Config()
sys_type = 'vserver'
vserver_name = 'tmack_test'
vserver_path = '/vservers/%(vserver_name)s/'
url = None
node = config.TEST_NODE_HOSTNAME_1


#plc.install(sys_type, vserver_name, url)
#plc.config(sys_type, vserver_name)
#plc.start(sys_type, vserver_name)

# Add test site, node, person and slice data
# Adds slice to node and person to slice 
#plc.add_test_data()

# Boot test node and confirm boot state
#plc.boot_node(node)
#if plc.get_boot_state(node) not in ['boot']:
#    raise Exception, "%(node)s not fully booted" % locals()

# Restart node manager on the node
#priv_key_path = "%(vserver_path)/etc/planetlab/root_ssh_key.rsa" % locals() 
#restart_nm = 'service nm restart'	
#plc.remote_call(priv_key_path, node, restart_nm)

# Try to access the test  slice on the test node
#email = config.TEST_PERSON_EMAIL
#slice = config.TEST_SLICE_NAME
#plc.access_slice(email, slice, node)
   
