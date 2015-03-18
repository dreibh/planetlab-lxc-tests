# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
# remove slice_spec['omf-friendly'] 
#
# this is for testing the system with a broken OMF-friendly feature
# as it happens the lxc builds can't build rvm
# in a first step I had created a no_omf branch but that was definitely a wrong idea

def remove_omf (plc_spec):
    for slice in plc_spec['slices']:
        if 'omf-friendly' in slice:
            print('Turning off omf-friendly in slice',slice['slice_fields']['name'])
            del slice['omf-friendly']
    return plc_spec

def config (plc_specs, options):
    return [ remove_omf(plc) for plc in plc_specs ]
    
