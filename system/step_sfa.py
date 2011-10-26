# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
from TestPlc import TestPlc

def run01sfa_plcclean (test_plc):   return test_plc.sfa_plcclean()
def run02sfa_dbclean (test_plc):   return test_plc.sfa_dbclean()
def run03sfa_import (test_plc):   return test_plc.sfa_import()
def run04sfi_configure (test_plc):   return test_plc.sfi_configure()
def run05sfa_add_user (test_plc):   return test_plc.sfa_add_user()
def run06sfa_add_slice (test_plc):     return test_plc.sfa_add_slice()
def run07sfa_discover (test_plc):     return test_plc.sfa_discover()
def run08sfa_create_slice (test_plc):     return test_plc.sfa_create_slice()
def run09sfa_check_slice_plc (test_plc):     return test_plc.sfa_check_slice_plc()
def run10sfa_update_user (test_plc):     return test_plc.sfa_update_user()
def run11sfa_update_slice (test_plc):     return test_plc.sfa_update_slice()
def run12sfa_view (test_plc):     return test_plc.sfa_view()
def run13sfa_utest (test_plc):     return test_plc.sfa_utest()
def run14sfa_delete_slice (test_plc):     return test_plc.sfa_delete_slice()
def run15sfa_delete_user (test_plc):     return test_plc.sfa_delete_user()
