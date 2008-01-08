
import os, sys
import traceback
from qa import utils
from qa.Test import Test

class install(Test):
    """
    Installs a myplc
    """

    def call(self, url=None):
	
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
        (stdin, stdout, stderr) = os.popen3('set -x; rpm -Uvh ' + url)
        self.errors = stderr.readlines()
        if self.errors: raise "\n".join(self.errors)	
	
	return 1
