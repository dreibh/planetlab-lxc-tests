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
            command = "/usr/sbin/vserver %s exec %s " % (self['vserver'], command)
	
	return command

    def get_remote_command(self, command):
	(command) = self.get_command(command)

	if 'host' in self and self['host'] not in ['localhost', self.config.hostname, self.config.ip]:
	    options = ""
            options += " -o StrictHostKeyChecking=no "
	    if 'host_rootkey' in self and self['host_rootkey']:
                options +=  " -i %s " % self['host_rootkey']
            command = "ssh %s root@%s \"%s\" " % (options, self['host'], command)
	return command 

    def popen(self, command, fatal = True):
	command = self.get_remote_command(command)
	return utils.popen(command, fatal, self.config.verbose, self.logfile)

    def popen3(self, command):
	command = self.get_remote_command(command)
	return utils.popen3(command, self.config.verbose, self.logfile) 

    def commands(self, command, fatal = True):
	command = self.get_remote_command(command) 
	return utils.commands(command, fatal, self.config.verbose, self.logfile)

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
	return utils.commands(command, logfile =  self.logfile)

    def scp_from(self, localfile, remotefile, recursive = False):
	command  = self.get_scp_command(localfile, remotefile, 'from', recursive)
	return utils.commands(command, logfile = self.logfile)

    def wget(self, url, targetdir, user = 'root'):
        if self.config.verbose:
            utils.header("Downloading %(url)s to %(targetdir)s" % locals())

        cmd_prefix = ""
        if user not in ['root']:
            cmd_prefix = " su - user -c "
        fileparts = url.split(os.sep)
        filename = fileparts[-1:][0]
        cleanup_cmd = "%(cmd_prefix)s rm -f %(targetdir)s/%(filename)s" % locals()
        print >> self.logfile, cleanup_cmd
        self.commands(cleanup_cmd, False)

        wget_cmd = "%(cmd_prefix)s wget -nH -P %(targetdir)s %(url)s" % locals()
        print >> self.logfile, wget_cmd
        self.commands(wget_cmd)

class VRemote(Remote):
    def get_remote_command(self, command, user = 'root', key = None):
        if key is None and 'rootkey' in self:
            key = self['rootkey']
        options = ""
        options += " -o StrictHostKeyChecking=no "
        if key:
            options += " -i %(key)s" % locals()
        host = self['hostname']
        if 'type' in self and self['type'] in ['vm']:
            if 'redir_ssh_port' in self and self['redir_ssh_port']:
                options += " -p %s " % self['redir_ssh_port']
            host = self.get_host_ip()
        command = "ssh %(options)s %(user)s@%(host)s \'%(command)s\'" % locals()
        return self.get_host_command(command)

    def get_scp_command(self, localfile, remotefile, direction, recursive = False, user = 'root', key = None):
        # scp options
        options = ""
        options += " -o StrictHostKeyChecking=no "
        if recursive:
            options += " -r "
        if key:
            options += " -i %(key)s "% locals()
        elif self['rootkey']:
            options += " -i %s " % self['rootkey']

        # Are we copying to a real node or a virtual node hosted
        # at another machine 
        host = self['hostname']
        if 'type' in self and self['type'] in ['vm']:
            if 'redir_ssh_port' in self and self['redir_ssh_port']:
                options += " -P %s " % self['redir_ssh_port']
            host = self.get_host_ip()

        if direction in ['to']:
            command = "scp %(options)s %(localfile)s %(user)s@%(host)s:/%(remotefile)s" % locals()
        elif direction in ['from']:
            command = "scp %(options)s %(user)s@%(host)s:/%(remotefile)s %(localfile)s" % locals()
        else:
            raise Error, "Invalid direction, must be 'to' or 'from'."
        return command

    # Host remote commands
    def host_popen(self, command, fatal = True, logfile = None):
	if logfile is None:
	    logfile = self.logfile
        command = self.get_host_command(command)
        return utils.popen(command, fatal, self.config.verbose, logfile)

    def host_popen3(self, command, logfile = None):
	if logfile is None:
	    logfile = self.logfile
        command = self.get_host_command(command)
        return utils.popen3(command, self.config.verbose, logfile)

    def host_commands(self, command, fatal = True, logfile = None):
	if logfile is None:
	    logfiile = self.logfile
        command = self.get_host_command(command)
        return utils.commands(command, fatal, self.config.verbose, logfile)

    # Slice remote commands
    def slice_popen(self, command, user = 'root', key = None, fatal = True):
        command = self.get_remote_command(command, user, key)
        return utils.popen(command, fatal, logfile = self.logfile)

    def slice_popen3(self, command, user = 'root', key = None, fatal = True):
        command = self.get_remote_command(command, user, key)
        return utils.popen3(command, fatal, self.logfile)

    def slice_commands(self, command, user = 'root', key = None, fatal = True):
        command = self.get_remote_command(command, user, key)
        return utils.commands(command, fatal, logfile = self.logfile)

    # Host scp 
    def scp_to_host(self, localfile, remotefile, recursive = False):
        command = self.get_host_scp_command(localfile, remotefile, 'to', recursive)
        return utils.commands(command, logfile = self.logfile)

    def scp_from_host(self, remotefile, localfile, recursive = False):
        command = self.get_host_scp_command(localfile, remotefile, 'from', recursive)
        return utils.commands(command, logfile = self.logfile)

    # Node scp
    def scp_to(self, localfile, remotefile, recursive = False, user = 'root', key = None):
        # if node is vm, we must scp file(s) to host machine first
        # then run scp from there
        if 'type' in self and self['type'] in ['vm']:
            fileparts = localfile.split(os.sep)
            filename = fileparts[-1:][0]
            tempfile = '/var/tmp/%(filename)s' % locals()
            self.scp_to_host(localfile, tempfile, recursive)
            command = self.get_scp_command(tempfile, remotefile, 'to', recursive, user, key)
            return self.host_commands(command, logfile = self.logfile)
        else:

            command = self.get_scp_command(localfile, remotefile, 'to', recursive, user, key)
            return utils.commands(command, logfile = self.logfile)

    def scp_from(self, remotefile, localfile, recursive = False, user = 'root', key = None):
        # if node is vm, we must scp file(s) onto host machine first
        # then run scp from there
        if 'type' in self and self['type'] in ['vm']:
            fileparts = remotefile.split(os.sep)
            filename = fileparts[-1:][0]
            tempfile = '/var/tmp/%(filename)s' % locals()
            command = self.get_scp_command(tempfile, remotefile, 'from', recursive, user, key)
            self.host_commands(command, logfile = self.logfile)
            return self.scp_from_host(tempfile, localfile, recursive)
        else:

            command = self.get_scp_command(localfile, remotefile, 'from', recursive, user, key)
            return utils.commands(command, logfile = self.logfile)

