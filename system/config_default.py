# the defaults
import utils
import TestPlc

# this default is for the OneLab test infrastructure

def config (plc_specs, options):

    import config_main
    plcs = config_main.config([],options)
    if options.verbose:
        print '======================================== AFTER main'
        for plc in plcs: TestPlc.TestPlc.display_mapping_plc(plc)
        print '========================================'

    import config_1testqemus
    plcs = config_1testqemus.config (plcs,options)
    if options.verbose:
        print '======================================== AFTER testqemus'
        for plc in plcs: TestPlc.TestPlc.display_mapping_plc(plc)
        print '========================================'

    import config_1vnodes
    plcs = config_1vnodes.config(plcs,options)
    if options.verbose:
        print '======================================== AFTER vnodes'
        for plc in plcs: TestPlc.TestPlc.display_mapping_plc(plc)
        print '========================================'

    import config_1vplcs
    plcs = config_1vplcs.config (plcs,options)
    if options.verbose:
        print '======================================== AFTER vservers'
        for plc in plcs: TestPlc.TestPlc.display_mapping_plc(plc)
        print '========================================'

    return plcs

