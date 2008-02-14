# $Id$
# this models a box that hosts qemu nodes
# could probably also be used for boxes that host plc instances
import utils

class TestBox:

    def __init__(self,hostname,key=None):
        self.hostname=hostname
        self.key=key

    def run (self,command):
        if self.hostname == "localhost":
            return utils.system(command)
        else:
            if self.key:
                to_run="ssh -i %s.rsa %s %s"%(self.key,self.hostname,
                                              utils.backslash_shell_specials(command))
            else:
                to_run="ssh %s %s"%(self.hostname,
                                    utils.backslash_shell_specials(command))
            return utils.system(to_run)
        
    def copy (self,local_file):
        if self.hostname == "localhost":
            return 0
        else:
            if self.key:
                to_run="scp -i %s.rsa %s %s:"%(self.key,local_file,self.hostname)
            else:
                to_run="scp %s %s:"%(local_file,self.hostname)
            return utils.system(to_run)
        
    def kill_all_qemus(self):
        self.run("killall qemu")

