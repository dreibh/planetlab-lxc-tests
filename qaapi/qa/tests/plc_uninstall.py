#!/usr/bin/python

import os, sys
import traceback
from Test import Test
from qa import utils

class plc_uninstall(Test):
    """
    Completely removes the installed myplc
    """

    def call(self, remove_all = False):
	
	command = "/sbin/service plc safestop; rpm -e myplc " 
	if remove_all:
	    command += " && rm -rf /plc/data" 

	if self.config.verbose:
            utils.header("Removing myplc")

	(stdout, stderr) = utils.popen(command)
	if self.config.verbose:
	    utils.header("\n".join(stdout))
		
	(stdout, stderr) = utils.popen(command)
	if self.config.verbose:
	    utiils.header("\n".join(stdout))
	
	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_unistall()(*args)
