# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
# class for issuing commands on a box, either local or remote
#
# the notion of 'buildname' is for providing each test run with a dir of its own
# buildname is generally the name of the build being tested, and can be considered unique
#
# thus 'run_in_buildname' mostly :
# (*) either runs locally in . - as on a local node we are already in a dedicated directory
# (*) or makes sure that there's a remote dir called 'buildname' and runs in it
#
# also, the copy operations
# (*) either do nothing if ran locally
# (*) or copy a local file into the remote 'buildname' 
# 

import os.path
import utils
import shutil

class TestSsh:
    
    # inserts a backslash before each occurence of the following chars
    # \ " ' < > & | ; ( ) $ * ~ 
    @staticmethod
    def backslash_shell_specials (command):
        result=''
        for char in command:
            if char in "\\\"'<>&|;()$*~":
                result +='\\'+char
            else:
                result +=char
        return result

    # check main IP address against the provided hostname
    @staticmethod
    def is_local_hostname (hostname):
        if hostname == "localhost":
            return True
        import socket
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            remote_ip = socket.gethostbyname(hostname)
            return local_ip==remote_ip
        except:
            utils.header("WARNING : something wrong in is_local_hostname with hostname=%s"%hostname)
            return False

    def __init__(self,hostname,buildname=None,key=None, username=None):
        self.hostname=hostname
        self.buildname=buildname
        self.key=key
        self.username=username

    def is_local(self):
        return TestSsh.is_local_hostname(self.hostname)
     
    std_options="-o BatchMode=yes -o StrictHostKeyChecking=no -o CheckHostIP=no -o ConnectTimeout=5 -o UserKnownHostsFile=/dev/null "
    
    def key_part (self):
        if not self.key:
            return ""
        return "-i %s "%self.key

    def hostname_part (self):
        if not self.username:
            return self.hostname
        else:
            return "%s@%s"%(self.username,self.hostname)
    
    # command gets run on the right box
    def actual_command (self, command,keep_stdin=False):
        if self.is_local():
            return command
        ssh_command = "ssh "
        if not keep_stdin:
            ssh_command += "-n "
        ssh_command += TestSsh.std_options
        ssh_command += self.key_part()
        ssh_command += "%s %s" %(self.hostname_part(),TestSsh.backslash_shell_specials(command))
        return ssh_command

    def run(self, command,background=False):
        local_command = self.actual_command(command)
        return utils.system(local_command,background)

    def clean_dir (self,dirname):
        if self.is_local():
            return 0
        return self.run("rm -rf %s"%dirname)

    def mkdir (self,dirname=None):
        if self.is_local():
            if dirname:
                return os.path.mkdir(dirname)
            return 0
        if dirname:
            dirname="%s/%s"%(self.buildname,dirname)
        else:
            dirname=self.buildname
        return self.run("mkdir -p %s"%dirname)

    def rmdir (self,dirname=None):
        if self.is_local():
            if dirname:
                return shutil.rmtree(dirname)
            return 0
        if dirname:
            dirname="%s/%s"%(self.buildname,dirname)
        else:
            dirname=self.buildname
        return self.run("rm -rf %s"%dirname)

    def create_buildname_once (self):
        if self.is_local():
            return
        # create remote buildname on demand
        try:
            self.buildname_created
        except:
            self.mkdir()
            self.buildname_created=True

    def run_in_buildname (self,command, background=False):
        if self.is_local():
            return utils.system(command,background)
        self.create_buildname_once()
        return self.run("cd %s ; %s"%(self.buildname,command),background)

    def copy (self,local_file,recursive=False):
        if self.is_local():
            return 0
        self.create_buildname_once()
        scp_command="scp "
        scp_command += TestSsh.std_options
        if recursive: scp_command += "-r "
        scp_command += self.key_part()
        scp_command += "%s %s:%s/%s"%(local_file,self.hostname_part(),
                                      self.buildname,os.path.basename(local_file) or ".")
        return utils.system(scp_command)

    def copy_abs (self,local_file,remote_file,recursive=False):
        if self.is_local():
            dest=""
        else:
            dest= "%s:"%self.hostname_part()
        scp_command="scp "
        scp_command += TestSsh.std_options
        if recursive: scp_command += "-r "
        scp_command += self.key_part()
        scp_command += "%s %s%s"%(local_file,dest,remote_file)
        return utils.system(scp_command)

    def copy_home (self, local_file, recursive=False):
        return self.copy_abs(local_file,os.path.basename(local_file),recursive)

    def fetch (self, remote_file, local_file, recursive=False):
        if self.is_local():
            command="cp "
            if recursive: command += "-r "
            command += "%s %s"%(remote_file,local_file)
        else:
            command="scp "
            command += TestSsh.std_options
            if recursive: command += "-r "
            command += self.key_part()
            # absolute path - do not preprend buildname
            if remote_file.find("/")==0:
                remote_path=remote_file
            else:
                remote_path="%s/%s"%(self.buildname,remote_file)
            command += "%s:%s %s"%(self.hostname_part(),remote_path,local_file)
        return utils.system(command)

    # this is only to avoid harmless message when host cannot be identified
    # convenience only
    # the only place where this is needed is when tring to reach a slice in a node,
    # which is done from the test master box
    def clear_known_hosts (self):
        known_hosts = "%s/.ssh/known_hosts"%os.getenv("HOME")
        utils.header("Clearing entry for %s in %s"%(self.hostname,known_hosts))
        return utils.system("sed -i -e /^%s/d %s"%(self.hostname,known_hosts))
        
