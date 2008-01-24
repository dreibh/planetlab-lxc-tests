import os, sys
import traceback
from new import classobj
from Test import Test


class AddPerson(Test): pass

class AddSite(Test): pass

class GetNodes(Test):

    def call(self, hostname):
	return self.config.api.GetNodes(self.config.auth, hostname)

for name in ['Get', 'Update' ,'Delete']:
    tc = classobj(name, (Test,), {})
    setattr(tc, 'call', lambda x: 1)
    globals()[name] = tc
    del(tc)	 	  

		
 
