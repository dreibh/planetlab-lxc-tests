# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2012 INRIA 
#
# allow one hour for the node to install

def config (plc_specs, options):
    def tweak_timers (plc_spec):
        plc_spec['ssh_node_boot_timers'] (60, 58)
        return plc_spec
    return [tweak_timers (plc_spec) for plc_spec in plc_specs ]

    
