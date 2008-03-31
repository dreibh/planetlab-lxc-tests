#
from TestMapper import TestMapper

# using mapper to do the reallocation job

def config (plcs, options):

    mapper = {'plc': [ ('*' , {'hostname':target,
                               'PLC_DB_HOST':target,
                               'PLC_API_HOST':target,
                               'PLC_BOOT_HOST':target,
                               'PLC_WWW_HOST':target,
                               'name':'%s64' } ) ],
              'node': [ ('*' , {'host_box': target } ) ],
              }
    
    return TestMapper(plcs,options).map(mapper)
