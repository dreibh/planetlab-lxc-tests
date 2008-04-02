#this class is  used for any ssh command and
#also for any remote or a local command independently
#on which box this must be done.

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

    def __init__(self,hostname,buildname=None,key=None):
        self.hostname=hostname
        self.buildname=buildname
        self.key=key

    def is_local(self):
        return TestSsh.is_local_hostname(self.hostname)
     
    std_options="-o StrictHostKeyChecking=no -o BatchMode=yes "
    
    def key_part (self):
        if not self.key:
            return ""
        return "-i %s.rsa "%self.key
    
    # command gets run on the right box
    def actual_command (self, command):
        if self.is_local():
            return command
        ssh_command = "ssh "
        ssh_command += TestSsh.std_options
        ssh_command += self.key_part()
        ssh_command += "%s %s" %(self.hostname,TestSsh.backslash_shell_specials(command))
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
        return self.run("mkdir %s"%dirname)

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
            return utils.system(command)
        self.create_buildname_once()
        return self.run("cd %s ; %s"%(self.buildname,command),background)

    def copy (self,local_file,recursive=False):
        if self.is_local():
            return 0
        self.create_buildname_once()
        scp_command="scp "
        if recursive: scp_command += "-r "
        scp_command += self.key_part()
        scp_command += "%s %s:%s/%s"%(local_file,self.hostname,self.buildname,
                                      os.path.basename(local_file) or ".")
        return utils.system(scp_command)
        
