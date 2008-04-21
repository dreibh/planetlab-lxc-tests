# the defaults
# long story short, this does
# main (standard scenario), 1vnodes (map node(s) in the onelab pool) and then
# 1testbox32 or 64 depending on the personality option

def config (plc_specs, options):
    import config_main
    plcs = config_main.config([],options)
    import config_1vnodes
    plcs = config_1vnodes.config(plcs,options)
    import config_1testbox
    plcs = config_1testbox.config (plcs,options)

    if options.native:
        import config_1vservers
        plcs = config_1vservers.config (plcs,options)

    return plcs

