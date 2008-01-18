import utils
import os.path

# from 01 to 09
available = [ ( i, 'vnode%02d.inria.fr'%i, '138.96.250.13%d'%i) for i in range(1,10) ]

def config (plcs,options):
    available.reverse()
    plc_counter=0
    for plc in plcs:
        ### locating the next available hostname (using ping)
        while True:
            try:
                (i,hostname,ip)=available.pop()
                if not utils.check_ping(hostname):
                    break
            except:
                raise Exception('Cannot find an available IP for %s - exiting'%plc['name'])
        # compute a helpful vserver name
        plc_counter += 1
        vservername = os.path.basename(options.myplc_url)
        vservername = vservername.replace(".rpm","")
        if len(plcs) == 1 :
            vservername = "%s-%s" % (vservername,ip)
        else:
            vservername = "%s-%d-%s" % (vservername,plc_counter,ip)
        plc['vservername']=vservername
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
