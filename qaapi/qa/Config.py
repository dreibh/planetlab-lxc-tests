import xmlrpclib
import os

class Config:

    path = os.path.dirname(os.path.abspath(__file__))	
    def __init__(self, config_file = path+os.sep+'qa_config'):
	try:
            execfile(config_file, self.__dict__)
        except:
	    print __file__
            raise "Could not find system config in %s" % config_file

	self.auth = {}
	self.auth['Username'] = self.PLC_ROOT_USER
	self.auth['AuthString'] = self.PLC_ROOT_PASSWORD
	self.auth['AuthMethod'] = 'password'
	self.api = xmlrpclib.Server('https://%s/PLCAPI/' % self.PLC_API_HOST)
	self.verbose = True	

