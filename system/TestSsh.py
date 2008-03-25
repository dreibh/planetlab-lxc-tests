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
     
    # command gets run on the right box
    def to_host(self,command):
        if self.is_local():
            return command
        else:
            return "ssh %s %s"%(self.hostname,TestSsh.backslash_shell_specials(command))

    def clean_dir (self,dirname):
        if self.is_local():
            return 0
        return utils.system(self.to_host("rm -rf %s"%dirname))

    def mkdir (self,dirname):
        if self.is_local():
            return 0
        return utils.system(self.to_host("mkdir %s"%dirname))

    def run_in_buildname (self,command):
        if self.is_local():
            return utils.system(command)
        ssh_command="ssh "
        if self.key:
            ssh_command += "-i %s.rsa "%(self.key)
        ssh_command += "%s %s/%s"%(self.hostname,self.buildname,TestSsh.backslash_shell_specials(command))
        return utils.system(ssh_command)

    def copy (self,local_file,recursive=False):
        if self.is_local():
            return 0
        command="scp "
        if recursive: command += "-r "
        if self.key:
            command += "-i %s.rsa "
        command +="%s %s:%s/%s"%(local_file,self.hostname,self.buildname,
                                 os.path.basename(local_file) or ".")
        return utils.system(command)
        
