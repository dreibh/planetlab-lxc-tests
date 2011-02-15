# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
# a macro for releasing all local resources and cleanup trackers

"release local resources (stop vs, kill qemus, clean trackers)"

from TestPlc import TestPlc

def run01_vs_stop (test_plc):
    return test_plc.vs_stop()

def run02_qemu_stop (test_plc):
    return test_plc.qemu_kill_mine()

def run03_free_trackers (test_plc):
    return test_plc.local_rel()
