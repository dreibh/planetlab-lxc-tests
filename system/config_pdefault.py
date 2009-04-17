# the defaults
import utils
import TestPlc

# this default is for the Princeton test infrastructure

def config (plc_specs, options):

    import config_main
    plcs = config_main.config([],options)
    if options.verbose:
        print '======================================== AFTER main'
        for plc in plcs: TestPlc.TestPlc.display_mapping_plc(plc)
        print '========================================'

    import config_ptestqemus
    plcs = config_ptestqemus.config (plcs,options)
    if options.verbose:
        print '======================================== AFTER testqemus'
        for plc in plcs: TestPlc.TestPlc.display_mapping_plc(plc)
        print '========================================'

    import config_pvnodes
    plcs = config_pvnodes.config(plcs,options)
    if options.verbose:
        print '======================================== AFTER vnodes'
        for plc in plcs: TestPlc.TestPlc.display_mapping_plc(plc)
        print '========================================'

    import config_pvplcs
    plcs = config_pvplcs.config (plcs,options)
    if options.verbose:
        print '======================================== AFTER vservers'
        for plc in plcs: TestPlc.TestPlc.display_mapping_plc(plc)
        print '========================================'

    return plcs

