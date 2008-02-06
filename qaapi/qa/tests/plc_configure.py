#!/usr/bin/python
import os, sys
import traceback
from Test import Test
from qa import utils

class plc_configure(Test):
    """
    Configure the myplc from config options in config file
    """

    def call(self, plc_config_option=None, plc_config_value=None):
	
	services = ['API', 'DB', 'WWW', 'BOOT']
	plc_options = [] 
	# Get plc configuration variables
	if plc_config_option is not None and \
	   plc_config_value  is not None:
	    # Set option passed in from user
	    plc_options.append((plc_config_option, plc_config_value))
	else:
	    # Use hostname and ip of host we are running on
	    for service in services:
		host_option = 'PLC_%(service)s_HOST' % locals()
	        ip_option = 'PLC_%(service)s_IP' % locals() 
		plc_options.append((host_option, self.config.hostname))
		plc_options.append((ip_option, self.config.ip))	
	    # Load any other options found in config file
	    for attr in dir(self.config):
	        if attr.startswith('PLC'):
		    plc_options.append((attr, getattr(self.config, attr)))
		
	# Write temporary plc-config file
	tmpname = '/tmp/plc-config-tty-%d' % os.getpid()
	fileconf = open(tmpname, 'w')
	for (option, value) in plc_options:
	    fileconf.write('e %s\n%s\n' % (option, value) )
	fileconf.write('w\nq\n')
	fileconf.close()

	# Update plc config file
	command = "plc-config-tty < %(tmpname)s" % locals()
	if self.config.verbose:
	    utils.header(command)	 	
        (stdout, stderr) = utils.popen(command)
        (stdout, stderr) = utils.popen("rm %s" % tmpname)

	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_configure()(*args)
