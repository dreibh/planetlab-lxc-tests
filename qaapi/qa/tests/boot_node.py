#!/usr/bin/python

import os
import sys
import signal
import time
import tempfile
import select
import base64
from Test import Test
from qa import utils

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
        if self.config.verbose:
            utils.header("%(hostname)s boot_state is %(boot_state)s" % locals()) 
            
        if boot_state in ['boot', 'debug']:
            self.exit = True

	if self.config.verbose:
	    if boot_state in ['boot']:
		utils.header("%(hostname)s correctly installed and booted" % locals())
	    else:
		utils.header("%(hostname)s not fully booted" % locals())
        self.boot_state = boot_state
        return self.exit
        
    def console_nanny(self,console_states):
        ready = select.select([],[self.stdout],[],1)[1]
        output = 0
        if len(ready)>0:
            output = 1
            line = self.stdout.readline()
            for searchstring in console_states.keys():
                result = line.find(searchstring)
                # if result... ret = console_states[searchstring]
                break
                # check result for whether we found it

            # for now just print it out
            utils.header(line) 
            # should be parsing for special strings that indicate whether
            # we've reached a particular state within the boot sequence

        return output

    def call(self, hostname, image_type = 'node-iso', disk_size="4G", wait = 30):
        # wait up to 30 minutes for a node to boot and install itself correctly
        self.hostname = hostname
        self.totaltime = 60*60*wait

	api = self.config.api
	auth = self.config.auth
	tdir = "/usr/tmp/"
	
	# validate hostname
	nodes = api.GetNodes(auth, [hostname], ['hostname'])
	if not nodes:
	    raise Exception, "No such node %(hostname)s" % locals() 

	bootimage = api.GetBootMedium(auth, hostname, image_type, '')
	bootimage_path = '/%(tdir)s/%(hostname)s-bootcd.iso' % locals()

	if self.config.verbose:
            utils.header("Creating bootcd for %(hostname)s at %(bootimage_path)s" % locals())	
	# Create a temporary bootcd file
	fp = open(bootimage_path, 'w')
	fp.write(base64.b64decode(bootimage))
	fp.close()
	
	# Create a temporary disk image
	diskimage_path = "/%(tdir)s/%(hostname)s-hda.img" % locals() 
	qemu_img_cmd = "qemu-img create -f qcow2 %(diskimage_path)s %(disk_size)s" % locals()
	(stdin, stdout, stderr) = os.popen3(qemu_img_cmd)
	self.errors = stderr.readlines()
	if self.errors: 
	    raise Exception, "Unable to create disk image\n" + \
			    "\n".join(self.errors)

	if self.config.verbose:
            utils.header("Booting %(hostname)s" % locals())

	# Attempt to boot this node image

        # generate a temp filename to which qemu should store its pid (crappy approach)
        tmp = tempfile.mkstemp(".pid","qemu_")
        pidfile=tmp[1]
        os.unlink(pidfile)
        os.close(tmp[0])

        # boot node with ramsize memory
        ramsize=400

        # always use the 64 bit version of qemu, as this will work on both 32 & 64 bit host kernels
        bootcmd = "qemu-system-x86_64" 
        # tell qemu to store its pid ina  file
        bootcmd = bootcmd + " -pidfile %(pidfile)s " % locals()
        # boot with ramsize memory
        bootcmd = bootcmd + " -m %(ramsize)s" % locals()
        # uniprocessor only
        bootcmd = bootcmd + " -smp 1"
        # no graphics support -> assume we are booting via serial console
        bootcmd = bootcmd + " -nographic"
        # boot from the supplied cdrom iso file
        bootcmd = bootcmd + " -boot d"
        bootcmd = bootcmd + " -cdrom %(bootimage_path)s" % locals()
        # hard disk image to use for the node
        bootcmd = bootcmd + " %(diskimage_path)s" % locals()
        # launch qemu
	(self.stdin, self.stdout, self.stderr) = os.popen3(bootcmd)

        # wait for qemu to start up
        time.sleep(3)
        
        # get qemu's pid from its pidfile (crappy approach)
        fp = file(pidfile)
        buf=fp.read()
        self.pid=int(buf)
        fp.close()
        os.unlink(pidfile)

        # loop until the node is either fully booted, some error
        # occured, or we've reached our totaltime out
        def catch(sig, frame):
            self.totaltime = self.totaltime -1
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

            console_states = {"login:":1}
            while not self.exit:
                try:
                    self.console_nanny(console_states)
                except: # need a better way to catch exceptions
                    pass

            signal.alarm(0)
        except:
            signal.alarm(0)

        killqemu(self.pid)
	return 1

if __name__ == '__main__':
    args = tuple(sys.argv[1:])
    boot_node()(*args)  
