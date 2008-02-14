# $Id$
# this models a box that hosts qemu nodes
# could probably also be used for boxes that host plc instances
import utils

class TestBox:

    def __init__(self,hostname,key=None):
        self.hostname=hostname
        self.key=key

    def run (command):
        if self.hostname == "localhost":
            return utils.system(command)
        else:
            if self.key:
                to_run="ssh -i %s.rsa %s %s"%(self.key,self.hostname,command)
            else:
                to_run="ssh %s %s"%(self.key,self.hostname,command)
            return utils.system(to_run)
        
    def step_all_qemus(hostname):
        self.run("killall qemu")
