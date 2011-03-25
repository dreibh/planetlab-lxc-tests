# tweak the config so that aggregates.xml point to slice managers instead of AMs
def config (plc_specs, options):
    for plc_spec in plc_specs:
        plc_spec['sfa']['neighbours-port']=12347
    return plc_specs
