import utils
import os

class Remote:

    def get_path(self, user = 'root'):
	path = ""
	if 'host' in self and self['host']:
	    if self['host'] not in ['localhost', self.config.hostname, None]:  
	        path += "%s@%s:" % (user, self['host']) 
	if 'vserver' in self and self['vserver']:
	    path += '/vservers/%s/' % self['vserver'] 
	if 'chroot' in self and self['chroot']:
	    path += self['chroot'] + os.sep
	#if 'homedir' in self and self['homedir']:
	#    path += self['homedir'] + os.sep
	
	return path  

    def get_command(self, command):
	# Chroot if necessary 
        if 'chroot' in self and self['chroot']:
            command = " chroot %s %s" % (self['chroot'], command)

        # Execute vserver exec if necessary
        if 'vserver' in self and self['vserver']:
            command = " vserver %s exec %s " % (self['vserver'], command)
	
	return command

    def get_remote_command(self, command):
	(command) = self.get_command(command)

	if 'host' in self and self['host'] not in ['localhost', self.config.hostname, self.config.ip]:
	    options = " -q "
            options += " -o StrictHostKeyChecking=no "
	    if 'host_rootkey' in self and self['host_rootkey']:
                options +=  " -i %s " % self['host_rootkey']
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

    def get_scp_command(self, localfile, remotefile, direction, recursive = False, user = 'root'):
	options = " -q "
	options += " -o StrictHostKeyChecking=no "
	path = ""
	host = self['host']
	if 'host_rootkey' in self and self['host_rootkey']: 
	    options += ' -i %s ' % self['host_rootkey']
	if recursive:
	    options += ' -r '
 
	path = self.get_path(user)
	if direction in ['to']:
	    command = "scp %(options)s %(localfile)s %(path)s/%(remotefile)s" % locals()
	elif direction in ['from']:
	    command = "scp %(options)s %(path)s/%(remotefile)s %(localfile)s" % locals()
	else:
	    raise Error, "Invalid direction, must be 'to' or 'from'."  
 	return command
 
    def scp_to(self, localfile, remotefile, recursive = False):
	command = self.get_scp_command(localfile, remotefile, 'to', recursive)
	return utils.commands(command)

    def scp_from(self, localfile, remotefile, recursive = False):
	command  = self.get_scp_command(localfile, remotefile, 'from', recursive)
	return utils.commands(command)
