#!/usr/bin/python

import os, sys
import traceback
from Test import Test
from qa import utils
from qa.PLCs import PLC, PLCs

class plc_stop(Test):
    """
    Installs a myplc
    """

    def call(self, plc_name):
	
        # Get plc qa config
        plc = PLC(self.config)
        plcs = getattr(self.config, 'plcs', [])
        for p in plcs:
            if p['name'] in [plc_name]:
                plc.update(p)

 	command = " /sbin/service plc stop "
	if self.config.verbose:
	    utils.header(command)
	
	(status, output) = plc.commands(command)

	if self.config.verbose:
	    utils.header(output)

	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_stop()(*args)	
