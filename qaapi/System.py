from optparse import OptionParser
from logger import log 
import utils
import os, sys
import traceback
from Config import Config


class System:
    """
    Installs a myplc and starts the service. This is required
    before any other tests can take place.
    """	

    def __init__(self):
	self.path=os.path.dirname(sys.argv[0])
	self.config = Config()
	self.errors = []

    def check(method, fatal = True):
	"""
	Check if there were errors
	"""
	def wrapper(*args, **kwds):
	    result = method(*args, **kwds)
	    if self.errors:
	        print "\n".join(self.errors)
	        if fatal: sys.exit(1)
	    return result

    @check	
    @log
    def get_url(self):
	"""
	Determine current url and save it
	"""
	try:
	    if len(self.args) == 1: self.url = self.args[0]
	    else:
		url_file=open("%s/URL"%self.path)
                self.url=url_file.read().strip()
                url_file.close()
		
	    if self.options.verbose:
	    	utils.header('Saving current myplc url into %s/URL' % self.path)
	    fsave=open('%s/URL'%self.path,"w")
            fsave.write(url+'\n')
  	    fsave.close()	
	except:
	    self.errors = ["Cannot determine myplc url"]
            self.parser.print_help()
	    raise

    @check
    @log
    def install_plc(self):
	"""
	Install the myplc
	"""
	if self.options.verbose:
	    utils.header("Installing myplc from url %s" % self.url)
	(stdin, stdout, stderr) = os.popen3('set -x; rpm -Uvh ' + self.url)
	self.errors = stderr.readlines()
	if self.errors: raise "\n".join(self.errors)
	

    @check
    @log	
    def config_plc(self):
	""" 
	Configure the plc
	"""
	tmpname='/tmp/plc-config-tty-%d'%os.getpid()
        fileconf=open(tmpname,'w')
        for var in [ 'PLC_NAME',
                     'PLC_ROOT_PASSWORD',
                     'PLC_ROOT_USER',
                     'PLC_MAIL_ENABLED',
                     'PLC_MAIL_SUPPORT_ADDRESS',
                     'PLC_DB_HOST',
                     'PLC_API_HOST',
                     'PLC_WWW_HOST',
                     'PLC_BOOT_HOST',
                     'PLC_NET_DNS1',
                     'PLC_NET_DNS2']:
            fileconf.write ('e %s\n%s\n'%(var,config[var]))
        fileconf.write('w\nq\n')
        fileconf.close()

        if self.options.verbose: os.system('set -x ; cat %s'%tmpname)
        (stdin, stdout, stderr) = \
            os.popen3('set -x ; chroot /plc/root  plc-config-tty < %s'%tmpname)
	self.errors = stderr.readlines()
	if self.errors: raise "\n".join(self.errors)
     	os.system('set -x; rm %s'%tmpname)
 
 
    @check 
    @log 
    def start_plc(self):
	""" 
	Start the plc service
        """
	(stdin, stdout, stderr) = os.popen3('set -x ; service plc start')
	self.errors = stderr.readlines()
	if self.errors: raise "\n".join(self.errors)
 
    @check 
    @log  
    def remove_plc(self):
	"""
	Completely remove all traces of myplc install
	"""
	if self.options.verbose:
            utils.header("Removing myplc")
        (stdin, stdout, stderr) = os.popen3('set -x; service plc safestop')
	self.errors = stderr.readlines()
        (stdin, stdout, stderr) = os.popen3('set -x; rpm -e myplc')
	self.errors.extend(stderr.readlines())
        if self.errors: raise "\n".join(self.errors)
	(stdin, stdout, stderr) = os.popen3('set -x; rm -rf  /plc/data')
	self.errors.extend(stderr.readlines())
	if self.errors: raise "\n".join(self.errors)

    def run(self):
	try:
            usage = """usage: %prog [options] [myplc-url]
	    myplc-url defaults to the last value used, 
	    as stored in URL"""
            self.parser=OptionParser(usage=usage)

            #parser.add_option("-d","--display", action="store", dest="Xdisplay", default='bellami:0.0',
            #                  help="sets DISPLAY for vmplayer")
            self.parser.add_option("-v","--verbose", action="store_true", dest="verbose", default=False,
                              help="Run in verbose mode")
            (self.options, self.args) = self.parser.parse_args()
	    
	    self.get_url()
	    self.install_plc()

	except:
	    pass	



if __name__ == 'main':
    System().run()	
