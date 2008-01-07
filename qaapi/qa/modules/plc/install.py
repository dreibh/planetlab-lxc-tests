
import os, sys
import traceback
from qa.Test import Test


class install(Test):
    """
    Installs a myplc
    """

    def call(self, url=None):
	
	# Determine url 
	if not url:
	    url_file = open("%s/URL" % self.path)
	    url = url_file.read().strip()
	    url_file.close()
	
	# Save url
	if self.config.verbose:
	    utils.header('Saving current myplc url into %s/URL' % self.path)
	fsave=open('%s/URL' % self.path, "w")
 	fsave.write(url+'\n')
	fsave.close()
	
	# Instal myplc from url    	 
	if self.config.verbose:
	    utils.header('Installing myplc from url %s' % url)
        (stdin, stdout, stderr) = os.popen3('set -x; rpm -Uvh ' + self.url)
        self.errors = stderr.readlines()
        if self.errors: raise "\n".join(self.errors)	
	
	return 1
