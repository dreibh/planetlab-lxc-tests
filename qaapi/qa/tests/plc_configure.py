#!/usr/bin/python
import os, sys
import traceback
from Test import Test
from qa import utils
import tempfile

class plc_configure(Test):
    """
    Configure the myplc from config options in config file
    """

    def call(self, plc_config_option=None, plc_config_value=None):
	
	services = ['API', 'DB', 'WWW', 'BOOT']
	plc_options = [] 
        # Turn off plc (for good measure)
	command = "/sbin/service plc stop"
	if self.config.verbose: utils.header(command)
        (stdout, stderr) = utils.popen(command)

	# mount plc (need to do this optionally, as we do not want this for myplc-native)
	command = "/sbin/service plc mount"
	if self.config.verbose: utils.header(command)
        (stdout, stderr) = utils.popen(command)

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
        tmpfconf, tmpfname = tempfile.mkstemp(".config","plc-config-tty")
	if self.config.verbose:
            utils.header("generating temporary config file %(tmpfname)s"%locals())
	for (option, value) in plc_options:
            os.write(tmpfconf, 'e %s\n%s\n' % (option, value))
        os.write(tmpfconf,'w\nq\n')
	os.close(tmpfconf)
        
        # configure plc
	command = "plc-config-tty < %(tmpfname)s" % locals()
	if self.config.verbose: utils.header(command)
        (stdout, stderr) = utils.popen(command)

	# clean up temporary conf file
	if self.config.verbose: utils.header("removing %(tmpfname)s"%locals())
        os.unlink(tmpfname)

	# umount plc (need to do this optionally, as we do not want this for myplc-native)
	command = "/sbin/service plc umount"
	if self.config.verbose: utils.header(command)
        (stdout, stderr) = utils.popen(command)

	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_configure()(*args)
