import os
import traceback
import time
import sys
import commands

class Logfile:
    """
    Represents a logfile. Used to write data to a file. e.g.

 	logfile = Logfile('filename')
        print >> logfile, data	 	
    """		
    def __init__(self, filename, date_in_filename = True):
	
	# whats the date
	localtime = time.localtime()
        (year, month, day) = localtime[:3]
        date = "%(year)s.%(month)s.%(day)s" % locals()

	# append date to filename
	if date_in_filename:
	    if filename.find(".log") > -1:
		filename = filename.split(".log")[0] 
	    filename = "%(filename)s-%(date)s.log" % locals()
	
	filename_parts = filename.split(os.sep)
	# Add directory (qaapi) to files path
	if 'qaapi' not in filename_parts: 
	    filename_parts.insert(len(filename_parts)-1, 'qaapi')
	# Add directory(today's date) to file's path
	if date not in filename_parts:
	    filename_parts.insert(len(filename_parts)-1, date)
	 
	# Make sure file's parent directory exists
	self.dir = filename_dir = os.sep + os.sep.join(filename_parts[:-1]) + os.sep
	filename = os.sep + os.sep.join(filename_parts) 
	(status, output) = commands.getstatusoutput("mkdir -p %(filename_dir)s" % locals())
        self.filename = filename

    def rotate(self):
	if os.path.isfile(self.filename):
	    (status, output) = utils.commands("ls %s*" % self.filename)
	    files = output.split("\n")
	    files.sort()
	    lastfile = files[-1:][0]
	    index = lastfile.split(self.logfile.filename)[1].replace(".", "")
	
	    if not index:
		index = "1"
	    else:
		index = str(int(index) +1)
	    utils.commands("mv %s %s.%s" % (self.filename, self.filename, index))	  	
	 	

    def write(self, data):
        try:
            fd = os.open(self.filename, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0644)
            os.write(fd, '%s' % data)
            os.close(fd)
        except OSError:
            sys.stderr.write(data)
            sys.stderr.flush()

log_filename = '/var/log/qaapi.log'
logfile = Logfile(log_filename)

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

