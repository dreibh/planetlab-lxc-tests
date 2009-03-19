#!/usr/bin/python
# Module: VNET+
# Description: 	
# Connect to the node manager
# Author: acb@cs.princeton.edu/sapanb@cs.princeton.edu

import sys

from xmlrpclib import ServerProxy

if (len(sys.argv)!=2):
    print "[FAILED] Please pass the name of the slice this script runs in as the first argument.\n";
else:
    nodemanager = ServerProxy('http://127.0.0.1:812/')
    try:
        nodemanager.SetLoans(sys.argv[1], [])
    except:
        print "[FAILED] SetLoans didn't work, probably because the packets of this connection are not getting tagged.\n";
