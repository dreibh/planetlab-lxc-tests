import os, sys
import traceback
from qa.Test import Test
from qa import utils

class start(Test):
    """
    Starts the myplc service
    """

    def call(self, system_type, vserver_or_root_dir_name):
	
	start_command = " /sbin/service plc start "
	full_command = ""

	if system_type in ['vserv', 'vserver']:
	    full_command += " vserver %(vserver_or_root_dir_name)s exec "
	elif system_type in ['chroot']:
	    pass
	else:
	    raise Exception, "Invalid system type %(system_type)s" % locals()
	
	full_command += start_command 
	full_command = full_command % locals()

	if self.config.verbose:
	    utils.header(full_command)	

	(stdin, stdout, stderr) = os.popen3(full_command)
        self.errors = stderr.readlines()
        if self.errors: raise Exception, "\n".join(self.errors)

	return 1
