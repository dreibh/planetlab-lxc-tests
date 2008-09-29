#!/usr/bin/python

import sys
import os


##################################################################################
###  check for util-vserver 'chkconfig on'  ######################################
##################################################################################
files = [
	'/etc/rc1.d/K90util-vserver',
	'/etc/rc2.d/S10util-vserver',
	'/etc/rc3.d/S10util-vserver',
	'/etc/rc4.d/S10util-vserver',
	'/etc/rc5.d/S10util-vserver',
	'/etc/rc6.d/K90util-vserver',
]
for file in files:
	if os.path.exits(file):
		print "[PASSED] util-vserver init script is enabled."
	else:
		print "[FAILED] util-vserver does not appear to be enabled via 'chkconfig util-vserver on'."
		sys.exit(1)
