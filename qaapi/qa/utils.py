# $Id$
import time

# how could this accept a list again ?
def header(message):
    now=time.strftime("%H:%M:%S", time.localtime())
    print "*",now,'--',message
