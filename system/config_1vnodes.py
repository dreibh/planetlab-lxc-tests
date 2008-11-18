# map all nodes onto the avail. pool

from TestMapper import TestMapper
from TestPool import TestPool

onelab_plcs_pool = [ 
    ( 'vnode%02d.inria.fr'%i, '138.96.255.%d'%(220+i), '02:34:56:00:00:%02d'%i) for i in range(1,10) ]
site_dict = {
    'interface_fields:gateway':'138.96.248.250',
    'interface_fields:network':'138.96.0.0',
    'interface_fields:broadcast':'138.96.255.255',
    'interface_fields:netmask':'255.255.0.0',
    'interface_fields:dns1': '138.96.0.10',
    'interface_fields:dns2': '138.96.0.11',
}

def config (plcs, options):
    
    test_pool = TestPool (onelab_plcs_pool,options)
    test_mapper = TestMapper (plcs, options)

    all_nodenames = test_mapper.node_names()
    maps = []
    for nodename in all_nodenames:
        if len(options.ips_node) != 0:
            ip=options.ips_node[0]
            options.ips_node=options.ips_node[1:]
            (hostname,ip,mac)=test_pool.locate(ip)
        else:
            (hostname,ip,mac) = test_pool.next_free()
        node_dict= {'node_fields:hostname':hostname,
                    'interface_fields:ip':ip, 
                    'interface_fields:mac':mac,
                    }
    
        node_dict.update(site_dict)
        maps.append ( ( nodename, node_dict) )

    plc_map = [ ( '*' , { 'PLC_NET_DNS1' : site_dict [ 'interface_fields:dns1' ],
                        'PLC_NET_DNS2' : site_dict [ 'interface_fields:dns2' ], } ) ]

    return test_mapper.map ({'node': maps, 'plc' : plc_map } )
