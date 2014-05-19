# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import time, os, re, glob, sys
from pprint import PrettyPrinter

options={}

def init_options(options_arg):
    global options
    options=options_arg

# how could this accept a list again ?
def header(message):
    now=time.strftime("%H:%M:%S", time.localtime())
    print "*",now,'--',message

def pprint(message,spec,depth=2):
    now=time.strftime("%H:%M:%S", time.localtime())
    print ">",now,"--",message
    PrettyPrinter(indent=8,depth=depth).pprint(spec)



def system(command,background=False,silent=False, dry_run=None):
    dry_run = dry_run if dry_run is not None else getattr(options,'dry_run',False)
    if dry_run:
        print 'dry_run:',command
        return 0
    
    if silent :    
        if command.find(';')>=0: command = "(%s) 2> /dev/null" % command
        else: command += " 2> /dev/null"
    if background: command += " &"
    if silent:
        print '.',
        sys.stdout.flush()
    else:
        now=time.strftime("%H:%M:%S", time.localtime())
        # don't show in summary
        print "->",now,'--',
        sys.stdout.flush()
    if not silent:
        command = "set -x; " + command
    return os.system(command)

### WARNING : this ALWAYS does its job, even in dry_run mode
def output_of (command):
    import commands
    (code,string) = commands.getstatusoutput(command)
    return (code,string)


# convenience: translating shell-like pattern into regexp
def match (string, pattern):
    # tmp - there's probably much simpler
    # rewrite * into .*, ? into .
    pattern=pattern.replace("*",".*")
    pattern=pattern.replace("?",".")
    return re.compile(pattern).match(string)
    
def locate_hooks_scripts (message,path,extensions):
    print message,'searching',path,'for extensions',extensions
    scripts=[]
    for ext in extensions:
        # skip helper programs
        scripts += glob.glob (path+'/[a-zA-Z]*.'+ext)
    return scripts
    
# quick & dirty - should probably use the parseroption object instead
# and move to TestMain as well
exclude_options_keys = [ 'ensure_value' , 'read_file', 'read_module' ]
def show_options (message,options):
    now=time.strftime("%H:%M:%S", time.localtime())
    print ">",now,"--",message
    for k in dir(options):
        if k.find("_")==0: continue
        if k in exclude_options_keys: continue
        print "    ",k,":",getattr(options,k)



