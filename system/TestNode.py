# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import sys, os, os.path, time, base64
import xmlrpclib

import utils
from TestUser import TestUser
from TestBoxQemu import TestBoxQemu
from TestSsh import TestSsh

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

    # this returns a TestBoxQemu instance - cached in .test_box_value
    def test_box (self):
        try:
            return self.test_box_value
        except:
            self.test_box_value = TestBoxQemu (self.host_box(),self.buildname())
            return self.test_box_value

    def create_node (self):
        ownername = self.node_spec['owner']
        user_spec = self.test_site.locate_user(ownername)
        test_user = TestUser(self.test_plc,self.test_site,user_spec)
        userauth = test_user.auth()
        utils.header("node %s created by user %s"%(self.name(),test_user.name()))
        rootauth=self.test_plc.auth_root()
        server = self.test_plc.apiserver
        server.AddNode(userauth,
                       self.test_site.site_spec['site_fields']['login_base'],
                       self.node_spec['node_fields'])
        server.SetNodePlainBootstrapfs(userauth,
                                       self.node_spec['node_fields']['hostname'],
                                       'YES')
        # create as reinstall to avoid user confirmation
        server.UpdateNode(userauth, self.name(), {'boot_state':'reinstall'})
        # populate network interfaces - primary
        server.AddInterface(userauth,self.name(),
                                            self.node_spec['interface_fields'])
        # populate network interfaces - others
        if self.node_spec.has_key('extra_interfaces'):
            for interface in self.node_spec['extra_interfaces']:
                server.AddInterface(userauth,self.name(), interface['interface_fields'])
                if interface.has_key('settings'):
                    for (attribute,value) in interface['settings'].iteritems():
                        # locate node network
                        interface = server.GetInterfaces(userauth,{'ip':interface['interface_fields']['ip']})[0]
                        interface_id=interface['interface_id']
                        # locate or create node network attribute type
                        try:
                            interface_tagtype = server.GetTagTypes(userauth,{'name':attribute})[0]
                        except:
                            interface_tagtype = server.AddTagType(rootauth,{'category':'test',
                                                                            'tagname':attribute})
                        # attach value
                        server.AddInterfaceTag(userauth,interface_id,attribute,value)

    def delete_node (self):
        # uses the right auth as far as poss.
        try:
            ownername = self.node_spec['owner']
            user_spec = self.test_site.locate_user(ownername)
            test_user = TestUser(self.test_plc,self.test_site,user_spec)
            auth = test_user.auth()
        except:
            auth=self.test_plc.auth_root()
        self.test_plc.apiserver.DeleteNode(auth,self.name())

    # Do most of the stuff locally - will be pushed on host_box - *not* the plc - later if needed
    def qemu_local_init(self):
        utils.system("rm -rf %s"%self.nodedir())
        utils.system("mkdir %s"%self.nodedir())
        if not self.is_qemu():
            return True
        return utils.system("rsync -v -a --exclude .svn template-qemu/ %s/"%self.nodedir())==0

    def bootcd(self):
        utils.header("Calling GetBootMedium for %s"%self.name())
        options = []
        if self.is_qemu():
            options.append('serial')
            options.append('no-hangcheck')
        encoded=self.test_plc.apiserver.GetBootMedium(self.test_plc.auth_root(), 
                                                      self.name(), 'node-iso', '', options)
        if (encoded == ''):
            raise Exception, 'GetBootmedium failed'

        filename="%s/%s.iso"%(self.nodedir(),self.name())
        utils.header('Storing boot medium into %s'%filename)
        if self.test_plc.options.dry_run:
            print "Dry_run: skipped writing of iso image"
            return True
        else:
            file(filename,'w').write(base64.b64decode(encoded))
            return True

    def nodestate_reinstall (self):
        self.test_plc.apiserver.UpdateNode(self.test_plc.auth_root(),
                                           self.name(),{'boot_state':'reinstall'})
        return True
    
    def nodestate_safeboot (self):
        self.test_plc.apiserver.UpdateNode(self.test_plc.auth_root(),
                                           self.name(),{'boot_state':'safeboot'})
        return True
    
    def nodestate_boot (self):
        self.test_plc.apiserver.UpdateNode(self.test_plc.auth_root(),
                                           self.name(),{'boot_state':'boot'})
        return True

    def nodestate_show (self):
        if self.test_plc.options.dry_run:
            print "Dry_run: skipped getting current node state"
            return True
        state=self.test_plc.apiserver.GetNodes(self.test_plc.auth_root(), self.name(), ['boot_state'])[0]['boot_state']
        print self.name(),':',state
        return True
    
    def qemu_local_config(self):
        if not self.is_qemu():
            return
        mac=self.node_spec['interface_fields']['mac']
        hostname=self.node_spec['node_fields']['hostname']
        ip=self.node_spec['interface_fields']['ip']
        auth=self.test_plc.auth_root()
        target_arch=self.test_plc.apiserver.GetPlcRelease(auth)['build']['target-arch']
        conf_filename="%s/qemu.conf"%(self.nodedir())
        if self.test_plc.options.dry_run:
            print "dry_run: skipped actual storage of qemu.conf"
            return True
        utils.header('Storing qemu config for %s in %s'%(self.name(),conf_filename))
        file=open(conf_filename,'w')
        file.write('MACADDR=%s\n'%mac)
        file.write('NODE_ISO=%s.iso\n'%self.name())
        file.write('HOSTNAME=%s\n'%hostname)
        file.write('IP=%s\n'%ip)
        file.write('TARGET_ARCH=%s\n'%target_arch)
        file.close()
        return True

    def qemu_export (self):
        # if relevant, push the qemu area onto the host box
        if self.test_box().is_local():
            return True
        utils.header ("Cleaning any former sequel of %s on %s"%(self.name(),self.host_box()))
        self.test_box().run_in_buildname("rm -rf %s"%self.nodedir())
        utils.header ("Transferring configuration files for node %s onto %s"%(self.name(),self.host_box()))
        return self.test_box().copy(self.nodedir(),recursive=True)==0
            
    def qemu_start (self):
        model=self.node_spec['node_fields']['model']
        #starting the Qemu nodes before 
        if self.is_qemu():
            self.start_qemu()
        else:
            utils.header("TestNode.qemu_start : %s model %s taken as real node"%(self.name(),model))
        return True

    def timestamp_qemu (self):
        test_box = self.test_box()
        test_box.run_in_buildname("mkdir -p %s"%self.nodedir())
        now=int(time.time())
        return test_box.run_in_buildname("echo %d > %s/timestamp"%(now,self.nodedir()))==0

    def start_qemu (self):
        test_box = self.test_box()
        utils.header("Starting qemu node %s on %s"%(self.name(),test_box.hostname()))

        test_box.run_in_buildname("%s/qemu-bridge-init start >> %s/log.txt"%(self.nodedir(),self.nodedir()))
        # kick it off in background, as it would otherwise hang
        test_box.run_in_buildname("%s/qemu-start-node 2>&1 >> %s/log.txt"%(self.nodedir(),self.nodedir()))

    def list_qemu (self):
        utils.header("Listing qemu for host %s on box %s"%(self.name(),self.test_box().hostname()))
        command="%s/qemu-kill-node -l %s"%(self.nodedir(),self.name())
        self.test_box().run_in_buildname(command)
        return True

    def kill_qemu (self):
        #Prepare the log file before killing the nodes
        test_box = self.test_box()
        # kill the right processes 
        utils.header("Stopping qemu for node %s on box %s"%(self.name(),self.test_box().hostname()))
        command="%s/qemu-kill-node %s"%(self.nodedir(),self.name())
        self.test_box().run_in_buildname(command)
        return True

    def gather_qemu_logs (self):
        if not self.is_qemu():
            return True
        remote_log="%s/log.txt"%self.nodedir()
        local_log="logs/node.qemu.%s.txt"%self.name()
        self.test_box().test_ssh.fetch(remote_log,local_log)

    def keys_clear_known_hosts (self):
        TestSsh(self.name()).clear_known_hosts()
        return True

    def create_test_ssh(self):
        # get the plc's keys for entering the node
        vservername=self.test_plc.vservername
###        # assuming we've run testplc.fetch_keys()
###        key = "keys/%(vservername)s.rsa"%locals()
        # fetch_keys doesn't grab the root key anymore
        key = "keys/key1.rsa"
        return TestSsh(self.name(), buildname=self.buildname(), key=key)

    def check_hooks (self):
        extensions = [ 'py','pl','sh' ]
        path='hooks/node'
        scripts=utils.locate_hooks_scripts ('node '+self.name(), path,extensions)
        overall = True
        for script in scripts:
            if not self.check_hooks_script (script):
                overall = False
        return overall

    def check_hooks_script (self,local_script):
        # push the script on the node's root context
        script_name=os.path.basename(local_script)
        utils.header ("NODE hook %s (%s)"%(script_name,self.name()))
        test_ssh=self.create_test_ssh()
        test_ssh.copy_home(local_script)
        if test_ssh.run("./"+script_name) != 0:
            utils.header ("WARNING: node hooks check script %s FAILED (ignored)"%script_name)
            #return False
            return True
        else:
            utils.header ("SUCCESS: node hook %s OK"%script_name)
            return True

    def has_libvirt (self):
        test_ssh=self.create_test_ssh()
        return test_ssh.run ("rpm -q libvirt-client")==0

    def check_systemslice (self, slicename,dry_run=False):
        sitename=self.test_plc.plc_spec['PLC_SLICE_PREFIX']
        vservername="%s_%s"%(sitename,slicename)
        test_ssh=self.create_test_ssh()
        if self.has_libvirt():
            return test_ssh.run("virsh --connect lxc:// list | grep -q ' %s '"%vservername,
                                dry_run=dry_run)==0
        else:
            (retcod,output)=utils.output_of(test_ssh.actual_command("cat /vservers/%s/etc/slicefamily 2> /dev/null")%vservername)
            # get last line only as ssh pollutes the output
            slicefamily=output.split("\n")[-1]
            utils.header("system slice %s has slicefamily %s"%(slicename, slicefamily))
            if retcod != 0: 
                return False
            return test_ssh.run("vserver-stat | grep %s"%vservername,dry_run=dry_run)==0
        
        
