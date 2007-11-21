#!/usr/bin/env python
import sys

class TestCases:

    def __init__ (self):
	pass

    def initialize (self):
	print "Performing : initialize"
	print "current options",self.options
	print "e.g. verbose=",self.options.verbose

    def cleanup (self):
	print "Cleaning up"

    def testcase_1 (self):
	print "\tRunning testcase 1"

    def testcase_2 (self):
	print "\tRunning testcase 2"

    def testcase_3 (self):
	print "\tRunning testcase 3"

    def testcase_standard (self):
	print "\tRunning testcase standard"

    def main (self):

	from optparse import OptionParser
	usage="""Usage: %prog [options] steps
steps can include + like in %prog 1 2+3"""
	parser = OptionParser (usage=usage)
	parser.add_option ("-v","--verbose",action="store_true",
			   dest="verbose",default=False,
			   help="run in verbose mode")
	parser.add_option ("-a","--all",action="store_true",
			   dest="all",default=False,
			   help="Run all known testcases")
	(self.options, args)=parser.parse_args()
	
	### get the list of steps to run
	steps=[]
	if self.options.all:
	    # locates all local methods starting with "testcase_"
	    for method_name in dir(self):
		# does it start with testcase_
		if (method_name.find('testcase_',0,len('testcase_'))==0):
		    print 'considering method',method_name
		    steps+=[method_name]
	else:
	    for arg in args:
		# support for the 2+3 syntax
		steplist=arg.split("+")
		for step in steplist:
		    steps += [ 'testcase_'+step]

	### run them
	# args contains the steps to run
	for method_name in steps:
	    method=getattr(self,method_name)
	    if method:
		print '============================== TestCases mainloop'
		self.initialize()
		method()
		self.cleanup()

if __name__ == "__main__":
    TestCases().main()
