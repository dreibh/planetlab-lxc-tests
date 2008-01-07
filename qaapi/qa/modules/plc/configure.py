
import os, sys
import traceback
from qa.Test import Test

class configure(Test):
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
	    fileconf.write('e %s\n%s\n' % (var, self.config[var]))
	fileconf.write('w\nq\n')
	fileconf.close()

	 # set configuration options
	if self.config.verbose: os.system('set -x ; cat %s'%tmpname)
        (stdin, stdout, stderr) = \
            os.popen3('set -x ; chroot /plc/root  plc-config-tty < %s'%tmpname)
        self.errors = stderr.readlines()
        if self.errors: raise "\n".join(self.errors)
        os.system('set -x; rm %s'%tmpname)

	return 1
