#!/usr/bin/python
import os, sys
import traceback
from Test import Test
from qa import utils

class plc_configure(Test):
    """
    Configure the myplc from config options in config file
    """

    def call(self):

	# Get plc configuration variables
	plc_vars = []
	for attr in dir(self.config):
	    if attr.startswith('PLC'):
		plc_vars.append(attr)
		
	# Write temporary plc-config file
	tmpname = '/tmp/plc-config-tty-%d' % os.getpid()
	fileconf = open(tmpname, 'w')
	for var in plc_vars:
	    fileconf.write('e %s\n%s\n' % (var, getattr(self.config, var)))
	fileconf.write('w\nq\n')
	fileconf.close()

	# Update config file
	command = "/sbin/service plc mount && plc-config-tty < %(tmpname)s" % locals()
	if self.config.verbose:
	    utils.header(command)	 	
        (stdout, stderr) = utils.popen(command)
        (stdout, stderr) = utils.popen("rm %s" % tmpname)

	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_configure()(*args)
