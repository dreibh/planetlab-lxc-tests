import os
import traceback
import time

class Logfile:
    """
    Represents a logfile. Used to write data to a file. e.g.

 	logfile = Logfile('filename')
        print >> logfile, data	 	
    """		
    def __init__(self, filename):
        self.filename = filename

    def write(self, data):
        try:
            fd = os.open(self.filename, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0644)
            os.write(fd, '%s' % data)
            os.close(fd)
        except OSError:
            sys.stderr.write(data)
            sys.stderr.flush()



logfile = Logfile('qaapi.log')

def log(method, method_name = None, \
	log_filename = 'system.log', errorlog_filename = 'system_error.log'):
    """
    Logs whether the specified method completed successfully or not and 
    returns the method result. Use as a decorator, e.g.,
	
        @log
	def foo(...):
	    ...
	
    Or:
	def foo(...):
	    ...
	foo = log(foo)

    Or:
	result = log(foo)(...)		   	

    """
    logfile = Logfile(log_filename)
    error_logfile = Logfile(errorlog_filename) 			
    
    if method_name is None:
    	method_name = method.__name__
    
    def wrapper(*args, **kwds):
        
	print >> logfile, method_name + ": ",
        try:
	    #print >> logfile, args, 
            result = method(*args, **kwds)
            print >> logfile, " [OK]"
        except:
            print >>logfile, " [FAILED]"
            print >> error_logfile, "%s: %s\n" % (method_name, traceback.format_exc())
	    raise

    return wrapper

