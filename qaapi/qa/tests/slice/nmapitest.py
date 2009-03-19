#!/usr/bin/python
# Module: VNET+
# Description: 	
# Connect to the node manager
# Author: acb@cs.princeton.edu

from xmlrpclib import ServerProxy

nodemanager = ServerProxy('http://127.0.0.1:812/')
nodemanager.SetLoans('pl_sirius', [])
