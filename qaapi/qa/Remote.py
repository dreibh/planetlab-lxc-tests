import utils
import os

class Remote:

    def get_path(self):
	path = ""
	if 'host' in self and self['host']:
	    if self['host'] not in ['localhost', self.config.hostname, None]:  
	        path += "root@host:" 
	if 'vserver' in self and self['vserver']:
	    path += '/vservers/%s/' % self['vserver'] 
	if 'chroot' in self and self['chroot']:
	    path += self['chroot'] + os.sep
	if 'homedir' in self and self['homedir']:
	    path += self['homedir'] + os.sep
	
	return path  

    def get_command(self, command):
	options = " -o StrictHostKeyChecking=no "
	# Chroot if necessary 
        if 'chroot' in self and self['chroot']:
            command = " chroot %s %s" % (self['chroot'], command)

        # Execute vserver exec if necessary
        if 'vserver' in self and self['vserver']:
            command = " vserver %s exec %s " % (self['vserver'], command)
	
	# Use root key if necessary	
	if 'host' in self and self['host'] not in ['localhost', self.config.hostname]:
            if 'rootkey' in self and self['rootkey']:
                options +=  " -i %s " % self['rootkey']

	return (command, options)

    def get_host_command(self, command):
        (command, options) = self.get_command(command)
        if 'host' in self and self['host'] not in ['localhost', self.config.hostname]:
            command = "ssh %s root@%s \"%s\" " % (options, self['host'], command)
	return command

    def get_remote_command(self, command):
	(command, options) = self.get_command(command)
	if 'type' in self and self['type'] in ['vm']:
            if 'redir_port' in self and self['redir_port']:
                options += " -p %s " % self['redir_port']	
	
	# attempt ssh self['host'] is not the machine we are running on or
	# if this is a virtual node 
	if 'host' in self and self['host'] not in ['localhost', self.config.hostname] or \
	   'type' in self and self['type'] in ['vm']:
            command = "ssh %s root@%s \"%s\" " % (options, self['host'], command)
	return command 

    def popen(self, command, fatal = True):
	command = self.get_remote_command(command)
	return utils.popen(command, fatal, self.config.verbose)

    def popen3(self, command):
	command = self.get_remote_command(command)
	return utils.popen3(command, self.config.verbose) 

    def commands(self, command, fatal = True):
	command = self.get_remote_command(command) 
	return utils.commands(command, fatal, self.config.verbose)

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

