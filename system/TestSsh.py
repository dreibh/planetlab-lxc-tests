#
# Thierry Parmentelat - INRIA
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
     
    std_options="-o StrictHostKeyChecking=no -o BatchMode=yes "
    
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
    def actual_command (self, command):
        if self.is_local():
            return command
        ssh_command = "ssh "
        ssh_command += TestSsh.std_options
        ssh_command += self.key_part()
        ssh_command += "%s %s" %(self.hostname_part(),TestSsh.backslash_shell_specials(command))
        return ssh_command

    def run(self, command,background=False):
        local_command = self.actual_command(command)
        if background:
            local_command += " &"
        return utils.system(local_command)

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
        scp_command += TestSh.std_options
        if recursive: scp_command += "-r "
        scp_command += self.key_part()
        scp_command += "%s %s:%s/%s"%(local_file,self.hostname_part(),
                                      self.buildname,os.path.basename(local_file) or ".")
        return utils.system(scp_command)

    def fetch (self, remote_file, local_file, recursive=False):
        if self.is_local():
            command="cp "
            if recursive: command += "-r "
            command += "%s %s"%(remote_file,local_file)
        else:
            command="scp "
            command += TestSh.std_options
            if recursive: command += "-r "
            command += self.key_part()
            command += "%s:%s/%s %s"%(self.hostname_part(),self.buildname,remote_file,local_file)
        utils.system(command)
