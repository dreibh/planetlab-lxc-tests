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
	plc = PLC(self.config)
	plcs = getattr(self.config, 'plcs', [])
	for p in plcs:
	    if p['name'] in [plc_name]:
		plc.update(p)	
	 	
	command = "/sbin/service plc start "
	if self.config.verbose:
	    utils.header(command)	
	(status, output) = plc.commands(command)

	if self.config.verbose:
	    utils.header(output)
	
	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_start()(*args)
