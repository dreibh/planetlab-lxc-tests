# $Id$
# this models a box that hosts qemu nodes
# could probably also be used for boxes that host plc instances
import os.path

import utils

class TestBox:

    def __init__(self,hostname,buildname,key=None):
        self.hostname_value=hostname
        self.buildname=buildname
        self.key=key

    def hostname (self):
        return self.hostname_value

    def is_local(self):
        return utils.is_local (self.hostname())
    
    def tar_logs(self):
        if os.path.isdir("nodeslogs"):
            tar_command="tar cvf nodeslogs.tar nodeslogs/ && rm -rf nodeslogs"
            self.run_in_buildname (tar_command)
            return True
        return False
    
    def run_in_buildname (self,command):
        if self.is_local():
            return utils.system(command)
        ssh_comand="ssh "
        if self.key:
            ssh_comand += "-i %s.rsa "%(self.key)
        ssh_command += "%s/%s"%(self.buildname,utils.backslash_shell_specials(command))
        return utils.system(ssh_command)
        
    # should use rsync instead
    def copy (self,local_file,recursive=False):
        if self.is_local():
            return 0
        command="scp "
        if recursive: command += "-r "
        if self.key:
            command += "-i %s.rsa "
        command +="%s %s:%s/%s"%(local_file,self.hostname(),self.buildname,
                                 os.path.basename(local_file) or ".")
        return utils.system(command)
        
    def clean_dir (self):
        if self.is_local():
            return 0
        return utils.system("rm -rf %s"%self.buildname)            

    def mkdir (self):
        if self.is_local():
            return 0
        return utils.system("mkdir %s"%self.buildname)            

    def kill_all_qemus(self):
        self.run_in_buildname("killall qemu")

