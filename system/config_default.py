# the defaults
import utils

def config (plc_specs, options):

# tmp : force small test 
    utils.header("XXX WARNING : forcing small tests in config_default")
    options.small_test = True

    import config_main
    plcs = config_main.config([],options)
    import config_1vnodes
    plcs = config_1vnodes.config(plcs,options)
    import config_1testbox
    plcs = config_1testbox.config (plcs,options)

    import config_1vservers
    plcs = config_1vservers.config (plcs,options)

    return plcs

