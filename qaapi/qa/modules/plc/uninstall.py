import os, sys
import traceback
from qa.Test import Test
from qa import utils

class uninstall(Test):
    """
    Completely removes the installed myplc
    """

    def call(self):
	if self.config.verbose:
            utils.header("Removing myplc")
        (stdin, stdout, stderr) = os.popen3('set -x; service plc safestop')
        self.errors = stderr.readlines()
        (stdin, stdout, stderr) = os.popen3('set -x; rpm -e myplc')
        self.errors.extend(stderr.readlines())
        if self.errors: raise "\n".join(self.errors)
        (stdin, stdout, stderr) = os.popen3('set -x; rm -rf  /plc/data')
        self.errors.extend(stderr.readlines())
        if self.errors: raise "\n".join(self.errors)
	
	return 1
