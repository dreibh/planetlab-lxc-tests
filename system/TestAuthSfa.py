# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import os, os.path

import utils
from TestSsh import TestSsh
from TestUserSfa import TestUserSfa
from TestSliceSfa import TestSliceSfa


def slice_sfa_mapper (method):
    def actual(self,*args, **kwds):
        # used to map on several slices...
        overall=True
        slice_method = TestSliceSfa.__dict__[method.__name__]
        slice_spec=self.auth_sfa_spec['slice_spec']
        test_slice_sfa = TestSliceSfa(self,slice_spec)
        if not slice_method(test_slice_sfa, *args, **kwds): overall=False
        return overall
    # restore the doc text
    actual.__doc__=TestSliceSfa.__dict__[method.__name__].__doc__
    return actual


def user_sfa_mapper (method):
    def actual(self,*args, **kwds):
        overall=True
        user_method = TestUserSfa.__dict__[method.__name__]
        for user_spec in [ self.auth_sfa_spec['user_spec'] ]:
            test_user_sfa = TestUserSfa(self,user_spec)
            if not user_method(test_user_sfa, *args, **kwds): overall=False
        return overall
    # restore the doc text
    actual.__doc__=TestUserSfa.__dict__[method.__name__].__doc__
    return actual


class TestAuthSfa:

    def __init__ (self,test_plc,auth_sfa_spec):
	self.test_plc=test_plc
	self.auth_sfa_spec=auth_sfa_spec
        self.test_ssh=TestSsh(self.test_plc.test_ssh)
#        # shortcuts
        self.login_base=self.auth_sfa_spec['login_base']
#        self.piuser=self.auth_sfa_spec['piuser']
#        self.regularuser=self.auth_sfa_spec['regularuser']
#        self.slicename=self.auth_sfa_spec['slicename']
#        
#    def plc_name(self):
#        return self.auth_sfa_spec['plc_slicename']
    
    def rspec_style (self): return self.auth_sfa_spec['rspec_style']

    def sfi_path (self):
        return "/root/sfi/%s"%(self.rspec_style())

    # the hrn for the root authority
    def root_hrn (self):
        return self.test_plc.plc_spec['sfa']['SFA_REGISTRY_ROOT_AUTH']

    # the hrn for the auth/site
    def auth_hrn (self):
        return "%s.%s"%(self.root_hrn(),self.login_base)

    # something in this site (users typically); for use by classes for subobjects
    def obj_hrn (self, name):
        return "%s.%s"%(self.auth_hrn(),name)

    # xxx this needs tweaks with more recent versions of sfa that have pgv2 as the default ?
    # dir_name is local and will be pushed later on by TestPlc
    # by default set SFI_USER to the pi, we'll overload this
    # on the command line when needed
    def sfi_configure (self,dir_name):
        plc_spec=self.test_plc.plc_spec
        # cheat a bit: retrieve the global SFA spec from the plc obj
        sfa_spec=self.test_plc.plc_spec['sfa']
        # fetch keys in config spec and expose to sfi
        for spec_name in ['pi_spec','user_spec']:
            user_spec=self.auth_sfa_spec[spec_name]
            user_leaf=user_spec['name']
            key_name=user_spec['key_name']
            key_spec = self.test_plc.locate_key (key_name)
            for (kind,ext) in [ ('private', 'pkey'), ('public', 'pub') ] :
                contents=key_spec[kind]
                file_name=os.path.join(dir_name,self.obj_hrn(user_leaf))+"."+ext
                fileconf=open(file_name,'w')
                fileconf.write (contents)
                fileconf.close()
                utils.header ("(Over)wrote %s"%file_name)
        #
	file_name=dir_name + os.sep + 'sfi_config'
        fileconf=open(file_name,'w')
	SFI_AUTH=self.auth_hrn()
        fileconf.write ("SFI_AUTH='%s'"%SFI_AUTH)
	fileconf.write('\n')
        # default is to run as a PI
	SFI_USER=self.obj_hrn(self.auth_sfa_spec['pi_spec']['name'])
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
        command="sfaadmin reg register -t authority -x %s"%self.auth_hrn()
        return self.test_plc.run_in_guest(command)==0

    def sfa_add_pi (self, options):
        "bootstrap a PI user for that site"
        pi_spec = self.auth_sfa_spec['pi_spec']
        pi_hrn=self.obj_hrn(pi_spec['name'])
        pi_mail=pi_spec['email']
        # as installed by sfi_config
        pi_key=os.path.join(self.sfi_path(),self.obj_hrn(pi_spec['name']+'.pub'))
        command="sfaadmin reg register -t user -x %s --email %s --key %s"%(pi_hrn,pi_mail,pi_key)
        if self.test_plc.run_in_guest(command)!=0: return False
        command="sfaadmin reg update -t authority -x %s --pi %s"%(self.auth_hrn(),pi_hrn)
        return self.test_plc.run_in_guest(command)==0

    # run as pi
    def sfi_pi (self, command):
        pi_name=self.auth_sfa_spec['pi_spec']['name']
        return "sfi -d %s -u %s %s"%(self.sfi_path(),self.obj_hrn(pi_name), command,)
    # the sfi command line option to run as a regular user
    def sfi_user (self, command):
        user_name=self.auth_sfa_spec['user_spec']['name']
        return "sfi -d %s -u %s %s"%(self.sfi_path(),self.obj_hrn(user_name), command,)

    # user management
    @user_sfa_mapper
    def sfa_add_user (self, *args, **kwds): pass
    @user_sfa_mapper
    def sfa_update_user (self, *args, **kwds): pass
    @user_sfa_mapper
    def sfa_delete_user (self, *args, **kwds): pass

    def sfi_list (self, options):
        "run (as regular user) sfi list (on Registry)"
	return \
            self.test_plc.run_in_guest(self.sfi_user("list -r %s"%self.root_hrn()))==0 and \
            self.test_plc.run_in_guest(self.sfi_user("list %s"%(self.auth_hrn())))==0

    def sfi_show_slice (self, options):
        "run (as PI) sfi show -n <slice> (on Registry)"
        slice_spec=self.auth_sfa_spec['slice_spec']
        slice_hrn=self.obj_hrn(slice_spec['name'])
        return \
            self.test_plc.run_in_guest(self.sfi_pi("show -n %s"%slice_hrn))==0

    def sfi_show_site (self, options):
        "run (as regular user) sfi show (on Registry)"
	return \
            self.test_plc.run_in_guest(self.sfi_user("show %s"%(self.auth_hrn())))==0

    # those are step names exposed as methods of TestPlc, hence the _sfa
    @slice_sfa_mapper
    def sfa_add_slice (self, *args, **kwds): pass
    @slice_sfa_mapper
    def sfa_renew_slice (self, *args, **kwds): pass
    @slice_sfa_mapper
    def sfa_discover (self, *args, **kwds): pass
    @slice_sfa_mapper
    def sfa_create_slice (self, *args, **kwds): pass
    @slice_sfa_mapper
    def sfa_check_slice_plc (self, *args, **kwds): pass
    @slice_sfa_mapper
    def sfa_update_slice (self, *args, **kwds): pass
    @slice_sfa_mapper
    def sfa_delete_slice (self, *args, **kwds): pass
    @slice_sfa_mapper
    def ssh_slice_sfa     (self, *args, **kwds): pass

