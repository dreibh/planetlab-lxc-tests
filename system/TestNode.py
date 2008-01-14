import os, sys, time, base64
import xmlrpclib

import utils
from TestUser import TestUser

class TestNode:

    def __init__ (self,test_plc,test_site,node_spec):
	self.test_plc=test_plc
	self.test_site=test_site
	self.node_spec=node_spec

    def name(self):
        return self.node_spec['node_fields']['hostname']
        
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
                if interface.has_key('attributes'):
                    for (attribute,value) in interface['attributes'].iteritems():
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

    def conffile(self,image,hostname,path):
        template='%s/template-vmplayer/node.vmx'%(path)
        actual='%s/vmplayer-%s/node.vmx'%(path,hostname)
        sed_command="sed -e s,@BOOTCD@,%s,g %s > %s"%(image,template,actual)
        utils.header('Creating %s from %s'%(actual,template))
        utils.system(sed_command)

    def create_boot_cd(self,path):
        node_spec=self.node_spec
        hostname=node_spec['node_fields']['hostname']
        utils.header('Initializing vmplayer area for node %s'%hostname)
        clean_dir="rm -rf %s/vmplayer-%s"%(path,hostname)
        mkdir_command="mkdir -p %s/vmplayer-%s"%(path,hostname)
        tar_command="tar -C %s/template-vmplayer -cf - . | tar -C %s/vmplayer-%s -xf -"%(path,path,hostname)
        utils.system(clean_dir)
        utils.system(mkdir_command)
        utils.system(tar_command);
        utils.header('Creating boot medium for node %s'%hostname)
        encoded=self.test_plc.server.GetBootMedium(self.test_plc.auth_root(), hostname, 'node-iso', '')
        if (encoded == ''):
            raise Exception, 'boot.iso not found'
        file=open(path+'/vmplayer-'+hostname+'/boot_file.iso','w')
        file.write(base64.b64decode(encoded))
        file.close()
        utils.header('boot cd created for %s'%hostname)
        self.conffile('boot_file.iso',hostname, path)

    def start_node (self,options):
        model=self.node_spec['node_fields']['model']
        if model.find("vmware") >= 0:
            self.start_vmware(options)
        elif model.find("qemu") >= 0:
            self.start_qemu(options)
        else:
            utils.header("TestNode.start_node : ignoring model %s"%model)

    def start_vmware (self,options):
        hostname=self.node_spec['node_fields']['hostname']
        path=options.path
        display=options.display
        utils.header('Starting vmplayer for node %s on %s'%(hostname,display))
        utils.system('cd %s/vmplayer-%s ; DISPLAY=%s vmplayer node.vmx < /dev/null >/dev/null 2>/dev/null &'%(path,hostname,display))

    def start_qemu (self, options):
        utils.header ("TestNode.start_qemu: not implemented yet")
