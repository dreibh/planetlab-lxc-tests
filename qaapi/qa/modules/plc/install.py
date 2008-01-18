
import os, sys
import traceback
from qa import utils
from qa.Test import Test

class install(Test):
    """
    Installs a myplc
    """

    def call(self, url=None, system_type, root_dir):
	
	url_path = self.config.path
	# Determine url
	if not url:
	    try:

		print self.config.path 
	        url_file = open("%s/URL" % url_path)
	        url = url_file.read().strip()
	        url_file.close()
	    except IOError:
	  	pass 
	if not url:
	    print "URL not specified" 
	    sys.exit(1)	 
	     	
	# Save url
	if self.config.verbose:
	    utils.header('Saving current myplc url into %s/URL' % url_path)
	fsave=open('%s/URL' % url_path, "w")
 	fsave.write(url+'\n')
	fsave.close()
	
	# Instal myplc from url    	 
	if self.config.verbose:
	    utils.header('Installing myplc from url %s' % url)

	# build command
	full_command = ""
	if system_type in ['vserv', 'vserver']:
	    full_command += " vserver %(root_dir)s exec "
	elif system_type in ['chroot']:
	    pass
	else:
	    raise Exception, "Invalid system type %(system_type)s" % locals() 

        (stdout, stderr) = utils.popen(full_command + " rpm -Uvh " + url)
	if self.config.verbose:
	    utils.header("\n".join(stdout))
	
	return 1
