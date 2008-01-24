import os, sys
import traceback
from Test import Test
from qa import utils

class plc_uninstall(Test):
    """
    Completely removes the installed myplc
    """

    def call(self, system_type, root_dir):
	
	remove_command = " rpm -e myplc " 
	full_command = ""

	if system_type in ['vserv', 'vserver']:
	    full_command += " vserver %(root_dir)s exec "
	elif system_type in ['chroot']:
	    pass
	else: 
	    raise Exception, "Invalid system type %(system_type)s" % locals()
	 
	if self.config.verbose:
            utils.header("Removing myplc")

	full_command = full_command % locals()
	(stdout, stderr) = utils.popen(full_command + "/sbin/service plc safestop")
	if self.config.verbose:
	    utils.header("\n".join(stdout))
		
        (stdout, stderr) = utils.popen(full_command + remove_command)
        if self.config.verbose:
	    utils.header("\n".join(stdout))

	(stdout, stderr) = utils.popen(full_command + " rm -rf  /plc/data")
	if self.config.verbose:
	    utiils.header("\n".join(stdout))
	
	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_unistall()(*args)
