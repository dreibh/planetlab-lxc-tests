available = [ ('vbuild1.inria.fr','138.96.250.131'),
              ('vbuild2.inria.fr','138.96.250.132'),
              ('vbuild3.inria.fr','138.96.250.133'),
              ('vbuild4.inria.fr','138.96.250.134'),
              ]

def config (plcs,options):
    available.reverse()
    for plc in plcs:
        # get next slot -- xxx shoud check for running ones
        (name,ip)=available.pop()
        plc['vservername']=name
        plc['vserverip']=ip
        for key in [ 'PLC_DB_HOST',
                     'PLC_API_HOST',
                     'PLC_WWW_HOST',
                     'PLC_BOOT_HOST',
                     ]:
            plc[key] = name

    return plcs
