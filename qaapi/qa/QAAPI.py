import sys, os
import traceback
import qa.modules
from qa.Config import Config
from qa.logger import log	

class QAAPI:
   
    modules_path = os.path.realpath(qa.modules.__path__[0])
    methods = []
		
	
    def __init__(self, globals, config = None, logging=None, verbose=None):
	if config is None: self.config = Config()
	else: self.config = Config(config)

	module_files = self.module_files(self.modules_path)
	callables = set()
        # determine what is callable
	for file in module_files:
	    callables.update(self.callables(file))
		
	# Add methods to self and global environemt	
        for method in callables:	    
	    if logging: method = log(method, method.mod_name)
	    elif hasattr(self.config, 'log') and self.config.log:
	        method = log(method, method.mod_name)
	   
	    class Dummy: pass
            paths = method.mod_name.split(".")
	    print dir(method)
	    
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
                            setattr(obj, path, method)
		            globals[method.mod_name]=obj  
                        else:
                            setattr(obj, path, Dummy())
                    obj = getattr(obj, path)
	    else:
	        if globals is not None:
	            globals[method.mod_name] = method		

    def module_files(self, module_dir):
	"""
	Build a list of files   
    	"""     
	
	# Load files from modules direcotry
        real_files = lambda name: not name.startswith('__init__') \
                                  and  name.endswith('.py')
        remove_ext = lambda name: name.split(".py")[0]
        iterator = os.walk(module_dir)
        (root, basenames, files) = iterator.next()
        module_base = ""
        module_files = []
        module_files.extend([method_base+file for file in map(remove_ext, filter(real_files, files))])

        # recurse through directory             
        for (root, dirs, files) in iterator:
            parts = root.split(os.sep)
            for basename in basenames:
                if basename in parts:
                    module_base = ".".join(parts[parts.index(basename):])+"."
            files = filter(real_files, files)
            files = map(remove_ext, files)
            module_files.extend([module_base+file for file in  files])

	return module_files 

    def callables(self, module_file):
    	"""
    	Return a new instance of the specified method. 
    	"""	 
        
    	# Get new instance of method
	parts = module_file.split(".")
	# add every part except for the last to name (filename)
	module_dir =  "qa.modules."
	module_basename = ".".join(parts[:-1])
	module_path = module_dir + module_file
    	try:
	    module = __import__(module_path, globals(), locals(), module_path)
	    callables = []

	    for attribute in dir(module):
		attr = getattr(module, attribute)
	        if callable(attr):
		    setattr(attr, 'mod_name', module_basename+"."+attribute)
		    callables.append(attr(self.config))
	    return callables 
    	except ImportError, AttributeError:
	    raise  
    	 
    		 
