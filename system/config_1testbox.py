import sys

from TestMapper import TestMapper

# using mapper to do the reallocation job

def config (plcs, options):

    if options.arch == "i386":
        target = 'testbox32.one-lab.org'
    elif options.arch == "x86_64":
        target = 'testbox64.one-lab.org'
    else:
        print 'Unsupported arch %s'%options.arch
        sys.exit(1)

    mapper = {'plc': [ ('*' , {'hostname':target,
                               'PLC_DB_HOST':target,
                               'PLC_API_HOST':target,
                               'PLC_BOOT_HOST':target,
                               'PLC_WWW_HOST':target,
                               'name':'%s'+options.arch } ) ],
              'node': [ ('*' , {'host_box': target } ) ],
              }
    
    return TestMapper(plcs,options).map(mapper)
