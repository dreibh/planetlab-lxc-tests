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

def main(args):
    if len(args) > 0:
        config = Config(args[0])
    else:
        config = Config()
    config.load("qa/qa_config.py")

    plc_configure(config)("TestPLC")
    plc_start(config)()

    # Add test site, node, person and slice data
    # Adds slice to node and person to slice 
    config.update_api()
    add_test_data(config)()

    # Update plc with tests user's current public key
    # person = config.TEST_PERSON_EMAIL
    # sync_person_key(config)(person)


    sys.exit(0)
    # Boot test node and confirm boot state
    boot_node(config)(node)

    # Restart node manager on the node
    restart_nm = 'service nm restart'	
    node_remote_call(node, restart_nm)

    # Try to access the test  slice on the test node
    email = config.TEST_PERSON_EMAIL
    slice = config.TEST_SLICE_NAME
    access_slice(email, slice, node)

    # Run node tests
    node_run_tests(config)(node)

if __name__ == '__main__':
    main(sys.argv[1:])
