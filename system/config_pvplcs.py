import utils
import os.path
from TestPool import TestPoolIP

# using vplc01 .. vplc15 - keep [16,17,18] for 4.2 and 19 and 20 for long-haul tests
princeton_plcs_ip_pool = [ 
    ("p-plc-01.onelab.eu","128.112.139.99", "de:ad:be:ef:ff:01"),
    ("p-plc-02.onelab.eu","128.112.139.100","de:ad:be:ef:ff:02"),
    ("p-plc-03.onelab.eu","128.112.139.103","de:ad:be:ef:ff:03"),
    ("p-plc-04.onelab.eu","128.112.139.105","de:ad:be:ef:ff:04"),
    ("p-plc-05.onelab.eu","128.112.139.106","de:ad:be:ef:ff:05"),
    ("p-plc-06.onelab.eu","128.112.139.109","de:ad:be:ef:ff:06"),
    ("p-plc-07.onelab.eu","128.112.139.110","de:ad:be:ef:ff:07"),
    ("p-plc-08.onelab.eu","128.112.139.122","de:ad:be:ef:ff:08"),
]

def config (plcs,options):
    
    utils.header ("Turning configuration into a vserver-based one for princeton")

    ip_pool = TestPoolIP (princeton_plcs_ip_pool,options)

    plc_counter=0
    for plc in plcs:
        try:
            if options.ips_plc :
                ip_or_hostname=options.ips_plc.pop()
                (hostname,ip,mac)=ip_pool.locate_entry(ip_or_hostname)
                if not options.quiet:
                    utils.header("Using user-provided %s %s for plc %s"%(
                            hostname,ip_or_hostname,plc['name']))
            else:
                (hostname,ip,mac)=ip_pool.next_free()
                if not options.quiet:
                    utils.header("Using auto-allocated %s %s for plc %s"%(
                            hostname,ip,plc['name']))

            ### rewrite fields in plc
            # compute a helpful vserver name - remove domain in hostname
            simplehostname=hostname.split('.')[0]
            vservername = options.buildname
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
