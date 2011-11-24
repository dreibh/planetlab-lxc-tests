sequence=[
    'show', SEP,
    'vs_delete','timestamp_vs','vs_create', SEP,
    'plc_install', 'plc_configure', 'plc_start', SEP,
    'keys_fetch', 'keys_store', 'keys_clear_known_hosts', SEP,
    'initscripts', 'sites', 'nodes', 'slices', 'nodegroups', 'leases', SEP,
    'nodestate_reinstall', 'qemu_local_init','bootcd', 'qemu_local_config', SEP,
    'qemu_export', 'qemu_kill_mine', 'qemu_start', 'timestamp_qemu', SEP,
    'sfa_install_all', 'sfa_configure', 'cross_sfa_configure', 'sfa_start', 'sfa_import', SEPSFA,
    'sfi_configure@1', 'sfa_add_user@1', 'sfa_add_slice@1', 'sfa_discover@1', SEPSFA,
    'sfa_create_slice@1', 'sfa_check_slice_plc@1', SEPSFA, 
    'sfa_update_user@1', 'sfa_update_slice@1', 'sfa_view@1', 'sfa_utest@1',SEPSFA,
]
