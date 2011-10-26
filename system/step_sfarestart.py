# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
from TestPlc import TestPlc

def run01_pcleean (test_plc):
    return test_plc.sfa_plcclean()
def run02_dclean (test_plc):
    return test_plc.sfa_dbclean()
def run03_lclean (test_plc):
    return test_plc.logclean_sfa()
def run04_stop (test_plc):
    return test_plc.sfa_stop()
def run11_iclean (test_plc):
    return test_plc.sfi_clean()
def run21_conf (test_plc):
    return test_plc.sfa_configure()
def run22_import (test_plc):
    return test_plc.sfa_import()
def run23_start (test_plc):
    return test_plc.sfa_start()
def run31_iconf (test_plc):
    return test_plc.sfi_configure()
