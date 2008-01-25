#!/usr/bin/python

import traceback
import sys
from Test import Test
from qa import utils

class plc_start(Test):
    """
    Starts the myplc service
    """

    def call(self):
	
	command = " /sbin/service plc start "

	if self.config.verbose:
	    utils.header(command)	

	(stdout, stderr) = utils.popen(command)
	
	if self.config.verbose:
            utils.header("".join(stdout))
         
	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_start()(*args)
