# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2012 INRIA 
#
# allow one hour for the node to install

def config (plc_specs, options):
    def remove_initscripts (plc_spec):
        slice_specs = plc_spec['slices']
        for slice_spec in slice_specs:
            for key in ['initscriptcode', 'initscriptname', 'initscriptstamp']:
                if key in slice_spec:
                    del slice_spec[key]
        return plc_spec
    return [remove_initscripts (plc_spec) for plc_spec in plc_specs ]
