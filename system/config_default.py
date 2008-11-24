# the defaults
import utils
import TestPlc

# this default is for the OneLab test infrastructure

def config (plc_specs, options):

#    for step in ['main','1testbox','1nodes','1vservers']:
#        module=__import__(

    import config_main
    plcs = config_main.config([],options)
    if options.verbose:
        print '======================================== AFTER main'
        for plc in plcs: TestPlc.TestPlc.display_mapping_plc(plc)
        print '========================================'

    import config_1testbox
    plcs = config_1testbox.config (plcs,options)
    if options.verbose:
        print '======================================== AFTER testbox'
        for plc in plcs: TestPlc.TestPlc.display_mapping_plc(plc)
        print '========================================'

    import config_1vnodes
    plcs = config_1vnodes.config(plcs,options)
    if options.verbose:
        print '======================================== AFTER vnodes'
        for plc in plcs: TestPlc.TestPlc.display_mapping_plc(plc)
        print '========================================'

    import config_1vservers
    plcs = config_1vservers.config (plcs,options)
    if options.verbose:
        print '======================================== AFTER vservers'
        for plc in plcs: TestPlc.TestPlc.display_mapping_plc(plc)
        print '========================================'

    return plcs

