import utils
from TestPlc import TestPlc
from TestSite import TestSite

# requirement is to implement
# run (plc_spec, options)

def run (test_plc,options):

    result=True
    for site_spec in test_plc.plc_spec['sites']:
        utils.header('Checking slices')
        if not TestSite(test_plc,site_spec).check_slices():
            result=False
    return result
