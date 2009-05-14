#
# $Id$
# 
# this is only an example file, the actual file sits on our testmaster's homedirectory
# 
# 

from TestResources import TestResources

class OnelabTestResources (TestResources):
    
    # we use only one for now but who knows
    def plc_boxes (self):
        return [ 'testbox-plc.onelab.eu' ]

    def network_dict (self):
        return { 'interface_fields:gateway':'138.96.248.250',
                 'interface_fields:network':'138.96.0.0',
                 'interface_fields:broadcast':'138.96.255.255',
                 'interface_fields:netmask':'255.255.0.0',
                 'interface_fields:dns1': '138.96.0.10',
                 'interface_fields:dns2': '138.96.0.11',
                 }

    def nodes_ip_pool (self):
        return [ ( 'vnode%02d.inria.fr'%i, 
                   '138.96.255.%d'%(230+i), 
                   '02:34:56:00:00:%02d'%i) for i in range(1,10) ]
    
    def qemus_ip_pool (self):
        return [ ( 'testqemu%d.onelab.eu'%i, None, None) for i in range(1,4) ]

    def max_qemus (self):
        return 3

    def plcs_ip_pool (self):
        return [  ( 'vplc%02d.inria.fr'%i, 
                    '138.96.255.%d'%(200+i), 
                    '02:34:56:00:ee:%02d'%i) for i in range(1,16) ]

    def max_plcs (self):
        return 12


local_resources = OnelabTestResources ()
