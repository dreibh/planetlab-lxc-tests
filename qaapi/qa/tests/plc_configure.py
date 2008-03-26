#!/usr/bin/python
import os, sys
import traceback
from Test import Test
from qa import utils
import tempfile
from qa.PLCs import PLC, PLCs

class plc_configure(Test):
    """
    Configure the myplc from config options in config file
    """

    def call(self, plc_name, plc_config_option=None, plc_config_value=None):
	
	# Get plc configuration from config
	plc = self.config.get_plc(plc_name)
	services = ['API', 'DB', 'WWW', 'BOOT']
	plc_options = [] 
        
	# Turn off plc (for good measure)
	command = "/sbin/service plc stop"
	if self.config.verbose: utils.header(command)
        (status, output) = plc.commands(command)

	# mount plc (need to do this optionally, as we do not want this for myplc-native)
	command = "/sbin/service plc mount"
	if self.config.verbose: utils.header(command)
        (status, output) = plc.commands(command)

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
		plc_options.append((host_option, plc['host']))
		plc_options.append((ip_option, plc['ip']))	
	    # Load any other options found in config file
	    for attr in dir(self.config):
	        if attr.startswith('PLC'):
		    plc_options.append((attr, getattr(self.config, attr)))
		
	# Write temporary plc-config file
	# XX use plc instance to copy file
        tmpfconf, tmpfname = tempfile.mkstemp(".config","plc-config-tty", '/usr/tmp/')
	tmpfname_parts = tmpfname.split(os.sep)
	if self.config.verbose:
            utils.header("generating temporary config file %(tmpfname)s"%locals())
	for (option, value) in plc_options:
            os.write(tmpfconf, 'e %s\n%s\n' % (option, value))
        os.write(tmpfconf,'w\nq\n')
	os.close(tmpfconf)
	#plc.scp(tmpfname, "%s:/usr/tmp" % (plc['host']))

        # configure plc
	command = "plc-config-tty < %(tmpfname)s" % locals()
	if self.config.verbose: utils.header(command)
        (status, output) = plc.commands(command)

	# clean up temporary conf file
	# XX use plc instance to copy file
	if self.config.verbose: utils.header("removing %(tmpfname)s"%locals())
        os.unlink(tmpfname)

	# umount plc (need to do this optionally, as we do not want this for myplc-native)
	command = "/sbin/service plc umount"
	if self.config.verbose: utils.header(command)
        (status, output) = plc.commands(command)

	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_configure()(*args)
