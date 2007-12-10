import os, sys, time, base64
import xmlrpclib
import pprint

import TestConfig
import utils

class TestNode:

    def __init__ (self,test_plc,test_site,node_spec):
	self.test_plc=test_plc
	self.test_site=test_site
	self.node_spec=node_spec

    def create_node (self,role):
        auth = self.test_site.anyuser_auth (role)
        filter={'boot_state':'rins'}
        try:
            if (role=='pi' and self.node_spec['owned']=='pi'):
                self.node_id = \
                    self.test_plc.server.AddNode(auth,
                                                 self.test_site.site_spec['site_fields']['login_base'],
                                                 self.node_spec)
                self.test_plc.server.AddNodeNetwork(auth,self.node_id,
                                                    self.node_spec['network'])
                self.test_plc.server.UpdateNode(auth, self.node_id, filter)
                return self.node_id
            
            elif (role=='tech' and self.node_spec['owned']=='tech'):
                self.node_id = \
                    self.test_plc.server.AddNode(auth,
                                                 self.test_site.site_spec['site_fields']['login_base'],
                                                 self.node_spec)
                self.test_plc.server.AddNodeNetwork(auth,self.node_id,
                                                    self.node_spec['network'])
                self.test_plc.server.UpdateNode(auth, self.node_id, filter)
                return self.node_id
        except Exception, e:
                print str(e)

    def create_slice(self, role):
        auth = self.test_site.anyuser_auth (role)
        liste_hosts=[]
        #for l in liste_nodes_spec :
        #    liste_hosts.append(l['hostname'])
        try:
            for slicespec in TestConfig.slices_specs :
                utils.header('Creating Slice')
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(slicespec)
                slice_id=self.test_plc.server.AddSlice(auth,slicespec['slice_spec'])
                for sliceuser in slicespec['slice_users']:
                    self.test_plc.server.AddPersonToSlice(auth, 
                                                          sliceuser['email'], 
                                                          slice_id)
                for slicenode in slicespec['slice_nodes']:
                    liste_hosts.append(slicenode['hostname'])
                    self.test_plc.server.AddSliceToNodes(auth,
                                                         slice_id,
                                                         liste_hosts)
        except Exception, e:
            print str(e)
            sys.exit(1)
        
    def conffile(self,image,hostname,path):
        template='%s/template-vmplayer/node.vmx'%(path)
        actual='%s/vmplayer-%s/node.vmx'%(path,hostname)
        sed_command="sed -e s,@BOOTCD@,%s/%s,g %s > %s"%(path,image,template,actual)
        utils.header('Creating %s from %s'%(actual,template))
        os.system('set -x; ' + sed_command)

    def create_boot_cd(self,path):
        node_spec=self.node_spec
        hostname=node_spec['hostname']
        try:
            utils.header('Initializing vmplayer area for node %s'%hostname)
            clean_dir="rm -rf %s/vmplayer-%s"%(path,hostname)
            mkdir_command="mkdir -p %s/vmplayer-%s"%(path,hostname)
            tar_command="tar -C %s/template-vmplayer -cf - . | tar -C %s/vmplayer-%s -xf -"%(path,path,hostname)
            os.system('set -x; ' +clean_dir + ';' + mkdir_command + ';' + tar_command);
            utils.header('Creating boot medium for node %s'%hostname)
            encoded=self.test_plc.server.GetBootMedium(self.test_plc.auth_root(), hostname, 'node-iso', '')
            if (encoded == ''):
                raise Exception, 'boot.iso not found'
            file=open(path+'/vmplayer-'+hostname+'/boot_file.iso','w')
            file.write(base64.b64decode(encoded))
            file.close()
            utils.header('boot cd created for %s'%hostname)
            self.conffile('boot_file.iso',hostname, path)
        except Exception, e:
            print str(e)
            sys.exit(1)
