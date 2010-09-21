# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
# a configuration module is expected:
# (*) to define a config method
# (*) that takes two arguments
#     (**) the current set of plc_specs as output by the preceding config modules
#     (**) TestMain options field
# (*) and that returns the new set of plc_specs

# this config is defined to run on top of another one 
# and just sets the nodes as 'reservable'
# 
# use e.g. with
# run -c default -c resa

import config_default

def config (plc_specs, options):
    for plc_spec in plc_specs:
        for site in plc_spec['sites']:
            for node in site['nodes']:
                node['node_fields']['node_type']='reservable'
    return plc_specs
