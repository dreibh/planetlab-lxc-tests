#
from TestMapper import TestMapper

# using mapper to do the reallocation job

def config (plcs, options):

    mapper = {'plc': [ ('*' , {'hostname':'testbox32.one-lab.org',
                               'name':'%s2' } ) ],
              'node': [ ('*' , {'host_box':'testbox32.one-lab.org'} ) ],
              }
    
    return TestMapper(plcs,mapper,options).map()
