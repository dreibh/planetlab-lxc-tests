# -*- python3 -*-
# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2015 INRIA 
#
# increment SFA_API_LOGLEVEL on all incoming plc_spec's

def config (plc_specs, options):
    def tweak_loglevel (plc_spec):
        plc_spec['sfa']['settings']['SFA_API_LOGLEVEL'] += 1
        return plc_spec
    return [tweak_loglevel (plc_spec) for plc_spec in plc_specs ]

    
