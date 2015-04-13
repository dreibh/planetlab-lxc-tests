# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import sys
import os, os.path
import time
import base64

import utils
from TestUser import TestUser
from TestBoxQemu import TestBoxQemu
from TestSsh import TestSsh
from Completer import CompleterTask

class CompleterTaskNodeSsh(CompleterTask):
    def __init__(self, hostname, qemuname, local_key, command=None,
                  boot_state="boot", expected=True, dry_run=False):
        self.hostname = hostname
        self.qemuname = qemuname
        self.boot_state = boot_state
        self.local_key = local_key
        self.command = command if command is not None else "hostname;uname -a"
        self.expected = expected
        self.dry_run = dry_run
        self.test_ssh =  TestSsh(self.hostname, key=self.local_key)
    def run(self, silent):
        command = self.test_ssh.actual_command(self.command)
        retcod = utils.system(command, silent=silent, dry_run=self.dry_run)
        if self.expected:
            return retcod == 0
        else:
            return retcod != 0
    def failure_epilogue(self):
        print("Cannot reach {} in {} mode".format(self.hostname, self.boot_state))

class TestNode:

    def __init__(self, test_plc, test_site, node_spec):
        self.test_plc = test_plc
        self.test_site = test_site
        self.node_spec = node_spec
        
    def name(self):
        return self.node_spec['node_fields']['hostname']
    
    def dry_run(self):
        return self.test_plc.options.dry_run

    @staticmethod
    def is_qemu_model(model):
        return model.find("qemu") >= 0
    def is_qemu(self):
        return TestNode.is_qemu_model(self.node_spec['node_fields']['model'])

    @staticmethod
    def is_real_model(model):
        return not TestNode.is_qemu_model(model)
    def is_real(self):
        return TestNode.is_real_model(self.node_spec['node_fields']['model'])

    def buildname(self):
        return self.test_plc.options.buildname
        
    def nodedir(self):
        if self.is_qemu():
            return "qemu-{}".format(self.name())
        else:
            return "real-{}".format(self.name())

    # this returns a hostname
    def host_box(self):
        if self.is_real():
            return 'localhost'
        else:
            try:
                return self.node_spec['host_box']
            except:
                utils.header("WARNING : qemu nodes need a host box")
                return 'localhost'

    # this returns a TestBoxQemu instance - cached in .test_box_value
    def test_box(self):
        try:
            return self.test_box_value
        except:
            self.test_box_value = TestBoxQemu(self.host_box(),self.buildname())
            return self.test_box_value

    def create_node(self):
        ownername = self.node_spec['owner']
        user_spec = self.test_site.locate_user(ownername)
        test_user = TestUser(self.test_plc,self.test_site,user_spec)
        userauth = test_user.auth()
        utils.header("node {} created by user {}".format(self.name(), test_user.name()))
        rootauth = self.test_plc.auth_root()
        server  =  self.test_plc.apiserver
        node_id = server.AddNode(userauth,
                                 self.test_site.site_spec['site_fields']['login_base'],
                                 self.node_spec['node_fields'])
        # create as reinstall to avoid user confirmation
        server.UpdateNode(userauth, self.name(), { 'boot_state' : 'reinstall' })

        # you are supposed to make sure the tags exist
        for tagname, tagvalue in self.node_spec['tags'].items():
            server.AddNodeTag(userauth, node_id, tagname, tagvalue)
            
        if not self.test_plc.has_addresses_api():
#            print 'USING OLD INTERFACE'
            # populate network interfaces - primary
            server.AddInterface(userauth, self.name(),
                                self.node_spec['interface_fields'])
        else:
#            print 'USING NEW INTERFACE with separate ip addresses'
            # this is for setting the 'dns' stuff that now goes with the node
            server.UpdateNode(userauth, self.name(), self.node_spec['node_fields_nint'])
            interface_id = server.AddInterface(userauth, self.name(),self.node_spec['interface_fields_nint'])
            server.AddIpAddress(userauth, interface_id, self.node_spec['ipaddress_fields'])
            route_fields = self.node_spec['route_fields']
            route_fields['interface_id'] = interface_id
            server.AddRoute(userauth, node_id, self.node_spec['route_fields'])
            pass
        # populate network interfaces - others
        if 'extra_interfaces' in self.node_spec:
            for interface in self.node_spec['extra_interfaces']:
                server.AddInterface(userauth, self.name(), interface['interface_fields'])
                if 'settings' in interface:
                    for attribute, value in interface['settings'].items():
                        # locate node network
                        interface = server.GetInterfaces( userauth,
                                                          {'ip' : interface['interface_fields']['ip']})[0]
                        interface_id = interface['interface_id']
                        # locate or create node network attribute type
                        try:
                            interface_tagtype = server.GetTagTypes(userauth, {'name' : attribute})[0]
                        except:
                            interface_tagtype = server.AddTagType(rootauth,{'category' : 'test',
                                                                            'tagname' : attribute})
                        # attach value
                        server.AddInterfaceTag(userauth, interface_id, attribute, value)

    def delete_node(self):
        # uses the right auth as far as poss.
        try:
            ownername = self.node_spec['owner']
            user_spec = self.test_site.locate_user(ownername)
            test_user = TestUser(self.test_plc, self.test_site, user_spec)
            auth = test_user.auth()
        except:
            auth = self.test_plc.auth_root()
        self.test_plc.apiserver.DeleteNode(auth, self.name())

    # Do most of the stuff locally - will be pushed on host_box - *not* the plc - later if needed
    def qemu_local_init(self):
        "all nodes : init a clean local directory for holding node-dep stuff like iso image..."
        utils.system("rm -rf {}".format(self.nodedir()))
        utils.system("mkdir {}".format(self.nodedir()))
        if not self.is_qemu():
            return True
        return utils.system("rsync -v -a --exclude .svn template-qemu/ {}/"\
                            .format(self.nodedir())) == 0

    def bootcd(self):
        "all nodes: invoke GetBootMedium and store result locally"
        utils.header("Calling GetBootMedium for {}".format(self.name()))
        # this would clearly belong in the config but, well ..
        options = self.node_spec['bootmedium_options'] if 'bootmedium_options' in self.node_spec else []
        encoded = self.test_plc.apiserver.GetBootMedium(
            self.test_plc.auth_root(), self.name(), 'node-iso', '', options)
        if encoded == '':
            raise Exception('GetBootmedium failed')

        filename = "{}/{}.iso".format(self.nodedir(), self.name())
        utils.header('Storing boot medium into {}'.format(filename))

        # xxx discovered with python3, but a long stading issue:
        # encoded at this point is a str instead of a bytes
        # Quick & dirty : we convert this explicitly to a bytearray
        # Longer run : clearly it seems like the plcapi server side should
        # tag its result with <base64></base64> rather than as a string
        bencoded = str.encode(encoded)
        if self.dry_run():
            print("Dry_run: skipped writing of iso image")
            return True
        else:
            # with python3 we need to call decodestring here
            with open(filename,'wb') as storage:
                storage.write(base64.decodestring(bencoded))
            return True

    def nodestate_reinstall(self):
        "all nodes: mark PLCAPI boot_state as reinstall"
        self.test_plc.apiserver.UpdateNode(self.test_plc.auth_root(),
                                           self.name(),{'boot_state':'reinstall'})
        return True
    
    def nodestate_safeboot(self):
        "all nodes: mark PLCAPI boot_state as safeboot"
        self.test_plc.apiserver.UpdateNode(self.test_plc.auth_root(),
                                           self.name(),{'boot_state':'safeboot'})
        return True
    
    def nodestate_boot(self):
        "all nodes: mark PLCAPI boot_state as boot"
        self.test_plc.apiserver.UpdateNode(self.test_plc.auth_root(),
                                           self.name(),{'boot_state':'boot'})
        return True

    def nodestate_show(self):
        "all nodes: show PLCAPI boot_state"
        if self.dry_run():
            print("Dry_run: skipped getting current node state")
            return True
        state = self.test_plc.apiserver.GetNodes(self.test_plc.auth_root(), self.name(), ['boot_state'])[0]['boot_state']
        print(self.name(),':',state)
        return True
    
    def qemu_local_config(self):
        "all nodes: compute qemu config qemu.conf and store it locally"
        if not self.is_qemu():
            return
        mac = self.node_spec['interface_fields']['mac']
        hostname = self.node_spec['node_fields']['hostname']
        ip = self.node_spec['interface_fields']['ip']
        auth = self.test_plc.auth_root()
        target_arch = self.test_plc.apiserver.GetPlcRelease(auth)['build']['target-arch']
        conf_filename = "{}/qemu.conf".format(self.nodedir())
        if self.dry_run():
            print("dry_run: skipped actual storage of qemu.conf")
            return True
        utils.header('Storing qemu config for {} in {}'.format(self.name(), conf_filename))
        with open(conf_filename,'w') as file:
            file.write('MACADDR={}\n'.format(mac))
            file.write('NODE_ISO={}.iso\n'.format(self.name()))
            file.write('HOSTNAME={}\n'.format(hostname))
            file.write('IP={}\n'.format(ip))
            file.write('TARGET_ARCH={}\n'.format(target_arch))
        return True

    def qemu_clean(self):
        utils.header("Cleaning up qemu for host {} on box {}"\
                     .format(self.name(),self.test_box().hostname()))
        dry_run = self.dry_run()
        self.test_box().rmdir(self.nodedir(), dry_run=dry_run)
        return True

    def qemu_export(self):
        "all nodes: push local node-dep directory on the qemu box"
        # if relevant, push the qemu area onto the host box
        if self.test_box().is_local():
            return True
        dry_run = self.dry_run()
        utils.header("Cleaning any former sequel of {} on {}"\
                     .format(self.name(), self.host_box()))
        utils.header("Transferring configuration files for node {} onto {}"\
                     .format(self.name(), self.host_box()))
        return self.test_box().copy(self.nodedir(), recursive=True, dry_run=dry_run) == 0
            
    def qemu_start(self):
        "all nodes: start the qemu instance (also runs qemu-bridge-init start)"
        model = self.node_spec['node_fields']['model']
        #starting the Qemu nodes before 
        if self.is_qemu():
            self.start_qemu()
        else:
            utils.header("TestNode.qemu_start : {} model {} taken as real node"\
                         .format(self.name(), model))
        return True

    def qemu_timestamp(self):
        "all nodes: start the qemu instance (also runs qemu-bridge-init start)"
        test_box = self.test_box()
        test_box.run_in_buildname("mkdir -p {}".format(self.nodedir()), dry_run=self.dry_run())
        now = int(time.time())
        return test_box.run_in_buildname("echo {:d} > {}/timestamp"\
                                         .format(now, self.nodedir()), dry_run=self.dry_run()) == 0

    def start_qemu(self):
        test_box = self.test_box()
        utils.header("Starting qemu node {} on {}".format(self.name(), test_box.hostname()))

        test_box.run_in_buildname("{}/qemu-bridge-init start >> {}/log.txt"\
                                  .format(self.nodedir(), self.nodedir()),
                                  dry_run=self.dry_run())
        # kick it off in background, as it would otherwise hang
        test_box.run_in_buildname("{}/qemu-start-node 2>&1 >> {}/log.txt"\
                                  .format(self.nodedir(), self.nodedir()))

    def list_qemu(self):
        utils.header("Listing qemu for host {} on box {}"\
                     .format(self.name(), self.test_box().hostname()))
        command = "{}/qemu-kill-node -l {}".format(self.nodedir(), self.name())
        self.test_box().run_in_buildname(command, dry_run=self.dry_run())
        return True

    def kill_qemu(self):
        #Prepare the log file before killing the nodes
        test_box = self.test_box()
        # kill the right processes 
        utils.header("Stopping qemu for node {} on box {}"\
                     .format(self.name(), self.test_box().hostname()))
        command = "{}/qemu-kill-node {}".format(self.nodedir(),self.name())
        self.test_box().run_in_buildname(command, dry_run=self.dry_run())
        return True

    def gather_qemu_logs(self):
        if not self.is_qemu():
            return True
        remote_log = "{}/log.txt".format(self.nodedir())
        local_log = "logs/node.qemu.{}.txt".format(self.name())
        self.test_box().test_ssh.fetch(remote_log,local_log,dry_run=self.dry_run())

    def keys_clear_known_hosts(self):
        "remove test nodes entries from the local known_hosts file"
        TestSsh(self.name()).clear_known_hosts()
        return True

    def create_test_ssh(self):
        # get the plc's keys for entering the node
        vservername = self.test_plc.vservername
###        # assuming we've run testplc.fetch_keys()
###        key = "keys/{vservername}.rsa".format(**locals())
        # fetch_keys doesn't grab the root key anymore
        key = "keys/key_admin.rsa"
        return TestSsh(self.name(), buildname=self.buildname(), key=key)

    def check_hooks(self):
        extensions = [ 'py','pl','sh' ]
        path = 'hooks/node'
        scripts = utils.locate_hooks_scripts('node '+self.name(), path,extensions)
        overall = True
        for script in scripts:
            if not self.check_hooks_script(script):
                overall = False
        return overall

    def check_hooks_script(self,local_script):
        # push the script on the node's root context
        script_name = os.path.basename(local_script)
        utils.header("NODE hook {} ({})".format(script_name, self.name()))
        test_ssh = self.create_test_ssh()
        test_ssh.copy_home(local_script)
        if test_ssh.run("./"+script_name) != 0:
            utils.header("WARNING: node hooks check script {} FAILED (ignored)"\
                         .format(script_name))
            #return False
            return True
        else:
            utils.header("SUCCESS: node hook {} OK".format(script_name))
            return True

    def has_libvirt(self):
        test_ssh = self.create_test_ssh()
        return test_ssh.run("rpm -q --quiet libvirt-client") == 0

    def _check_system_slice(self, slicename, dry_run=False):
        sitename = self.test_plc.plc_spec['settings']['PLC_SLICE_PREFIX']
        vservername = "{}_{}".format(sitename, slicename)
        test_ssh = self.create_test_ssh()
        if self.has_libvirt():
            utils.header("Checking system slice {} using virsh".format(slicename))
            return test_ssh.run("virsh --connect lxc:// list | grep -q ' {} '".format(vservername),
                                dry_run = dry_run) == 0
        else:
            retcod, output = \
                    utils.output_of(test_ssh.actual_command("cat /vservers/{}/etc/slicefamily 2> /dev/null")\
                                    .format(vservername))
            # get last line only as ssh pollutes the output
            slicefamily = output.split("\n")[-1]
            utils.header("Found slicefamily '{}'for slice {}".format(slicefamily,slicename))
            if retcod != 0: 
                return False
            utils.header("Checking system slice {} using vserver-stat".format(slicename))
            return test_ssh.run("vserver-stat | grep {}".format(vservername), dry_run=dry_run) == 0
        
        
