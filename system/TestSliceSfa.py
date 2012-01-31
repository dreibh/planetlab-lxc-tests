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

    def __init__ (self,test_plc,test_site,sfa_slice_spec):
	self.test_plc=test_plc
	self.test_site=test_site
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
    def site_hrn (self):
        return "%s.%s"%(self.test_plc.plc_spec['sfa']['SFA_REGISTRY_ROOT_AUTH'],
                        self.login_base)

    # something in the site (users typically)
    def qualified_hrn (self, name):
        return "%s.%s"%(self.site_hrn(),name)

    # the slice hrn
    def hrn(self): return self.qualified_hrn (self.slicename)

    # result name
    def resname (self,name,ext): return "%s.%s"%(name,ext)

    def addslicefile (self): return self.resname("addslice","xml")
    def addpersonfile (self): return self.resname("addperson","xml")
    def adfile (self): return self.resname("ad","rspec")
    def reqfile (self): return self.resname("req","rspec")
    def nodefile (self): return self.resname("nodes","txt")
    # xxx this needs tweaks with more recent versions of sfa that have pgv2 as the default ?
    def discover_option(self):
        if self.rspec_style()=='pg': return "-r protogeni"
        else:                        return "-r sfa"

    def sfi_path (self):
        return "/root/sfi/%s"%self.slicename

    def locate_key(self):
        for username,keyname in self.sfa_slice_spec['usernames']:
                key_spec=self.test_plc.locate_key(keyname)
                test_key=TestKey(self.test_plc,key_spec)
                publickey=test_key.publicpath()
                privatekey=test_key.privatepath()
                if os.path.isfile(publickey) and os.path.isfile(privatekey):
                    found=True
        return (found,privatekey)

    # dir_name is local and will be pushed later on by TestPlc
    # by default set SFI_USER to the pi, we'll overload this
    # on the command line when needed
    def sfi_config (self,dir_name):
        plc_spec=self.test_plc.plc_spec
        sfa_spec=self.sfa_spec
        sfa_slice_spec=self.sfa_slice_spec
        # store private key for sfa pi user
	file_name=dir_name + os.sep + self.qualified_hrn (self.piuser) + '.pkey'
        fileconf=open(file_name,'w')
        fileconf.write (plc_spec['keys'][0]['private'])
        fileconf.close()
        utils.header ("(Over)wrote %s"%file_name)
        # store private key for sfa regular user
	file_name=dir_name + os.sep + self.qualified_hrn(self.regularuser) + '.pkey'
        fileconf=open(file_name,'w')
        fileconf.write (plc_spec['keys'][1]['private'])
        fileconf.close()
        utils.header ("(Over)wrote %s"%file_name)
        #
	file_name=dir_name + os.sep + self.addpersonfile()
        fileconf=open(file_name,'w')
	fileconf.write(sfa_slice_spec['slice_person_xml'])
	fileconf.write('\n')
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
        #
	file_name=dir_name + os.sep + self.addslicefile()
        fileconf=open(file_name,'w')
	fileconf.write(sfa_slice_spec['slice_add_xml'])
	fileconf.write('\n')
        utils.header ("(Over)wrote %s"%file_name)
        fileconf.close()

    # user management
    def sfa_add_user (self, options):
        return TestUserSfa(self.test_plc, self.sfa_slice_spec, self).add_user()
    def sfa_update_user (self, options):
        return TestUserSfa(self.test_plc, self.sfa_slice_spec, self).update_user()
    def sfa_delete_user (self, options):
        return TestUserSfa(self.test_plc, self.sfa_slice_spec, self).delete_user()

    # run as pi
    def sfi_pi (self, command):
        return "sfi.py -d %s -u %s %s"%(self.sfi_path(),self.qualified_hrn(self.piuser), command,)
    # the sfi.py command line option to run as a regular user
    def sfi_user (self, command):
        return "sfi.py -d %s -u %s %s"%(self.sfi_path(),self.qualified_hrn(self.regularuser), command,)

    # those are step names exposed as methods of TestPlc, hence the _sfa
    def sfa_view (self, options):
        "run (as regular user) sfi list and sfi show (both on Registry) and sfi slices (on SM)"
	root_auth=self.test_plc.plc_spec['sfa']['SFA_REGISTRY_ROOT_AUTH']
	return \
	self.test_plc.run_in_guest(self.sfi_user("list %s"%(self.site_hrn())))==0 and \
	self.test_plc.run_in_guest(self.sfi_user("show %s"%(self.site_hrn())))==0 and \
	self.test_plc.run_in_guest(self.sfi_user("slices"))==0 

    # needs to be run as pi
    def sfa_add_slice(self,options):
	return self.test_plc.run_in_guest(self.sfi_pi("add %s"%(self.addslicefile())))==0

    # run as user
    def sfa_discover(self,options):
        return self.test_plc.run_in_guest(self.sfi_user(\
                "resources %s -o %s/%s"% (self.discover_option(),self.sfi_path(),self.adfile())))==0

    # run sfi create as a regular user
    def sfa_create_slice(self,options):
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
        return self.sfa_create_slice(options)

    # run as pi
    def sfa_delete_slice(self,options):
	self.test_plc.run_in_guest(self.sfi_pi("delete %s"%(self.hrn(),)))
	return self.test_plc.run_in_guest(self.sfi_pi("remove -t slice %s"%(self.hrn(),)))==0

    # check the resulting sliver
    def ssh_slice_sfa(self,options,timeout_minutes=40,silent_minutes=30,period=15):
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
                        restart_test_ssh=TestSsh(hostname,key="keys/key1.rsa")
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

