#!/usr/bin/python3 -u
# -*- python3 -*-
# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2015 INRIA 
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
      return [ 'buzzcocks' ]

   # the lxc-capable box for PLCs
   def plc_lxc_boxes_spec (self):
      # we now use the same box as for builds
      return [ ('buzzcocks', 20), ]  

   def qemu_boxes_spec (self):
      # ditto, a single big box now is enough
      return [ ('boxtops', 64), ]

   
   # may use vplc01 to 25 - out of the existing 30
   # keep 5 upper addresses for more persistent instances
   def vplc_ips (self):
      return [  ( 'vplc{:02d}'.format(i),       # DNS name
                  'unused')                     # MAC address 
                for i in range(1,26) ] 

   # vnode01 to 20
   # the nodes IP pool has a MAC address as user-data (3rd elt in tuple)
   def vnode_ips (self):
      return [ ( 'vnode{:02d}'.format(i),            # DNS name               
                 '02:34:56:00:00:{:02d}'.format(i))  # MAC address
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

# the hostname for the testmaster that orchestrates the whole business
   def testmaster (self): 
      return 'testmaster'

local_substrate = OnelabSubstrate ()

if __name__ == '__main__':
   local_substrate.main()
