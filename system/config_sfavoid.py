# -*- python3 -*-
# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2015 INRIA 
#
# this config is defined to run on top of another one 
# and just sets the generic flavour to 'void'

def config (plc_specs, options):
    def tweak_loglevel (plc_spec):
        plc_spec['sfa']['SFA_GENERIC_FLAVOUR'] = 'void'
        plc_spec['sfa']['SFA_AGGREGATE_ENABLED'] = 'false'
        return plc_spec
    return [ tweak_loglevel (plc_spec) for plc_spec in plc_specs ]
