import os, sys
import traceback
from Test import Test
from qa import utils

class plc_stop(Test):
    """
    Installs a myplc
    """

    def call(self, system_type, root_dir):
        
 	stop_command = " /sbin/service plc stop "
	full_command = ""
	if system_type in ['vserv', 'vserver']:
	    full_command += " vserver %(root_dir)s exec "
	elif system_type in ['chroot']:
	    pass
	else:
	    raise Exception, "Invalid system type %(system_type)s" % locals() 	
	
	full_command += stop_command % locals()

	if self.config.verbose:
	    utils.header(full_command)
	
	(stdout, stderr) = utils.popen(full_command)

	if self.config.verbose:
	    utils.header("\n".join(stdout))

	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_stop()(*args)	
