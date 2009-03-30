#!/usr/bin/python
# Module: VNET+
# Description: 	
# Connect to the node manager
# Author: acb@cs.princeton.edu/sapanb@cs.princeton.edu

import sys
import os

from xmlrpclib import ServerProxy

homedir=os.environ['HOME']
slice_name = homedir.rsplit('/')[0]

nodemanager = ServerProxy('http://127.0.0.1:812/')
try:
    nodemanager.SetLoans(slice_name, [])
except:
    print "[FAILED] SetLoans didn't work, probably because the packets of this connection are not getting tagged.\n";
