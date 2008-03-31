# $Id$
import time
import os
from pprint import PrettyPrinter

# how could this accept a list again ?
def header(message):
    now=time.strftime("%H:%M:%S", time.localtime())
    print "*",now,'--',message

def pprint(message,spec,depth=2):
    now=time.strftime("%H:%M:%S", time.localtime())
    print ">",now,"--",message
    PrettyPrinter(indent=8,depth=depth).pprint(spec)

def show_site_spec (site):
    print '======== site',site['site_fields']['name']
    for (k,v) in site.iteritems():
        if k=='nodes':
            if v: 
                print '\t\t','nodes : ',
                for node in v:  
                    print node['node_fields']['hostname'],'',
                print ''
        elif k=='users':
            if v: 
                print '\t\tusers : ',
                for user in v:  
                    print user['name'],'',
                print ''
        elif k == 'site_fields':
            print '\t\tlogin_base',':',v['login_base']
        elif k == 'address_fields':
            pass
        else:
            print '\t\t',k,
            PrettyPrinter(indent=8,depth=2).pprint(v)
        
def show_initscript_spec (initscript):
    print '======== initscript',initscript['initscript_fields']['name']

def show_key_spec (key):
    print '======== key',key['name']

def show_slice_spec (slice):
    print '======== slice',slice['slice_fields']['name']
    for (k,v) in slice.iteritems():
        if k=='nodenames':
            if v: 
                print '\t\tnodes : ',
                for nodename in v:  
                    print nodename,'',
                print ''
        elif k=='usernames':
            if v: 
                print '\t\tusers : ',
                for username in v:  
                    print username,'',
                print ''
        elif k=='slice_fields':
            print '\t\tfields',':',
            print 'max_nodes=',v['max_nodes'],
            print ''
        else:
            print '\t\t',k,v

def show_test_spec (message,all_plc_specs):
    now=time.strftime("%H:%M:%S", time.localtime())
    print ">",now,"--",message
    for plc_spec in all_plc_specs:
        show_test_spec_pass (plc_spec,1)
        show_test_spec_pass (plc_spec,2)

def show_test_spec_pass (plc_spec,passno):
    for (key,val) in plc_spec.iteritems():
        if passno == 2:
            if key == 'sites':
                for site in val:
                    show_site_spec(site)
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
                print '\t',key,':',val

def system(command):
    now=time.strftime("%H:%M:%S", time.localtime())
    print "+",now,':',command
    return os.system("set -x; " + command)


    
