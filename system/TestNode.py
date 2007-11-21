import os
import sys
import time
import base64
import TestConfig
import xmlrpclib

class TestNode:

    def __init__ (self,test_plc,test_site,node_spec):
	self.test_plc=test_plc
	self.test_site=test_site
	self.node_spec=node_spec
        self.timset=time.strftime("%H:%M:%S", time.localtime())
    def create_node (self,role):
        auth = self.test_site.anyuser_auth (role)
        filter={'boot_state':'rins'}
        try:
            if (role=='pi' and self.node_spec['owned']=='pi'):
                self.node_id = self.test_plc.server.AddNode(auth,
                                                            self.test_site.site_spec['site_fields']['login_base'],
                                                            self.node_spec)
                self.test_plc.server.AddNodeNetwork(auth,self.node_id,
                                                    self.node_spec['network'])
                self.test_plc.server.UpdateNode(auth, self.node_id, filter)
                return self.node_id
            
            elif (role=='tech' and self.node_spec['owned']=='tech'):
                self.node_id = self.test_plc.server.AddNode(auth,
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
                print '========>Creating slice at :'+self.timset+' : ',slicespec
                slice_id=self.test_plc.server.AddSlice(auth,slicespec['slice_spec'])
                for sliceuser in slicespec['slice_users']:
                    self.test_plc.server.AddPersonToSlice(auth, sliceuser['email'], slice_id)##affecting person to the slice
                for slicenode in slicespec['slice_nodes']:
                    liste_hosts.append(slicenode['hostname'])
                self.test_plc.server.AddSliceToNodes(auth, slice_id, liste_hosts)##add slice to the spec nodes
            print 'fin creation slices'
        except Exception, e:
            print str(e)
            sys.exit(1)
        
    def conffile(self,image,hostname,path):
        try:
            file=path+'/VirtualFile-'+hostname+'/My_Virtual_Machine.vmx'
            f2=open(file,'w')
            
            f1=open(path+'/My-Virtual-Machine-model/My_Virtual_Machine.vmx','r')
            while 1:
                txt = f1.readline()
                if txt=='':
                    f1.close()
                    f2.close()
                    break
                if txt[0]!='*' :
                    f2.write(txt)
                else :
                    f2.write('ide1:1.fileName = '+'"'+image+'"' '\n')
          
            
        except Exception, e:
            print str(e)

    def create_boot_cd(self,node_spec,path):
        try:
            os.system('mkdir  -p  %s/VirtualFile-%s  &&  cp  %s/My-Virtual-Machine-model/*  %s/VirtualFile-%s'
                      %(path, node_spec['hostname'], path, path, node_spec['hostname']))
            link1=self.test_plc.server.GetBootMedium(self.test_plc.auth_root(),
                                                     node_spec['hostname'], 'node-iso', '')
            if (link1 == ''):
                raise Exception, 'boot.iso not found'
            file1=open(path+'/VirtualFile-'+node_spec['hostname']+'/boot_file.iso','w')
            file1.write(base64.b64decode(link1))
            file1.close()
            print '========> boot cd created for :',self.node_spec['hostname']
            self.conffile('boot_file.iso',self.node_spec['hostname'], path) #create 2 conf file for the vmware based
        except Exception, e:
            print str(e)
            sys.exit(1)
