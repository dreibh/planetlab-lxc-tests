import utils
import os.path

# the pool of IP addresses available
# from 01 to 09
available = [ ( 'vnode%02d.inria.fr'%i, '138.96.250.13%d'%i) for i in range(1,10) ]

# let's be flexible
def locate (user_provided):
    global available
    for (hostname,ip) in available:
        if hostname.find(user_provided) >=0 or ip.find(user_provided) >=0:
            return (hostname,ip)

def config (plcs,options):
    global available
    available.reverse()
    if len(options.ips) != 0:
        options.ips.reverse()
    plc_counter=0
    for plc in plcs:
        if len(options.ips) != 0:
            utils.header('ips=%r'%options.ips)
            user_provided = options.ips.pop()
            utils.header('vserver IP assignment : using user-provided %s'%user_provided)
            (hostname,ip) = locate(user_provided)
        else:
            ### locating the next available hostname (using ping)
            while True:
                try:
                    (hostname,ip)=available.pop()
                    utils.header('vserver IP assignment : scanning IP %s'%ip)
                    if not utils.check_ping(hostname):
                        utils.header('IP %s is OK'%ip)
                        break
                except:
                    raise Exception('Cannot find an available IP for %s - exiting'%plc['name'])
        # compute a helpful vserver name
        plc_counter += 1
        simplehostname=hostname.split('.')[0]
        vservername = os.path.basename(options.myplc_url)
        vservername = vservername.replace(".rpm","")
        vservername = vservername.replace("myplc","vtest")
        if len(plcs) == 1 :
            vservername = "%s-%s" % (vservername,simplehostname)
        else:
            vservername = "%s-%d-%s" % (vservername,plc_counter,simplehostname)
        plc['vservername']=vservername
        plc['vserverip']=ip
        plc['name'] = "%s_%s"%(plc['name'],simplehostname)
        utils.header("Attaching plc %s to vserver %s (%s)"%\
                         (plc['name'],plc['vservername'],plc['vserverip']))
        for key in [ 'PLC_DB_HOST',
                     'PLC_API_HOST',
                     'PLC_WWW_HOST',
                     'PLC_BOOT_HOST',
                     ]:
            plc[key] = hostname

    return plcs
