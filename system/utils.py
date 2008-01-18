# $Id$
import time
import os
import commands
import pprint

# how could this accept a list again ?
def header(message):
    now=time.strftime("%H:%M:%S", time.localtime())
    print "*",now,'--',message

def show_spec(message,spec,depth=2):
    now=time.strftime("%H:%M:%S", time.localtime())
    print ">",now,"--",message
    pprint.PrettyPrinter(indent=6,depth=depth).pprint(spec)

def system(command):
    now=time.strftime("%H:%M:%S", time.localtime())
    print "+",now
    return os.system("set -x; " + command)

# checks whether a given hostname/ip responds to ping
ping_timeout_option = None
def check_ping (hostname):
    # check OS (support for macos)
    global ping_timeout_option
    if not ping_timeout_option:
        (status,osname) = commands.getstatusoutput("uname -s")
        if status != 0:
            raise Exception, "Cannot figure your OS name"
        if osname == "Linux":
            ping_timeout_option="-w"
        elif osname == "Darwin":
            ping_timeout_option="-t"

    command="ping -c 1 %s 1 %s"%(ping_timeout_option,hostname)
    (status,output) = commands.getstatusoutput(command)
    return status == 0
