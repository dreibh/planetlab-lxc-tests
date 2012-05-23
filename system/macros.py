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
    'sfa_view', 
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
    'sfa_update_user', 'sfa_update_slice', 'sfa_view', 'sfa_utest',
]

sequences['sfa_view'] = [
    'sfa-list',
    'sfa-show',
    'sfa-slices',
]

# something that can given to the nightly to prepare a standalone sfa setup
# after what you'll want to tweak the config to point to a myplc some place else
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
    'sfi_configure',
    'sfa-add-site',
    'sfa-add-pi',
    'sfa-add-user',
    'sfa-add-slice',
    'sfa-view',
    'sfa-delete-slice',
    'sfa-delete-user',
    'sfa-view',
]


