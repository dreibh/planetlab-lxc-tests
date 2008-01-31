#!/usr/bin/python
import os, sys
from Test import Test
from qa import utils

class node_remote_call(Test):
    """
    Attempt to connect to a node using the plc root key and
    issue a command.
    """

    def call(self, hostname, command, root_key_path = "/etc/planetlab/root_ssh_key.rsa"):
	if not os.path.isfile(root_key_path):
	    raise Exception, "no such private key file %(root_key_path)s" % locals()
	 
	full_command = "ssh -i %(root_key_path)s root@%(hostname)s %(command)s" % locals()
	if self.config.verbose:
	    utils.header(full_command)
	(stdout, stderr) = utils.popen(full_command)
	
	if self.config.verbose:
	    utils.header("\n".join(stdout))


	return 1 

if  __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_remote_call()(*args)	 		
