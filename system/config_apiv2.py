def config (plc_specs, options):
    for plc_spec in plc_specs:
        plc_spec['sfa']['SFA_AGGREGATE_API_VERSION']=2
    return plc_specs
