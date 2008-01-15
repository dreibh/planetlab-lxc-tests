import os,sys
import base64
from qa.Test import Test
from qa import utils

class boot_node(Test):

    def call(self, hostname, disk_size = "500M"):
	api = self.config.api
	auth = self.config.auth
	
	# validate hostname
	nodes = api.GetNodes(auth, [hostname], ['hostname'])
	if not nodes:
	    raise Exception, "No such node %s" 

	bootimage = api.GetBootMedium(auth, hostname, 'node-iso', '')
	bootimage_path = '/tmp/%(hostname)s-bootcd.iso' % locals()

	if self.config.verbose:
            utils.header("Creating bootcd for %(hostname)s at %(bootimage_path)s" % locals())	
	# Create a temporary bootcd file
	file = open(bootimage_path, 'w')
	file.write(base64.b64decode(bootimage))
	file.close()
	
	# Create a temporary disk image
	diskimage_path = "/tmp/%(hostname)s-hda.img" % locals() 
	qemu_img_cmd = "qemu-img create %(diskimage_path)s %(disk_size)s" % locals()
	(stdin, stdout, stderr) = os.popen3(qemu_img_cmd)
	self.errors = stderr.readlines()
	if self.errors: 
	    raise Exception, "Unable to create disk image\n" + \
			    "\n".join(self.errors)

	if self.config.verbose:
            utils.header("Booting %(hostname)s" % locals())
	# Attempt to boot this node image
	bootcmd = "qemu -kernel-kqemu -hda %(diskimage_path)s -cdrom %(bootimage_path)s" % \
		  locals()
	(stdin, stdout, stderr) = os.popen3(bootcmd)
	self.errors = stderr.readlines()
	if self.errors:
            raise Exception, "Unable to boot node image\n" + \
                            "\n".join(self.errors)	
	 
	return True	
