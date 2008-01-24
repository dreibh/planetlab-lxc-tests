import os, sys
import time
from qa import utils
from Test import Test

class check_boot_state(Test):
    """
    Continually checks the boot_state of the specified node until
    either the node reaches boot, the node reaches debug or the 
    timeout is reached. 

    Timeout represents the ammout of time (in minutes) we should 
    continue trying before quitting.

    Sleep represnet the ammount of time (in seconds) to wait in 
    between checks.

    Returns the boot state of the node.
    """
    def call(self, hostname, timeout = 5, sleep = 30):
	exit = False
	api = self.config.api
	auth = self.config.auth
	
	# Validate hostname
	nodes = api.GetNodes(auth, [hostname], ['hostname'])
	if not nodes:
	    raise Exception, "No such hostname %(hostname)s" % locals()
	
	start_time = time.time()
	end_time = start_time + (timeout * 60)
	
	while not exit:
	    nodes = api.GetNodes(auth, [hostname], ['boot_state'])
	    node = nodes[0]
	    boot_state = node['boot_state']
	    if self.config.verbose:
	  	utils.header("%(hostname)s boot_state is %(boot_state)s" % locals()) 

	    if boot_state in ['boot', 'debug']:
		exit = True
	    elif time.time() < end_time:
		time.sleep(sleep)
	    else:
		exit = True


	if self.config.verbose:
	    if boot_state in ['boot']:
		utils.header("%(hostname)s correctly installed and booted" % locals())
	    else:
		utils.header("%(hostname)s not fully booted" % locals())

	return boot_state

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    check_boot_state()(*args)
