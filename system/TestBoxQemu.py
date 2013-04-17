# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
# this models a box that hosts qemu nodes
# could probably also be used for boxes that host plc instances
import os.path
import utils
from TestSsh import TestSsh

# Apriol 2013 - using /vservers/ for hosting this stuff as well, making IT-like stuff easier
KVMROOT="/vservers"

# xxx this should probably inherit TestSsh
class TestBoxQemu:

    def __init__(self,hostname,buildname,key=None):
        self.hostname_value=hostname
        self.buildname=buildname
        self.key=key
        self.test_ssh=TestSsh(self.hostname_value,self.buildname,self.key,root=KVMROOT)
        
    def hostname (self):
        return self.hostname_value

    def is_local(self):
        return self.test_ssh.is_local()
    
    def run_in_buildname (self,command,background=False, dry_run=False):
        message="On %s: running %s"%(self.hostname(),command)
        if background: message += " &"
        utils.header(message)
        return self.test_ssh.run_in_buildname (command,background, dry_run)

    # xxx could/should use rsync instead
    def copy (self,local_file,recursive=False,dry_run=False):
        return self.test_ssh.copy (local_file,recursive,dry_run=dry_run)

    def rmdir (self,dirname, dry_run=False):
        return self.test_ssh.rmdir(dirname, dry_run=dry_run)

    def mkdir (self,dirname):
        return self.test_ssh.mkdir(dirname)

    # we need at least one nodename, as template-qemu is not synced on remote testboxes
    def qemu_kill_all(self,nodedir):
        self.run_in_buildname("%s/qemu-kill-node"%nodedir)
        return True

    def qemu_list_all(self):
        self.run_in_buildname("template-qemu/qemu-kill-node -l")
        return True

