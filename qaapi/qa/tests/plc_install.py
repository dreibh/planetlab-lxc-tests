
import os, sys
import traceback
from qa import utils
from Test import Test

class plc_install(Test):
    """
    Installs a myplc
    """

    def call(self, system_type, root_dir, url=None):
	
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
	    utils.header('Installing myplc from url %s' % url)

	# build command
	full_command = ""
	install_command = " rpm -Uvh %(url)s "
	if system_type in ['vserv', 'vserver']:
	    full_command += " vserver %(root_dir)s exec "
	elif system_type in ['chroot']:
	    pass
	else:
	    raise Exception, "Invalid system type %(system_type)s" % locals() 

	full_command += install_command % locals()
        try: (stdout, stderr) = utils.popen(full_command)
	except: (stdout, stderr) = utils.popen("yum localupdate %(url)s")

	if self.config.verbose:
	    utils.header("\n".join(stdout))
	
	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    plc_install()(*args)