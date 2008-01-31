#!/usr/bin/python
import os, sys
import traceback
import time
from Test import Test
from qa import utils

class access_slice(Test):
    """
    Repeatedly attempt to use the specified users credentials to 
    access the specified node on the specified slice.    
    """	

    def call(self, email, slice_name, hostname, timeout=3):
	api = self.config.api
	auth = self.config.auth
 	email_parts = email.split("@")
        keys_filename = email_parts[0]
        keys_path = self.config.KEYS_PATH
        private_key_path = keys_path + os.sep + keys_filename
        public_key_path = private_key_path + ".pub"

	# Validate slice
	slices = api.GetSlices(auth, [slice_name], ['name', 'slice_id', 'node_ids'])
	if not slices:
	    raise Exception, "No such slice %(slice_name)s" % locals()
	slice = slices[0]

	# Validate node
	nodes = api.GetNodes(auth, [hostname], ['hostname', 'node_id', 'slice_ids'])
	if not nodes:
	    raise Exception, "No such node %(hostname)s" % locals()
	node = nodes[0]
	if slice['slice_id'] not in node['slice_ids']:
	    raise Exception, "%(slice_name)s not on %(hostname)s" % locals()  

	# Validate user
	persons = api.GetPersons(auth, ['email'], ['person_id', 'key_ids', 'slice_ids'])
	if not persons:
	    raise Exception, "No such person %(email)s" % locals()
	person = persons[0]
	if slice['slice_id'] not in person['slice_ids']:
	    raise Exception, "%(email)s not in slice %(slice_name)s" % locals()

	# get keys
	if not os.path.isfile(private_key_path) or \
           not os.path.isfile(public_key_path):
	    # keys dont exist, call api.sync_user_key()
	    from qa.modules.api.sync_user_key import sync_user_key
	    sync_user_key()(email)

	# attempt to access slice
	start_time = time.time()
	end_time = start_time + timeout*60
	sleep = 30
	while time.time() <  endtime:
	    if self.config.verbose:
	        utils.header("Trying to connect to %(slice_name)s@%(hostname)s" % locals())
	    ssh_command = "ssh -i %(private_key_path)s %(slice_name)s@%(hostname)s" % locals() 	   
	    host_check = os.system(ssh_command + " hostname ")
	    if host_check == 0:
		if self.config.verbose:
		    utils.header("connecteed to %(slice_name)s@%(hostname)s" % locals())
		return 1
	    else:
		if self.config.verbose:
		    utils.header("failed to connect to %(slice_name)s@%(hostname)s" % locals())		
	    time.sleep(sleep) 		
		
	return 0

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    access_slice()(*args) 	
