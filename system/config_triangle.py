# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
# just overwrite options.size to be 2 and re-use the default config
import config_default

# for checking antiloop on some decent scale
def config (plc_specs, options):
    options.size=3
    return config_default.config(plc_specs,options)
    
