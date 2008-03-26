#!/usr/bin/python

import os, sys
import traceback
from Test import Test
from qa import utils

class plc_uninstall(Test):
    """
    Completely removes the installed myplc
    """

    def call(self, plc_name = None, remove_all = False):

	# Get plc configuration from config
	plc = self.config.get_plc(plc_name)	
	command = "/sbin/service plc safestop && rpm -e myplc " 
	if remove_all:
	    command += " && rm -rf /plc/data" 

	if self.config.verbose:
            utils.header("Removing myplc")
	    utils.header("\n".join(command))
	
	(status, output) = plc.commands(command)
		
	if self.config.verbose:
	    utiils.header("\n".join(output))
	
	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_unistall()(*args)
