import utils

available = [ ( i, 'vnode%02d.inria.fr'%i, '138.96.250.13%d'%i) for i in range(1,10) ]

def config (plcs,options):
    available.reverse()
    for plc in plcs:
        ### locating the next available hostname (using ping)
        while True:
            try:
                (i,hostname,ip)=available.pop()
                if not utils.check_ping(hostname):
                    break
            except:
                raise Exception('Cannot find an available IP for %s - exiting'%plc['name'])
        plc['vservername']=hostname
        plc['vserverip']=ip
        plc['name'] = "%s_%02d"%(plc['name'],i)
        utils.header("Attaching plc %s to vserver %s (%s)"%\
                         (plc['name'],plc['vservername'],plc['vserverip']))
        for key in [ 'PLC_DB_HOST',
                     'PLC_API_HOST',
                     'PLC_WWW_HOST',
                     'PLC_BOOT_HOST',
                     ]:
            plc[key] = hostname

    return plcs
