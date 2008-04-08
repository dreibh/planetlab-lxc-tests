from TestPlc import TestPlc

def run01_uninstall (test_plc):
    return test_plc.uninstall()
def run02_install (test_plc):
    return test_plc.install()
def run03_configure (test_plc):
    return test_plc.configure()
def run04_dump_just_installed (test_plc):
    options.dbname='just-installed'
    return test_plc.db_dump()
