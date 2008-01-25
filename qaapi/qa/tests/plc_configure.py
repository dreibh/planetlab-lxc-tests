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
	tmpname = '/tmp/plc-cinfig-tty-%d' % os.getpid()
	fileconf = open(tmpname, 'w')
	for var in [ 'PLC_NAME',
                     'PLC_ROOT_PASSWORD',
                     'PLC_ROOT_USER',
                     'PLC_MAIL_ENABLED',
                     'PLC_MAIL_SUPPORT_ADDRESS',
                     'PLC_DB_HOST',
                     'PLC_API_HOST',
                     'PLC_WWW_HOST',
                     'PLC_BOOT_HOST',
                     'PLC_NET_DNS1',
                     'PLC_NET_DNS2']:
	    fileconf.write('e %s\n%s\n' % (var, getattr(self.config, var)))
	fileconf.write('w\nq\n')
	fileconf.close()

	command = "/sbin/service plc mount && plc-config-tty < %(tmpname)s" % locals()
	if self.config.verbose:
	    utils.header(command)	 	
        (stdout, stderr) = utils.popen(command)
        (stdout, stderr) = utils.popen("rm %s" % tmpname)

	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_configure()(*args)
