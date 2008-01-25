#!/usr/bin/python

import os, sys
import traceback
from Test import Test
from qa import utils

class plc_stop(Test):
    """
    Installs a myplc
    """

    def call(self):
        
 	command = " /sbin/service plc stop "

	if self.config.verbose:
	    utils.header(command)
	
	(stdout, stderr) = utils.popen(command)

	if self.config.verbose:
	    utils.header("\n".join(stdout))

	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_stop()(*args)	
