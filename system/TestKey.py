# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import utils
import os, os.path
from TestSsh import TestSsh

class TestKey:

    def __init__ (self, test_plc, key_spec):
        self.test_plc = test_plc
        self.key_spec = key_spec
        self.test_ssh = TestSsh(self.test_plc.test_ssh)
        
    def name(self):
        return self.key_spec['key_name']

    def publicpath(self):
        return "keys/{}.pub".format(self.name())
    def privatepath(self):
        return "keys/{}.rsa".format(self.name())

    def store_key(self):
        pub = self.publicpath()
        priv = self.privatepath()
        utils.header("Storing key {} in {}".format(self.name(), pub))
        dir = os.path.dirname(pub)
        if not os.path.isdir(dir):
            os.mkdir(dir)
        with open(pub,"w") as f:
            f.write(self.key_spec['key_fields']['key'])
        with open(priv,"w") as f:
            f.write(self.key_spec['private'])
        os.chmod(priv,0o400)
        os.chmod(pub,0o444)
            
