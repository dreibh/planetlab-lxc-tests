#!/usr/bin/python

import traceback
import sys
from Test import Test
from qa import utils
from qa.PLCs import PLC, PLCs

class plc_start(Test):
    """
    Starts the myplc service
    """

    def call(self, plc_name = None):

	# Get plc configuration from config
	plc = self.config.get_plc(plc_name)
	command = "/sbin/service plc start "
	if self.config.verbose:
	    utils.header(command)	
	(status, output) = plc.commands(command)

	if self.config.verbose:
	    utils.header(output)

	# Some plcs may fail when trying to start the http/xmlrpc server 
	# because the port is already in use. We must start a server on 
	# another port.
	plc.start_xmlrpc_server()  
  
	
	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_start()(*args)
