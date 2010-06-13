# a configuration module is expected:
# (*) to define a config method
# (*) that takes two arguments
#     (**) the current set of plc_specs as output by the preceding config modules
#     (**) TestMain options field
# (*) and that returns the new set of plc_specs

# values like 'hostname', 'ip' and the like are rewritten later with a TestPool object

import config_default

def config (plc_specs, options):
    result=plc_specs
    for i in range (options.size):
        plc = config_default.plc(options,i+1)
        for site in plc['sites']:
            for node in site['nodes']:
                node['node_fields']['node_type']='reservable'
        result.append(plc) 
        
    return result
    
