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
	plc = self.config.get_plc(plc_name)
 	command = " /sbin/service plc stop "
	if self.config.verbose:
	    utils.header(command, logfile = self.config.logfile)
	
	(status, output) = plc.commands(command)

	if self.config.verbose:
	    utils.header(output, logfile = self.config.logfile)

	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_stop()(*args)	
