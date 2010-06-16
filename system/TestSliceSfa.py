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
	#self.slice_spec=plc_spec_sfa['slices_sfa'][0]
	self.slice_spec=slice_spec
        self.test_ssh=TestSsh(self.test_plc.test_ssh)
        
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

    def add_slice(self):
	return self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ add slice.xml")==0

    def create_slice(self):
	auth=self.test_plc.plc_spec['sfa']['SFA_REGISTRY_ROOT_AUTH']
        self.test_plc_run_in_guest("sfi.py -d /root/.sfi/ resources > /root/.sfi/resources_in.rspec")
        self.test_plc_run_in_guest("sfiListNodes.py -i resources_in.rspec -o all_nodes.txt")
        self.test_plc_run_in_guest("sfiAddSliver.py -i resources_in.rspec -n all_nodes.txt -o resources_out.rspec")
	return self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ create %s.main.fslc1 resources_out.rspec"%auth)==0

    def update_slice(self):
	auth=self.test_plc.plc_spec['sfa']['SFA_REGISTRY_ROOT_AUTH']
        self.test_plc_run_in_guest("sfi.py -d /root/.sfi/ resources > /root/.sfi/resources_in.rspec")
        self.test_plc_run_in_guest("sfiListNodes.py -i resources_in.rspec -o all_nodes.txt")
        self.test_plc_run_in_guest("sfiAddSliver.py -i resources_in.rspec -n all_nodes.txt -o resources_out.rspec")
	return self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ create %s.main.fslc1 resources_out.rspec"%auth)==0

    def delete_slice(self):
	auth=self.test_plc.plc_spec['sfa']['SFA_REGISTRY_ROOT_AUTH']
	self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ delete %s.main.fslc1"%auth)
	return self.test_plc.run_in_guest("sfi.py -d /root/.sfi/ remove -t slice %s.main.fslc1"%auth)==0

    def check_slice_sfa(self,options,timeout_minutes=40,silent_minutes=30,period=15):
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
