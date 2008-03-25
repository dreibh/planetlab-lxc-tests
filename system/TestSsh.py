#this class is  used for any ssh command and
#also for any remote or a local command independently
#on which box this must be done.
#new TestSsh object take like an argument an instance
#of the class where it was created 

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

    def __init__(self,caller):
        self.caller=caller

    def hostname(self):
        return self.caller.hostname()
    def is_local(self):
        return TestSsh.is_local_hostname(self.hostname())
    def buildname(self):
        return self.caller.buildname()

    # command gets run on the right box
    def to_host(self,command):
        if self.is_local():
            return command
        else:
            return "ssh %s %s"%(self.hostname(),TestSsh.backslash_shell_specials(command))

    def full_command(self,command):
        return self.to_host(self.caller.host_to_guest(command))

    def run_in_guest (self,command):
        return utils.system(self.full_command(command))
    
    def run_in_host (self,command):
        return utils.system(self.to_host(command))

    # xxx quick n dirty
    def run_in_guest_piped (self,local,remote):
        return utils.system(local+" | "+self.full_command(remote))
    
    def run_in_buildname (self,command):
        if self.is_local():
            return utils.system(command)
        ssh_command="ssh "
        if self.caller.key:
            ssh_command += "-i %s.rsa "%(self.caller.key)
        ssh_command += "%s/%s"%(self.buildname(),TestSsh.backslash_shell_specials(command))
        return utils.system(ssh_command)

    def copy (self,local_file,recursive=False):
        if self.is_local():
            return 0
        command="scp "
        if recursive: command += "-r "
        if self.caller.key:
            command += "-i %s.rsa "
        command +="%s %s:%s/%s"%(local_file,self.hostname(),self.buildname(),
                                 os.path.basename(local_file) or ".")
        return utils.system(command)
        
