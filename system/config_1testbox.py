import sys

from TestMapper import TestMapper

# using mapper to do the reallocation job

def config (plcs, options):

    if options.arch == "i386":
        testbox1 = 'testbox32.onelab.eu'
        testbox2 = 'testbox64_2.onelab.eu'
        target=testbox1
    elif options.arch == "x86_64":
        testbox1 = 'testbox64_1.onelab.eu'
        testbox2 = 'testbox64_2.onelab.eu'
        target=testbox1
    else:
        print 'Unsupported arch %s'%options.arch
        sys.exit(1)

    mapper = {'plc': [ ('*' , {'hostname':target,
                               'PLC_DB_HOST':target,
                               'PLC_API_HOST':target,
                               'PLC_BOOT_HOST':target,
                               'PLC_WWW_HOST':target,
                               'name':'%s-'+options.arch } ) 
                       ],
              'node': [ ('deferred01' , {'host_box': testbox1 } ),
                        ('deferred02' , {'host_box': testbox2 } ),
                        ],
              }
    
    return TestMapper(plcs,options).map(mapper)
