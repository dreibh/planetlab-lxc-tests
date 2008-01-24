import sys, os
import traceback
import tests
from Config import Config
from logger import log	

class QAAPI:
   
    tests_path = os.path.realpath(tests.__path__[0])
    methods = []
		
	
    def __init__(self, globals, config = None, logging=None, verbose=None):
	if config is None: self.config = Config()
	else: self.config = Config(config)

	test_files = self.test_files(self.tests_path)
	callables = set()
        # determine what is callable
	for file in test_files:
	    tests = self.callables(file)
	    tests = filter(lambda t: t.test_name not in ['Test'], tests)
	    callables.update(tests)
		
	# Add methods to self and global environemt	
        for method in callables:
	    if logging: method = log(method, method.test_name)
	    elif hasattr(self.config, 'log') and self.config.log:
	        method = log(method, method.test_name)
	    class Dummy: pass
            paths = method.test_name.split(".")
	    
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
		            globals[method.test_name]=obj  
                        else:
                            setattr(obj, path, Dummy())
                    obj = getattr(obj, path)
	    else:
	        if globals is not None:
	            globals[method.test_name] = method		

    def test_files(self, tests_dir):
	"""
	Build a list of files   
    	"""     
	
	# Load files from tests direcotry
        real_files = lambda name: not name.startswith('__init__') \
                                  and  name.endswith('.py')
        remove_ext = lambda name: name.split(".py")[0]
        iterator = os.walk(tests_dir)
        (root, basenames, files) = iterator.next()
        test_base = ""
        test_files = []
        test_files.extend([test_base+file for file in map(remove_ext, filter(real_files, files))])
        
  	# recurse through directory             
        for (root, dirs, files) in iterator:
            parts = root.split(os.sep)
            for basename in basenames:
                if basename in parts:
                    test_base = ".".join(parts[parts.index(basename):])+"."
            files = filter(real_files, files)
            files = map(remove_ext, files)
            test_files.extend([test_base+file for file in  files])
	return list(set(test_files)) 

    def callables(self, test_file):
    	"""
    	Return a new instance of the specified method. 
    	"""	 
        
    	# Get new instance of method
	parts = test_file.split(".")
	# add every part except for the last to name (filename)
	tests_dir =  "tests."
	test_basename = ".".join(parts[:-1])
	if test_basename: test_basename += '.'
	test_path = tests_dir + test_file
    	try:
	    test = __import__(test_path, globals(), locals(), test_path)
	    callables = []

	    for attribute in dir(test):
		attr = getattr(test, attribute)
	        if callable(attr) and hasattr(attr, 'status'):
		    setattr(attr, 'test_name', test_basename+attribute)
		    callables.append(attr(self.config))
	    return callables 
    	except ImportError, AttributeError:
	    raise  
    	 
    		 
