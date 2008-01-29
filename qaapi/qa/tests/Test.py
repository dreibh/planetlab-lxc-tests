import sys, os
from types import *
from pprint import pprint

# Add qa root directory to the path to make
# imports easier 
path = os.path.dirname(os.path.abspath(__file__))
path_parts = path.split(os.sep)
sys.path.append(os.sep.join(path_parts[:-2]))

from qa import utils
from qa.logger import log
from qa.Config import Config

class Test:
    """
    Base class for all QA test functions. At a minimum all tests
    must define:

    call(arg1, arg2, ...): method body
    """

    accepts = []
    returns = bool
    status = "current" 

    def call(self, *args):
	"""
  	Method body for test functions. Must override.
	"""
	return True

    def __init__(self, config = Config()):
	self.name = self.__class__.__name__
	self.path=os.path.abspath(os.path.dirname(sys.argv[0]))
	self.config = config
	self.errors = []


    def __call__(self, *args, **kwds):
	"""
	Main entry point for test functions. logs methods
	"""

	#(min_args, max_args, defaults) = self.args()
	
	# Check that the right number of arguments were passed in
        #if len(args) < len(min_args) or len(args) > len(max_args):
        #    raise Exception#, (len(args), len(min_args), len(max_args))

	module = self.__class__.__module__.replace(".", os.sep)
	file = self.path + os.sep + module + ".py"
	try:
	    result = self.call(*args, **kwds)
	except NameError:
	    command = "%s %s" % (file, " ".join(args))
	    utils.header(command)
	    (stdout, stderr) = utils.popen(command)
	    print "".join(stdout)
	    result = None
 
	return result	
	    

    def args(self):
        """
        Returns a tuple:

        ((arg1_name, arg2_name, ...),
         (arg1_name, arg2_name, ..., optional1_name, optional2_name, ...),
         (None, None, ..., optional1_default, optional2_default, ...))

        That represents the minimum and maximum sets of arguments that
        this function accepts and the defaults for the optional arguments.
        """

        # Inspect call. Remove self from the argument list.
        max_args = self.call.func_code.co_varnames[1:self.call.func_code.co_argcount]
        defaults = self.call.func_defaults
        if defaults is None:
            defaults = ()

        min_args = max_args[0:len(max_args) - len(defaults)]
        defaults = tuple([None for arg in min_args]) + defaults

        return (min_args, max_args, defaults)
