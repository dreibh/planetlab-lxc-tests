
import os, sys
import traceback
from Test import Test
from qa import utils

class plc_configure(Test):
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
	    fileconf.write('e %s\n%s\n' % (var, getattr(self.config, var)))
	fileconf.write('w\nq\n')
	fileconf.close()

	mount_command = "/sbin/service plc mount"
	full_command = ""
	if system_type in ['vserv', 'vserver']:
	    full_command += " vserver %(root_dir)s exec " % locals()
	elif system_type in ['chroot']:
	    full_command += " chroot %(root_dir)s " % locals()
	else:
	    raise Exception, "Invalid system type %(sytem_type)s" % locals()

	full_command += " plc-config-tty < %(tmpname)s" % locals()
	commands = [mount_command, full_command]
	for command in commands:
	    if self.config.verbose:
	        utils.header(command)	 	
            (stdout, stderr) = utils.popen(command)
        (stdout, stderr) = utils.popen("rm %s" % tmpname)

	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_configure()(*args)
