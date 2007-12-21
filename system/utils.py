# $Id$
import time
import os
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

