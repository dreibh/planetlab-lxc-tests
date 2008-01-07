import os, sys
import traceback
from qa.Test import Test

class start(Test):
    """
    Installs a myplc
    """

    def call(self):
	(stdin, stdout, stderr) = os.popen3('set -x ; service plc start')
        self.errors = stderr.readlines()
        if self.errors: raise "\n".join(self.errors)

	return 1
