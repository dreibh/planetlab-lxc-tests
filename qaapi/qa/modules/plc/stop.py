import os, sys
import traceback
from qa.Test import Test
from qa import utils

class stop(Test):
    """
    Installs a myplc
    """

    def call(self, system_type, root_dir):

 	stop command = " /sbin/service plc stop "
	full_command = ""
	if system_type in ['vserv', 'vserver']:
	    full_command += " vserver %(root_dir)s exec "
	elif system_type in ['chroot']:
	    pass
	else:
	    raise Exception, "Invalid system type %(system_type)s" locals() 	
	
	full_command += stop_command
	full_command = full_command % locals()

	if self.config.verbose:
	    utils.header(full_command)
	
	(stdout, stderr) = utils.popen(full_command)

	if self.config.verbose:
	    utils.header("\n".join(stdout))

	return 1
