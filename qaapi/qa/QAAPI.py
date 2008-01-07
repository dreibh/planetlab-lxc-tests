import sys, os
import traceback
import qa.modules
from qa.Config import Config
from qa.logger import log	

class QAAPI:
   
    modules_path = os.path.realpath(qa.modules.__path__[0])
    methods = []
		
	
    def __init__(self, globals = globals(), config = None, logging=None):
	if config is None: self.config = Config()
	else: self.config = Config(config)

	# Load methods
	real_files = lambda name: not name.startswith('__init__') \
				  and  name.endswith('.py')
	remove_ext = lambda name: name.split(".py")[0]  
	iterator = os.walk(self.modules_path)
	(root, basenames, files) = iterator.next()
	method_base = ""
	self.methods.extend([method_base+file for file in map(remove_ext, filter(real_files, files))])	
	for (root, dirs, files) in iterator:
	    parts = root.split(os.sep)	
	    for basename in basenames:
	        if basename in parts:
	    	    method_base = ".".join(parts[parts.index(basename):])+"."
	    files = filter(real_files, files)
	    files = map(remove_ext, files)	
	    self.methods.extend([method_base+file for file in  files]) 

	# Add methods to self and global environment 
        for method in self.methods:
	    callable = self.callable(method)(self.config)
	    if logging: callable = log(callable, method)
	    elif hasattr(self.config, 'log') and self.config.log:
		 callable = log(callable, method)
	    
	    class Dummy: pass
            paths = method.split(".")
            if len(paths) > 1:
                first = paths.pop(0)

                if not hasattr(self, first):
                    obj = Dummy()
                    setattr(self, first, obj)
                    # Also add to global environment if specified
                    if globals is not None:
                        globals[first] = obj

                obj = getattr(self, first)

                for path in paths:
                    if not hasattr(obj, path):
                        if path == paths[-1]:
                            setattr(obj, path, callable)
			    globals[method]=obj  
                        else:
                            setattr(obj, path, Dummy())
                    obj = getattr(obj, path)
	    else:
	        if not hasattr(self, method):
		    setattr(self, method, callable)
	        if globals is not None:
		    globals[method] = callable		
	        

    def callable(self, method):
    	"""
    	Return a new instance of the specified method. 
    	"""	 
        
    	# Look up test	
    	if method not in self.methods:
	    raise Exception, "Invalid method: %s" % method

    	# Get new instance of method
    	try:
	    #classname = method.split(".")[-1]
	    module_name = "qa.modules."+method
	    module = __import__(module_name, globals(), locals(), module_name)
	    components = module_name.split('.')
	    module = getattr(module, components[-1:][0]) 	
	    return module
    	except ImportError, AttributeError:
	    raise  
    	 
    		 
