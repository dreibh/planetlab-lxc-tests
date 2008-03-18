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
        self.test_ssh =TestSsh(self)

    def is_local(self):
        return self.test_plc.is_local()
    
    def host_to_guest(self,command):
        return self.test_plc.host_to_guest(command)
    
    def get_privateKey(self,slice_spec):
        try:
            (found,remote_privatekey)=self.test_slice.locate_key(slice_spec)
            return (found,remote_privatekey)
        except Exception,e:
            print str(e)
            
    def get_initscript(self,slice_spec):
	(found,remote_privatekey)=self.get_privateKey(slice_spec)
        if not found :
            raise Exception,"Cannot find a valid key for slice %s"%self.test_slice.name()
        for hostname in  slice_spec['nodenames']:
            utils.header("Checking initiscript %s on the slice %s@%s"
                         %(slice_spec['initscriptname'],self.test_slice.name(),hostname))
            init_file=self.test_ssh.run_in_guest('ssh -i %s %s@%s ls -l /tmp/init* '
                                                 %(remote_privatekey,self.test_slice.name(),hostname))
            if ( init_file):
                return False
            
        return True
    
    def run_tcpcheck(self,peer_spec,remote_privatekey):
        if peer_spec['peer_name']=="server":
            tcp_command="ssh -i %s %s@%s ./tcptest.py server -t 10"%(remote_privatekey, peer_spec['slice_name'],
                                                                   peer_spec['server_name'])
            return self.test_ssh.run_in_guest(tcp_command)
        
        else:
            tcp_command="ssh -i %s %s@%s ./tcptest.py client -a %s -p %d"%(remote_privatekey, peer_spec['slice_name'],
                                                                           peer_spec['client_name'],peer_spec['peer_server'],
                                                                           peer_spec['server_port'])
            return self.test_ssh.run_in_guest(tcp_command)



    def do_check_tcp(self,tcp_param,options):
        for tcp_spec in tcp_param:
            #copy the tcptest file under the chroot
            localfile=remotefile="tcptest.py"
            self.test_plc.copy_in_guest(localfile, remotefile, False)
            peer_param=tcp_spec['tcp_fields']
            if (tcp_spec['tcp_fields']['peer_name']=='server'):
                #server instruction
                utils.header("Transfert the tcp script to the server at %s@%s"%(peer_param['slice_name'],
                                                                                peer_param['server_name']))
                slice_spec=self.test_slice.get_slice(peer_param['slice_name'])
                (found,remote_privatekey)=self.get_privateKey(slice_spec)
                cp_server_command="scp -i %s ./tcptest.py %s@%s:"%(remote_privatekey,peer_param['slice_name'],
                                                                   peer_param['server_name'])
                self.test_ssh.run_in_guest(cp_server_command)
                serv_status=self.run_tcpcheck(peer_param,remote_privatekey)
                if (serv_status):
                    utils.header("FAILED to check loop Connexion  on the %s server side"%peer_param['server_name'])
                    return False
            else:
                #Client instruction
                utils.header("Transfert the tcp script to the client at %s@%s" %(peer_param['slice_name'],
                                                                                 peer_param['client_name']))
                slice_spec=self.test_slice.get_slice(peer_param['slice_name'])
                (found,remote_privatekey)=self.get_privateKey(slice_spec)
                cp_client_command="scp -i %s ./tcptest.py %s@%s:"%(remote_privatekey, peer_param['slice_name'],
                                                                   peer_param['client_name'])
                self.test_ssh.run_in_guest(cp_client_command)
                client_status=self.run_tcpcheck(peer_param,remote_privatekey)
                if ( serv_status):
                    utils.header("FAILED to Contact the server %s from the client side %s"%(peer_param['peer_server'],
                                                                                            peer_param['client_name']))
                    return False


        self.test_ssh.run_in_guest("rm -rf tcptest.py")
        return True


