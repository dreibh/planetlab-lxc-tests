#
# Thierry Parmentelat - INRIA Sophia Antipolis 
#
# pool class
# 
# allows to pick an available IP among a pool
#
# input is expressed as a list of tuples ('hostname_or_ip',user_data)
# can be searched iteratively
# e.g.
# pool = [ (hostname1,ip1,user_data1),  (hostname2,ip2,user_data2),  
#          (hostname3,ip3,user_data2),  (hostname4,ip4,user_data4) ]
# assuming that ip1 and ip3 are taken (pingable), then we'd get
# pool=TestPool(pool)
# pool.next_free() -> entry2
# pool.next_free() -> entry4
# pool.next_free() -> None
# that is, even if ip2 is not busy/pingable when the second next_free() is issued

import commands
import utils

class TestPool:

    def __init__ (self, pool, options):
        self.pool=pool
        self.options=options
        self.busy=[]

    # let's be flexible
    def locate (self, hostname_or_ip, busy=False):
        for (h,i,u) in self.pool:
            if h.find(hostname_or_ip)>=0  or i.find(hostname_or_ip)>=0 :
                if busy:
                    self.busy.append(h)
                return (h,i,u)
        return None

    def next_free (self):
        # if preferred is provided, let's re-order
        for (host,ip,user_data) in self.pool:
            if host in self.busy:
                continue
            utils.header('TestPool : checking %s'%host)
            if not TestPool.check_ping (host):
                utils.header('%s is available'%host)
                self.busy.append(host)
                return (host,ip,user_data)
            else:
                self.busy.append(host)
        return None

# OS-dependent ping option (support for macos, for convenience)
    ping_timeout_option = None
# checks whether a given hostname/ip responds to ping
    @staticmethod
    def check_ping (hostname):
        if not TestPool.ping_timeout_option:
            (status,osname) = commands.getstatusoutput("uname -s")
            if status != 0:
                raise Exception, "TestPool: Cannot figure your OS name"
            if osname == "Linux":
                TestPool.ping_timeout_option="-w"
            elif osname == "Darwin":
                TestPool.ping_timeout_option="-t"

        command="ping -c 1 %s 1 %s"%(TestPool.ping_timeout_option,hostname)
        (status,output) = commands.getstatusoutput(command)
        return status == 0
