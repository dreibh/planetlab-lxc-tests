#!/usr/bin/python
import os,sys
from Test import Test
from qa import utils

class vserver_create(Test):
    """
    Create a vsever given the specified name, reference,
    mailto options. Installs the specified myplc distro.
    """

    def call(self, name, fcdistro, mailto):
 	

	if self.config.verbose:
	    utils.header("Creating vserver: %(name)s" % locals()) 
	# Create vserver
	vcreate_script = self.config.vserver_scripts_path + 'vtest-nightly.sh'
	command = "%(vcreate_script)s -b %(name)s -f %(fcdistro)s -m %(mailto)s -w /tmp/" % locals()
	(status, output) = utils.commands(command)

	# Start vserver
	command = "vserver %(name)s start" % locals()
	(status, output) = utils.commands(command)	

	return 1 
