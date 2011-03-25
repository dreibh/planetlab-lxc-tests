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

class TestSliceSfa:

    def __init__ (self,test_plc,test_site,slice_spec):
	self.test_plc=test_plc
	self.test_site=test_site
	self.slice_spec=slice_spec
        self.test_ssh=TestSsh(self.test_plc.test_ssh)
        # shortcuts
        self.sfa_spec=test_plc.plc_spec['sfa']
        self.piuser=self.sfa_spec['piuser']
        self.regularuser=self.sfa_spec['regularuser']
        self.slicename=self.sfa_spec['slicename']
        self.login_base=self.sfa_spec['login_base']
        
    def name(self):
        return self.slice_spec['slice_fields']['name']
    
    def locate_key(self):
        for username,keyname in self.slice_spec['usernames']:
                key_spec=self.test_plc.locate_key(keyname)
                test_key=TestKey(self.test_plc,key_spec)
                publickey=test_key.publicpath()
                privatekey=test_key.privatepath()
                if os.path.isfile(publickey) and os.path.isfile(privatekey):
                    found=True
        return (found,privatekey)

    # those are step names exposed as methods of TestPlc, hence the _sfa
    def sfa_add_slice(self,options):
	return self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ add slice.xml")==0

    def sfa_discover(self,options):
        return self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ resources -o /root/.sfi/resources_in.rspec")==0

    def sfa_create_slice(self,options):
	root_auth=self.test_plc.plc_spec['sfa']['SFA_REGISTRY_ROOT_AUTH']
        commands=[
            "sfiListNodes.py -i /root/.sfi/resources_in.rspec -o /root/.sfi/all_nodes.txt",
            "sfiAddSliver.py -i /root/.sfi/resources_in.rspec -n /root/.sfi/all_nodes.txt -o /root/.sfi/resources_out.rspec",
            "sfi.py -d /root/.sfi/ create %s.%s.%s resources_out.rspec"%(root_auth,self.login_base,self.slicename),
            ]
        for command in commands:
            if self.test_plc.run_in_guest(command)!=0: return False
        return True

    # all local nodes in slice ?
    def sfa_check_slice_plc (self,options):
        slice_fields = self.slice_spec['slice_fields']
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

    def sfa_delete_slice(self,options):
	root_auth=self.test_plc.plc_spec['sfa']['SFA_REGISTRY_ROOT_AUTH']
	self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ delete %s.%s.%s"%(root_auth,self.login_base,self.slicename))
	return self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ remove -t slice %s.%s.%s"%(root_auth,self.login_base,self.slicename))==0

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
        slice_spec = self.slice_spec
        restarted=[]
        tocheck=[]
        for nodename in slice_spec['nodenames']:
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
