import sys

from TestMapper import TestMapper

# using mapper to do the reallocation job

def config (plcs, options):

    if options.personality == "linux32":
        plc_box   ='speedball.inria.fr'
        node_box1 = 'testbox64_1.onelab.eu'
        node_box2 = 'testbox64_2.onelab.eu'
        label="32"
    elif options.personality == "linux64":
        plc_box =   'speedball.inria.fr'
        node_box1 = 'testbox64_1.onelab.eu'
        node_box2 = 'testbox64_2.onelab.eu'
        label="64"
    else:
        print 'Unsupported personality %s'%options.personality
        sys.exit(1)

    mapper = {'plc': [ ('*' , {'hostname':plc_box,
                               'PLC_DB_HOST':plc_box,
                               'PLC_API_HOST':plc_box,
                               'PLC_BOOT_HOST':plc_box,
                               'PLC_WWW_HOST':plc_box,
                               'name':'%s-'+label } ) 
                       ],
              'node': [ ('node1' , {'host_box': node_box1 } ),
                        ('node2' , {'host_box': node_box2 } ),
                        ],
              }
    
    return TestMapper(plcs,options).map(mapper)
