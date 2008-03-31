import utils
import os

class Remote:

    def get_remote_command(self, command):
	if 'chroot' in self and self['chroot']:
	    command = " chroot %s %s" % (self['chroot'], command)
	if 'vserver' in self and self['vserver']:
            command = " vserver %s exec %s " % (self['vserver'], command)
        if 'host' in self and self['host'] not in ['localhost', self.confg.hostname]:
            options = ""
            if 'rootkey' in self and self['rootkey']:
                options = "-i %s " % self['rootkey']
            command = "ssh %s root@%s \"%s\" " % (options, self['host'], command)	
	
	return command

    def popen(self, command, fatal = True):
	command = self.get_remote_command(command)
	if self.config.verbose:
	    utils.header(command)
	return utils.popen(command, fatal)

    def popen3(self, command):
	command = self.get_remote_command(command)
	if self.config.verbose:
	    utils.header(command)
	return utils.popen3(command) 

    def commands(self, command, fatal = True):
	command = self.get_remote_command(command) 
        if self.config.verbose:
	    utils.header(command)
	return utils.commands(command, fatal)

    def scp(self, src, dest):
	options = "" 
	if 'rootkey' in self and self['rootkey'] is not None:
	     options += " -i %s " % (self['rootkey']) 
	path = ""
	if 'chroot' in self and self['chroot'] is not None:
	    path += "/plc/root/"
	if 'vserver' in self and self['vserver'] is not None:
	    path += '/vservers/%s/' % self['vserver']	 	

	src_cmd = ""
	src_parts = src.split(":")
	dest_cmd = ""
	dest_parts = dest.split(":")
	command = "scp "
	if len(src_parts) == 1:
	    src_cmd = src
	elif src_parts[0].find('localhost')  != -1: 
	    src_cmd = path + os.sep + src_parts[1]
	else:
	    host, file  = src_parts[0], src_parts[1]
	    src_cmd = 'root@%(host)s:%(path)s%(file)s ' % locals()

	if len(dest_parts) == 1:
	    dest_cmd = dest
	elif dest_parts[0].find('localhost') != -1:
	    dest_cmd = path +os.sep+ dest_parts[1]
	else:
	    host, file = dest_parts[0], dest_parts[1]
	    dest_cmd = 'root@%(host)s:%(path)s%(file)s'  % locals()

	command = 'scp %(options)s %(src_cmd)s %(dest_cmd)s' % locals()
	if self.config.verbose:
	    utils.header(command)
	return utils.commands(command)	    

