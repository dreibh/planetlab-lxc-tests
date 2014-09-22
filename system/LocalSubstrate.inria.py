#!/usr/bin/python -u
# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
# this is only an example file
# the actual file is installed in your testmaster box as /root/LocalTestResources.py
# 

if __name__ == '__main__':
   import sys, os.path
   sys.path.append(os.path.expanduser("~/git-tests/system"))

from Substrate import Substrate

# domain name .pl.sophia.inria.fr is implicit on our network
class OnelabSubstrate (Substrate):

   def test_box_spec (self):
      return 'testmaster'

   # the experimental lxc-based build box
   def build_lxc_boxes_spec (self):
# velvet needs attention
#      return [ 'liquid', 'reed', 'velvet' ]
      return [ 'liquid', 'reed' ]

   # the lxc-capable box for PLCs
   def plc_lxc_boxes_spec (self):
      return [ 
# gotan looks in bad shape and I can't use its drac from the US
#         ('gotan', 20),         # how many plcs max in this box 
         ('deathvegas', 12),    
         ]  

   # vplc01 to 40
   def vplc_ips (self):
      return [  ( 'vplc%02d'%i,                 # DNS name
                  'unused')                     # MAC address 
                for i in range(1,41) ] 

# as of jan 2014 this is renumbered so that 1 is preferred
   def qemu_boxes_spec (self):
      return [ # (hostname, how many qemus max in this box)
# speedball (1) - old school but robust and a big disk
         ('speedball', 2), # 4 cores, 4Gb, 840 Gb
# used to have kruder too, but it is broken/dead
# dorfmeister (2)
         ('dorfmeister', 2), # 4 cores, 4Gb
# enfoui - L119 as it won't work well under the KVM in L102A
# use F10 to enter BIOS setup
# nodes spawned in this box won't get network connectivity
#         ('enfoui', 4), # 4 cores, 8Gb
# estran (4) - big mem but small disk
         ('estran', 2), # 4 cores, 8Gb
# lodos (5) - rather old/small
         ('lodos', 1), # 2 cores, 4Gb
# cyblok (6)        
         ('cyblok', 1), # 2 cores, 4Gb
         ]

   # the nodes pool has a MAC address as user-data (3rd elt in tuple)
   def vnode_ips (self):
      return [ ( 'vnode%02d'%i,                 # DNS name               
                 '02:34:56:00:00:%02d'%i)       # MAC address
               for i in range(1,21) ] 
   
   # local network settings
   def domain (self):
      return 'pl.sophia.inria.fr'

   def network_settings (self):
      return { 'interface_fields:gateway':      '138.96.112.250',
               'route_fields:next_hop':         '138.96.112.250',
               'interface_fields:network':      '138.96.112.0',
               'interface_fields:broadcast':    '138.96.119.255',
               'interface_fields:netmask':      '255.255.248.0',
               'interface_fields:dns1':         '138.96.112.1',
               'interface_fields:dns2':         '138.96.112.2',
               'node_fields_nint:dns':          '138.96.112.1,138.96.112.2',
               'ipaddress_fields:netmask':      '255.255.248.0',
               }

# the hostname for the testmaster - in case we'd like to run this remotely
   def testmaster (self): 
      return 'testmaster'

local_substrate = OnelabSubstrate ()

if __name__ == '__main__':
   local_substrate.main()
