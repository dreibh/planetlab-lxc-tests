import utils
import os.path
from TestPool import TestPoolIP

onelab_plcs_ip_pool = [ 
    ( 'vplc%02d.inria.fr'%i, 
      '138.96.255.%d'%(200+i), 
      '02:34:56:00:ee:%02d'%i) for i in range(1,21) ]

def config (plcs,options):
    
    utils.header ("Turning configuration into a vserver-based one for onelab")

    ip_pool = TestPoolIP (onelab_plcs_ip_pool,options)

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
