#
from TestMapper import TestMapper

# using mapper to do the reallocation job

def config (plcs, options):

    mapper = {'plc': [ ('*' , {'hostname':'testbox2.inria.fr',
                               'name':'%s2' } ) ],
              'node': [ ('*' , {'host_box':'testbox2.inria.fr'} ) ],
              }
    
    return TestMapper(plcs,mapper,options).map()
