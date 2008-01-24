import os, sys
from qa import utils
from Test import Test

class sync_person_key(Test):
    """
    Make sure specified users public key on file matches whats 
    recorded at plc. Create a public/private keypair for the 
    specified user if one doesnt exist already.	 
    """

    def make_keys(path, name):
        if not os.path.isdir(path):
            os.mkdir(path)
        key_path = path + os.sep + name
        command = "ssh-keygen -f %(key_path)s -t rsa -N ''"  % locals()
        (stdout, stderr) = utils.popen(command)

    def call(self, email):
	api = self.config.api
	auth = self.config.auth
	email_parts = email.split("@")
	keys_filename = email_parts[0]
	keys_path = self.config.KEYS_PATH 
	private_key_path = keys_path + os.sep + keys_filename
	public_key_path = private_key_path + ".pub"
	
	# Validate person
	persons = api.GetPersons(auth, [email], ['person_id', 'key_ids'])
	if not persons:
	    raise Exception, "No such person %(email)s"
	person = persons[0]

	# make keys if they dont already exist 	
	if not os.path.isfile(private_key_path) or \
	   not os.path.isfile(public_key_path):
	    # Make new keys
	    self.make_keys(keys_path, keys_filename)
	    if self.config.verbose:
		utils.header("Made new key pair %(private_key_path)s %(public_key_path)s " %\
		locals())
	    
	# sync public key  
	public_key_file = open(public_key_path, 'r')
	public_key = public_key_file.readline()
		
	keys = api.GetKeys(auth, person['key_ids'])
	if not keys:
	    # Add current key to db
	    key_fields = {'type': 'rsa',
			  'key': public_key}
	    api.AddPersonKey(auth, person['person_id'], key_fields)
	    if self.config.verbose:
		utils.header("Added public key in %(public_key_path)s to db" % locals() )
	else:
	    # keys need to be checked and possibly updated
	    key = keys[0]
	    if key['key'] != public_key:
		api.UpdateKey(auth, key['key_id'], public_key)
		if self.config.verbose:
		    utils.header("Updated plc with new public key in %(public_key_path)s " % locals())
	    else:
	  	if self.config.verbose:
		    utils.header("Key in %(public_key_path)s matchs public key in plc" % locals())    	 		

if __name__ == '__main__':
    args = typle(sys.argv[1:])
    sync_user_key()(*args)	    	