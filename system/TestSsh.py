# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
# class for issuing commands on a box, either local or remote
#
# the notion of 'buildname' is for providing each test run with a dir of its own
# buildname is generally the name of the build being tested, and can be considered unique
#
# thus 'run_in_buildname' mostly :
# (*) either runs locally in . - as on a local node we are already in a dedicated directory
# (*) or makes sure that there's a remote dir called 'buildname' and runs in it
#
# also, the copy operations
# (*) either do nothing if ran locally
# (*) or copy a local file into the remote 'buildname' 
# 

import sys
import os.path
import utils
import shutil

class TestSsh:
    
    # inserts a backslash before each occurence of the following chars
    # \ " ' < > & | ; ( ) $ * ~ 
    @staticmethod
    def backslash_shell_specials(command):
        result = ''
        for char in command:
            if char in "\\\"'<>&|;()$*~":
                result += '\\'+char
            else:
                result += char
        return result

    # check main IP address against the provided hostname
    @staticmethod
    def is_local_hostname(hostname):
        if hostname == "localhost":
            return True
        import socket
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            remote_ip = socket.gethostbyname(hostname)
            return local_ip == remote_ip
        except:
            utils.header("WARNING : something wrong in is_local_hostname with hostname=%s"%hostname)
            return False

    # some boxes have their working space in user's homedir (/root), 
    # some others in a dedicated area with max. space (/vservers)
    # when root is not specified we use the homedir
    def __init__(self, hostname, buildname=None, key=None, username=None, unknown_host=True, root=None):
        self.hostname = hostname
        self.buildname = buildname
        self.key = key
        self.username = username
        self.unknown_host = unknown_host
        self.root = root

    def __repr__(self):
        result = "{}@{}".format(self.username or 'root', self.hostname)
        if self.key:
            result += " <key {}>".format(self.key)
        return result

    def is_local(self):
        return TestSsh.is_local_hostname(self.hostname)
     
    std_options="-o BatchMode=yes -o StrictHostKeyChecking=no -o CheckHostIP=no -o ConnectTimeout=5 "
    unknown_option="-o UserKnownHostsFile=/dev/null "
    
    def key_part(self):
        if not self.key:
            return ""
        return "-i %s " % self.key

    def hostname_part(self):
        if not self.username:
            return self.hostname
        else:
            return "%s@%s" % (self.username,self.hostname)
    
    # command gets run on the right box
    def actual_command(self, command, keep_stdin=False, dry_run=False, backslash=True):
        if self.is_local():
            return command
        ssh_command = "ssh "
        if not dry_run:
            if not keep_stdin:
                ssh_command += "-n "
            ssh_command += TestSsh.std_options
            if self.unknown_host: ssh_command += TestSsh.unknown_option
        ssh_command += self.key_part()
        ssh_command += self.hostname_part() + " "
        if backslash:
            ssh_command += TestSsh.backslash_shell_specials(command)
        else:
            ssh_command += command
        return ssh_command

    # same in argv form
    def actual_argv (self, argv, keep_stdin=False, dry_run=False):
        if self.is_local():
            return argv
        ssh_argv = []
        ssh_argv.append('ssh')
        if not dry_run:
            if not keep_stdin:
                ssh_argv.append('-n')
            ssh_argv += TestSsh.std_options.split()
            if self.unknown_host:
                ssh_argv += TestSsh.unknown_option.split()
        ssh_argv += self.key_part().split()
        ssh_argv.append(self.hostname_part())
        ssh_argv += argv
        return ssh_argv

    def header(self, message):
        if not message:
            return
        print "===============",message
        sys.stdout.flush()

    def run(self, command, message=None, background=False, dry_run=False):
        local_command = self.actual_command(command, dry_run=dry_run)
        if dry_run:
            utils.header("DRY RUN " + local_command)
            return 0
        else:
            self.header(message)
            return utils.system(local_command, background)

    def run_in_buildname(self, command, background=False, dry_run=False):
        if self.is_local():
            return utils.system(command, background)
        self.create_buildname_once(dry_run)
        return self.run("cd %s ; %s" % (self.fullname(self.buildname), command),
                        background=background, dry_run=dry_run)

    def fullname(self, dirname):
        if self.root==None:
            return dirname
        else:
            return os.path.join(self.root,dirname)
        
    def mkdir(self, dirname=None, abs=False, dry_run=False):
        if self.is_local():
            if dirname:
                return os.path.mkdir(dirname)
            return 0
        # ab. paths remain as-is
        if not abs:
            if dirname:
                dirname = "%s/%s" % (self.buildname,dirname)
            else:
                dirname = self.buildname
            dirname = self.fullname(dirname)
        if dirname == '.':
            return
        return self.run("mkdir -p %s" % dirname, dry_run=dry_run)

    def rmdir(self, dirname=None, dry_run=False):
        if self.is_local():
            if dirname:
                return shutil.rmtree(dirname)
            return 0
        if dirname:
            dirname = "%s/%s" % (self.buildname,dirname)
        else:
            dirname = self.buildname
        dirname = self.fullname(dirname)
        return self.run("rm -rf %s" % dirname, dry_run=dry_run)

    def create_buildname_once(self, dry_run):
        if self.is_local():
            return
        # create remote buildname on demand
        try:
            self.buildname_created
        except:
            self.mkdir(dry_run=dry_run)
            self.buildname_created = True

    def copy(self, local_file, recursive=False, dry_run=False):
        if self.is_local():
            return 0
        self.create_buildname_once(dry_run)
        scp_command = "scp "
        if not dry_run:
            scp_command += TestSsh.std_options
        if recursive:
            scp_command += "-r "
        scp_command += self.key_part()
        scp_command += "%s %s:%s/%s" % (local_file, self.hostname_part(),
                                        self.fullname(self.buildname),
                                        os.path.basename(local_file) or ".")
        if dry_run:
            utils.header("DRY RUN TestSsh.copy %s" % scp_command)
            # need to be consistent with the non-dry-run mode
            return 0
        return utils.system(scp_command)

    def copy_abs(self, local_file, remote_file,
                 recursive=False, dry_run=False):
        if self.is_local():
            dest = ""
        else:
            dest = "%s:" % self.hostname_part()
        scp_command = "scp "
        scp_command += TestSsh.std_options
        if recursive:
            scp_command += "-r "
        scp_command += self.key_part()
        scp_command += "%s %s%s" % (local_file, dest, remote_file)
        if dry_run:
            utils.header("DRY RUN TestSsh.copy %s" % scp_command)
            # need to be consistent with the non-dry-run mode
            return 0
        return utils.system(scp_command)

    def copy_home(self, local_file, recursive=False):
        return self.copy_abs(local_file, os.path.basename(local_file), recursive)

    def fetch (self, remote_file, local_file, recursive=False, dry_run=False):
        if self.is_local():
            command="cp "
            if recursive:
                command += "-r "
            command += "%s %s" % (remote_file,local_file)
        else:
            command = "scp "
            if not dry_run:
                command += TestSsh.std_options
            if recursive:
                command += "-r "
            command += self.key_part()
            # absolute path - do not preprend buildname
            if remote_file.find("/") == 0:
                remote_path = remote_file
            else:
                remote_path = "%s/%s" % (self.buildname, remote_file)
                remote_path = self.fullname(remote_path)
            command += "%s:%s %s" % (self.hostname_part(), remote_path, local_file)
        return utils.system(command)

    # this is only to avoid harmless message when host cannot be identified
    # convenience only
    # the only place where this is needed is when tring to reach a slice in a node,
    # which is done from the test master box
    def clear_known_hosts(self):
        known_hosts = "%s/.ssh/known_hosts" % os.getenv("HOME")
        utils.header("Clearing entry for %s in %s" % (self.hostname, known_hosts))
        return utils.system("sed -i -e /^%s/d %s" % (self.hostname, known_hosts))
        
