import sys

from TestMapper import TestMapper

# using mapper to do the reallocation job

def config (plcs, options):

    if options.arch == "i386":
        plc_box   ='speedball.inria.fr'
        node_box1 = 'testbox64_1.onelab.eu'
        node_box2 = 'testbox64_2.onelab.eu'
    elif options.arch == "x86_64":
        plc_box =   'speedball.inria.fr'
        node_box1 = 'testbox64_1.onelab.eu'
        node_box2 = 'testbox64_2.onelab.eu'
    else:
        print 'Unsupported arch %s'%options.arch
        sys.exit(1)

    mapper = {'plc': [ ('*' , {'hostname':plc_box,
                               'PLC_DB_HOST':plc_box,
                               'PLC_API_HOST':plc_box,
                               'PLC_BOOT_HOST':plc_box,
                               'PLC_WWW_HOST':plc_box,
                               'name':'%s-'+options.arch } ) 
                       ],
              'node': [ ('deferred01' , {'host_box': node_box1 } ),
                        ('deferred02' , {'host_box': node_box2 } ),
                        ],
              }
    
    return TestMapper(plcs,options).map(mapper)
