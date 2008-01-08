import sys, os
from types import *
from qa import utils
from qa.logger import log

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

    def __init__(self, config):
	self.name = self.__class__.__name__
	self.path=os.path.dirname(sys.argv[0])
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
		
	result = self.call(*args, **kwds)
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
