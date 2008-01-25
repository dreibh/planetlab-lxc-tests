#!/usr/bin/python

import os, sys
import traceback
from qa import utils
from Test import Test

class plc_install(Test):
    """
    Installs a myplc
    """

    def call(self, url=None):
	
	url_path = self.config.path
	# Determine url
	if not url:
	    try:
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
	    utils.header('Downloading myplc from url %s' % url)

	url_parts = url.split(os.sep)
	rpm_file = url[-1:]
	download_cmd = "wget %(url)s /tmp/%(rpm_file)s" % locals()

	# build command
	rpm_install = "rpm -Uvh /tmp/%(rpm_file)s" % locals()
	yum_install = "yum -y localinstall /tmp/%(rpm_file)s" % locals()

	if self.config.verbose:
	    utils.header("Trying: %(rpm_install)s" % locals())
        try: 
   	    (stdout, stderr) = utils.popen(rpm_install)
	except:
	    if self.config.verbose:
		utils.header("Trying %(yum_install)s" % locals()) 
	    (stdout, stderr) = utils.popen(yum_install)

	if self.config.verbose:
	    utils.header("\n".join(stdout))
	
	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_install()(*args)
