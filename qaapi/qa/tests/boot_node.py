#!/usr/bin/python

import os
import sys
import signal
import time
import tempfile
import select
import base64
import traceback
from Test import Test
from qa import utils
from qa.Nodes import Node, Nodes

image_types = ['node-iso', 'node-usb', 'generic-iso', 'generic-usb']

def killqemu(pid):
    try:
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid,os.WNOHANG)
    except:
        pass

class boot_node(Test):
    """
    Attempts to boot the specified node using qemu. 
    """

    def state_nanny(self):
        hostname = self.hostname
        nodes = self.config.api.GetNodes(self.config.auth, [hostname], ['boot_state'])
        node = nodes[0]
        boot_state = node['boot_state']
        if True or self.config.verbose:
            utils.header("%(hostname)s boot_state is %(boot_state)s" % locals(), False) 
            
        if boot_state in ['boot']:
            self.exit = True

	if self.config.verbose:
	    if boot_state in ['boot']:
		utils.header("%(hostname)s correctly installed and booted" % locals(), False)
	    else:
		utils.header("%(hostname)s not fully booted" % locals(), False)
        self.boot_state = boot_state
        return self.exit
        
    def console_nanny(self,console_states):
        #ready = select.select([],[self.stdout],[],1)[1]
        output = 0
        if True or len(ready)>0:
            output = 1
            retry = True
            while retry:
                try:
                    lines = self.stdout.readlines()
                    retry = False
                except IOError, e:
                    pass

            #for searchstring in console_states.keys():
            #    result = line.find(searchstring)
                # if result... ret = console_states[searchstring]
            #    break
                # check result for whether we found it

            # for now just print it out
	    for line in lines:
                print line
            	utils.header(line) 
            # should be parsing for special strings that indicate whether
            # we've reached a particular state within the boot sequence

        return output

    def call(self, plc_name, hostname, image_type = 'node-iso', disk_size="17G", wait = 30):

        
	# Get this nodes configuration 
	node = self.config.get_node(hostname)
	# Which plc does this node talk to 
	plc = self.config.get_plc(plc_name)
        api = plc.config.api
        auth = plc.config.auth
	path = node.get_path()
	host = node['host']
	homedir = node['homedir']
	tmpdir = '/usr/tmp/'
	bootimage_filename = "%(hostname)s-bootcd.iso" % locals()
	diskimage_filename = "%(hostname)s-hda.img" % locals() 
	bootimage = "%(homedir)s/%(bootimage_filename)s" % locals()
	diskimage = "%(homedir)s/%(diskimage_filename)s" % locals() 
	diskimage_path = "/%(path)s/%(diskimage_filename)s" % locals() 
        bootimage_tmppath = "%(tmpdir)s/%(bootimage_filename)s" % locals()
	bootimage_path = "%(path)s/%(bootimage_filename)s" % locals()
	remote_bootimage_path = "%(homedir)s/%(bootimage_filename)s" % locals()	
	 
	# wait up to 30 minutes for a node to boot and install itself correctly
        self.hostname = hostname
        self.totaltime = 60*60*wait

	# validate hostname
	nodes = api.GetNodes(auth, [hostname], ['hostname', 'boot_state'])
	if not nodes:
	    raise Exception, "%s not found at plc  %s" % (hostname, plc['name'])
	node.update(nodes[0])

	# try reinstalling the node if it is in debug state
	if node['boot_state'] in ['dbg']:
	    if self.config.verbose:
		utils.header("%(hostname)s is in debug state. Attempting a re-install" % locals())
	    api.UpdateNode(auth, node['node_id'], {'boot_state': 'rins'}) 
	
	# Create boot image
	if self.config.verbose:
            utils.header("Creating bootcd for %(hostname)s at %(bootimage_path)s" % locals())	
	nodeimage = api.GetBootMedium(auth, hostname, image_type, '', ['serial'])
	fp = open(bootimage_tmppath, 'w')
	fp.write(base64.b64decode(nodeimage))
	fp.close()

	# Move the boot image to the nodes home directory
	node.host_commands("mkdir -p %(homedir)s" % locals())
	node.scp_to_host(bootimage_tmppath, "%(remote_bootimage_path)s" % locals())
	
	# Create a temporary disk image if it doesnt already exist or we are reinstalling
	img_check_cmd =  "ls -ld %(diskimage)s" % locals()
	(status, output) = node.host_commands(img_check_cmd, False)
	if status != 0 or node['boot_state'] in ['rins', 'inst']:
	    qemu_img_cmd = "qemu-img create -f qcow2 %(diskimage)s %(disk_size)s" % locals()
	    node.host_commands(qemu_img_cmd)

	if self.config.verbose:
            utils.header("Booting %(hostname)s" % locals())

	# Attempt to boot this node image

        # generate a temp filename to which qemu should store its pid (crappy approach)
        tmp = tempfile.mkstemp(".pid","qemu_")
        pidfile=tmp[1]
        os.unlink(pidfile)
        
	os.close(tmp[0])
        # boot node with ramsize memory
        ramsize=1024

        # always use the 64 bit version of qemu, as this will work on both 32 & 64 bit host kernels
        bootcmd = "qemu-system-x86_64" 
        # tell qemu to store its pid ina  file
        bootcmd = bootcmd + " -pidfile %(pidfile)s " % locals()
        # boot with ramsize memory
        bootcmd = bootcmd + " -m %(ramsize)s" % locals()
        # uniprocessor only
        bootcmd = bootcmd + " -smp 1"
	# redirect incomming tcp connections on specified port to guest node
	if 'redir_ssh_port' in node and node['redir_ssh_port']:
	    port = node['redir_ssh_port']
	    ip = node['nodenetworks'][0]['ip']
	    bootcmd = bootcmd + " -redir tcp:%(port)s:%(ip)s:22" % locals() 
        # no graphics support -> assume we are booting via serial console
        bootcmd = bootcmd + " -nographic"
        # boot from the supplied cdrom iso file
        bootcmd = bootcmd + " -boot d"
        bootcmd = bootcmd + " -cdrom %(bootimage)s" % locals()
        # hard disk image to use for the node
        bootcmd = bootcmd + " %(diskimage)s" % locals()
	# redirect stdout, stderr to logfile
	bootcmd = bootcmd + " 2>&1 >> %s " % (node.logfile.filename)
        
	# kill any old qemu processes for this node
	pid_cmd = "ps -elfy | grep qemu | grep %(hostname)s | awk '{print$3}'" % locals()
	(status, output) = node.host_commands(pid_cmd)
	pids = " ".join(output.split("\n")).strip() 
	if pids:
	    kill_cmd = "kill %(pids)s" % locals()  
	    (status, output) = node.host_commands(kill_cmd)
	
	time.sleep(2)
	# launch qemu
	(self.stdin, self.stdout, self.stderr) = node.host_popen3(bootcmd)
        
	# wait for qemu to start up
        time.sleep(5)
        # get qemu's pid from its pidfile (crappy approach)
	pid_cmd = "cat %(pidfile)s" % locals()
	(staus, output)  = node.host_commands(pid_cmd)
	self.pid = output.strip()   
        #fp = file(pidfile)
        #buf=fp.read()
        #self.pid=int(buf)
        #fp.close()
        #os.unlink(pidfile)
        
	# loop until the node is either fully booted, some error
        # occured, or we've reached our totaltime out
        def catch(sig, frame):
            self.totaltime = self.totaltime -1
	    utils.header("beep %d\n" %self.totaltime, False)
            total = self.totaltime
            if (total == 0) or \
                   (((total % 60)==0) and self.state_nanny()):
                killqemu(self.pid)
                self.exit = True
            else:
                signal.alarm(1)

        try:
            signal.signal(signal.SIGALRM, catch)
            signal.alarm(1)
            self.exit = False

            #console_states = {"login:":1}
            while not self.exit:
		pass
                #try:
                #    self.console_nanny(console_states)
                #except: # need a better way to catch exceptions
                #    traceback.print_exc()
                #    pass

            signal.alarm(0)
        except:
            signal.alarm(0)

        killqemu(self.pid)
	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    boot_node()(*args)  
