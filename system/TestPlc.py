# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA
#
import sys
import time
import os, os.path
import traceback
import socket
from datetime import datetime, timedelta

import utils
from Completer import Completer, CompleterTask
from TestSite import TestSite
from TestNode import TestNode, CompleterTaskNodeSsh
from TestUser import TestUser
from TestKey import TestKey
from TestSlice import TestSlice
from TestSliver import TestSliver
from TestBoxQemu import TestBoxQemu
from TestSsh import TestSsh
from TestApiserver import TestApiserver
from TestAuthSfa import TestAuthSfa
from PlcapiUrlScanner import PlcapiUrlScanner

from TestBonding import TestBonding

has_sfa_cache_filename="sfa-cache"

# step methods must take (self) and return a boolean (options is a member of the class)

def standby(minutes, dry_run):
    utils.header('Entering StandBy for {:d} mn'.format(minutes))
    if dry_run:
        print('dry_run')
    else:
        time.sleep(60*minutes)
    return True

def standby_generic(func):
    def actual(self):
        minutes = int(func.__name__.split("_")[1])
        return standby(minutes, self.options.dry_run)
    return actual

def node_mapper(method):
    def map_on_nodes(self, *args, **kwds):
        overall = True
        node_method = TestNode.__dict__[method.__name__]
        for test_node in self.all_nodes():
            if not node_method(test_node, *args, **kwds):
                overall = False
        return overall
    # maintain __name__ for ignore_result
    map_on_nodes.__name__ = method.__name__
    # restore the doc text
    map_on_nodes.__doc__ = TestNode.__dict__[method.__name__].__doc__
    return map_on_nodes

def slice_mapper(method):
    def map_on_slices(self):
        overall = True
        slice_method = TestSlice.__dict__[method.__name__]
        for slice_spec in self.plc_spec['slices']:
            site_spec = self.locate_site (slice_spec['sitename'])
            test_site = TestSite(self,site_spec)
            test_slice = TestSlice(self,test_site,slice_spec)
            if not slice_method(test_slice, self.options):
                overall=False
        return overall
    # maintain __name__ for ignore_result
    map_on_slices.__name__ = method.__name__
    # restore the doc text
    map_on_slices.__doc__ = TestSlice.__dict__[method.__name__].__doc__
    return map_on_slices

def bonding_redirector(method):
    bonding_name = method.__name__.replace('bonding_', '')
    def redirect(self):
        bonding_method = TestBonding.__dict__[bonding_name]
        return bonding_method(self.test_bonding)
    # maintain __name__ for ignore_result
    redirect.__name__ = method.__name__
    # restore the doc text
    redirect.__doc__ = TestBonding.__dict__[bonding_name].__doc__
    return redirect

# run a step but return True so that we can go on
def ignore_result(method):
    def ignoring(self):
        # ssh_slice_ignore->ssh_slice
        ref_name = method.__name__.replace('_ignore', '').replace('force_', '')
        ref_method = TestPlc.__dict__[ref_name]
        result = ref_method(self)
        print("Actual (but ignored) result for {ref_name} is {result}".format(**locals()))
        return Ignored(result)
    name = method.__name__.replace('_ignore', '').replace('force_', '')
    ignoring.__name__ = name
    ignoring.__doc__ = "ignored version of " + name
    return ignoring

# a variant that expects the TestSlice method to return a list of CompleterTasks that
# are then merged into a single Completer run to avoid wating for all the slices
# esp. useful when a test fails of course
# because we need to pass arguments we use a class instead..
class slice_mapper__tasks(object):
    # could not get this to work with named arguments
    def __init__(self, timeout_minutes, silent_minutes, period_seconds):
        self.timeout = timedelta(minutes = timeout_minutes)
        self.silent = timedelta(minutes = silent_minutes)
        self.period = timedelta(seconds = period_seconds)
    def __call__(self, method):
        decorator_self=self
        # compute augmented method name
        method_name = method.__name__ + "__tasks"
        # locate in TestSlice
        slice_method = TestSlice.__dict__[ method_name ]
        def wrappee(self):
            tasks=[]
            for slice_spec in self.plc_spec['slices']:
                site_spec = self.locate_site (slice_spec['sitename'])
                test_site = TestSite(self, site_spec)
                test_slice = TestSlice(self, test_site, slice_spec)
                tasks += slice_method (test_slice, self.options)
            return Completer (tasks, message=method.__name__).\
                run(decorator_self.timeout, decorator_self.silent, decorator_self.period)
        # restore the doc text from the TestSlice method even if a bit odd
        wrappee.__name__ = method.__name__
        wrappee.__doc__ = slice_method.__doc__
        return wrappee

def auth_sfa_mapper(method):
    def actual(self):
        overall = True
        auth_method = TestAuthSfa.__dict__[method.__name__]
        for auth_spec in self.plc_spec['sfa']['auth_sfa_specs']:
            test_auth = TestAuthSfa(self, auth_spec)
            if not auth_method(test_auth, self.options):
                overall=False
        return overall
    # restore the doc text
    actual.__doc__ = TestAuthSfa.__dict__[method.__name__].__doc__
    return actual

class Ignored:
    def __init__(self, result):
        self.result = result

SEP = '<sep>'
SEPSFA = '<sep_sfa>'

class TestPlc:

    default_steps = [
        'show', SEP,
        'plcvm_delete','plcvm_timestamp','plcvm_create', SEP,
        'django_install', 'plc_install', 'plc_configure', 'plc_start', SEP,
        'keys_fetch', 'keys_store', 'keys_clear_known_hosts', SEP,
        'plcapi_urls','speed_up_slices', SEP,
        'initscripts', 'sites', 'nodes', 'slices', 'nodegroups', 'leases', SEP,
# slices created under plcsh interactively seem to be fine but these ones don't have the tags
# keep this our of the way for now
        'check_vsys_defaults_ignore', SEP,
# run this first off so it's easier to re-run on another qemu box
        'qemu_kill_mine', 'nodestate_reinstall', 'qemu_local_init','bootcd', 'qemu_local_config', SEP,
        'qemu_clean_mine', 'qemu_export', 'qemu_cleanlog', SEP,
        'qemu_start', 'qemu_timestamp', 'qemu_nodefamily', SEP,
        'sfa_install_all', 'sfa_configure', 'cross_sfa_configure', 'sfa_start', 'sfa_import', SEPSFA,
        'sfi_configure@1', 'sfa_register_site@1','sfa_register_pi@1', SEPSFA,
        'sfa_register_user@1', 'sfa_update_user@1', 'sfa_register_slice@1', 'sfa_renew_slice@1', SEPSFA,
        'sfa_remove_user_from_slice@1','sfi_show_slice_researchers@1',
        'sfa_insert_user_in_slice@1','sfi_show_slice_researchers@1', SEPSFA,
        'sfa_discover@1', 'sfa_rspec@1', SEPSFA,
        'sfa_allocate@1', 'sfa_provision@1', 'sfa_describe@1', SEPSFA,
        'sfa_check_slice_plc@1', 'sfa_update_slice@1', SEPSFA,
        'sfi_list@1', 'sfi_show_site@1', 'sfa_utest@1', SEPSFA,
        # we used to run plcsh_stress_test, and then ssh_node_debug and ssh_node_boot
        # but as the stress test might take a while, we sometimes missed the debug mode..
        'probe_kvm_iptables',
        'ping_node', 'ssh_node_debug', 'plcsh_stress_test@1', SEP,
        'ssh_node_boot', 'node_bmlogs', 'ssh_slice', 'ssh_slice_basics', SEP,
        'ssh_slice_sfa@1', SEPSFA,
        'sfa_rspec_empty@1', 'sfa_allocate_empty@1', 'sfa_provision_empty@1','sfa_check_slice_plc_empty@1', SEPSFA,
        'sfa_delete_slice@1', 'sfa_delete_user@1', SEPSFA,
        'cross_check_tcp@1', 'check_system_slice', SEP,
        # for inspecting the slice while it runs the first time
        #'fail',
        # check slices are turned off properly
        'debug_nodemanager',
        'empty_slices', 'ssh_slice_off', 'slice_fs_deleted_ignore', SEP,
        # check they are properly re-created with the same name
        'fill_slices', 'ssh_slice_again', SEP,
        'gather_logs_force', SEP,
        ]
    other_steps = [
        'export', 'show_boxes', 'super_speed_up_slices', SEP,
        'check_hooks', 'plc_stop', 'plcvm_start', 'plcvm_stop', SEP,
        'delete_initscripts', 'delete_nodegroups','delete_all_sites', SEP,
        'delete_sites', 'delete_nodes', 'delete_slices', 'keys_clean', SEP,
        'delete_leases', 'list_leases', SEP,
        'populate', SEP,
        'nodestate_show','nodestate_safeboot','nodestate_boot', 'nodestate_upgrade', SEP,
        'nodedistro_show','nodedistro_f14','nodedistro_f18', SEP,
        'nodedistro_f20', 'nodedistro_f21','nodedistro_f22', SEP,
        'qemu_list_all', 'qemu_list_mine', 'qemu_kill_all', SEP,
        'sfa_install_core', 'sfa_install_sfatables', 'sfa_install_plc', 'sfa_install_client', SEPSFA,
        'sfa_plcclean', 'sfa_dbclean', 'sfa_stop','sfa_uninstall', 'sfi_clean', SEPSFA,
        'sfa_get_expires', SEPSFA,
        'plc_db_dump' , 'plc_db_restore', SEP,
        'check_netflow','check_drl', SEP,
        'slice_fs_present', 'check_initscripts', SEP,
        'standby_1_through_20','yes','no',SEP,
        'install_syslinux6', 'bonding_builds', 'bonding_nodes', SEP,
        ]
    default_bonding_steps = [
        'bonding_init_partial',
        'bonding_add_yum',
        'bonding_install_rpms', SEP,
        ]

    @staticmethod
    def printable_steps(list):
        single_line = " ".join(list) + " "
        return single_line.replace(" "+SEP+" ", " \\\n").replace(" "+SEPSFA+" ", " \\\n")
    @staticmethod
    def valid_step(step):
        return step != SEP and step != SEPSFA

    # turn off the sfa-related steps when build has skipped SFA
    # this was originally for centos5 but is still valid
    # for up to f12 as recent SFAs with sqlalchemy won't build before f14
    @staticmethod
    def _has_sfa_cached(rpms_url):
        if os.path.isfile(has_sfa_cache_filename):
            with open(has_sfa_cache_filename) as cache:
                cached = cache.read() == "yes"
            utils.header("build provides SFA (cached):{}".format(cached))
            return cached
        # warning, we're now building 'sface' so let's be a bit more picky
        # full builds are expected to return with 0 here
        utils.header("Checking if build provides SFA package...")
        retcod = utils.system("curl --silent {}/ | grep -q sfa-".format(rpms_url)) == 0
        encoded = 'yes' if retcod else 'no'
        with open(has_sfa_cache_filename,'w') as cache:
            cache.write(encoded)
        return retcod

    @staticmethod
    def check_whether_build_has_sfa(rpms_url):
        has_sfa = TestPlc._has_sfa_cached(rpms_url)
        if has_sfa:
            utils.header("build does provide SFA")
        else:
            # move all steps containing 'sfa' from default_steps to other_steps
            utils.header("SFA package not found - removing steps with sfa or sfi")
            sfa_steps = [ step for step in TestPlc.default_steps
                          if step.find('sfa') >= 0 or step.find("sfi") >= 0 ]
            TestPlc.other_steps += sfa_steps
            for step in sfa_steps:
                TestPlc.default_steps.remove(step)

    def __init__(self, plc_spec, options):
        self.plc_spec = plc_spec
        self.options = options
        self.test_ssh = TestSsh(self.plc_spec['host_box'], self.options.buildname)
        self.vserverip = plc_spec['vserverip']
        self.vservername = plc_spec['vservername']
        self.vplchostname = self.vservername.split('-')[-1]
        self.url = "https://{}:443/PLCAPI/".format(plc_spec['vserverip'])
        self.apiserver = TestApiserver(self.url, options.dry_run)
        (self.ssh_node_boot_timeout, self.ssh_node_boot_silent) = plc_spec['ssh_node_boot_timers']
        (self.ssh_node_debug_timeout, self.ssh_node_debug_silent) = plc_spec['ssh_node_debug_timers']

    def has_addresses_api(self):
        return self.apiserver.has_method('AddIpAddress')

    def name(self):
        name = self.plc_spec['name']
        return "{}.{}".format(name,self.vservername)

    def hostname(self):
        return self.plc_spec['host_box']

    def is_local(self):
        return self.test_ssh.is_local()

    # define the API methods on this object through xmlrpc
    # would help, but not strictly necessary
    def connect(self):
        pass

    def actual_command_in_guest(self,command, backslash=False):
        raw1 = self.host_to_guest(command)
        raw2 = self.test_ssh.actual_command(raw1, dry_run=self.options.dry_run, backslash=backslash)
        return raw2

    def start_guest(self):
      return utils.system(self.test_ssh.actual_command(self.start_guest_in_host(),
                                                       dry_run=self.options.dry_run))

    def stop_guest(self):
      return utils.system(self.test_ssh.actual_command(self.stop_guest_in_host(),
                                                       dry_run=self.options.dry_run))

    def run_in_guest(self, command, backslash=False):
        raw = self.actual_command_in_guest(command, backslash)
        return utils.system(raw)

    def run_in_host(self,command):
        return self.test_ssh.run_in_buildname(command, dry_run=self.options.dry_run)

    # backslashing turned out so awful at some point that I've turned off auto-backslashing
    # see e.g. plc_start esp. the version for f14
    #command gets run in the plc's vm
    def host_to_guest(self, command):
        ssh_leg = TestSsh(self.vplchostname)
        return ssh_leg.actual_command(command, keep_stdin=True)

    # this /vservers thing is legacy...
    def vm_root_in_host(self):
        return "/vservers/{}/".format(self.vservername)

    def vm_timestamp_path(self):
        return "/vservers/{}/{}.timestamp".format(self.vservername, self.vservername)

    #start/stop the vserver
    def start_guest_in_host(self):
        return "virsh -c lxc:/// start {}".format(self.vservername)

    def stop_guest_in_host(self):
        return "virsh -c lxc:/// destroy {}".format(self.vservername)

    # xxx quick n dirty
    def run_in_guest_piped(self,local,remote):
        return utils.system(local+" | "+self.test_ssh.actual_command(self.host_to_guest(remote),
                                                                     keep_stdin = True))

    def dnf_check_installed(self, rpms):
        if isinstance(rpms, list):
            rpms=" ".join(rpms)
        return self.run_in_guest("rpm -q {}".format(rpms)) == 0

    # does a yum install in the vs, ignore yum retcod, check with rpm
    def dnf_install(self, rpms):
        if isinstance(rpms, list):
            rpms=" ".join(rpms)
        yum_mode = self.run_in_guest("dnf -y install {}".format(rpms))
        if yum_mode != 0:
            self.run_in_guest("dnf -y install --allowerasing {}".format(rpms))
        # yum-complete-transaction comes with yum-utils, that is in vtest.pkgs
        # nothing similar with dnf, forget about this for now
        # self.run_in_guest("yum-complete-transaction -y")
        return self.dnf_check_installed(rpms)

    def pip_install(self, package):
        return self.run_in_guest("pip3 install {}".format(package)) == 0

    def auth_root(self):
        return {'Username'   : self.plc_spec['settings']['PLC_ROOT_USER'],
                'AuthMethod' : 'password',
                'AuthString' : self.plc_spec['settings']['PLC_ROOT_PASSWORD'],
                'Role'       : self.plc_spec['role'],
                }

    def locate_site(self,sitename):
        for site in self.plc_spec['sites']:
            if site['site_fields']['name'] == sitename:
                return site
            if site['site_fields']['login_base'] == sitename:
                return site
        raise Exception("Cannot locate site {}".format(sitename))

    def locate_node(self, nodename):
        for site in self.plc_spec['sites']:
            for node in site['nodes']:
                if node['name'] == nodename:
                    return site, node
        raise Exception("Cannot locate node {}".format(nodename))

    def locate_hostname(self, hostname):
        for site in self.plc_spec['sites']:
            for node in site['nodes']:
                if node['node_fields']['hostname'] == hostname:
                    return(site, node)
        raise Exception("Cannot locate hostname {}".format(hostname))

    def locate_key(self, key_name):
        for key in self.plc_spec['keys']:
            if key['key_name'] == key_name:
                return key
        raise Exception("Cannot locate key {}".format(key_name))

    def locate_private_key_from_key_names(self, key_names):
        # locate the first avail. key
        found = False
        for key_name in key_names:
            key_spec = self.locate_key(key_name)
            test_key = TestKey(self,key_spec)
            publickey = test_key.publicpath()
            privatekey = test_key.privatepath()
            if os.path.isfile(publickey) and os.path.isfile(privatekey):
                found = True
        if found:
            return privatekey
        else:
            return None

    def locate_slice(self, slicename):
        for slice in self.plc_spec['slices']:
            if slice['slice_fields']['name'] == slicename:
                return slice
        raise Exception("Cannot locate slice {}".format(slicename))

    def all_sliver_objs(self):
        result = []
        for slice_spec in self.plc_spec['slices']:
            slicename = slice_spec['slice_fields']['name']
            for nodename in slice_spec['nodenames']:
                result.append(self.locate_sliver_obj(nodename, slicename))
        return result

    def locate_sliver_obj(self, nodename, slicename):
        site,node = self.locate_node(nodename)
        slice = self.locate_slice(slicename)
        # build objects
        test_site = TestSite(self, site)
        test_node = TestNode(self, test_site, node)
        # xxx the slice site is assumed to be the node site - mhh - probably harmless
        test_slice = TestSlice(self, test_site, slice)
        return TestSliver(self, test_node, test_slice)

    def locate_first_node(self):
        nodename = self.plc_spec['slices'][0]['nodenames'][0]
        site,node = self.locate_node(nodename)
        test_site = TestSite(self, site)
        test_node = TestNode(self, test_site, node)
        return test_node

    def locate_first_sliver(self):
        slice_spec = self.plc_spec['slices'][0]
        slicename = slice_spec['slice_fields']['name']
        nodename = slice_spec['nodenames'][0]
        return self.locate_sliver_obj(nodename,slicename)

    # all different hostboxes used in this plc
    def get_BoxNodes(self):
        # maps on sites and nodes, return [ (host_box,test_node) ]
        tuples = []
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite(self,site_spec)
            for node_spec in site_spec['nodes']:
                test_node = TestNode(self, test_site, node_spec)
                if not test_node.is_real():
                    tuples.append( (test_node.host_box(),test_node) )
        # transform into a dict { 'host_box' -> [ test_node .. ] }
        result = {}
        for (box,node) in tuples:
            if box not in result:
                result[box] = [node]
            else:
                result[box].append(node)
        return result

    # a step for checking this stuff
    def show_boxes(self):
        'print summary of nodes location'
        for box,nodes in self.get_BoxNodes().items():
            print(box,":"," + ".join( [ node.name() for node in nodes ] ))
        return True

    # make this a valid step
    def qemu_kill_all(self):
        'kill all qemu instances on the qemu boxes involved by this setup'
        # this is the brute force version, kill all qemus on that host box
        for (box,nodes) in self.get_BoxNodes().items():
            # pass the first nodename, as we don't push template-qemu on testboxes
            nodedir = nodes[0].nodedir()
            TestBoxQemu(box, self.options.buildname).qemu_kill_all(nodedir)
        return True

    # make this a valid step
    def qemu_list_all(self):
        'list all qemu instances on the qemu boxes involved by this setup'
        for box,nodes in self.get_BoxNodes().items():
            # this is the brute force version, kill all qemus on that host box
            TestBoxQemu(box, self.options.buildname).qemu_list_all()
        return True

    # kill only the qemus related to this test
    def qemu_list_mine(self):
        'list qemu instances for our nodes'
        for (box,nodes) in self.get_BoxNodes().items():
            # the fine-grain version
            for node in nodes:
                node.list_qemu()
        return True

    # kill only the qemus related to this test
    def qemu_clean_mine(self):
        'cleanup (rm -rf) qemu instances for our nodes'
        for box,nodes in self.get_BoxNodes().items():
            # the fine-grain version
            for node in nodes:
                node.qemu_clean()
        return True

    # kill only the right qemus
    def qemu_kill_mine(self):
        'kill the qemu instances for our nodes'
        for box,nodes in self.get_BoxNodes().items():
            # the fine-grain version
            for node in nodes:
                node.kill_qemu()
        return True

    #################### display config
    def show(self):
        "show test configuration after localization"
        self.show_pass(1)
        self.show_pass(2)
        return True

    # uggly hack to make sure 'run export' only reports about the 1st plc
    # to avoid confusion - also we use 'inri_slice1' in various aliases..
    exported_id = 1
    def export(self):
        "print cut'n paste-able stuff to export env variables to your shell"
        # guess local domain from hostname
        if TestPlc.exported_id > 1:
            print("export GUESTHOSTNAME{:d}={}".format(TestPlc.exported_id, self.plc_spec['vservername']))
            return True
        TestPlc.exported_id += 1
        domain = socket.gethostname().split('.',1)[1]
        fqdn   = "{}.{}".format(self.plc_spec['host_box'], domain)
        print("export BUILD={}".format(self.options.buildname))
        print("export PLCHOSTLXC={}".format(fqdn))
        print("export GUESTNAME={}".format(self.vservername))
        print("export GUESTHOSTNAME={}.{}".format(self.vplchostname, domain))
        # find hostname of first node
        hostname, qemubox = self.all_node_infos()[0]
        print("export KVMHOST={}.{}".format(qemubox, domain))
        print("export NODE={}".format(hostname))
        return True

    # entry point
    always_display_keys=['PLC_WWW_HOST', 'nodes', 'sites']
    def show_pass(self, passno):
        for (key,val) in self.plc_spec.items():
            if not self.options.verbose and key not in TestPlc.always_display_keys:
                continue
            if passno == 2:
                if key == 'sites':
                    for site in val:
                        self.display_site_spec(site)
                        for node in site['nodes']:
                            self.display_node_spec(node)
                elif key == 'initscripts':
                    for initscript in val:
                        self.display_initscript_spec(initscript)
                elif key == 'slices':
                    for slice in val:
                        self.display_slice_spec(slice)
                elif key == 'keys':
                    for key in val:
                        self.display_key_spec(key)
            elif passno == 1:
                if key not in ['sites', 'initscripts', 'slices', 'keys']:
                    print('+   ', key, ':', val)

    def display_site_spec(self, site):
        print('+ ======== site', site['site_fields']['name'])
        for k,v in site.items():
            if not self.options.verbose and k not in TestPlc.always_display_keys:
                continue
            if k == 'nodes':
                if v:
                    print('+       ','nodes : ', end=' ')
                    for node in v:
                        print(node['node_fields']['hostname'],'', end=' ')
                    print('')
            elif k == 'users':
                if v:
                    print('+       users : ', end=' ')
                    for user in v:
                        print(user['name'],'', end=' ')
                    print('')
            elif k == 'site_fields':
                print('+       login_base', ':', v['login_base'])
            elif k == 'address_fields':
                pass
            else:
                print('+       ', end=' ')
                utils.pprint(k, v)

    def display_initscript_spec(self, initscript):
        print('+ ======== initscript', initscript['initscript_fields']['name'])

    def display_key_spec(self, key):
        print('+ ======== key', key['key_name'])

    def display_slice_spec(self, slice):
        print('+ ======== slice', slice['slice_fields']['name'])
        for k,v in slice.items():
            if k == 'nodenames':
                if v:
                    print('+       nodes : ', end=' ')
                    for nodename in v:
                        print(nodename,'', end=' ')
                    print('')
            elif k == 'usernames':
                if v:
                    print('+       users : ', end=' ')
                    for username in v:
                        print(username,'', end=' ')
                    print('')
            elif k == 'slice_fields':
                print('+       fields',':', end=' ')
                print('max_nodes=',v['max_nodes'], end=' ')
                print('')
            else:
                print('+       ',k,v)

    def display_node_spec(self, node):
        print("+           node={} host_box={}".format(node['name'], node['host_box']), end=' ')
        print("hostname=", node['node_fields']['hostname'], end=' ')
        print("ip=", node['interface_fields']['ip'])
        if self.options.verbose:
            utils.pprint("node details", node, depth=3)

    # another entry point for just showing the boxes involved
    def display_mapping(self):
        TestPlc.display_mapping_plc(self.plc_spec)
        return True

    @staticmethod
    def display_mapping_plc(plc_spec):
        print('+ MyPLC',plc_spec['name'])
        # WARNING this would not be right for lxc-based PLC's - should be harmless though
        print('+\tvserver address = root@{}:/vservers/{}'.format(plc_spec['host_box'], plc_spec['vservername']))
        print('+\tIP = {}/{}'.format(plc_spec['settings']['PLC_API_HOST'], plc_spec['vserverip']))
        for site_spec in plc_spec['sites']:
            for node_spec in site_spec['nodes']:
                TestPlc.display_mapping_node(node_spec)

    @staticmethod
    def display_mapping_node(node_spec):
        print('+   NODE {}'.format(node_spec['name']))
        print('+\tqemu box {}'.format(node_spec['host_box']))
        print('+\thostname={}'.format(node_spec['node_fields']['hostname']))

    # write a timestamp in /vservers/<>.timestamp
    # cannot be inside the vserver, that causes vserver .. build to cough
    def plcvm_timestamp(self):
        "Create a timestamp to remember creation date for this plc"
        now = int(time.time())
        # TODO-lxc check this one
        # a first approx. is to store the timestamp close to the VM root like vs does
        stamp_path = self.vm_timestamp_path()
        stamp_dir = os.path.dirname(stamp_path)
        utils.system(self.test_ssh.actual_command("mkdir -p {}".format(stamp_dir)))
        return utils.system(self.test_ssh.actual_command("echo {:d} > {}".format(now, stamp_path))) == 0

    # this is called inconditionnally at the beginning of the test sequence
    # just in case this is a rerun, so if the vm is not running it's fine
    def plcvm_delete(self):
        "vserver delete the test myplc"
        stamp_path = self.vm_timestamp_path()
        self.run_in_host("rm -f {}".format(stamp_path))
        self.run_in_host("virsh -c lxc:/// destroy {}".format(self.vservername))
        self.run_in_host("virsh -c lxc:/// undefine {}".format(self.vservername))
        self.run_in_host("rm -fr /vservers/{}".format(self.vservername))
        return True

    ### install
    # historically the build was being fetched by the tests
    # now the build pushes itself as a subdir of the tests workdir
    # so that the tests do not have to worry about extracting the build (svn, git, or whatever)
    def plcvm_create(self):
        "vserver creation (no install done)"
        # push the local build/ dir to the testplc box
        if self.is_local():
            # a full path for the local calls
            build_dir = os.path.dirname(sys.argv[0])
            # sometimes this is empty - set to "." in such a case
            if not build_dir:
                build_dir="."
            build_dir += "/build"
        else:
            # use a standard name - will be relative to remote buildname
            build_dir = "build"
            # remove for safety; do *not* mkdir first, otherwise we end up with build/build/
            self.test_ssh.rmdir(build_dir)
            self.test_ssh.copy(build_dir, recursive=True)
        # the repo url is taken from arch-rpms-url
        # with the last step (i386) removed
        repo_url = self.options.arch_rpms_url
        for level in [ 'arch' ]:
            repo_url = os.path.dirname(repo_url)

        # invoke initvm (drop support for vs)
        script = "lbuild-initvm.sh"
        script_options = ""
        # pass the vbuild-nightly options to [lv]test-initvm
        script_options += " -p {}".format(self.options.personality)
        script_options += " -d {}".format(self.options.pldistro)
        script_options += " -f {}".format(self.options.fcdistro)
        script_options += " -r {}".format(repo_url)
        vserver_name = self.vservername
        try:
            vserver_hostname = socket.gethostbyaddr(self.vserverip)[0]
            script_options += " -n {}".format(vserver_hostname)
        except:
            print("Cannot reverse lookup {}".format(self.vserverip))
            print("This is considered fatal, as this might pollute the test results")
            return False
        create_vserver="{build_dir}/{script} {script_options} {vserver_name}".format(**locals())
        return self.run_in_host(create_vserver) == 0

    ### install django through pip
    def django_install(self):
        # plcapi requires Django, that is no longer provided py fedora as an rpm
        # so we use pip instead
        """
        pip install Django
        """
        return self.pip_install('Django')

    ### install_rpm
    def plc_install(self):
        """
        yum install myplc, noderepo
        """

        # compute nodefamily
        if self.options.personality == "linux32":
            arch = "i386"
        elif self.options.personality == "linux64":
            arch = "x86_64"
        else:
            raise Exception("Unsupported personality {}".format(self.options.personality))
        nodefamily = "{}-{}-{}".format(self.options.pldistro, self.options.fcdistro, arch)

        # check it's possible to install just 'myplc-core' first
        if not self.dnf_install("myplc-core"):
            return False

        pkgs_list = []
        pkgs_list.append("myplc")
        pkgs_list.append("slicerepo-{}".format(nodefamily))
        pkgs_list.append("noderepo-{}".format(nodefamily))
        pkgs_string=" ".join(pkgs_list)
        return self.dnf_install(pkgs_list)

    def install_syslinux6(self):
        """
        install syslinux6 from the fedora21 release
        """
        key = 'http://mirror.onelab.eu/keys/RPM-GPG-KEY-fedora-21-primary'

        rpms = [
            'http://mirror.onelab.eu/fedora/releases/21/Everything/x86_64/os/Packages/s/syslinux-6.03-1.fc21.x86_64.rpm',
            'http://mirror.onelab.eu/fedora/releases/21/Everything/x86_64/os/Packages/s/syslinux-nonlinux-6.03-1.fc21.noarch.rpm',
            'http://mirror.onelab.eu/fedora/releases/21/Everything/x86_64/os/Packages/s/syslinux-perl-6.03-1.fc21.x86_64.rpm',
        ]
        # this can be done several times
        self.run_in_guest("rpm --import {key}".format(**locals()))
        return self.run_in_guest("yum -y localinstall {}".format(" ".join(rpms))) == 0

    def bonding_builds(self):
        """
        list /etc/yum.repos.d on the myplc side
        """
        self.run_in_guest("ls /etc/yum.repos.d/*partial.repo")
        return True

    def bonding_nodes(self):
        """
        List nodes known to the myplc together with their nodefamiliy
        """
        print("---------------------------------------- nodes")
        for node in self.apiserver.GetNodes(self.auth_root()):
            print("{} -> {}".format(node['hostname'],
                                    self.apiserver.GetNodeFlavour(self.auth_root(),node['hostname'])['nodefamily']))
        print("---------------------------------------- nodes")


    ###
    def mod_python(self):
        """yum install mod_python, useful on f18 and above so as to avoid broken wsgi"""
        return self.dnf_install( ['mod_python'] )

    ###
    def plc_configure(self):
        "run plc-config-tty"
        tmpname = '{}.plc-config-tty'.format(self.name())
        with open(tmpname,'w') as fileconf:
            for var, value in self.plc_spec['settings'].items():
                fileconf.write('e {}\n{}\n'.format(var, value))
            fileconf.write('w\n')
            fileconf.write('q\n')
        utils.system('cat {}'.format(tmpname))
        self.run_in_guest_piped('cat {}'.format(tmpname), 'plc-config-tty')
        utils.system('rm {}'.format(tmpname))
        return True

    # care only about f>=27
    def start_stop_systemd(self, service, start_or_stop):
        "utility to start/stop a systemd-defined service (sfa)"
        return self.run_in_guest("systemctl {} {}".format(start_or_stop, service)) == 0

    def plc_start(self):
        "start plc through systemclt"
        return self.start_stop_systemd('plc', 'start')

    def plc_stop(self):
        "stop plc through systemctl"
        return self.start_stop_systemd('plc', 'stop')

    def plcvm_start(self):
        "start the PLC vserver"
        self.start_guest()
        return True

    def plcvm_stop(self):
        "stop the PLC vserver"
        self.stop_guest()
        return True

    # stores the keys from the config for further use
    def keys_store(self):
        "stores test users ssh keys in keys/"
        for key_spec in self.plc_spec['keys']:
                TestKey(self,key_spec).store_key()
        return True

    def keys_clean(self):
        "removes keys cached in keys/"
        utils.system("rm -rf ./keys")
        return True

    # fetches the ssh keys in the plc's /etc/planetlab and stores them in keys/
    # for later direct access to the nodes
    def keys_fetch(self):
        "gets ssh keys in /etc/planetlab/ and stores them locally in keys/"
        dir="./keys"
        if not os.path.isdir(dir):
            os.mkdir(dir)
        vservername = self.vservername
        vm_root = self.vm_root_in_host()
        overall = True
        prefix = 'debug_ssh_key'
        for ext in ['pub', 'rsa'] :
            src = "{vm_root}/etc/planetlab/{prefix}.{ext}".format(**locals())
            dst = "keys/{vservername}-debug.{ext}".format(**locals())
            if self.test_ssh.fetch(src, dst) != 0:
                overall=False
        return overall

    def sites(self):
        "create sites with PLCAPI"
        return self.do_sites()

    def delete_sites(self):
        "delete sites with PLCAPI"
        return self.do_sites(action="delete")

    def do_sites(self, action="add"):
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite(self,site_spec)
            if (action != "add"):
                utils.header("Deleting site {} in {}".format(test_site.name(), self.name()))
                test_site.delete_site()
                # deleted with the site
                #test_site.delete_users()
                continue
            else:
                utils.header("Creating site {} & users in {}".format(test_site.name(), self.name()))
                test_site.create_site()
                test_site.create_users()
        return True

    def delete_all_sites(self):
        "Delete all sites in PLC, and related objects"
        print('auth_root', self.auth_root())
        sites = self.apiserver.GetSites(self.auth_root(), {}, ['site_id','login_base'])
        for site in sites:
            # keep automatic site - otherwise we shoot in our own foot, root_auth is not valid anymore
            if site['login_base'] == self.plc_spec['settings']['PLC_SLICE_PREFIX']:
                continue
            site_id = site['site_id']
            print('Deleting site_id', site_id)
            self.apiserver.DeleteSite(self.auth_root(), site_id)
        return True

    def nodes(self):
        "create nodes with PLCAPI"
        return self.do_nodes()
    def delete_nodes(self):
        "delete nodes with PLCAPI"
        return self.do_nodes(action="delete")

    def do_nodes(self, action="add"):
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite(self, site_spec)
            if action != "add":
                utils.header("Deleting nodes in site {}".format(test_site.name()))
                for node_spec in site_spec['nodes']:
                    test_node = TestNode(self, test_site, node_spec)
                    utils.header("Deleting {}".format(test_node.name()))
                    test_node.delete_node()
            else:
                utils.header("Creating nodes for site {} in {}".format(test_site.name(), self.name()))
                for node_spec in site_spec['nodes']:
                    utils.pprint('Creating node {}'.format(node_spec), node_spec)
                    test_node = TestNode(self, test_site, node_spec)
                    test_node.create_node()
        return True

    def nodegroups(self):
        "create nodegroups with PLCAPI"
        return self.do_nodegroups("add")
    def delete_nodegroups(self):
        "delete nodegroups with PLCAPI"
        return self.do_nodegroups("delete")

    YEAR = 365*24*3600
    @staticmethod
    def translate_timestamp(start, grain, timestamp):
        if timestamp < TestPlc.YEAR:
            return start + timestamp*grain
        else:
            return timestamp

    @staticmethod
    def timestamp_printable(timestamp):
        return time.strftime('%m-%d %H:%M:%S UTC', time.gmtime(timestamp))

    def leases(self):
        "create leases (on reservable nodes only, use e.g. run -c default -c resa)"
        now = int(time.time())
        grain = self.apiserver.GetLeaseGranularity(self.auth_root())
        print('API answered grain=', grain)
        start = (now//grain)*grain
        start += grain
        # find out all nodes that are reservable
        nodes = self.all_reservable_nodenames()
        if not nodes:
            utils.header("No reservable node found - proceeding without leases")
            return True
        ok = True
        # attach them to the leases as specified in plc_specs
        # this is where the 'leases' field gets interpreted as relative of absolute
        for lease_spec in self.plc_spec['leases']:
            # skip the ones that come with a null slice id
            if not lease_spec['slice']:
                continue
            lease_spec['t_from']  = TestPlc.translate_timestamp(start, grain, lease_spec['t_from'])
            lease_spec['t_until'] = TestPlc.translate_timestamp(start, grain, lease_spec['t_until'])
            lease_addition = self.apiserver.AddLeases(self.auth_root(), nodes, lease_spec['slice'],
                                                      lease_spec['t_from'], lease_spec['t_until'])
            if lease_addition['errors']:
                utils.header("Cannot create leases, {}".format(lease_addition['errors']))
                ok = False
            else:
                utils.header('Leases on nodes {} for {} from {:d} ({}) until {:d} ({})'\
                             .format(nodes, lease_spec['slice'],
                                     lease_spec['t_from'],  TestPlc.timestamp_printable(lease_spec['t_from']),
                                     lease_spec['t_until'], TestPlc.timestamp_printable(lease_spec['t_until'])))

        return ok

    def delete_leases(self):
        "remove all leases in the myplc side"
        lease_ids = [ l['lease_id'] for l in self.apiserver.GetLeases(self.auth_root())]
        utils.header("Cleaning leases {}".format(lease_ids))
        self.apiserver.DeleteLeases(self.auth_root(), lease_ids)
        return True

    def list_leases(self):
        "list all leases known to the myplc"
        leases = self.apiserver.GetLeases(self.auth_root())
        now = int(time.time())
        for l in leases:
            current = l['t_until'] >= now
            if self.options.verbose or current:
                utils.header("{} {} from {} until {}"\
                             .format(l['hostname'], l['name'],
                                     TestPlc.timestamp_printable(l['t_from']),
                                     TestPlc.timestamp_printable(l['t_until'])))
        return True

    # create nodegroups if needed, and populate
    def do_nodegroups(self, action="add"):
        # 1st pass to scan contents
        groups_dict = {}
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite(self,site_spec)
            for node_spec in site_spec['nodes']:
                test_node = TestNode(self, test_site, node_spec)
                if 'nodegroups' in node_spec:
                    nodegroupnames = node_spec['nodegroups']
                    if isinstance(nodegroupnames, str):
                        nodegroupnames = [ nodegroupnames ]
                    for nodegroupname in nodegroupnames:
                        if nodegroupname not in groups_dict:
                            groups_dict[nodegroupname] = []
                        groups_dict[nodegroupname].append(test_node.name())
        auth = self.auth_root()
        overall = True
        for (nodegroupname,group_nodes) in groups_dict.items():
            if action == "add":
                print('nodegroups:', 'dealing with nodegroup',\
                    nodegroupname, 'on nodes', group_nodes)
                # first, check if the nodetagtype is here
                tag_types = self.apiserver.GetTagTypes(auth, {'tagname':nodegroupname})
                if tag_types:
                    tag_type_id = tag_types[0]['tag_type_id']
                else:
                    tag_type_id = self.apiserver.AddTagType(auth,
                                                            {'tagname' : nodegroupname,
                                                             'description' : 'for nodegroup {}'.format(nodegroupname),
                                                             'category' : 'test'})
                print('located tag (type)', nodegroupname, 'as', tag_type_id)
                # create nodegroup
                nodegroups = self.apiserver.GetNodeGroups(auth, {'groupname' : nodegroupname})
                if not nodegroups:
                    self.apiserver.AddNodeGroup(auth, nodegroupname, tag_type_id, 'yes')
                    print('created nodegroup', nodegroupname, \
                        'from tagname', nodegroupname, 'and value', 'yes')
                # set node tag on all nodes, value='yes'
                for nodename in group_nodes:
                    try:
                        self.apiserver.AddNodeTag(auth, nodename, nodegroupname, "yes")
                    except:
                        traceback.print_exc()
                        print('node', nodename, 'seems to already have tag', nodegroupname)
                    # check anyway
                    try:
                        expect_yes = self.apiserver.GetNodeTags(auth,
                                                                {'hostname' : nodename,
                                                                 'tagname'  : nodegroupname},
                                                                ['value'])[0]['value']
                        if expect_yes != "yes":
                            print('Mismatch node tag on node',nodename,'got',expect_yes)
                            overall = False
                    except:
                        if not self.options.dry_run:
                            print('Cannot find tag', nodegroupname, 'on node', nodename)
                            overall = False
            else:
                try:
                    print('cleaning nodegroup', nodegroupname)
                    self.apiserver.DeleteNodeGroup(auth, nodegroupname)
                except:
                    traceback.print_exc()
                    overall = False
        return overall

    # a list of TestNode objs
    def all_nodes(self):
        nodes=[]
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite(self,site_spec)
            for node_spec in site_spec['nodes']:
                nodes.append(TestNode(self, test_site, node_spec))
        return nodes

    # return a list of tuples (nodename,qemuname)
    def all_node_infos(self) :
        node_infos = []
        for site_spec in self.plc_spec['sites']:
            node_infos += [ (node_spec['node_fields']['hostname'], node_spec['host_box']) \
                                for node_spec in site_spec['nodes'] ]
        return node_infos

    def all_nodenames(self):
        return [ x[0] for x in self.all_node_infos() ]
    def all_reservable_nodenames(self):
        res = []
        for site_spec in self.plc_spec['sites']:
            for node_spec in site_spec['nodes']:
                node_fields = node_spec['node_fields']
                if 'node_type' in node_fields and node_fields['node_type'] == 'reservable':
                    res.append(node_fields['hostname'])
        return res

    # silent_minutes : during the first <silent_minutes> minutes nothing gets printed
    def nodes_check_boot_state(self, target_boot_state, timeout_minutes,
                               silent_minutes, period_seconds = 15):
        if self.options.dry_run:
            print('dry_run')
            return True

        class CompleterTaskBootState(CompleterTask):
            def __init__(self, test_plc, hostname):
                self.test_plc = test_plc
                self.hostname = hostname
                self.last_boot_state = 'undef'
            def actual_run(self):
                try:
                    node = self.test_plc.apiserver.GetNodes(self.test_plc.auth_root(),
                                                            [ self.hostname ],
                                                            ['boot_state'])[0]
                    self.last_boot_state = node['boot_state']
                    return self.last_boot_state == target_boot_state
                except:
                    return False
            def message(self):
                return "CompleterTaskBootState with node {}".format(self.hostname)
            def failure_epilogue(self):
                print("node {} in state {} - expected {}"\
                    .format(self.hostname, self.last_boot_state, target_boot_state))

        timeout = timedelta(minutes=timeout_minutes)
        graceout = timedelta(minutes=silent_minutes)
        period   = timedelta(seconds=period_seconds)
        # the nodes that haven't checked yet - start with a full list and shrink over time
        utils.header("checking nodes boot state (expected {})".format(target_boot_state))
        tasks = [ CompleterTaskBootState(self,hostname) \
                      for (hostname,_) in self.all_node_infos() ]
        message = 'check_boot_state={}'.format(target_boot_state)
        return Completer(tasks, message=message).run(timeout, graceout, period)

    def nodes_booted(self):
        return self.nodes_check_boot_state('boot', timeout_minutes=30, silent_minutes=28)

    def probe_kvm_iptables(self):
        (_,kvmbox) = self.all_node_infos()[0]
        TestSsh(kvmbox).run("iptables-save")
        return True

    # probing nodes
    def check_nodes_ping(self, timeout_seconds=60, period_seconds=10):
        class CompleterTaskPingNode(CompleterTask):
            def __init__(self, hostname):
                self.hostname = hostname
            def run(self, silent):
                command="ping -c 1 -w 1 {} >& /dev/null".format(self.hostname)
                return utils.system(command, silent=silent) == 0
            def failure_epilogue(self):
                print("Cannot ping node with name {}".format(self.hostname))
        timeout = timedelta(seconds = timeout_seconds)
        graceout = timeout
        period = timedelta(seconds = period_seconds)
        node_infos = self.all_node_infos()
        tasks = [ CompleterTaskPingNode(h) for (h,_) in node_infos ]
        return Completer(tasks, message='ping_node').run(timeout, graceout, period)

    # ping node before we try to reach ssh, helpful for troubleshooting failing bootCDs
    def ping_node(self):
        "Ping nodes"
        return self.check_nodes_ping()

    def check_nodes_ssh(self, debug, timeout_minutes, silent_minutes, period_seconds=15):
        # various delays
        timeout  = timedelta(minutes=timeout_minutes)
        graceout = timedelta(minutes=silent_minutes)
        period   = timedelta(seconds=period_seconds)
        vservername = self.vservername
        if debug:
            message = "debug"
            completer_message = 'ssh_node_debug'
            local_key = "keys/{vservername}-debug.rsa".format(**locals())
        else:
            message = "boot"
            completer_message = 'ssh_node_boot'
            local_key = "keys/key_admin.rsa"
        utils.header("checking ssh access to nodes (expected in {} mode)".format(message))
        node_infos = self.all_node_infos()
        tasks = [ CompleterTaskNodeSsh(nodename, qemuname, local_key,
                                        boot_state=message, dry_run=self.options.dry_run) \
                      for (nodename, qemuname) in node_infos ]
        return Completer(tasks, message=completer_message).run(timeout, graceout, period)

    def ssh_node_debug(self):
        "Tries to ssh into nodes in debug mode with the debug ssh key"
        return self.check_nodes_ssh(debug = True,
                                    timeout_minutes = self.ssh_node_debug_timeout,
                                    silent_minutes = self.ssh_node_debug_silent)

    def ssh_node_boot(self):
        "Tries to ssh into nodes in production mode with the root ssh key"
        return self.check_nodes_ssh(debug = False,
                                    timeout_minutes = self.ssh_node_boot_timeout,
                                    silent_minutes = self.ssh_node_boot_silent)

    def node_bmlogs(self):
        "Checks that there's a non-empty dir. /var/log/bm/raw"
        return utils.system(self.actual_command_in_guest("ls /var/log/bm/raw")) == 0

    @node_mapper
    def qemu_local_init(self): pass
    @node_mapper
    def bootcd(self): pass
    @node_mapper
    def qemu_local_config(self): pass
    @node_mapper
    def qemu_export(self): pass
    @node_mapper
    def qemu_cleanlog(self): pass
    @node_mapper
    def nodestate_reinstall(self): pass
    @node_mapper
    def nodestate_upgrade(self): pass
    @node_mapper
    def nodestate_safeboot(self): pass
    @node_mapper
    def nodestate_boot(self): pass
    @node_mapper
    def nodestate_show(self): pass
    @node_mapper
    def nodedistro_f14(self): pass
    @node_mapper
    def nodedistro_f18(self): pass
    @node_mapper
    def nodedistro_f20(self): pass
    @node_mapper
    def nodedistro_f21(self): pass
    @node_mapper
    def nodedistro_f22(self): pass
    @node_mapper
    def nodedistro_show(self): pass

    ### check hooks : invoke scripts from hooks/{node,slice}
    def check_hooks_node(self):
        return self.locate_first_node().check_hooks()
    def check_hooks_sliver(self) :
        return self.locate_first_sliver().check_hooks()

    def check_hooks(self):
        "runs unit tests in the node and slice contexts - see hooks/{node,slice}"
        return self.check_hooks_node() and self.check_hooks_sliver()

    ### initscripts
    def do_check_initscripts(self):
        class CompleterTaskInitscript(CompleterTask):
            def __init__(self, test_sliver, stamp):
                self.test_sliver = test_sliver
                self.stamp = stamp
            def actual_run(self):
                return self.test_sliver.check_initscript_stamp(self.stamp)
            def message(self):
                return "initscript checker for {}".format(self.test_sliver.name())
            def failure_epilogue(self):
                print("initscript stamp {} not found in sliver {}"\
                    .format(self.stamp, self.test_sliver.name()))

        tasks = []
        for slice_spec in self.plc_spec['slices']:
            if 'initscriptstamp' not in slice_spec:
                continue
            stamp = slice_spec['initscriptstamp']
            slicename = slice_spec['slice_fields']['name']
            for nodename in slice_spec['nodenames']:
                print('nodename', nodename, 'slicename', slicename, 'stamp', stamp)
                site,node = self.locate_node(nodename)
                # xxx - passing the wrong site - probably harmless
                test_site = TestSite(self, site)
                test_slice = TestSlice(self, test_site, slice_spec)
                test_node = TestNode(self, test_site, node)
                test_sliver = TestSliver(self, test_node, test_slice)
                tasks.append(CompleterTaskInitscript(test_sliver, stamp))
        return Completer(tasks, message='check_initscripts').\
            run (timedelta(minutes=5), timedelta(minutes=4), timedelta(seconds=10))

    def check_initscripts(self):
        "check that the initscripts have triggered"
        return self.do_check_initscripts()

    def initscripts(self):
        "create initscripts with PLCAPI"
        for initscript in self.plc_spec['initscripts']:
            utils.pprint('Adding Initscript in plc {}'.format(self.plc_spec['name']), initscript)
            self.apiserver.AddInitScript(self.auth_root(), initscript['initscript_fields'])
        return True

    def delete_initscripts(self):
        "delete initscripts with PLCAPI"
        for initscript in self.plc_spec['initscripts']:
            initscript_name = initscript['initscript_fields']['name']
            print(('Attempting to delete {} in plc {}'.format(initscript_name, self.plc_spec['name'])))
            try:
                self.apiserver.DeleteInitScript(self.auth_root(), initscript_name)
                print(initscript_name, 'deleted')
            except:
                print('deletion went wrong - probably did not exist')
        return True

    ### manage slices
    def slices(self):
        "create slices with PLCAPI"
        return self.do_slices(action="add")

    def delete_slices(self):
        "delete slices with PLCAPI"
        return self.do_slices(action="delete")

    def fill_slices(self):
        "add nodes in slices with PLCAPI"
        return self.do_slices(action="fill")

    def empty_slices(self):
        "remove nodes from slices with PLCAPI"
        return self.do_slices(action="empty")

    def do_slices(self,  action="add"):
        for slice in self.plc_spec['slices']:
            site_spec = self.locate_site(slice['sitename'])
            test_site = TestSite(self,site_spec)
            test_slice=TestSlice(self,test_site,slice)
            if action == "delete":
                test_slice.delete_slice()
            elif action == "fill":
                test_slice.add_nodes()
            elif action == "empty":
                test_slice.delete_nodes()
            else:
                test_slice.create_slice()
        return True

    @slice_mapper__tasks(20, 10, 15)
    def ssh_slice(self): pass
    @slice_mapper__tasks(20, 19, 15)
    def ssh_slice_off(self): pass
    @slice_mapper__tasks(1, 1, 15)
    def slice_fs_present(self): pass
    @slice_mapper__tasks(1, 1, 15)
    def slice_fs_deleted(self): pass

    # use another name so we can exclude/ignore it from the tests on the nightly command line
    def ssh_slice_again(self): return self.ssh_slice()
    # note that simply doing ssh_slice_again=ssh_slice would kind of work too
    # but for some reason the ignore-wrapping thing would not

    @slice_mapper
    def ssh_slice_basics(self): pass
    @slice_mapper
    def check_vsys_defaults(self): pass

    @node_mapper
    def keys_clear_known_hosts(self): pass

    def plcapi_urls(self):
        """
        attempts to reach the PLCAPI with various forms for the URL
        """
        return PlcapiUrlScanner(self.auth_root(), ip=self.vserverip).scan()

    def speed_up_slices(self):
        "tweak nodemanager cycle (wait time) to 30+/-10 s"
        return self._speed_up_slices (30, 10)
    def super_speed_up_slices(self):
        "dev mode: tweak nodemanager cycle (wait time) to 5+/-1 s"
        return self._speed_up_slices(5, 1)

    def _speed_up_slices(self, p, r):
        # create the template on the server-side
        template = "{}.nodemanager".format(self.name())
        with open(template,"w") as template_file:
            template_file.write('OPTIONS="-p {} -r {} -d"\n'.format(p, r))
        in_vm = "/var/www/html/PlanetLabConf/nodemanager"
        remote = "{}/{}".format(self.vm_root_in_host(), in_vm)
        self.test_ssh.copy_abs(template, remote)
        # Add a conf file
        if not self.apiserver.GetConfFiles(self.auth_root(),
                                           {'dest' : '/etc/sysconfig/nodemanager'}):
            self.apiserver.AddConfFile(self.auth_root(),
                                        {'dest' : '/etc/sysconfig/nodemanager',
                                         'source' : 'PlanetLabConf/nodemanager',
                                         'postinstall_cmd' : 'service nm restart',})
        return True

    def debug_nodemanager(self):
        "sets verbose mode for nodemanager, and speeds up cycle even more (needs speed_up_slices first)"
        template = "{}.nodemanager".format(self.name())
        with open(template,"w") as template_file:
            template_file.write('OPTIONS="-p 10 -r 6 -v -d"\n')
        in_vm = "/var/www/html/PlanetLabConf/nodemanager"
        remote = "{}/{}".format(self.vm_root_in_host(), in_vm)
        self.test_ssh.copy_abs(template, remote)
        return True

    @node_mapper
    def qemu_start(self) : pass

    @node_mapper
    def qemu_timestamp(self) : pass

    @node_mapper
    def qemu_nodefamily(self): pass

    # when a spec refers to a node possibly on another plc
    def locate_sliver_obj_cross(self, nodename, slicename, other_plcs):
        for plc in [ self ] + other_plcs:
            try:
                return plc.locate_sliver_obj(nodename, slicename)
            except:
                pass
        raise Exception("Cannot locate sliver {}@{} among all PLCs".format(nodename, slicename))

    # implement this one as a cross step so that we can take advantage of different nodes
    # in multi-plcs mode
    def cross_check_tcp(self, other_plcs):
        "check TCP connectivity between 2 slices (or in loopback if only one is defined)"
        if 'tcp_specs' not in self.plc_spec or not self.plc_spec['tcp_specs']:
            utils.header("check_tcp: no/empty config found")
            return True
        specs = self.plc_spec['tcp_specs']
        overall = True

        # first wait for the network to be up and ready from the slices
        class CompleterTaskNetworkReadyInSliver(CompleterTask):
            def __init__(self, test_sliver):
                self.test_sliver = test_sliver
            def actual_run(self):
                return self.test_sliver.check_tcp_ready(port = 9999)
            def message(self):
                return "network ready checker for {}".format(self.test_sliver.name())
            def failure_epilogue(self):
                print("could not bind port from sliver {}".format(self.test_sliver.name()))

        sliver_specs = {}
        tasks = []
        managed_sliver_names = set()
        for spec in specs:
            # locate the TestSliver instances involved, and cache them in the spec instance
            spec['s_sliver'] = self.locate_sliver_obj_cross(spec['server_node'], spec['server_slice'], other_plcs)
            spec['c_sliver'] = self.locate_sliver_obj_cross(spec['client_node'], spec['client_slice'], other_plcs)
            message = "Will check TCP between s={} and c={}"\
                      .format(spec['s_sliver'].name(), spec['c_sliver'].name())
            if 'client_connect' in spec:
                message += " (using {})".format(spec['client_connect'])
            utils.header(message)
            # we need to check network presence in both slivers, but also
            # avoid to insert a sliver several times
            for sliver in [ spec['s_sliver'], spec['c_sliver'] ]:
                if sliver.name() not in managed_sliver_names:
                    tasks.append(CompleterTaskNetworkReadyInSliver(sliver))
                    # add this sliver's name in the set
                    managed_sliver_names .update( {sliver.name()} )

        # wait for the netork to be OK in all server sides
        if not Completer(tasks, message='check for network readiness in slivers').\
           run(timedelta(seconds=30), timedelta(seconds=24), period=timedelta(seconds=5)):
            return False

        # run server and client
        for spec in specs:
            port = spec['port']
            # server side
            # the issue here is that we have the server run in background
            # and so we have no clue if it took off properly or not
            # looks like in some cases it does not
            address = spec['s_sliver'].test_node.name()
            if not spec['s_sliver'].run_tcp_server(address, port, timeout=20):
                overall = False
                break

            # idem for the client side
            # use nodename from located sliver, unless 'client_connect' is set
            if 'client_connect' in spec:
                destination = spec['client_connect']
            else:
                destination = spec['s_sliver'].test_node.name()
            if not spec['c_sliver'].run_tcp_client(destination, port):
                overall = False
        return overall

    # painfully enough, we need to allow for some time as netflow might show up last
    def check_system_slice(self):
        "all nodes: check that a system slice is alive"
        # netflow currently not working in the lxc distro
        # drl not built at all in the wtx distro
        # if we find either of them we're happy
        return self.check_netflow() or self.check_drl()

    # expose these
    def check_netflow(self): return self._check_system_slice('netflow')
    def check_drl(self): return self._check_system_slice('drl')

    # we have the slices up already here, so it should not take too long
    def _check_system_slice(self, slicename, timeout_minutes=5, period_seconds=15):
        class CompleterTaskSystemSlice(CompleterTask):
            def __init__(self, test_node, dry_run):
                self.test_node = test_node
                self.dry_run = dry_run
            def actual_run(self):
                return self.test_node._check_system_slice(slicename, dry_run=self.dry_run)
            def message(self):
                return "System slice {} @ {}".format(slicename, self.test_node.name())
            def failure_epilogue(self):
                print("COULD not find system slice {} @ {}".format(slicename, self.test_node.name()))
        timeout = timedelta(minutes=timeout_minutes)
        silent  = timedelta(0)
        period  = timedelta(seconds=period_seconds)
        tasks = [ CompleterTaskSystemSlice(test_node, self.options.dry_run) \
                      for test_node in self.all_nodes() ]
        return Completer(tasks, message='_check_system_slice').run(timeout, silent, period)

    def plcsh_stress_test(self):
        "runs PLCAPI stress test, that checks Add/Update/Delete on all types - preserves contents"
        # install the stress-test in the plc image
        location = "/usr/share/plc_api/plcsh_stress_test.py"
        remote = "{}/{}".format(self.vm_root_in_host(), location)
        self.test_ssh.copy_abs("plcsh_stress_test.py", remote)
        command = location
        command += " -- --check"
        if self.options.size == 1:
            command +=  " --tiny"
        return self.run_in_guest(command) == 0

    # populate runs the same utility without slightly different options
    # in particular runs with --preserve (dont cleanup) and without --check
    # also it gets run twice, once with the --foreign option for creating fake foreign entries

    def sfa_install_all(self):
        "yum install sfa sfa-plc sfa-sfatables sfa-client"
        return (self.dnf_install("sfa sfa-plc sfa-sfatables sfa-client") and
                self.run_in_guest("systemctl enable sfa-registry")==0 and
                self.run_in_guest("systemctl enable sfa-aggregate")==0)

    def sfa_install_core(self):
        "yum install sfa"
        return self.dnf_install("sfa")

    def sfa_install_plc(self):
        "yum install sfa-plc"
        return self.dnf_install("sfa-plc")

    def sfa_install_sfatables(self):
        "yum install sfa-sfatables"
        return self.dnf_install("sfa-sfatables")

    # for some very odd reason, this sometimes fails with the following symptom
    # # yum install sfa-client
    # Setting up Install Process
    # ...
    # Downloading Packages:
    # Running rpm_check_debug
    # Running Transaction Test
    # Transaction Test Succeeded
    # Running Transaction
    # Transaction couldn't start:
    # installing package sfa-client-2.1-7.onelab.2012.05.23.i686 needs 68KB on the / filesystem
    # [('installing package sfa-client-2.1-7.onelab.2012.05.23.i686 needs 68KB on the / filesystem', (9, '/', 69632L))]
    # even though in the same context I have
    # [2012.05.23--f14-32-sfastd1-1-vplc07] / # df -h
    # Filesystem            Size  Used Avail Use% Mounted on
    # /dev/hdv1             806G  264G  501G  35% /
    # none                   16M   36K   16M   1% /tmp
    #
    # so as a workaround, we first try yum install, and then invoke rpm on the cached rpm...
    def sfa_install_client(self):
        "yum install sfa-client"
        first_try = self.dnf_install("sfa-client")
        if first_try:
            return True
        utils.header("********** Regular yum failed - special workaround in place, 2nd chance")
        code, cached_rpm_path = \
                utils.output_of(self.actual_command_in_guest('find /var/cache/yum -name sfa-client\*.rpm'))
        utils.header("rpm_path=<<{}>>".format(rpm_path))
        # just for checking
        self.run_in_guest("rpm -i {}".format(cached_rpm_path))
        return self.dnf_check_installed("sfa-client")

    def sfa_dbclean(self):
        "thoroughly wipes off the SFA database"
        return self.run_in_guest("sfaadmin reg nuke") == 0 or \
            self.run_in_guest("sfa-nuke.py") == 0 or \
            self.run_in_guest("sfa-nuke-plc.py") == 0 or \
            self.run_in_guest("sfaadmin registry nuke") == 0

    def sfa_fsclean(self):
        "cleanup /etc/sfa/trusted_roots and /var/lib/sfa"
        self.run_in_guest("rm -rf /etc/sfa/trusted_roots /var/lib/sfa/authorities")
        return True

    def sfa_plcclean(self):
        "cleans the PLC entries that were created as a side effect of running the script"
        # ignore result
        sfa_spec = self.plc_spec['sfa']

        for auth_sfa_spec in sfa_spec['auth_sfa_specs']:
            login_base = auth_sfa_spec['login_base']
            try:
                self.apiserver.DeleteSite(self.auth_root(),login_base)
            except:
                print("Site {} already absent from PLC db".format(login_base))

            for spec_name in ['pi_spec','user_spec']:
                user_spec = auth_sfa_spec[spec_name]
                username = user_spec['email']
                try:
                    self.apiserver.DeletePerson(self.auth_root(),username)
                except:
                    # this in fact is expected as sites delete their members
                    #print "User {} already absent from PLC db".format(username)
                    pass

        print("REMEMBER TO RUN sfa_import AGAIN")
        return True

    def sfa_uninstall(self):
        "uses rpm to uninstall sfa - ignore result"
        self.run_in_guest("rpm -e sfa sfa-sfatables sfa-client sfa-plc")
        self.run_in_guest("rm -rf /var/lib/sfa")
        self.run_in_guest("rm -rf /etc/sfa")
        self.run_in_guest("rm -rf /var/log/sfa_access.log /var/log/sfa_import_plc.log /var/log/sfa.daemon")
        # xxx tmp
        self.run_in_guest("rpm -e --noscripts sfa-plc")
        return True

    ### run unit tests for SFA
    # NOTE: for some reason on f14/i386, yum install sfa-tests fails for no reason
    # Running Transaction
    # Transaction couldn't start:
    # installing package sfa-tests-1.0-21.onelab.i686 needs 204KB on the / filesystem
    # [('installing package sfa-tests-1.0-21.onelab.i686 needs 204KB on the / filesystem', (9, '/', 208896L))]
    # no matter how many Gbs are available on the testplc
    # could not figure out what's wrong, so...
    # if the yum install phase fails, consider the test is successful
    # other combinations will eventually run it hopefully
    def sfa_utest(self):
        "dnf install sfa-tests and run SFA unittests"
        self.run_in_guest("dnf -y install sfa-tests")
        # failed to install - forget it
        if self.run_in_guest("rpm -q sfa-tests") != 0:
            utils.header("WARNING: SFA unit tests failed to install, ignoring")
            return True
        return self.run_in_guest("/usr/share/sfa/tests/testAll.py") == 0

    ###
    def confdir(self):
        dirname = "conf.{}".format(self.plc_spec['name'])
        if not os.path.isdir(dirname):
            utils.system("mkdir -p {}".format(dirname))
        if not os.path.isdir(dirname):
            raise Exception("Cannot create config dir for plc {}".format(self.name()))
        return dirname

    def conffile(self, filename):
        return "{}/{}".format(self.confdir(), filename)
    def confsubdir(self, dirname, clean, dry_run=False):
        subdirname = "{}/{}".format(self.confdir(), dirname)
        if clean:
            utils.system("rm -rf {}".format(subdirname))
        if not os.path.isdir(subdirname):
            utils.system("mkdir -p {}".format(subdirname))
        if not dry_run and not os.path.isdir(subdirname):
            raise "Cannot create config subdir {} for plc {}".format(dirname, self.name())
        return subdirname

    def conffile_clean(self, filename):
        filename=self.conffile(filename)
        return utils.system("rm -rf {}".format(filename))==0

    ###
    def sfa_configure(self):
        "run sfa-config-tty"
        tmpname = self.conffile("sfa-config-tty")
        with open(tmpname,'w') as fileconf:
            for var, value in self.plc_spec['sfa']['settings'].items():
                fileconf.write('e {}\n{}\n'.format(var, value))
            fileconf.write('w\n')
            fileconf.write('R\n')
            fileconf.write('q\n')
        utils.system('cat {}'.format(tmpname))
        self.run_in_guest_piped('cat {}'.format(tmpname), 'sfa-config-tty')
        return True

    def aggregate_xml_line(self):
        port = self.plc_spec['sfa']['neighbours-port']
        return '<aggregate addr="{}" hrn="{}" port="{}"/>'\
            .format(self.vserverip, self.plc_spec['sfa']['settings']['SFA_REGISTRY_ROOT_AUTH'], port)

    def registry_xml_line(self):
        return '<registry addr="{}" hrn="{}" port="12345"/>'\
            .format(self.vserverip, self.plc_spec['sfa']['settings']['SFA_REGISTRY_ROOT_AUTH'])


    # a cross step that takes all other plcs in argument
    def cross_sfa_configure(self, other_plcs):
        "writes aggregates.xml and registries.xml that point to all other PLCs in the test"
        # of course with a single plc, other_plcs is an empty list
        if not other_plcs:
            return True
        agg_fname = self.conffile("agg.xml")
        with open(agg_fname,"w") as out:
            out.write("<aggregates>{}</aggregates>\n"\
                      .format(" ".join([ plc.aggregate_xml_line() for plc in other_plcs ])))
        utils.header("(Over)wrote {}".format(agg_fname))
        reg_fname=self.conffile("reg.xml")
        with open(reg_fname,"w") as out:
            out.write("<registries>{}</registries>\n"\
                      .format(" ".join([ plc.registry_xml_line() for plc in other_plcs ])))
        utils.header("(Over)wrote {}".format(reg_fname))
        return self.test_ssh.copy_abs(agg_fname,
                                      '/{}/etc/sfa/aggregates.xml'.format(self.vm_root_in_host())) == 0 \
           and self.test_ssh.copy_abs(reg_fname,
                                      '/{}/etc/sfa/registries.xml'.format(self.vm_root_in_host())) == 0

    def sfa_import(self):
        "use sfaadmin to import from plc"
        auth = self.plc_spec['sfa']['settings']['SFA_REGISTRY_ROOT_AUTH']
        return self.run_in_guest('sfaadmin reg import_registry') == 0

    def sfa_start(self):
        "start SFA through systemctl"
        return (self.start_stop_systemd('sfa-registry', 'start') and
                self.start_stop_systemd('sfa-aggregate', 'start'))


    def sfi_configure(self):
        "Create /root/sfi on the plc side for sfi client configuration"
        if self.options.dry_run:
            utils.header("DRY RUN - skipping step")
            return True
        sfa_spec = self.plc_spec['sfa']
        # cannot use auth_sfa_mapper to pass dir_name
        for slice_spec in self.plc_spec['sfa']['auth_sfa_specs']:
            test_slice = TestAuthSfa(self, slice_spec)
            dir_basename = os.path.basename(test_slice.sfi_path())
            dir_name = self.confsubdir("dot-sfi/{}".format(dir_basename),
                                       clean=True, dry_run=self.options.dry_run)
            test_slice.sfi_configure(dir_name)
            # push into the remote /root/sfi area
            location = test_slice.sfi_path()
            remote = "{}/{}".format(self.vm_root_in_host(), location)
            self.test_ssh.mkdir(remote, abs=True)
            # need to strip last level or remote otherwise we get an extra dir level
            self.test_ssh.copy_abs(dir_name, os.path.dirname(remote), recursive=True)

        return True

    def sfi_clean(self):
        "clean up /root/sfi on the plc side"
        self.run_in_guest("rm -rf /root/sfi")
        return True

    def sfa_rspec_empty(self):
        "expose a static empty rspec (ships with the tests module) in the sfi directory"
        filename = "empty-rspec.xml"
        overall = True
        for slice_spec in self.plc_spec['sfa']['auth_sfa_specs']:
            test_slice = TestAuthSfa(self, slice_spec)
            in_vm = test_slice.sfi_path()
            remote = "{}/{}".format(self.vm_root_in_host(), in_vm)
            if self.test_ssh.copy_abs(filename, remote) !=0:
                overall = False
        return overall

    @auth_sfa_mapper
    def sfa_register_site(self): pass
    @auth_sfa_mapper
    def sfa_register_pi(self): pass
    @auth_sfa_mapper
    def sfa_register_user(self): pass
    @auth_sfa_mapper
    def sfa_update_user(self): pass
    @auth_sfa_mapper
    def sfa_register_slice(self): pass
    @auth_sfa_mapper
    def sfa_renew_slice(self): pass
    @auth_sfa_mapper
    def sfa_get_expires(self): pass
    @auth_sfa_mapper
    def sfa_discover(self): pass
    @auth_sfa_mapper
    def sfa_rspec(self): pass
    @auth_sfa_mapper
    def sfa_allocate(self): pass
    @auth_sfa_mapper
    def sfa_allocate_empty(self): pass
    @auth_sfa_mapper
    def sfa_provision(self): pass
    @auth_sfa_mapper
    def sfa_provision_empty(self): pass
    @auth_sfa_mapper
    def sfa_describe(self): pass
    @auth_sfa_mapper
    def sfa_check_slice_plc(self): pass
    @auth_sfa_mapper
    def sfa_check_slice_plc_empty(self): pass
    @auth_sfa_mapper
    def sfa_update_slice(self): pass
    @auth_sfa_mapper
    def sfa_remove_user_from_slice(self): pass
    @auth_sfa_mapper
    def sfa_insert_user_in_slice(self): pass
    @auth_sfa_mapper
    def sfi_list(self): pass
    @auth_sfa_mapper
    def sfi_show_site(self): pass
    @auth_sfa_mapper
    def sfi_show_slice(self): pass
    @auth_sfa_mapper
    def sfi_show_slice_researchers(self): pass
    @auth_sfa_mapper
    def ssh_slice_sfa(self): pass
    @auth_sfa_mapper
    def sfa_delete_user(self): pass
    @auth_sfa_mapper
    def sfa_delete_slice(self): pass

    def sfa_stop(self):
        "stop sfa through systemclt"
        return (self.start_stop_systemd('sfa-aggregate', 'stop') and
                self.start_stop_systemd('sfa-registry', 'stop'))

    def populate(self):
        "creates random entries in the PLCAPI"
        # install the stress-test in the plc image
        location = "/usr/share/plc_api/plcsh_stress_test.py"
        remote = "{}/{}".format(self.vm_root_in_host(), location)
        self.test_ssh.copy_abs("plcsh_stress_test.py", remote)
        command = location
        command += " -- --preserve --short-names"
        local = (self.run_in_guest(command) == 0);
        # second run with --foreign
        command += ' --foreign'
        remote = (self.run_in_guest(command) == 0);
        return local and remote


    ####################
    @bonding_redirector
    def bonding_init_partial(self): pass

    @bonding_redirector
    def bonding_add_yum(self): pass

    @bonding_redirector
    def bonding_install_rpms(self): pass

    ####################

    def gather_logs(self):
        "gets all possible logs from plc's/qemu node's/slice's for future reference"
        # (1.a) get the plc's /var/log/ and store it locally in logs/myplc.var-log.<plcname>/*
        # (1.b) get the plc's  /var/lib/pgsql/data/pg_log/ -> logs/myplc.pgsql-log.<plcname>/*
        # (1.c) get the plc's /root/sfi -> logs/sfi.<plcname>/
        # (2) get all the nodes qemu log and store it as logs/node.qemu.<node>.log
        # (3) get the nodes /var/log and store is as logs/node.var-log.<node>/*
        # (4) as far as possible get the slice's /var/log as logs/sliver.var-log.<sliver>/*
        # (1.a)
        print("-------------------- TestPlc.gather_logs : PLC's /var/log")
        self.gather_var_logs()
        # (1.b)
        print("-------------------- TestPlc.gather_logs : PLC's /var/lib/psql/data/pg_log/")
        self.gather_pgsql_logs()
        # (1.c)
        print("-------------------- TestPlc.gather_logs : PLC's /root/sfi/")
        self.gather_root_sfi()
        # (2)
        print("-------------------- TestPlc.gather_logs : nodes's QEMU logs")
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite(self,site_spec)
            for node_spec in site_spec['nodes']:
                test_node = TestNode(self, test_site, node_spec)
                test_node.gather_qemu_logs()
        # (3)
        print("-------------------- TestPlc.gather_logs : nodes's /var/log")
        self.gather_nodes_var_logs()
        # (4)
        print("-------------------- TestPlc.gather_logs : sample sliver's /var/log")
        self.gather_slivers_var_logs()
        return True

    def gather_slivers_var_logs(self):
        for test_sliver in self.all_sliver_objs():
            remote = test_sliver.tar_var_logs()
            utils.system("mkdir -p logs/sliver.var-log.{}".format(test_sliver.name()))
            command = remote + " | tar -C logs/sliver.var-log.{} -xf -".format(test_sliver.name())
            utils.system(command)
        return True

    def gather_var_logs(self):
        utils.system("mkdir -p logs/myplc.var-log.{}".format(self.name()))
        to_plc = self.actual_command_in_guest("tar -C /var/log/ -cf - .")
        command = to_plc + "| tar -C logs/myplc.var-log.{} -xf -".format(self.name())
        utils.system(command)
        command = "chmod a+r,a+x logs/myplc.var-log.{}/httpd".format(self.name())
        utils.system(command)

    def gather_pgsql_logs(self):
        utils.system("mkdir -p logs/myplc.pgsql-log.{}".format(self.name()))
        to_plc = self.actual_command_in_guest("tar -C /var/lib/pgsql/data/pg_log/ -cf - .")
        command = to_plc + "| tar -C logs/myplc.pgsql-log.{} -xf -".format(self.name())
        utils.system(command)

    def gather_root_sfi(self):
        utils.system("mkdir -p logs/sfi.{}".format(self.name()))
        to_plc = self.actual_command_in_guest("tar -C /root/sfi/ -cf - .")
        command = to_plc + "| tar -C logs/sfi.{} -xf -".format(self.name())
        utils.system(command)

    def gather_nodes_var_logs(self):
        for site_spec in self.plc_spec['sites']:
            test_site = TestSite(self, site_spec)
            for node_spec in site_spec['nodes']:
                test_node = TestNode(self, test_site, node_spec)
                test_ssh = TestSsh(test_node.name(), key="keys/key_admin.rsa")
                command = test_ssh.actual_command("tar -C /var/log -cf - .")
                command = command + "| tar -C logs/node.var-log.{} -xf -".format(test_node.name())
                utils.system("mkdir -p logs/node.var-log.{}".format(test_node.name()))
                utils.system(command)


    # returns the filename to use for sql dump/restore, using options.dbname if set
    def dbfile(self, database):
        # uses options.dbname if it is found
        try:
            name = self.options.dbname
            if not isinstance(name, str):
                raise Exception
        except:
            t = datetime.now()
            d = t.date()
            name = str(d)
        return "/root/{}-{}.sql".format(database, name)

    def plc_db_dump(self):
        'dump the planetlab5 DB in /root in the PLC - filename has time'
        dump=self.dbfile("planetab5")
        self.run_in_guest('pg_dump -U pgsqluser planetlab5 -f '+ dump)
        utils.header('Dumped planetlab5 database in {}'.format(dump))
        return True

    def plc_db_restore(self):
        'restore the planetlab5 DB - looks broken, but run -n might help'
        dump = self.dbfile("planetab5")
        self.run_in_guest('systemctl stop httpd')
        # xxx - need another wrapper
        self.run_in_guest_piped('echo drop database planetlab5', 'psql --user=pgsqluser template1')
        self.run_in_guest('createdb -U postgres --encoding=UNICODE --owner=pgsqluser planetlab5')
        self.run_in_guest('psql -U pgsqluser planetlab5 -f ' + dump)
        ##starting httpd service
        self.run_in_guest('systemctl start httpd')

        utils.header('Database restored from ' + dump)

    @staticmethod
    def create_ignore_steps():
        for step in TestPlc.default_steps + TestPlc.other_steps:
            # default step can have a plc qualifier
            if '@' in step:
                step, qualifier = step.split('@')
            # or be defined as forced or ignored by default
            for keyword in ['_ignore','_force']:
                if step.endswith(keyword):
                    step=step.replace(keyword,'')
            if step == SEP or step == SEPSFA :
                continue
            method = getattr(TestPlc,step)
            name = step + '_ignore'
            wrapped = ignore_result(method)
#            wrapped.__doc__ = method.__doc__ + " (run in ignore-result mode)"
            setattr(TestPlc, name, wrapped)

#    @ignore_result
#    def ssh_slice_again_ignore (self): pass
#    @ignore_result
#    def check_initscripts_ignore (self): pass

    def standby_1_through_20(self):
        """convenience function to wait for a specified number of minutes"""
        pass
    @standby_generic
    def standby_1(): pass
    @standby_generic
    def standby_2(): pass
    @standby_generic
    def standby_3(): pass
    @standby_generic
    def standby_4(): pass
    @standby_generic
    def standby_5(): pass
    @standby_generic
    def standby_6(): pass
    @standby_generic
    def standby_7(): pass
    @standby_generic
    def standby_8(): pass
    @standby_generic
    def standby_9(): pass
    @standby_generic
    def standby_10(): pass
    @standby_generic
    def standby_11(): pass
    @standby_generic
    def standby_12(): pass
    @standby_generic
    def standby_13(): pass
    @standby_generic
    def standby_14(): pass
    @standby_generic
    def standby_15(): pass
    @standby_generic
    def standby_16(): pass
    @standby_generic
    def standby_17(): pass
    @standby_generic
    def standby_18(): pass
    @standby_generic
    def standby_19(): pass
    @standby_generic
    def standby_20(): pass

    # convenience for debugging the test logic
    def yes(self): return True
    def no(self): return False
    def fail(self): return False
