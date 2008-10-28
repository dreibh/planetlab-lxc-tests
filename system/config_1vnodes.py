# map all nodes onto the avail. pool

from TestMapper import TestMapper
from TestPool import TestPool

onelab_plcs_pool = [ 
    ( 'vnode%02d.inria.fr'%i, '138.96.255.%d'%(220+i), '02:34:56:00:00:%02d'%i) for i in range(1,10) ]
site_dict = {
    'network_fields:gateway':'138.96.248.250',
    'network_fields:network':'138.96.0.0',
    'network_fields:broadcast':'138.96.255.255',
    'network_fields:netmask':'255.255.0.0',
    'network_fields:dns1': '138.96.0.10',
    'network_fields:dns2': '138.96.0.11',
}

def config (plcs, options):
    
    test_pool = TestPool (onelab_plcs_pool,options)
    test_mapper = TestMapper (plcs, options)

    all_nodenames = test_mapper.node_names()
    maps = []
    for nodename in all_nodenames:
        if len(options.node_ips) != 0:
            ip=options.node_ips[0]
            options.node_ips=options.node_ips[1:]
            (hostname,ip,mac)=test_pool.locate(ip)
        else:
            (hostname,ip,mac) = test_pool.next_free()
        node_dict= {'node_fields:hostname':hostname,
                    'network_fields:ip':ip, 
                    'network_fields:mac':mac,
                    }
    
        node_dict.update(site_dict)
        maps.append ( ( nodename, node_dict) )

    plc_map = [ ( '*' , { 'PLC_NET_DNS1' : site_dict [ 'network_fields:dns1' ],
                        'PLC_NET_DNS2' : site_dict [ 'network_fields:dns2' ], } ) ]

    return test_mapper.map ({'node': maps, 'plc' : plc_map } )
