# $Id$
import time, os, re, glob
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



def system(command,background=False):
    if background: command += " &"
    if options.dry_run:
        print 'dry_run:',command
        return 0
    else:
        return os.system("set -x; " + command)

### WARNING : this ALWAYS does its job, even in dry_run mode
def output_of (command):
    import commands
#    if options.dry_run:
#        print 'dry_run',command
#        return (0,'[[dry-run - fake output]]')
#    else:
    (code,string) = commands.getstatusoutput(command)
    return (code,string)



# convenience: translating shell-like pattern into regexp
def match (string, pattern):
    # tmp - there's probably much simpler
    # rewrite * into .*, ? into .
    pattern=pattern.replace("*",".*")
    pattern=pattern.replace("?",".")
    return re.compile(pattern).match(string)
    
def locate_sanity_scripts (message,path,extensions):
    print message,'searching',path,'for extensions',extensions
    scripts=[]
    for ext in extensions:
        scripts += glob.glob (path+'/*.'+ext)
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



#################### display config
# entry point
def show_plc_spec (plc_spec):
    show_plc_spec_pass (plc_spec,1)
    show_plc_spec_pass (plc_spec,2)

def show_plc_spec_pass (plc_spec,passno):
    for (key,val) in plc_spec.iteritems():
        if passno == 2:
            if key == 'sites':
                for site in val:
                    show_site_spec(site)
                    for node in site['nodes']:
                        show_node_spec(node)
            elif key=='initscripts':
                for initscript in val:
                    show_initscript_spec (initscript)
            elif key=='slices':
                for slice in val:
                    show_slice_spec (slice)
            elif key=='keys':
                for key in val:
                    show_key_spec (key)
        elif passno == 1:
            if key not in ['sites','initscripts','slices','keys']:
                print '*   ',key,':',val

def show_site_spec (site):
    print '* ======== site',site['site_fields']['name']
    for (k,v) in site.iteritems():
        if k=='nodes':
            if v: 
                print '*       ','nodes : ',
                for node in v:  
                    print node['node_fields']['hostname'],'',
                print ''
        elif k=='users':
            if v: 
                print '*       users : ',
                for user in v:  
                    print user['name'],'',
                print ''
        elif k == 'site_fields':
            print '*       login_base',':',v['login_base']
        elif k == 'address_fields':
            pass
        else:
            print '*       ',k,
            PrettyPrinter(indent=8,depth=2).pprint(v)
        
def show_initscript_spec (initscript):
    print '* ======== initscript',initscript['initscript_fields']['name']

def show_key_spec (key):
    print '* ======== key',key['name']

def show_slice_spec (slice):
    print '* ======== slice',slice['slice_fields']['name']
    for (k,v) in slice.iteritems():
        if k=='nodenames':
            if v: 
                print '*       nodes : ',
                for nodename in v:  
                    print nodename,'',
                print ''
        elif k=='usernames':
            if v: 
                print '*       users : ',
                for username in v:  
                    print username,'',
                print ''
        elif k=='slice_fields':
            print '*       fields',':',
            print 'max_nodes=',v['max_nodes'],
            print ''
        else:
            print '*       ',k,v

def show_node_spec (node):
    print "*           node",node['name'],"host_box=",node['host_box'],
    print "hostname=",node['node_fields']['hostname'],
    print "ip=",node['interface_fields']['ip']
    

