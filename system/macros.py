# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 

sequences={}

"release local resources (stop vs, kill qemus, clean trackers)"
sequences['free_all'] = [ 'vs_stop', 'qemu_kill_mine', ]

sequences['sfa_restart'] = [
    'sfa_stop',
    'sfa_plcclean',
    'sfa_dbclean',
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
    'sfa_dbclean',
    'sfa_import', 
    'sfi_configure', 
    'sfa_add_user', 
    'sfa_add_slice',
]

# run the whole SFA stuff but from scratch, new vs all reinstalled and all
sequences['sfa_scratch'] = [
    'show',
    'vs_delete','timestamp_vs','vs_create', 
    'plc_install', 'plc_configure', 'plc_start', 
    'keys_fetch', 'keys_store', 'keys_clear_known_hosts', 
    'initscripts', 'sites', 'nodes', 'slices', 'nodegroups', 'leases', 
    'nodestate_reinstall', 'qemu_local_init','bootcd', 'qemu_local_config', 
    'qemu_export', 'qemu_kill_mine', 'qemu_start', 'timestamp_qemu', 
    'sfa_install_all', 'sfa_configure', 'cross_sfa_configure', 'sfa_start', 'sfa_import', 
    'sfi_configure', 'sfa_add_user', 'sfa_add_slice', 'sfa_discover', 
    'sfa_create_slice', 'sfa_check_slice_plc', 
    'sfa_update_user', 'sfa_update_slice', 'sfi_view_all', 'sfa_utest',
]

sequences['sfi_view_all'] = [
    'sfi_list',
    'sfi_show',
    'sfi_slices',
]

# macro to exercice the registry only
# this requires the sfavoid config
# so that flavour=void and thus sfa-plc is not required
# xxx todo
# this initially was just a convenience to setup a reduced depl.
# clearly there is a lot more to check here in terms of consistency
sequences['sfa_standalone'] = [
    'show',
    'vs_delete',
    'timestamp_vs',
    'vs_create',
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
    'sfi_view_all',
    'sfa_delete_slice',
    'sfa_delete_user',
    'sfi_view_all',
]


