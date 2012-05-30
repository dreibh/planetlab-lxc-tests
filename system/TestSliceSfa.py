# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import utils
import os, os.path
import datetime
import time

from TestKey import TestKey
from TestUser import TestUser
from TestNode import TestNode
from TestSsh import TestSsh
from TestUserSfa import TestUserSfa

class TestSliceSfa:

    def __init__ (self,test_plc,sfa_slice_spec):
	self.test_plc=test_plc
	self.sfa_slice_spec=sfa_slice_spec
        self.test_ssh=TestSsh(self.test_plc.test_ssh)
        # shortcuts
        self.sfa_spec=test_plc.plc_spec['sfa']
        self.piuser=self.sfa_slice_spec['piuser']
        self.regularuser=self.sfa_slice_spec['regularuser']
        self.slicename=self.sfa_slice_spec['slicename']
        self.login_base=self.sfa_slice_spec['login_base']
        
    def name(self):
        return self.sfa_slice_spec['slice_fields']['name']
    
    def rspec_style (self): return self.sfa_slice_spec['rspec_style']

    # the hrn for the site
    def auth_hrn (self):
        return self.test_plc.plc_spec['sfa']['SFA_REGISTRY_ROOT_AUTH']

    # the hrn for the site
    def site_hrn (self):
        return "%s.%s"%(self.auth_hrn(),self.login_base)

    # something in the site (users typically)
    def qualified_hrn (self, name):
        return "%s.%s"%(self.site_hrn(),name)

    # the slice hrn
    def hrn(self): return self.qualified_hrn (self.slicename)

    # result name
    def resname (self,name,ext): return "%s.%s"%(name,ext)

    def adfile (self): return self.resname("ad","rspec")
    def reqfile (self): return self.resname("req","rspec")
    def nodefile (self): return self.resname("nodes","txt")
    # xxx this needs tweaks with more recent versions of sfa that have pgv2 as the default ?
    def discover_option(self):
        if self.rspec_style()=='pg': return "-r protogeni"
        else:                        return "-r sfa"

    def sfi_path (self):
        return "/root/sfi/%s%s"%(self.slicename,self.rspec_style())

    def locate_key(self):
        for key_name in self.sfa_slice_spec['slice_key_names']:
            key_spec=self.test_plc.locate_key(key_name)
            test_key=TestKey(self.test_plc,key_spec)
            publickey=test_key.publicpath()
            privatekey=test_key.privatepath()
            if os.path.isfile(publickey) and os.path.isfile(privatekey):
                found=True
        return (found,privatekey)

    # dir_name is local and will be pushed later on by TestPlc
    # by default set SFI_USER to the pi, we'll overload this
    # on the command line when needed
    def sfi_configure (self,dir_name):
        plc_spec=self.test_plc.plc_spec
        sfa_spec=self.sfa_spec
        sfa_slice_spec=self.sfa_slice_spec
        keys=plc_spec['keys']
        # fetch keys in config spec and expose to sfi
        for (hrn_leaf,key_name) in sfa_slice_spec['hrn_keys'].items():
            key_spec = self.test_plc.locate_key (key_name)
            for (kind,ext) in [ ('private', 'pkey'), ('public', 'pub') ] :
                contents=key_spec[kind]
                file_name=os.path.join(dir_name,self.qualified_hrn(hrn_leaf))+"."+ext
                fileconf=open(file_name,'w')
                fileconf.write (contents)
                fileconf.close()
                utils.header ("(Over)wrote %s"%file_name)
        #
	file_name=dir_name + os.sep + 'sfi_config'
        fileconf=open(file_name,'w')
	SFI_AUTH="%s"%(self.site_hrn())
        fileconf.write ("SFI_AUTH='%s'"%SFI_AUTH)
	fileconf.write('\n')
	SFI_USER=SFI_AUTH + '.' + self.piuser
        fileconf.write ("SFI_USER='%s'"%SFI_USER)
	fileconf.write('\n')
	SFI_REGISTRY='http://' + sfa_spec['SFA_REGISTRY_HOST'] + ':12345/'
        fileconf.write ("SFI_REGISTRY='%s'"%SFI_REGISTRY)
	fileconf.write('\n')
	SFI_SM='http://' + sfa_spec['SFA_SM_HOST'] + ':12347/'
        fileconf.write ("SFI_SM='%s'"%SFI_SM)
	fileconf.write('\n')
        fileconf.close()
        utils.header ("(Over)wrote %s"%file_name)

    # using sfaadmin to bootstrap
    def sfa_add_site (self, options):
        "bootstrap a site using sfaadmin"
        command="sfaadmin reg register -t authority -x %s"%self.site_hrn()
        return self.test_plc.run_in_guest(command)==0

    def sfa_add_pi (self, options):
        "bootstrap a PI user for that site"
        pi_hrn=self.qualified_hrn(self.piuser)
        pi_mail=self.sfa_slice_spec['pimail']
        # as installed by sfi_config
        pi_key=os.path.join(self.sfi_path(),self.qualified_hrn(self.piuser+'.pub'))
        command="sfaadmin reg register -t user -x %s --email %s --key %s"%(pi_hrn,pi_mail,pi_key)
        if self.test_plc.run_in_guest(command)!=0: return False
        command="sfaadmin reg update -t authority -x %s --pi %s"%(self.site_hrn(),pi_hrn)
        return self.test_plc.run_in_guest(command)==0

    # user management
    def sfa_add_user (self, options):
        "add a regular user using sfi add"
        return TestUserSfa(self.test_plc, self.sfa_slice_spec, self).add_user()
    def sfa_update_user (self, options):
        "update a user record using sfi update"
        return TestUserSfa(self.test_plc, self.sfa_slice_spec, self).update_user()
    def sfa_delete_user (self, options):
	"run sfi delete"
        return TestUserSfa(self.test_plc, self.sfa_slice_spec, self).delete_user()

    # run as pi
    def sfi_pi (self, command):
        return "sfi -d %s -u %s %s"%(self.sfi_path(),self.qualified_hrn(self.piuser), command,)
    # the sfi command line option to run as a regular user
    def sfi_user (self, command):
        return "sfi -d %s -u %s %s"%(self.sfi_path(),self.qualified_hrn(self.regularuser), command,)

    # those are step names exposed as methods of TestPlc, hence the _sfa

    def sfi_list (self, options):
        "run (as regular user) sfi list (on Registry)"
	return \
            self.test_plc.run_in_guest(self.sfi_user("list -r %s"%self.auth_hrn()))==0 and \
            self.test_plc.run_in_guest(self.sfi_user("list %s"%(self.site_hrn())))==0

    def sfi_show (self, options):
        "run (as regular user) sfi show (on Registry)"
	return \
            self.test_plc.run_in_guest(self.sfi_user("show %s"%(self.site_hrn())))==0

    def sfi_slices (self, options):
        "run (as regular user) sfi slices (on SM)"
	return \
            self.test_plc.run_in_guest(self.sfi_user("slices"))==0 

    # needs to be run as pi
    def sfa_add_slice(self,options):
        "run sfi add (on Registry) from slice.xml"
        sfi_options="add"
        for (k,v) in self.sfa_slice_spec['slice_sfi_options'].items():
            sfi_options += " %s %s"%(k,v)
	return self.test_plc.run_in_guest(self.sfi_pi("%s"%(sfi_options)))==0

    # run as user
    def sfa_discover(self,options):
        "discover resources into resouces_in.rspec"
        return self.test_plc.run_in_guest(self.sfi_user(\
                "resources %s -o %s/%s"% (self.discover_option(),self.sfi_path(),self.adfile())))==0

    # run sfi create as a regular user
    def sfa_create_slice(self,options):
        "run sfi create (on SM) - 1st time"
        commands=[
            "sfiListNodes.py -i %s/%s -o %s/%s"%(self.sfi_path(),self.adfile(),self.sfi_path(),self.nodefile()),
            "sfiAddSliver.py -i %s/%s -n %s/%s -o %s/%s"%\
                (self.sfi_path(),self.adfile(),self.sfi_path(),self.nodefile(),self.sfi_path(),self.reqfile()),
            self.sfi_user("create %s %s"%(self.hrn(),self.reqfile())),
            ]
        for command in commands:
            if self.test_plc.run_in_guest(command)!=0: return False
        return True

    # all local nodes in slice ?
    def sfa_check_slice_plc (self,options):
        "check sfa_create_slice at the plcs - all local nodes should be in slice"
        slice_fields = self.sfa_slice_spec['slice_fields']
        slice_name = slice_fields['name']
        slice=self.test_plc.apiserver.GetSlices(self.test_plc.auth_root(), slice_name)[0]
        nodes=self.test_plc.apiserver.GetNodes(self.test_plc.auth_root(), {'peer_id':None})
        result=True
        for node in nodes: 
            if node['node_id'] in slice['node_ids']:
                utils.header("local node %s found in slice %s"%(node['hostname'],slice['name']))
            else:
                utils.header("ERROR - local node %s NOT FOUND in slice %s"%(node['hostname'],slice['name']))
                result=False
        return result

    # actually the same for now
    def sfa_update_slice(self,options):
        "run sfi create (on SM) on existing object"
        return self.sfa_create_slice(options)

    # run as pi
    def sfa_delete_slice(self,options):
	"run sfi delete"
	self.test_plc.run_in_guest(self.sfi_pi("delete %s"%(self.hrn(),)))
	return self.test_plc.run_in_guest(self.sfi_pi("remove -t slice %s"%(self.hrn(),)))==0

    # check the resulting sliver
    def ssh_slice_sfa(self,options,timeout_minutes=40,silent_minutes=30,period=15):
	"tries to ssh-enter the SFA slice"
        timeout = datetime.datetime.now()+datetime.timedelta(minutes=timeout_minutes)
        graceout = datetime.datetime.now()+datetime.timedelta(minutes=silent_minutes)
        # locate a key
        (found,remote_privatekey)=self.locate_key()
        if not found :
            utils.header("WARNING: Cannot find a valid key for slice %s"%self.name())
            return False

        # convert nodenames to real hostnames
        sfa_slice_spec = self.sfa_slice_spec
        restarted=[]
        tocheck=[]
        for nodename in sfa_slice_spec['nodenames']:
            (site_spec,node_spec) = self.test_plc.locate_node(nodename)
            tocheck.append(node_spec['node_fields']['hostname'])

        utils.header("checking ssh access into slice %s on nodes %r"%(self.name(),tocheck))
        utils.header("max timeout is %d minutes, silent for %d minutes (period is %s)"%\
                         (timeout_minutes,silent_minutes,period))
        while tocheck:
            for hostname in tocheck:
                (site_spec,node_spec) = self.test_plc.locate_hostname(hostname)
                date_test_ssh = TestSsh (hostname,key=remote_privatekey,username=self.name())
                command = date_test_ssh.actual_command("echo hostname ; hostname; echo id; id; echo uname -a ; uname -a")
                date = utils.system (command, silent=datetime.datetime.now() < graceout)
                if date==0:
                    utils.header("Successfuly entered slice %s on %s"%(self.name(),hostname))
                    tocheck.remove(hostname)
                else:
                    # real nodes will have been checked once in case they're up - skip if not
                    if TestNode.is_real_model(node_spec['node_fields']['model']):
                        utils.header("WARNING : Checking slice %s on real node %s skipped"%(self.name(),hostname))
                        tocheck.remove(hostname)
                    # nm restart after first failure, if requested 
                    if options.forcenm and hostname not in restarted:
                        utils.header ("forcenm option : restarting nm on %s"%hostname)
                        restart_test_ssh=TestSsh(hostname,key="keys/key_admin.rsa")
                        access=restart_test_ssh.actual_command('service nm restart')
                        if (access==0):
                            utils.header('nm restarted on %s'%hostname)
                        else:
                            utils.header('Failed to restart nm on %s'%(hostname))
                        restarted.append(hostname)
            if not tocheck:
                # we're done
                return True
            if datetime.datetime.now() > timeout:
                for hostname in tocheck:
                    utils.header("FAILURE to ssh into %s@%s"%(self.name(),hostname))
                return False
            # wait for the period
            time.sleep (period)
        # for an empty slice
        return True

