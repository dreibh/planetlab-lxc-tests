import utils
import os.path
from TestPool import TestPool

# the pool of IP addresses available - from 01 to 09
onelab_plcs_pool = [ 
    ( 'vplc%02d.inria.fr'%i, '138.96.250.13%d'%i, 'ab:cd:ef:00:00:%02d'%i) for i in range(1,10) ]

# let's be flexible
def locate (user_provided):
    global available
    for (hostname,ip,mac) in available:
        if hostname.find(user_provided) >=0 or ip.find(user_provided) >=0:
            return (hostname,ip)

def config (plcs,options):
    
    utils.header ("Turning configuration into a vserver-based one for onelab")

    test_pool = TestPool (onelab_plcs_pool,options)

    if len(options.ips) != 0:
        utils.header('Using user-provided IPS:\nips=%r'%options.ips)
        options.ips.reverse()

    plc_counter=0
    for plc in plcs:
        try:
            if len (options.ips != 0):
                (hostname,ip,mac)=test_pool.locate(options.ips.pop())
            else:
                (hostname,ip,mac)=test_pool.next_free()

            ### rewrite fields in plc
            # compute a helpful vserver name - remove domain in hostname
            simplehostname=hostname.split('.')[0]
            # myplc rpm basename, without .rpm
            vservername = os.path.basename(options.myplc_url)
            vservername = vservername.replace(".rpm","")
            # vservername
            vservername = vservername.replace("myplc","vtest")
            if len(plcs) == 1 :
                vservername = "%s-%s" % (vservername,simplehostname)
            else:
                plc_counter += 1
                vservername = "%s-%d-%s" % (vservername,plc_counter,simplehostname)
            # apply
            plc['vservername']=vservername
            plc['vserverip']=ip
            plc['name'] = "%s_%s"%(plc['name'],simplehostname)
            utils.header("Attaching plc %s to vserver %s (%s)"%(
                    plc['name'],plc['vservername'],plc['vserverip']))
            for key in [ 'PLC_DB_HOST', 'PLC_API_HOST', 'PLC_WWW_HOST', 'PLC_BOOT_HOST',]:
                plc[key] = hostname
                
        except:
            raise Exception('Cannot find an available IP for %s - exiting'%plc['name'])

    return plcs