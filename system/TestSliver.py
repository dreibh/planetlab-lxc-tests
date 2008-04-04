import utils
import os, os.path
import datetime
import time
from TestSsh import TestSsh

class TestSliver:

    def __init__ (self,test_plc,test_node,test_slice):
        self.test_plc=test_plc
	self.test_node=test_node
        self.test_slice=test_slice
        self.test_ssh = self.create_test_ssh()

    def get_privateKey(self):
        slice_spec=self.test_slice.slice_spec
        try:
            (found,privatekey)=self.test_slice.locate_key()
            return (found,privatekey)
        except Exception,e:
            print str(e)
            
    def create_test_ssh(self):
        (found,privatekey) = self.get_privateKey()
        if not found:
            raise Exception,"Cannot find a valid key for slice %s"%self.test_slice.name()
        return TestSsh (self.test_node.name(),key=privatekey,username=self.test_slice.name(),
                        # so that copies end up in the home dir
                        buildname=".")

    def name (self):
        return "%s@%s"%(self.test_slice.name(),self.test_node.name())

    def check_initscript(self,initscript):
        slice_spec=self.test_slice.slice_spec
        initscript = slice_spec['initscriptname']
        utils.header("Checking initscript %s on sliver %s"%(initscript,self.name()))
        return self.test_ssh.run("ls -l /tmp/%s.stamp"%initscript)==0
    
    def run_tcp_server (self,port,timeout=10):
        server_command = "tcptest.py server -p %d -t %d"%(port,timeout)
        return self.test_ssh.copy("tcptest.py")==0 and self.test_ssh.run(server_command)==0

    def run_tcp_client (self,servername,port):
        client_command="tcptest.py client -a %s -p %d"%(servername,port)
        return self.test_ssh.copy("tcptest.py")==0 and self.test_ssh.run(client_command)==0

    def tar_var_logs (self):
        return self.test_ssh.actual_command("sudo tar -C /var/log -cf - .")
    
