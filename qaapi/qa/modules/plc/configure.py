
import os, sys
import traceback
from qa.Test import Test
from qa import utils

class configure(Test):
    """
    Configure the myplc from config options in config file
    """

    def call(self, system_type, root_dir):
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

	full_command = ""
	if system_type in ['vserv', 'vserver']:
	    full_command += " vserver %(root_dir)s exec "
	elif system_type in ['chroot']:
	    full_commnd += " chroot %(root_dir)s "
	else:
	    raise Exception, "Invalid system type %(sytem_type)s" % locals()

	full_command = full_command + " plc-config-tty < %(tmpname)s" % locals()	 	
        (stdout, stderr) = utils.popen(full_command)
        (stdout, stderr) = utils.popen("rm %s" % tmpname)

	return 1
