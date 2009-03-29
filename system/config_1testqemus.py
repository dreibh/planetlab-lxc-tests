import sys

from TestMapper import TestMapper
from TestPool import TestPoolQemu

onelab_qemus_pool = [ ( 'testqemu%d.onelab.eu'%i, None, None) for i in range(1,4) ]
    
def config (plcs, options):

    # all plcs on the same vserver box
    plc_box   ='testbox-plc.onelab.eu'
    # informative
    label=options.personality.replace("linux","")

    # all qemus on a unique pool of 64bits boxes
    node_map = []
    qemu_pool = TestPoolQemu (onelab_qemus_pool,options)
    for index in range(options.size):
        index += 1
        if options.ips_qemu:
            ip_or_hostname=options.ips_qemu.pop()
            (hostname,ip,unused)=qemu_pool.locate_entry(ip_or_hostname)
        else:
            (hostname,ip,unused) = qemu_pool.next_free()
        node_map += [ ('node%d'%index, {'host_box':hostname},) ]

    mapper = {'plc': [ ('*' , {'hostname':plc_box,
                               'PLC_DB_HOST':plc_box,
                               'PLC_API_HOST':plc_box,
                               'PLC_BOOT_HOST':plc_box,
                               'PLC_WWW_HOST':plc_box,
                               'name':'%s-'+label } ) 
                       ],
              'node': node_map,
              }
    
    return TestMapper(plcs,options).map(mapper)
