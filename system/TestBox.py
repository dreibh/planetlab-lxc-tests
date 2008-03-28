# $Id$
# this models a box that hosts qemu nodes
# could probably also be used for boxes that host plc instances
import os.path
import utils
from TestSsh import TestSsh

class TestBox:

    def __init__(self,hostname,buildname,key=None):
        self.hostname_value=hostname
        self.buildname=buildname
        self.key=key
        self.test_ssh=TestSsh(self.hostname_value,self.buildname,self.key)
        
    def hostname (self):
        return self.hostname_value

    def is_local(self):
        return self.test_ssh.is_local()
    
    def tar_logs(self):
        if os.path.isdir("nodeslogs"):
            tar_command="tar cvf nodeslogs.tar nodeslogs/"
            self.run_in_buildname (tar_command)
            return True
        return False
    
    def run_in_buildname (self,command):
        utils.header("Running command %s on testbox %s"%(command,self.hostname()))
        return self.test_ssh.run_in_buildname (command)

    # should use rsync instead
    def copy (self,local_file,recursive=False):
        return self.test_ssh.copy (local_file,recursive)

    def clean_dir (self,dirname):
        return self.test_ssh.clean_dir(dirname)

    def mkdir (self,direname):
        return self.test_ssh.mkdir(direname)

    def kill_all_qemus(self):
        self.run_in_buildname("killall qemu")
        return True

