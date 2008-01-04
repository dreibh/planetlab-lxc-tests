import utils
from TestPlc import TestPlc

# requirement is to implement
# run* (plc_spec, options)

def run01_uninstall (test_plc,options):
    return test_plc.uninstall(options)
def run02_install (test_plc,options):
    return test_plc.install(options)
def run03_configure (test_plc,options):
    return test_plc.configure(options)
def run04_dump_just_installed (test_plc,options):
    options.dbname='just-installed'
    return test_plc.db_dump(options)
