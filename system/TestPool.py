#
# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
#
# pool class
# 
# allows to pick an available IP among a pool
#
# input is expressed as a list of tuples (hostname,ip,user_data)
# that can be searched iteratively for a free slot
# TestPoolIP : look for a free IP address
# TestPoolQemu : look for a test_box with no qemu running
# e.g.
# pool = [ (hostname1,ip1,user_data1),  
#          (hostname2,ip2,user_data2),  
#          (hostname3,ip3,user_data2),  
#          (hostname4,ip4,user_data4) ]
# assuming that ip1 and ip3 are taken (pingable), then we'd get
# pool=TestPoolIP(pool)
# pool.next_free() -> entry2
# pool.next_free() -> entry4
# pool.next_free() -> None
# that is, even if ip2 is not busy/pingable when the second next_free() is issued

import commands
import utils

class TestPool:

    def __init__ (self, pool, options,message):
        self.pool=pool
        self.options=options
        self.busy=[]
        self.message=message

    # let's be flexible
    def match (self,triple,hostname_or_ip):
        (h,i,u)=triple
        return h.find(hostname_or_ip)>=0  or (i and i.find(hostname_or_ip)>=0) or hostname_or_ip.find(h)==0

    def locate_entry (self, hostname_or_ip):
        for (h,i,u) in self.pool:
            if self.match ( (h,i,u,), hostname_or_ip):
                self.busy.append(h)
                return (h,i,u)
        utils.header('TestPool.locate_entry: Could not locate entry for %r in pool:'%hostname_or_ip)
        return None

    # the hostnames provided (from a tracker) are considered last
    def next_free (self, tracker_hostnames):
        utils.header('TestPool is looking for a %s'%self.message)
        # create 2 lists of (h,i,u) entries, the ones not in the tracker, and the ones in the tracker
        in_track_pool=[]
        out_track_pool=[]
        for (h,i,u) in self.pool:
            in_tracker=False
            for hostname in tracker_hostnames:
                if self.match ( (h,i,u,) , hostname) : in_tracker = True
            if in_tracker: in_track_pool.append  ( (h,i,u,) )
            else:          out_track_pool.append ( (h,i,u,) )
        # consider outsiders first
        for (hostname,ip,user_data) in out_track_pool + in_track_pool:
            utils.header ('* candidate %s' % hostname)
        for (hostname,ip,user_data) in out_track_pool + in_track_pool:
            if hostname in self.busy:
                continue
            utils.header('TestPool : checking %s'%hostname)
            if self.free_hostname(hostname):
                utils.header('%s is available'%hostname)
                self.busy.append(hostname)
                return (hostname,ip,user_data)
            else:
                self.busy.append(hostname)
        raise Exception, "No space left in pool (%s)"%self.message

class TestPoolIP (TestPool):

    def __init__ (self,pool,options):
        TestPool.__init__(self,pool,options,"free IP address")

    def free_hostname (self, hostname):
        return not self.check_ping(hostname)

# OS-dependent ping option (support for macos, for convenience)
    ping_timeout_option = None
# checks whether a given hostname/ip responds to ping
    def check_ping (self,hostname):
        if not TestPoolIP.ping_timeout_option:
            (status,osname) = commands.getstatusoutput("uname -s")
            if status != 0:
                raise Exception, "TestPool: Cannot figure your OS name"
            if osname == "Linux":
                TestPoolIP.ping_timeout_option="-w"
            elif osname == "Darwin":
                TestPoolIP.ping_timeout_option="-t"

        if self.options.verbose:
            utils.header ("TestPoolIP: pinging %s"%hostname)
        command="ping -c 1 %s 1 %s"%(TestPoolIP.ping_timeout_option,hostname)
        (status,output) = commands.getstatusoutput(command)
        return status == 0

class TestPoolQemu (TestPool):
    
    def __init__ (self,pool,options):
        TestPool.__init__(self,pool,options,"free qemu box")

    def free_hostname (self, hostname):
        return not self.busy_qemu(hostname)

    # is there a qemu runing on that box already ?
    def busy_qemu (self, hostname):
        if self.options.verbose:
            utils.header("TestPoolQemu: checking for running qemu instances on %s"%hostname)
        command="ssh -o ConnectTimeout=5 root@%s ps -e -o cmd"%hostname
        (status,output) = commands.getstatusoutput(command)
        # if we fail to run that, let's assume we don't have ssh access, so
        # we pretend the box is busy
        if status!=0:
            return True
        elif output.find("qemu") >=0 :
            return True
        else:
            return False
