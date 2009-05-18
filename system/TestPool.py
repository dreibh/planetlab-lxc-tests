#
# Thierry Parmentelat - INRIA Sophia Antipolis 
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
    def locate_entry (self, hostname_or_ip, busy=True):
        for (h,i,u) in self.pool:
            if h.find(hostname_or_ip)>=0  or (i and i.find(hostname_or_ip)>=0) :
                if busy:
                    self.busy.append(h)
                return (h,i,u)
        return None

    def next_free (self):
        if self.options.quiet:
            print 'TestPool is looking for a %s'%self.message,
        for (hostname,ip,user_data) in self.pool:
            if hostname in self.busy:
                continue
            if not self.options.quiet:
                utils.header('TestPool : checking %s'%hostname)
            if self.options.quiet:
                print '.',
            if self.free_hostname(hostname):
                if not self.options.quiet:
                    utils.header('%s is available'%hostname)
                else:
                    print ''
                self.busy.append(hostname)
                return (hostname,ip,user_data)
            else:
                self.busy.append(hostname)
        raise Exception, "No space left in pool (%s)"%self.message

class TestPoolIP (TestPool):

    def __init__ (self,pool,options):
        TestPool.__init__(self,pool,options,"free IP address")

    def free_hostname (self, hostname):
        return not TestPoolIP.check_ping(hostname)

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
        return not TestPoolQemu.busy_qemu(hostname)

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
