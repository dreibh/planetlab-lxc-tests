import utils
import os, os.path
from TestSsh import TestSsh

class TestKey:

    def __init__ (self,test_plc,key_spec):
	self.test_plc=test_plc
	self.key_spec=key_spec
        self.test_ssh=TestSsh(self.test_plc.test_ssh)
        
    def name(self):
        return self.key_spec['name']

    def publicpath(self):
        return "keys/%s.pub"%(self.name())
    def privatepath(self):
        return "keys/%s.rsa"%(self.name())

    def store_remote_key(self,hostname):
        #Not tested yet, don't know if needed
        pub=self.publicpath()
        priv=self.privatepath()
        utils.header("Storing key %s in %s into %s "%(self.name(),pub,hostname))
        dir=os.path.dirname(pub)
        self.test_ssh.run("mkdir %s"%dir)
        self.test_ssh.run("cat %s >> %s"%(self.key_spec['key_fields']['key'],pub))
        self.test_ssh.run("cat %s >> %s"%(self.key_spec['private'],priv))
        self.test_ssh.run("chmod %s 0400"%priv)
        self.test_ssh.run("chmod %s 0444"%pub)
            
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
            
