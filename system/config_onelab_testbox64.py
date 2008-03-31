#
from TestMapper import TestMapper

# using mapper to do the reallocation job

def config (plcs, options):

    mapper = {'plc': [ ('*' , {'hostname':'testbox64.one-lab.org',
                               'name':'%s2' } ) ],
              'node': [ ('*' , {'host_box':'testbox64.one-lab.org'} ) ],
              }
    
    return TestMapper(plcs,mapper,options).map()
