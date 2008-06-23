import os
import socket
import traceback
from sendmail import sendmail
from Table import Table
from qa import utils

class Step(dict):
    
    def __init__(self, name, method, args, log_filename, fatal = True, mailto = []):
        
	self.name = name
	self.method = method
	self.args = args
	self.mailto = mailto
	self.fatal = fatal
	self.passed = None
	self.status = "Not Tested" 
	self.next_steps = []

	# transform logfile path into its url path
	hostname = socket.gethostname()
	port = '51080'
	self.update_logfile(log_filename, hostname, port)

    def update_logfile(self, log_filename, hostname, port):
	logfile_path = log_filename.replace('/var/log/', '')
        self.logfile = 'http://%(hostname)s:%(port)s/%(logfile_path)s' % locals()
    
    def run(self):
	try:
	    result = self.method(*self.args)
	    self.passed = True
	    self.status = "Passed"
	    for step in self.next_steps:
		step.run()	
	    return result
	except:
	    self.passed = False
	    self.status = "Failed"
	    utils.header("%s" % traceback.format_exc())	
	    if not self.fatal:
		for step in  self.next_step:
		    step.run()

	return None
	    
    def notify_contacts(self):
	if not self.mailto:
	    return None	
 
	to = self.mailto
	subject = "QA Test %s %s" % (self.name, self.status)
	log = self.logfile
	body = """
	Hello PlanetLab developer,
	
	The test script for your module has %(status)s. Please review this
	tests log for further details.
	%(log)s
	""" % locals()
		
	sendmail(to, subject, body)

    def get_results(self):
	(name, result, log) = (self.name, self.status, self.logfile)
	
	if result in ['Passed', 'Failed']:
	    body = "%(result)s\t (*) %(name)s %(log)s\n" % locals()
	else:
	    body = "%(result)s\t (*) %(name)s\n" % locals()

	for step in self.next_steps:
	    body += step.get_results()
	
	return body 
