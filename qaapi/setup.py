#!/usr/bin/python
#
# Setup script for PLCAPI
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: setup.py 5574 2007-10-25 20:33:17Z thierry $
#

import os
from distutils.core import setup
from glob import glob

path = os.getcwd()
name = 'qa'
path = path+os.sep+name
pkgs = [path]

iterator = os.walk(path)
for (root, dirs, files) in iterator:
    pkgs.extend([root+os.sep+d for d in dirs])			

print pkgs 
setup(name = name,
      packages = pkgs,
      scripts = ['qash']
                    )
