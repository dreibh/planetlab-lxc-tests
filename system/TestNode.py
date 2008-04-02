import os, sys, time, base64
import xmlrpclib

import utils
from TestUser import TestUser
from TestBox import TestBox

class TestNode:

    def __init__ (self,test_plc,test_site,node_spec):
	self.test_plc=test_plc
	self.test_site=test_site
	self.node_spec=node_spec
        
    def name(self):
        return self.node_spec['node_fields']['hostname']
    
    @staticmethod
    def is_qemu_model (model):
        return model.find("qemu") >= 0
    def is_qemu (self):
        return TestNode.is_qemu_model(self.node_spec['node_fields']['model'])

    @staticmethod
    def is_real_model (model):
        return not TestNode.is_qemu_model(model)
    def is_real (self):
        return TestNode.is_real_model (self.node_spec['node_fields']['model'])

    def buildname(self):
        return self.test_plc.options.buildname
        
    def nodedir (self):
        if self.is_qemu():
            return "qemu-%s"%self.name()
        else:
            return "real-%s"%self.name()

    # this returns a hostname
    def host_box (self):
        if self.is_real ():
            return 'localhost'
        else:
            try:
                return self.node_spec['host_box']
            except:
                utils.header("WARNING : qemu nodes need a host box")
                return 'localhost'

    # this returns a TestBox instance - cached in .test_box_value
    def test_box (self):
        try:
            return self.test_box_value
        except:
            self.test_box_value = TestBox (self.host_box(),self.buildname())
            return self.test_box_value

    def create_node (self):
        ownername = self.node_spec['owner']
        user_spec = self.test_site.locate_user(ownername)
        test_user = TestUser(self.test_plc,self.test_site,user_spec)
        userauth = test_user.auth()
        utils.header("node %s created by user %s"%(self.name(),test_user.name()))
        rootauth=self.test_plc.auth_root()
        server = self.test_plc.server
        server.AddNode(userauth,
                       self.test_site.site_spec['site_fields']['login_base'],
                       self.node_spec['node_fields'])
        # create as reinstall to avoid user confirmation
        server.UpdateNode(userauth, self.name(), {'boot_state':'rins'})
        # populate network interfaces - primary
        server.AddNodeNetwork(userauth,self.name(),
                                            self.node_spec['network_fields'])
        # populate network interfaces - others
        if self.node_spec.has_key('extra_interfaces'):
            for interface in self.node_spec['extra_interfaces']:
                server.AddNodeNetwork(userauth,self.name(),
                                                    interface['network_fields'])
                if interface.has_key('settings'):
                    for (attribute,value) in interface['settings'].iteritems():
                        # locate node network
                        nn = server.GetNodeNetworks(userauth,{'ip':interface['network_fields']['ip']})[0]
                        nnid=nn['nodenetwork_id']
                        # locate or create node network attribute type
                        try:
                            nnst = server.GetNodeNetworkSettingTypes(userauth,{'name':attribute})[0]
                        except:
                            nnst = server.AddNodeNetworkSettingType(rootauth,{'category':'test',
                                                                              'name':attribute})
                        # attach value
                        server.AddNodeNetworkSetting(userauth,nnid,attribute,value)

    def delete_node (self):
        # uses the right auth as far as poss.
        try:
            ownername = self.node_spec['owner']
            user_spec = self.test_site.locate_user(ownername)
            test_user = TestUser(self.test_plc,self.test_site,user_spec)
            auth = test_user.auth()
        except:
            auth=self.test_plc.auth_root()
        self.test_plc.server.DeleteNode(auth,self.name())

    # Do most of the stuff locally - will be pushed on host_box - *not* the plc - later if needed
    def prepare_area(self):
        utils.system("rm -rf %s"%self.nodedir())
        utils.system("mkdir %s"%self.nodedir())
        #create the tar log file
        utils.system("rm -rf nodeslogs && mkdir nodeslogs")
        if self.is_qemu():
            utils.system("rsync -v -a --exclude .svn template-qemu/ %s/"%self.nodedir())

    def create_boot_cd(self):
        utils.header("Calling GetBootMedium for %s"%self.name())
        options = []
        if self.is_qemu():
            options=['serial']
        encoded=self.test_plc.server.GetBootMedium(self.test_plc.auth_root(), self.name(), 'node-iso', '', options)
        if (encoded == ''):
            raise Exception, 'GetBootmedium failed'

        filename="%s/%s.iso"%(self.nodedir(),self.name())
        utils.header('Storing boot medium into %s'%filename)
        file(filename,'w').write(base64.b64decode(encoded))
    
    def configure_qemu(self):
        if not self.is_qemu():
            return
        mac=self.node_spec['network_fields']['mac']
        hostname=self.node_spec['node_fields']['hostname']
        conf_filename="%s/qemu.conf"%(self.nodedir())
        utils.header('Storing qemu config for %s in %s'%(self.name(),conf_filename))
        file=open(conf_filename,'w')
        file.write('MACADDR=%s\n'%mac)
        file.write('NODE_ISO=%s.iso\n'%self.name())
        file.write('HOSTNAME=%s\n'%hostname)
        file.close()

        # if relevant, push the qemu area onto the host box
        if ( not self.test_box().is_local()):
            utils.header ("Transferring configuration files for node %s onto %s"%(self.name(),self.host_box()))
#            self.test_box().clean_dir(self.buildname())
            self.test_box().mkdir("nodeslogs")
            self.test_box().copy(self.nodedir(),recursive=True)

            
    def start_node (self,options):
        model=self.node_spec['node_fields']['model']
        #starting the Qemu nodes before 
        if self.is_qemu():
            self.start_qemu(options)
        else:
            utils.header("TestNode.start_node : %s model %s taken as real node"%(self.name(),model))

    def start_qemu (self, options):
        test_box = self.test_box()
        utils.header("Starting qemu node %s on %s"%(self.name(),test_box.hostname()))

        test_box.run_in_buildname("qemu-%s/env-qemu start >> nodeslogs/%s.log"%(self.name(),self.name()))
        # kick it off in background, as it would otherwise hang
        test_box.run_in_buildname("qemu-%s/start-qemu-node 2>&1 >> nodeslogs/%s.log &"%(self.name(),self.name()),True)

    def list_qemu (self):
        utils.header("Listing qemu for host %s on box %s"%(self.name(),self.test_box().hostname()))
        command="qemu-%s/kill-qemu-node -l %s"%(self.name(),self.name())
        self.test_box().run_in_buildname(command)
        return True

    def kill_qemu (self):
        #Prepare the log file before killing the nodes
        test_box = self.test_box()
        if(not test_box.tar_logs()):
            utils.header("Failed to get the nodes log files")
        # kill the right processes 
        utils.header("Stopping qemu for host %s on box %s"%(self.name(),self.test_box().hostname()))
        command="qemu-%s/kill-qemu-node %s"%(self.name(),self.name())
        self.test_box().run_in_buildname(command)
        return True

    def gather_qemu_logs (self):
        utils.header("WARNING - Incomplete logs gathering TestNodes.gather_qemu_logs")

    def gather_var_logs (self):
        utils.header("WARNING - Incomplete logs gathering TestNodes.gather_var_logs")

