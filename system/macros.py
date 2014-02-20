# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 

sequences={}

"release local resources (stop vs, kill qemus)"
sequences['free_all'] = [ 'plcvm_stop', 'qemu_kill_mine', ]

sequences['sfa_restart'] = [
    'sfa_stop',
    'sfa_plcclean',
    'sfa_dbclean',
    'sfa_fsclean',
    'sfa_configure',
    'sfa_start',
    'sfa_import',
    'sfi_clean',
    'sfi_configure',
    ]

"re-run a complete sfa cycle from a nightly test"
sequences['sfa'] = [ 
    'sfa_restart',
    'sfa_add_site',
    'sfa_add_pi',
    'sfa_add_user', 
    'sfa_add_slice',
    'sfa_renew_slice',
    'sfa_discover', 
    'sfa_create_slice', 
    'sfa_check_slice_plc', 
    'sfa_update_user',
    'sfa_update_slice', 
    'sfi_view_all', 
    'sfa_utest', 
    'sfa_delete_slice', 
    'sfa_delete_user',
    ]

sequences['sfa_create'] = [
    'sfa_plcclean', 
    # nuke sometimes requires the service to be stopped b/c of db locks apparently
    'sfa_stop',
    'sfa_dbclean',
    'sfa_start',
    'sfa_import', 
    'sfi_clean',
    'sfi_configure', 
    'sfa_add_site',
    'sfa_add_pi',
    'sfa_add_user', 
    'sfa_add_slice',
]

sequences['sfa_provision'] = [ 
    'sfa-discover',
    'sfa-create_slice',
    'sfa_check_slice_plc',
    'sfi_view_all',
]

# run the whole SFA stuff but from scratch, new vs all reinstalled and all
sequences['sfa_scratch'] = [
    'show',
    'plcvm_delete','plcvm_timestamp','plcvm_create', 
    'plc_install', 'plc_configure', 'plc_start', 
    'keys_fetch', 'keys_store', 'keys_clear_known_hosts', 
    'initscripts', 'sites', 'nodes', 'slices', 'nodegroups', 'leases', 
    'nodestate_reinstall', 'qemu_local_init','bootcd', 'qemu_local_config', 
    'qemu_export', 'qemu_kill_mine', 'qemu_start', 'qemu_timestamp', 
    'sfa_install_all', 'sfa_configure', 'cross_sfa_configure', 'sfa_start', 'sfa_import', 
    'sfi_configure', 'sfa_add_user', 'sfa_add_slice', 'sfa_discover', 
    'sfa_create_slice', 'sfa_check_slice_plc', 
    'sfa_update_user', 'sfa_update_slice', 'sfi_view_all', 'sfa_utest',
]

sequences['sfi_view_all'] = [
    'sfi_list',
    'sfi_show',
]

# macro to exercice the registry only
# this requires the sfavoid config
# so that flavour=void and thus sfa-plc is not required
# xxx todo
# this initially was just a convenience to setup a reduced depl.
# clearly there is a lot more to check here in terms of consistency
sequences['sfa_standalone'] = [
    'show',
    'plcvm_delete',
    'plcvm_timestamp',
    'plcvm_create',
    'sfa_install_client',
    'sfa_install_core',
    'sfa_configure',
    'cross_sfa_configure',
    'sfa_start',
    'sfa_import',
    'sfi_configure',
    'sfa_add_site',
    'sfa_add_pi',
    'sfa_add_user',
    'sfa_add_slice',
    'sfi_list',
    'sfi_show',
    'sfa_delete_slice',
    'sfa_delete_user',
    'sfi_list',
    'sfi_show',
]

# re-run a qemu node when things go wrong
# we need a scheme where we can select another qemu box
# this is based on a 2-step mechanism
#
# run qemu_again1
# rm arg-ips-bnode (or echo anotherbox > arg-ips-bnode)
# run qemu-again2

sequences['qemu_again1'] = [
    'qemu-kill-mine',
]

sequences['qemu_again2']=[
    'qemu-clean-mine',
    'nodestate_reinstall', 'qemu_local_init','bootcd', 'qemu_local_config', 
    'qemu_clean_mine', 'qemu_export', 'qemu_start', 'qemu_timestamp', 
    'ping_node', 'ssh_node_debug',
    'ssh_node_boot', 'node_bmlogs', 'ssh_slice', 'ssh_slice_basics', 'check_initscripts',
]

# same but only up to ping 
sequences['qemu_again2_ping']=[
    'qemu-clean-mine',
    'nodestate_reinstall', 'qemu_local_init','bootcd', 'qemu_local_config', 
    'qemu_clean_mine', 'qemu_export', 'qemu_start', 'qemu_timestamp', 
    'ping_node',
]
    
