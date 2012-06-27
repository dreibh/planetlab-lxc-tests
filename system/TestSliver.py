# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
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
        private_key = self.test_slice.locate_private_key()
        if not private_key:
            raise Exception,"Cannot find the private key for slice %s"%self.test_slice.name()
        return TestSsh (self.test_node.name(),key=private_key,username=self.test_slice.name(),
                        # so that copies end up in the home dir
                        buildname=".")

    def name (self):
        return "%s@%s"%(self.test_slice.name(),self.test_node.name())

    def check_initscript_stamp(self,stamp):
        utils.header("Checking for initscript stamp %s on sliver %s"%(stamp,self.name()))
        return self.test_ssh.run("ls -l /tmp/%s.stamp"%stamp)==0
    
    def run_tcp_server (self,port,timeout=10):
        server_command = "./tcptest.py server -p %d -t %d"%(port,timeout)
        return self.test_ssh.copy("tcptest.py")==0 and \
            self.test_ssh.run(server_command,background=True)==0

    def run_tcp_client (self,servername,port,retry=5):
        client_command="./tcptest.py client -a %s -p %d"%(servername,port)
        if self.test_ssh.copy("tcptest.py")!=0: return False
        utils.header ("tcp client - first attempt")
        if self.test_ssh.run(client_command,background=False)==0: return True
        # if first try has failed, wait for <retry> s an try again
        time.sleep(retry)
        utils.header ("tcp client - second attempt")
        if self.test_ssh.run(client_command,background=False)==0: return True
        return False

    # use the node's main ssh root entrance, as the slice entrance might be down
    #def tar_var_logs (self):
    #    return self.test_ssh.actual_command("sudo tar -C /var/log -cf - .")
    def tar_var_logs (self):
        test_ssh=self.test_node.create_test_ssh()
        dir_to_tar="/vservers/%s/var/log"%self.test_slice.name()
        return test_ssh.actual_command("tar -C %s -cf - ."%dir_to_tar)
    
    def check_hooks (self):
        print 'NOTE: slice hooks check scripts NOT (yet?) run in sudo'
        extensions = [ 'py','pl','sh' ]
        path='hooks/slice/'
        scripts=utils.locate_hooks_scripts ('sliver '+self.name(), path,extensions)
        overall = True
        for script in scripts:
            if not self.check_hooks_script (script):
                overall = False
        return overall

    def check_hooks_script (self,local_script):
        script_name=os.path.basename(local_script)
        utils.header ("SLIVER hook %s (%s)"%(script_name,self.name()))
        test_ssh=self.create_test_ssh()
        test_ssh.copy_home(local_script)
        if test_ssh.run("./"+script_name) != 0:
            utils.header ("WARNING: hooks check script %s FAILED (ignored)"%script_name)
            #return False
            return True
        else:
            utils.header ("SUCCESS: sliver hook %s OK"%script_name)
            return True
    
