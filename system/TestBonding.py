"""
Utilities to create a setup made of 2 different builds
read : 2 different node flavours 
so that each myplc knows about the nodeflavour/slicefamily supported
by the other one
---
This would be the basics for running tests on multi-node myplc, 
in particular for node upgrades
"""

#################### WARNING

# this feature relies on a few assumptions that need to be taken care of
# more or less manually; this is based on the onelab.eu setup

# (*) the build host is expected to have /root/git-build.sh reasonably up-to-date
# with our build module, so we can locate partial-repo.sh
# this utility needs to be run on the build host so we can point at a PARTIAL-RPMS
# sub-repo that exposes the
# bootcd/bootstraps/ and the like rpms from one flavour to another

# a utility to create a bonding_plc_spec from
# a plc_spec and just a buildname

def onelab_bonding_spec (buildname):

    # essentially generic ..
    buildname      = buildname
    
    # visit the other build's test directory to figure its characteristics
    with open ("../{}/arg-fcdistro".format(buildname)) as input:
        fcdistro   = input.read().strip()
    with open ("../{}/arg-pldistro".format(buildname)) as input:
        pldistro   = input.read().strip()
    with open ("../{}/arg-ips-bplc".format(buildname)) as input:
        plc_box    = input.read().strip().split()[0]
    # e.g. http://build.onelab.eu/onelab//2015.03.15--f14/RPMS/x86_64
    with open ("../{}/arg-arch-rpms-url".format(buildname)) as input:
        arch_rpms_url = input.read().strip()
    arch           = arch_rpms_url.split('/')[-1]
    build_www_host = arch_rpms_url.split('/')[2]
    base_url       = arch_rpms_url.replace("RPMS/{}".format(arch), "PARTIAL-RPMS")
        
    # onelab specifics
    build_www_git = '/root/git-build/'
    build_www_dir  = '/build/{}/{}'.format(pldistro, buildname)
    
    return locals()

####################
import os, os.path
import socket

import utils
from TestSsh import TestSsh

####################
class TestBonding(object):

    """
    Holds details about a 'bonding' build
    so we can configure the local myplc (test_plc)
    for multi-flavour nodes and slices
    options is a TestMain options

    details for a bonding node (like hostname and IP) are
    computed from the underlying Substrate object and 
    stored in arg-bonding-{buildname}
    """
    
    def __init__(self, test_plc, bonding_spec, substrate, options):
        """
        test_plc is one local TestPlc instance
        bonding_spec is a dictionary that gives details on
        the build we want to be bonding with
        """
        # the local build & plc is described in options
        # the bonding build is described in bonding_spec
        self.test_plc = test_plc
        self.bonding_spec = bonding_spec
        self.substrate = substrate
        self.options = options
        # a little hacky : minimal provisioning and modify plc_spec on the fly
        self.provision()
    
    def nodefamily(self):
        return "{pldistro}-{fcdistro}-{arch}".format(**self.bonding_spec)
        
    #################### provisioning
    # store only hostname so it's either to set this manually
    def persistent_name(self):
        return "arg-bonding-{}".format(self.bonding_spec['buildname'])
    def persistent_store(self):
        with open(self.persistent_name(),'w') as f:
            f.write("{}\n".format(self.vnode_hostname))
    def persistent_load(self):
        try:
            with open(self.persistent_name()) as f:
                self.vnode_hostname = f.read().strip().split()[0]
                self.vnode_ip = socket.gethostbyname(self.vnode_hostname)
            return True
        except:
            return False

    def provision(self):
        # locate the first node in our own spec
        site_spec = self.test_plc.plc_spec['sites'][0]
        node_spec = site_spec['nodes'][0]
        # find a free IP for node
        if self.persistent_load():
            print("Re-using bonding nodes attributes from {}".format(self.persistent_name()))
        else:
            print("Sensing for an avail. IP (Could not load from {})".format(self.persistent_name()))
            vnode_pool = self.substrate.vnode_pool
            vnode_pool.sense()
            try:
                hostname, mac = vnode_pool.next_free()
                self.vnode_hostname = self.substrate.fqdn(hostname)
                self.vnode_ip = vnode_pool.get_ip(hostname)
                self.vnode_mac = mac
                self.persistent_store()
            except:
                raise Exception("Cannot provision bonding node")

        print("Bonding on node {} - {}".format(self.vnode_hostname, self.vnode_ip))

        # implement the node on another IP
        node_spec['node_fields']['hostname'] = self.vnode_hostname
        node_spec['interface_fields']['ip'] = self.vnode_ip
        # with the node flavour that goes with bonding plc
        for tag in ['arch', 'fcdistro', 'pldistro']:
            node_spec['tags'][tag] = self.bonding_spec[tag]

    #################### steps
    def init_partial(self):
        """
        runs partial-repo.sh for the bonding build
        this action takes place on the build host
        """
        test_ssh = TestSsh (self.bonding_spec['build_www_host'])
        command = "{build_www_git}/partial-repo.sh -i {build_www_dir}".\
                  format(**self.bonding_spec)
                         
        return test_ssh.run (command, dry_run = self.options.dry_run) == 0
        

    def add_yum(self):
        """
        creates a separate yum.repo file in the myplc box
        where our own build runs, and that points at the partial
        repo for the bonding build
        """

        # create a .repo file locally
        yumrepo_contents = """
[{buildname}]
name=Partial repo from bonding build {buildname}
baseurl={base_url}
enabled=1
gpgcheck=0
""".format(**self.bonding_spec)

        yumrepo_local = '{buildname}-partial.repo'.\
                        format(**self.bonding_spec)
        with open(yumrepo_local, 'w') as yumrepo_file:
            yumrepo_file.write(yumrepo_contents)
        utils.header("(Over)wrote {}".format(yumrepo_local))

        # push onto our myplc instance
        test_ssh = TestSsh (self.test_plc.vserverip)

        yumrepo_remote = '/etc/yum.repos.d/{bonding_buildname}-partial.repo'.\
                         format(bonding_buildname = self.bonding_spec['buildname'])

        if test_ssh.copy_abs (yumrepo_local, yumrepo_remote,
                              dry_run=self.options.dry_run) != 0:
            return False

        # xxx TODO looks like drupal also needs to be excluded
        # from the 2 entries in building.repo
        # otherwise subsequent yum update calls will fail

        return True
        
    def install_rpms(self):
        """
        once the 2 operations above have been performed, we can 
        actually install the various rpms that provide support for the 
        nodeflavour/slicefamily offered byt the bonding build to our own build
        """

        test_ssh = TestSsh (self.test_plc.vserverip)
        
        command1 = "yum -y update --exclude drupal"
        if test_ssh.run (command1, dry_run = self.options.dry_run) != 0:
            return False

        nodefamily = self.nodefamily()
        extra_list = [ 'bootcd', 'nodeimage', 'noderepo' ]

        extra_rpms = [ "{}-{}".format(rpm, nodefamily) for rpm in extra_list]

        command2 = "yum -y install " + " ".join(extra_rpms) 
        if test_ssh.run (command2, dry_run = self.options.dry_run) != 0:
            return False

        command3 = "/etc/plc.d/packages force"
        if test_ssh.run (command3, dry_run = self.options.dry_run) != 0:
            return False

        return True

### probably obsolete already    
if __name__ == '__main__':

    from TestPlc import TestPlc    

    from config_default import sample_test_plc_spec
    test_plc_spec = sample_test_plc_spec()
    test_plc = TestPlc (test_plc_spec)
    test_plc.show()

    print(test_plc.host_box)

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument ("-n", "--dry-run", dest='dry_run', default=False,
                         action='store_true', help="dry run")
    parser.add_argument ("build_name")
    args = parser.parse_args()

    test_bonding = TestBonding (test_plc,
                                onelab_bonding_spec(args.build_name),
                                dry_run = args.dry_run)

    test_bonding.bond ()
    
