import utils
from TestPlc import TestPlc
from TestSite import TestSite

# requirement is to implement
# run (plc_spec, options)

def run (test_plc,options):

    result=True
    for site_spec in test_plc.plc_spec['sites']:
        utils.header('Checking nodes')
        if not TestSite(test_plc,site_spec).check_nodes():
            result=False
    return result
