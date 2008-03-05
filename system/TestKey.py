import utils
import os, os.path

class TestKey:

    def __init__ (self,test_plc,key_spec):
	self.test_plc=test_plc
	self.key_spec=key_spec
        
    def name(self):
        return self.key_spec['name']

    def publicpath(self):
        return "/root/%s/keys/%s.pub"%(self.test_plc.path,self.name())
    def privatepath(self):
        return "/root/%s/keys/%s.rsa"%(self.test_plc.path,self.name())

    def store_key(self):
        pub=self.publicpath()
        priv=self.privatepath()
        utils.header("Storing key %s in %s"%(self.name(),pub))
        dir=os.path.dirname(pub)
        if not os.path.isdir(dir):
            os.mkdir(dir)
        f=open(pub,"w")
        f.write(self.key_spec['key_fields']['key'])
        f.close()
        f=open(priv,"w")
        f.write(self.key_spec['private'])
        f.close()
        os.chmod(priv,0400)
        os.chmod(pub,0444)
            
