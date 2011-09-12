# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
# re-use the default config with 3 myplc's and 
# 3 SFA's for checking antiloop on some decent scale
import config_default

def config (plc_specs, options):
    options.size=4
    return config_default.config(plc_specs,options)
    
