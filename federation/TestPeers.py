#!/usr/bin/env python
###
##############################
###
### preparation / requirements
###
### two separate instances of myplc
### for now they are located on the same box on lurch
###
### requirements :
### your myplcs should more or less come out of the box, 
### I prefer not to alter the default PLC_ROOT_USER value,
### instead we create a PI account on the site_id=1
###
##############################

subversion_id="$Id$"

import sys
import time
import os

sys.path.append("..")

from PLC.Shell import Shell
import PLC.Methods

####################

## try to support reload
try:
    globals()['plc']
except:
    plc=[None,None,None]
try:
    globals()['s']
except:
    s=[None,None,None]
    
####################
plc[1]={ 'plcname':'FederationTestPlc1',
         'hostname':'plc1.inria.fr',
         'url-format':'https://%s:443/PLCAPI/',
         'builtin-admin-id':'root@plc1.inria.fr',
         'builtin-admin-password':'root',
         'peer-admin-name':'peer1@planet-lab.eu',
         'peer-admin-password':'peer',
         'node-format':'n1-%03d.plc1.org',
         'plainname' : 'one',
         'site-format':'one%s',
         'person-format' : 'user-%d@plc.org',
         'key-format':'ssh-rsa somekey4plctestbed user%d-key%d',
         'person-password' : 'password1',
	 'gpg-keyring':'gpg_plc2.pub',
	 'api-cacert':'api_plc2.crt',
       }
plc[2]={ 'plcname':'FederationTestPlc2',
         'hostname':'plc2.inria.fr',
         'url-format':'https://%s:443/PLCAPI/',
         'builtin-admin-id':'root@plc2.inria.fr',
         'builtin-admin-password':'root',
         'peer-admin-name':'peer2@planet-lab.eu',
         'peer-admin-password':'peer',
         'node-format':'n2-%03d.plc2.org',
         'plainname' : 'two',
         'site-format':'two%s',
         'person-format' : 'user-%d@plc.org',
         'key-format':'ssh-rsa somekey4plctestbed user%d-key%d',
         'person-password' : 'password2',
	 'gpg-keyring':'gpg_plc1.pub',
	 'api-cacert':'api_plc1.crt',
       }

####################
# when running locally, we might wish to run only our local stuff
dummy_print_methods = [ 'RefreshPeer' ]
class DummyShell:
    class Callable:
        def __init__(self,method,index):
            self.method=method
            self.index=index
            self.printed=False
        def __call__ (self, *args, **kwds):
            if not self.printed or self.method in dummy_print_methods:
                print "Dummy method %s on remote peer %d skipped"%(self.method,self.index)
                self.printed=True
            return 0
    def __init__(self,index):
        self.index=index
        for method in PLC.Methods.methods:
            # ignore path-defined methods for now
            if "." not in method:
                setattr(self,method,DummyShell.Callable(method,self.index))
        
####################
# predefined stuff
# number of 'system' persons
# builtin maint, local root, 1 person for the peering
system_persons = 3
# among that, 1 gets refreshed - other ones are considered 'system'
system_persons_cross = 1

system_slices_ids = (1,)
def system_slices ():
    return len(system_slices_ids)
def total_slices ():
    return number_slices+system_slices()

def system_slivers ():
    return len(system_slices_ids)

# too tedious to do the maths : how many slices attached to node 1
expected_slivers=None
def total_slivers ():
    global expected_slivers
    if expected_slivers is None:
        expected_slivers=0
        actual_nodes_per_slice = min (number_nodes,number_nodes_per_slice)
        for ns in myrange(number_slices):
            slice_range = [ map_on_node (n+ns) for n in range(actual_nodes_per_slice)]
            if 1 in slice_range:
                expected_slivers += 1
    return expected_slivers+system_slivers()

####################
# set initial conditions
# actual persons_per_slice is min(number_persons,number_persons_per_slice)
# actual nodes_per_slice is min(number_nodes,number_nodes_per_slice)
# this is to prevent quadractic test times on big tests
def define_test (sites,persons,nodes,slices,
                 keys_per_person,nodes_per_slice,persons_per_slice,fast_mode=None):
    global number_sites, number_persons, number_nodes, number_slices
    global number_keys_per_person, number_nodes_per_slice, number_persons_per_slice, fast_flag
    number_sites = sites
    number_persons=persons
    number_nodes=nodes
    number_slices=slices
    number_keys_per_person=keys_per_person
    number_nodes_per_slice=nodes_per_slice
    number_persons_per_slice=persons_per_slice
    if fast_mode is not None:
        fast_flag=fast_mode

# when we run locally on a given peer
local_peer=None

def show_test():
    print '%d sites, %d persons, %d nodes & %d slices'%(
        number_sites,number_persons,number_nodes,number_slices)
    print '%d keys/person, %d nodes/slice & %d persons/slice'%(
        number_keys_per_person,number_nodes_per_slice,number_persons_per_slice)
    print 'fast_flag',fast_flag
    if local_peer is not None:
        print 'Running locally on index %d'%local_peer

def mini():
    define_test(1,1,1,1,1,1,1,True)
    
def normal():
    define_test (sites=4,persons=4,nodes=5,slices=4,
                 keys_per_person=2,nodes_per_slice=3,persons_per_slice=6,fast_mode=False)

def apply_factor (factor):
    global number_sites, number_persons, number_nodes, number_slices
    [number_sites, number_persons, number_nodes, number_slices] = \
                   [factor*x for x in     [number_sites, number_persons, number_nodes, number_slices]]
                                                                   

# use only 1 key in this case
big_factor=4
def big():
    global number_sites, number_persons, number_nodes, number_slices
    number_sites=200
    number_persons=500
    number_nodes=350
    number_slices=500
    global nodes_per_slice
    nodes_per_slice=3
    global number_keys_per_person
    number_keys_per_person=1
    global number_persons_per_slice
    number_persons_per_slice=3

#huge_factor=1000
def huge():
    global number_sites, number_persons, number_nodes, number_slices
    number_sites=1000
    number_persons=2000
    number_nodes=3000
    number_slices=2000
    global nodes_per_slice
    nodes_per_slice=3
    global number_keys_per_person
    number_keys_per_person=1
    global number_persons_per_slice
    number_persons_per_slice=3

# use mini test by default in interactive mode
mini()
#normal()

####################
# argh, for login_name that doesn't accept digits
plain_numbers=['zero','one','two','three','four','five','six','seven','eight','nine','ten',
	       'eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen','twenty']
plain_digits=['a','b','c','d','e','f','g','h','i','j']
####################
def peer_index(i):
    return 3-i

def plc_name (i):
    return plc[i]['plcname']

def site_name (i,n):
    x=site_login_base(i,n)
    return 'Site fullname '+x

def site_login_base (i,n):
    # for huge
    if number_sites<len(plain_numbers):
        return plc[i]['site-format']%plain_numbers[n]
    else:
        string=''
        while True:
            quo=n/10
            rem=n%10
            string=plain_digits[rem]+string
            if quo == 0:
                break
            else:
                n=quo
        return plc[i]['site-format']%string

def person_name (i,n):
    return plc[i]['person-format']%n

def key_name (i,n,k):
    return plc[i]['key-format']%(n,k)

def node_name (i,n):
    return plc[i]['node-format']%n

def slice_name (i,n):
    site_index=map_on_site(n)
    return "%s_slice%d"%(site_login_base(i,site_index),n)

def sat_name (i):
    return 'sat_%d'%i

# to have indexes start at 1
def map_on (n,max):
    result=(n%max)
    if result==0:
        result=max
    return result

def myrange (n):
    return range (1,n+1,1)

def map_on_site (n):
    return map_on (n,number_sites)

def map_on_person (n):
    return map_on (n,number_persons)

def map_on_node (n):
    return map_on (n,number_nodes)

def message (*args):
    print "====================",
    print args
    
##########
def timer_start ():
    global epoch,last_time
    epoch = time.time()
    last_time=epoch
    print '+++ timer start'

def timer_show ():
    global last_time
    now=time.time()
    print '+++ %.02f seconds ellapsed (%.02f)'%(now-epoch,now-last_time)
    last_time=now

####################
errors=0
def myassert (message,boolean):
    if not boolean:
        print 'ASSERTION FAILED',message
        global errors
        errors +=1

def epilogue ():
    if errors != 0:
        print 'TEST FAILED with %d errors'%errors
        assert errors == 0
        
####################
# init
def test00_init (args=[1,2],builtin_person=False):
    timer_start()
    for i in args:
        url=plc[i]['url-format']%plc[i]['hostname']
        plc[i]['url']=url
        if local_peer is None:
            # the regular remote mode
            print 'initializing s[%d]=>%s'%(i,url),
            if builtin_person:
                user=plc[i]['builtin-admin-id']
                password=plc[i]['builtin-admin-password']
            else:
                user=plc[i]['peer-admin-name']
                password=plc[i]['peer-admin-password']
            s[i]=Shell(url=url,
                       user=user,
                       password=password)
            print 'user=',user
        elif local_peer == i:
            # local mode - use Shell's Direct mode - use /etc/planetlab/plc_config
            s[i]=Shell()
        else:
            # remote peer in local mode : use dummy shell instead
            s[i]=DummyShell(i)

# use new person's account

def test00_print (args=[1,2]):
    for i in args:
        print '==================== s[%d]'%i
#        s[i].show_config()
        print 'show_config obsoleted'
    print '===================='

def check_nodes (el,ef,args=[1,2]):
    for i in args:
        # use a single request and sort afterwards for efficiency
        # could have used GetNodes's scope as well
        all_nodes = s[i].GetNodes()
        n = len ([ x for x in all_nodes if x['peer_id'] is None])
        f = len ([ x for x in all_nodes if x['peer_id'] is not None])
        print '%02d: Checking nodes: got %d local (e=%d) & %d foreign (e=%d)'%(i,n,el,f,ef)
        myassert ('local nodes',n==el)
        myassert ('foreign nodes',f==ef)

def check_keys (el,ef,args=[1,2]):
    for i in args:
        # use a single request and sort afterwards for efficiency
        # could have used GetKeys's scope as well
        all_keys = s[i].GetKeys()
        n = len ([ x for x in all_keys if x['peer_id'] is None])
        f = len ([ x for x in all_keys if x['peer_id'] is not None])
        print '%02d: Checking keys: got %d local (e=%d) & %d foreign (e=%d)'%(i,n,el,f,ef)
        myassert ('local keys',n==el)
        myassert ('foreign_keys',f==ef)

def check_persons (el,ef,args=[1,2]):
    for i in args:
        # use a single request and sort afterwards for efficiency
        # could have used GetPersons's scope as well
        all_persons = s[i].GetPersons()
        n = len ([ x for x in all_persons if x['peer_id'] is None])
        f = len ([ x for x in all_persons if x['peer_id'] is not None])
        print '%02d: Checking persons: got %d local (e=%d) & %d foreign (e=%d)'%(i,n,el,f,ef)
        myassert ('local persons',n==el)
        myassert ('foreign persons',f==ef)

# expected : local slices, foreign slices
def check_slices (els,efs,args=[1,2]):
    for i in args:
        ls=len(s[i].GetSlices({'peer_id':None}))
        fs=len(s[i].GetSlices({'~peer_id':None}))
        print '%02d: Checking slices: got %d local (e=%d) & %d foreign (e=%d)'%(i,ls,els,fs,efs)
        myassert ('local slices',els==ls)
        myassert ('foreign slices',efs==fs)

def show_nodes (i,node_ids):
    # same as above
    all_nodes = s[i].GetNodes(node_ids)
    loc_nodes = filter (lambda n: n['peer_id'] is None, all_nodes)
    for_nodes = filter (lambda n: n['peer_id'] is not None, all_nodes)

    for message,nodes in [ ['LOC',loc_nodes], ['FOR',for_nodes] ] :
        if nodes:
            print '[%s:%d] : '%(message,len(nodes)),
            for node in nodes:
                print node['hostname']+' ',
            print ''

def check_slice_nodes (expected_nodes, is_local_slice, args=[1,2]):
    for ns in myrange(number_slices):
	check_slice_nodes_n (ns,expected_nodes, is_local_slice, args)

def check_slice_nodes_n (ns,expected_nodes, is_local_slice, args=[1,2]):
    for i in args:
        peer=peer_index(i)
        if is_local_slice:
            sname=slice_name(i,ns)
            slice=s[i].GetSlices({'name':[sname],'peer_id':None})[0]
            message='local'
        else:
            sname=slice_name(peer,ns)
            slice=s[i].GetSlices({'name':[sname],'~peer_id':None})[0]
            message='foreign'
        print '%02d: %s slice %s (e=%d) '%(i,message,sname,expected_nodes),
        slice_node_ids=slice['node_ids']
        print 'on nodes ',slice_node_ids
        show_nodes (i,slice_node_ids)
        myassert ('slice nodes',len(slice_node_ids)>=expected_nodes)
	if len(slice_node_ids) != expected_nodes:
	    print 'TEMPORARY'

# expected : nodes on local slice
def check_local_slice_nodes (expected, args=[1,2]):
    check_slice_nodes(expected,True,args)

# expected : nodes on foreign slice
def check_foreign_slice_nodes (expected, args=[1,2]):
    check_slice_nodes(expected,False,args)

def check_conf_files (args=[1,2]):
    for nn in myrange(number_nodes):
	check_conf_files_n (nn,args)

def check_conf_files_n (nn,args=[1,2]):
    for i in args:
        nodename=node_name(i,nn)
        ndict= s[i].GetSlivers([nodename])[0]
        myassert ('conf files',ndict['hostname'] == nodename)
        conf_files = ndict['conf_files']
        print '%02d: %d conf_files in GetSlivers for node %s'%(i,len(conf_files),nodename)
        for conf_file in conf_files:
            print 'source=',conf_file['source'],'|',
            print 'dest=',conf_file['dest'],'|',
            print 'enabled=',conf_file['enabled'],'|',
            print ''

import pprint
pp = pprint.PrettyPrinter(indent=3)

def check_slivers (esn,args=[1,2]):
    for nn in myrange(number_nodes):
	check_slivers_n (nn,esn,args)

# too verbose to check all nodes, let's check only the first one
def check_slivers_1 (esn,args=[1,2]):
    check_slivers_n (1,esn,args)

def check_slivers_n (nn,esn,args=[1,2]):
    for i in args:
        nodename=node_name(i,nn)
        ndict= s[i].GetSlivers(nodename)
        myassert ('slivers hostname',ndict['hostname'] == nodename)
        slivers = ndict['slivers']
        print '%02d: %d slivers (exp. %d) in GetSlivers for node %s'\
              %(i,len(slivers),esn,nodename)
        for sliver in slivers:
            print '>>slivername = ',sliver['name']
            pretty_printer.pprint(sliver)
        myassert ('slivers count',len(slivers) == esn)
                

####################
def test00_admin_person (args=[1,2]):
    global plc
    for i in args:
        email = plc[i]['peer-admin-name']
        try:
            p=s[i].GetPersons([email])[0]
            plc[i]['peer-admin-id']=p['person_id']
        except:
            person_id=s[i].AddPerson({'first_name':'Local', 
                                      'last_name':'PeerPoint', 
                                      'role_ids':[10],
                                      'email':email,
                                      'password':plc[i]['peer-admin-password']})
            if person_id:
                print '%02d:== created peer admin account %d, %s - %s'%(
                    i, person_id,plc[i]['peer-admin-name'],plc[i]['peer-admin-password'])
            plc[i]['peer-admin-id']=person_id

def test00_admin_enable (args=[1,2]):
    for i in args:
        if s[i].AdmSetPersonEnabled(plc[i]['peer-admin-id'],True):
            s[i].AddRoleToPerson('admin',plc[i]['peer-admin-id'])
            print '%02d:== enabled+admin on account %d:%s'%(i,plc[i]['peer-admin-id'],plc[i]['peer-admin-name'])

####################
def locate_key (filename):
     " tries to locate a key file, either in . or in /etc/planetlab"
     try:
         return file("./"+filename).read()
     except:
         try:
             return file("/etc/planetlab/"+filename).read()
         except:
             raise Exception,"Could not locate key %s"%filename
             

def test00_peer (args=[1,2]):
    global plc
    for i in args:
        peer=peer_index(i)
        peername = plc_name(peer)
        try:
            p=s[i].GetPeers ( [peername])[0]
        except:
            try:
                keyringname=plc[i]['gpg-keyring']
                cacertname=plc[i]['api-cacert']
                print 'Trying to locate keys for peer on plc[%d]'%i,
                print 'in %s and %s'%(keyringname,cacertname)

                keyring=locate_key(keyringname)
                cacert=locate_key(cacertname)
                peer_id=s[i].AddPeer ( {'peername':peername,
                                        'peer_url':plc[peer]['url'],
                                        'key':keyring,
                                        'cacert': cacert,
                                        })
                print '%02d:Created peer %d'%(i,peer_id)
            except Exception,e:
                print 'Could not create peer,',e
    
# this one gets cached 
def get_peer_id (i):
    try:
        return plc[i]['peer_id']
    except:
        peername = plc_name (peer_index(i))
        peer_id = s[i].GetPeers([peername])[0]['peer_id']
        plc[i]['peer_id'] = peer_id
        return peer_id

##############################
def test00_refresh (message,args=[1,2]):
    print '=== refresh',message
    timer_show()
    for i in args:
        print '%02d:== Refreshing peer'%(i)
        timers=s[i].RefreshPeer(get_peer_id(i))
        print "+++ ellapsed: {",
        keys=timers.keys()
        keys.sort()
        for key in keys:
            print key,timers[key],
        print "}"
	timer_show()

####################
def test01_site (args=[1,2]):
    for ns in myrange(number_sites):
	test01_site_n (ns,True,args)

def test01_del_site (args=[1,2]):
    for ns in myrange(number_sites):
	test01_site_n (ns,False,args)

def test01_site_n (ns,add_if_true,args=[1,2]):
    for i in args:
	login_base = site_login_base (i,ns)
        try:
	    site_id = s[i].GetSites([login_base])[0]['site_id']
	    if not add_if_true:
                if s[i].DeleteSite(site_id):
                    print "%02d:== deleted site_id %d"%(i,site_id)
        except:
	    if add_if_true:
		sitename=site_name(i,ns)
		abbrev_name="abbr"+str(i)
		max_slices = number_slices
		site_id=s[i].AddSite ( {'name':plc_name(i),
                                        'abbreviated_name': abbrev_name,
                                        'login_base': login_base,
                                        'is_public': True,
                                        'url': 'http://%s.com/'%abbrev_name,
                                        'max_slices':max_slices})
                ### max_slices does not seem taken into account at that stage
                if site_id:
                    s[i].UpdateSite(site_id,{'max_slices':max_slices})
                    print '%02d:== Created site %d with max_slices=%d'%(i,site_id,max_slices)

####################
def test02_person (args=[1,2]):
    for np in myrange(number_persons):
	test02_person_n (np,True,args)

def test02_del_person (args=[1,2]):
    for np in myrange(number_persons):
	test02_person_n (np,False,args)

def test02_person_n (np,add_if_true,args=[1,2]):
    test02_person_n_ks (np, myrange(number_keys_per_person),add_if_true,args)

def test02_person_n_ks (np,nks,add_if_true,args=[1,2]):
    for i in args:
        email = person_name(i,np)
        try:
            person_id=s[i].GetPersons([email])[0]['person_id']
	    if not add_if_true:
                if s[i].DeletePerson(person_id):
                    print "%02d:== deleted person_id %d"%(i,person_id)
        except:
	    if add_if_true:
		password = plc[i]['person-password']
		person_id=s[i].AddPerson({'first_name':'Your average', 
					       'last_name':'User%d'%np, 
					       'role_ids':[30],
					       'email':email,
					       'password': password })
                if person_id:
                    print '%02d:== created user account %d, %s - %s'%(i, person_id,email,password)
                    for nk in nks:
                        key=key_name(i,np,nk)
                        s[i].AddPersonKey(email,{'key_type':'ssh', 'key':key})
                        print '%02d:== added key %s to person %s'%(i,key,email)

####################
# retrieves node_id from hostname - checks for local nodes only
def get_local_node_id(i,nodename):
    return s[i].GetNodes({'hostname':nodename,'peer_id':None})[0]['node_id']

# clean all local nodes - foreign nodes are not supposed to be cleaned up manually
def clean_all_nodes (args=[1,2]):
    for i in args:
        print '%02d:== Cleaning all nodes'%i
        local_nodes = s[i].GetNodes({'peer_id':None})
        if local_nodes:
            for node in local_nodes:
                print '%02d:==== Cleaning node %d'%(i,node['node_id'])
                s[i].DeleteNode(node['node_id'])

def test03_node (args=[1,2]):
    for nn in myrange(number_nodes):
	test03_node_n (nn,args)

def test03_node_n (nn,args=[1,2]):
    for i in args:
        nodename = node_name(i,nn)
        try:
            get_local_node_id(i,nodename)
        except:
	    login_base=site_login_base(i,map_on_site(nn))
            n=s[i].AddNode(login_base,{'hostname': nodename})
            if n:
                print '%02d:== Added node %d %s'%(i,n,node_name(i,nn))

def test02_delnode (args=[1,2]):
    for nn in myrange(number_nodes):
	test02_delnode_n (nn,args)

def test02_delnode_n (nn,args=[1,2]):
    for i in args:
        nodename = node_name(i,nn)
        node_id = get_local_node_id (i,nodename)
        retcod=s[i].DeleteNode(nodename)
        if retcod:
            print '%02d:== Deleted node %d, returns %s'%(i,node_id,retcod)

####################
def clean_all_slices (args=[1,2]):
    for i in args:
        print '%02d:== Cleaning all slices'%i
        for slice in s[i].GetSlices({'peer_id':None}):
            slice_id = slice['slice_id']
            if slice_id not in system_slices_ids:
                if s[i].DeleteSlice(slice_id):
                    print '%02d:==== Cleaned slice %d'%(i,slice_id)

def test04_slice (args=[1,2]):
    for n in myrange(number_slices):
	test04_slice_n (n,args)

def test04_slice_n (ns,args=[1,2]):
    for i in args:
        peer=peer_index(i)
        plcname=plc_name(i)
        slicename=slice_name(i,ns)
        max_nodes=number_nodes
        try:
            s[i].GetSlices([slicename])[0]
        except:
            slice_id=s[i].AddSlice ({'name':slicename,
                                     'description':'slice %s on %s'%(slicename,plcname),
                                     'url':'http://planet-lab.org/%s'%slicename,
                                     'max_nodes':max_nodes,
                                     'instanciation':'plc-instantiated',
                                     })
            if slice_id:
                print '%02d:== created slice %d - max nodes=%d'%(i,slice_id,max_nodes)
                actual_persons_per_slice = min (number_persons,number_persons_per_slice)
                person_indexes=[map_on_person (p+ns) for p in range(actual_persons_per_slice)]
                for np in person_indexes:
                    email = person_name (i,np)
                    retcod = s[i].AddPersonToSlice (email, slicename)
                    print '%02d:== Attached person %s to slice %s'%(i,email,slicename)
        

def test04_node_slice (is_local, add_if_true, args=[1,2]):
    for ns in myrange(number_slices):
	test04_node_slice_ns (ns,is_local, add_if_true, args)

def test04_node_slice_ns (ns,is_local, add_if_true, args=[1,2]):
    actual_nodes_per_slice = min (number_nodes,number_nodes_per_slice)
    node_indexes = [ map_on_node (n+ns) for n in range(actual_nodes_per_slice)]
    test04_node_slice_nl_n (node_indexes,ns,is_local, add_if_true, args)

def test04_node_slice_nl_n (nnl,ns,is_local, add_if_true, args=[1,2]):
    for i in args:
        peer=peer_index(i)
        sname = slice_name (i,ns)
        
        if is_local:
            hostnames=[node_name(i,nn) for nn in nnl]
            nodetype='local'
        else:
            hostnames=[node_name(peer,nn) for nn in nnl]
            nodetype='foreign'
        if add_if_true:
            res=s[i].AddSliceToNodes (sname,hostnames)
            message="added"
        else:
            res=s[i].DeleteSliceFromNodes (sname,hostnames)
            message="deleted"
        if res:
            print '%02d:== %s in slice %s %s '%(i,message,sname,nodetype),
            print hostnames

def test04_slice_add_lnode (args=[1,2]):
    test04_node_slice (True,True,args)

def test04_slice_add_fnode (args=[1,2]):
    test04_node_slice (False,True,args)

def test04_slice_del_lnode (args=[1,2]):
    test04_node_slice (True,False,args)

def test04_slice_del_fnode (args=[1,2]):
    test04_node_slice (False,False,args)

####################
def test05_sat (args=[1,2]):
    for i in args:
        name = sat_name(i)
        try:
            sat_id=s[i].GetSliceAttributeTypes ([name])[0]
        except:
            description="custom sat on plc%d"%i
            min_role_id=10
            sat_id=s[i].AddSliceAttributeType ({ 'name':name,
                                                 'description': description,
                                                 'min_role_id' : min_role_id})
            if sat_id:
                print '%02d:== created SliceAttributeType = %d'%(i,sat_id)

# for test, we create 4 slice_attributes
# on slice1 - sat=custom_made (see above) - all nodes
# on slice1 - sat=custom_made (see above) - node=n1
# on slice1 - sat='net_max' - all nodes
# on slice1 - sat='net_max' - node=n1

def test05_sa_atom (slice_name,sat_name,value,node,i):
    sa_id=s[i].GetSliceAttributes({'name':sat_name,
                                   'value':value})
    if not sa_id:
        if node:
            sa_id=s[i].AddSliceAttribute(slice_name,
                                         sat_name,
                                         value,
                                         node)
        else:
            print 'slice_name',slice_name,'sat_name',sat_name
            sa_id=s[i].AddSliceAttribute(slice_name,
                                         sat_name,
                                         value)
        if sa_id:
            print '%02d:== created SliceAttribute = %d'%(i,sa_id),
            print 'On slice',slice_name,'and node',node
        
def test05_sa (args=[1,2]):
    for i in args:
        test05_sa_atom (slice_name(i,1),sat_name(i),'custom sat/all nodes',None,i)
        test05_sa_atom (slice_name(i,1),sat_name(i),'custom sat/node1',node_name(i,1),i)
        test05_sa_atom (slice_name(i,1),'vref','predefined sat/all nodes',None,i)
        test05_sa_atom (slice_name(i,1),'vref','predefined sat/node1',node_name(i,1),i)
        
##############################
# readable dumps
##############################
def p_site (s):
    print s['site_id'],s['peer_id'],s['login_base'],s['name'],s['node_ids']

def p_key (k):
    print  k['key_id'],k['peer_id'],k['key']
    
def p_person (p):
    print  p['person_id'],p['peer_id'],p['email'],'keys:',p['key_ids'],'sites:',p['site_ids']

def p_node(n):
    print n['node_id'],n['peer_id'],n['hostname'],'sls=',n['slice_ids'],'site=',n['site_id']

def p_slice(s):
    print 'name: %-12s'%s['name'],'id: %02d'%s['slice_id'],'peer:',s['peer_id'],'nodes=',s['node_ids'],'persons=',s['person_ids']
    print '---','sa_ids=',s['slice_attribute_ids'],'creator: %03r'%s['creator_person_id']
    print "--- 'expires':",s['expires']

def p_sat(sat):
    print 'sat_id: %02d'%sat['attribute_type_id'], 'min_role_id:',sat['min_role_id'],
    print 'name:', sat['name'],'<',sat['description'],'>'

def p_sa (sa):
        print 'name: %-12s'%sa['name'], 
        print 'sa_id: %02d'%sa['slice_attribute_id'],'sat_id: %02d'%sa['attribute_type_id'],
        print 'sl=%02d'%sa['slice_id'],'v=',sa['value'],'n=',sa['node_id']

import pprint
pretty_printer=pprint.PrettyPrinter(5)

def p_sliver (margin,x):
    print margin,'SLIVERS for : hostname',x['hostname']
    print margin,'%d config files'%len(x['conf_files'])
    for sv in x['slivers']:
        p_sliver_slice(margin,sv,x['hostname'])

def p_sliver_slice(margin,sliver,hostname):
    print margin,'SLIVER on hostname %s, s='%hostname,sliver['name']
    print margin,'KEYS',
    pretty_printer.pprint(sliver['keys'])
    print margin,'ATTRIBUTES',
    pretty_printer.pprint(sliver['attributes'])

def dump (args=[1,2]):
    for i in args:
        print '%02d:============================== DUMPING'%i
        print '%02d: SITES'%i
        [p_site(x) for x in s[i].GetSites()]
        print '%02d: KEYS'%i
        [p_key(x) for x in s[i].GetKeys()]
        print '%02d: PERSONS'%i
        [p_person(x) for x in s[i].GetPersons()]
        print '%02d: NODES'%i
        [p_node(x) for x in s[i].GetNodes()]
        print '%02d: SLICES'%i
        [p_slice(x) for x in s[i].GetSlices()]
        print '%02d: Slice Attribute Types'%i
        [p_sat(x) for x in s[i].GetSliceAttributeTypes()]
        print '%02d: Slice Attributes'%i
        [p_sa(x) for x in s[i].GetSliceAttributes()]
        timer_show()
        snodes=min(3,number_nodes)
        print '%02d: SLIVERS for first %d nodes'%(i,snodes)
        print 'WARNING - GetSlivers needs fix'
#        for id in myrange(snodes):
#            p_sliver('%02d:'%i,s[i].GetSlivers(id))

        print '%02d:============================== END DUMP'%i
    

## for usage under the api
def pt ():
    for x in GetSites():
        p_site(x)
        
def pk ():
    for x in GetKeys():
        print  (x['key_id'],x['peer_id'],x['key']) 

def pp ():
    for x in GetPersons():
        p_person(x)

def pn ():
    for x in GetNodes():
        p_node(x)

def ps ():
    for x in GetSlices():
        p_slice(x)

def psat():
    for x in GetSliceAttributeTypes():
        p_sat(x)
        
def psa():
    for x in GetSliceAttributes():
        p_sa(x)
        
def pv ():
    for s in GetSlivers():
        p_sliver('',s)

def all():
    print 'SITES'
    pt()
    print 'KEYS'
    pk()
    print 'PERSONS'
    pp()
    print 'NODES'
    pn()
    print 'SLICES'
    ps()
    print 'SLICE ATTR TYPES'
    psat()
    print 'SLICE ATTRS'
    psa()
    print 'SLIVERS'
    pv()


####################
def test_all_init ():
    message ("INIT")
    test00_init (builtin_person=True)
    test00_print ()
    test00_admin_person ()
    test00_admin_enable ()
    test00_init (builtin_person=False)
# required before we can add peers
# use make -f peers-test.mk peers instead    
#    test00_push_public_peer_material()
    test00_peer ()

def test_all_sites ():
    test01_site ()
    test00_refresh ('after site creation')

def test_all_persons ():
    test02_del_person()
    test00_refresh ('before persons&keys creation')
    check_keys(0,0)
    check_persons(system_persons,system_persons_cross)
    message ("Creating persons&keys")
    test02_person ()
    if not fast_flag:
	message ("1 extra del/add cycle for unique indexes")
	test02_del_person([2])
	test02_person([2])
    check_keys(number_persons*number_keys_per_person,0)
    check_persons(system_persons+number_persons,system_persons_cross)
    test00_refresh ('after persons&keys creation')
    check_keys(number_persons*number_keys_per_person,number_persons*number_keys_per_person)
    check_persons(system_persons+number_persons,system_persons_cross+number_persons)

def test_all_nodes ():

    message ("RESETTING NODES")
    clean_all_nodes ()
    test00_refresh ('cleaned nodes')
    check_nodes(0,0)

    # create one node on each site
    message ("CREATING NODES")
    test03_node ()
    check_nodes(number_nodes,0)
    test00_refresh ('after node creation')
    check_nodes(number_nodes,number_nodes)
    test02_delnode([2])
    if not fast_flag:
	message ("2 extra del/add cycles on plc2 for different indexes")
	test03_node ([2])
	test02_delnode([2])
	test03_node ([2])
	test02_delnode([2])
    check_nodes(0,number_nodes,[2])
    test00_refresh('after deletion on plc2')
    check_nodes(number_nodes,0,[1])
    check_nodes(0,number_nodes,[2])
    message ("ADD on plc2 for different indexes")
    test03_node ([2])
    check_nodes (number_nodes,0,[1])
    check_nodes (number_nodes,number_nodes,[2])
    test00_refresh('after re-creation on plc2')
    check_nodes (number_nodes,number_nodes,)

def test_all_addslices ():

    # reset
    message ("RESETTING SLICES TEST")
    clean_all_nodes ()
    test03_node ()
    clean_all_slices ()
    test00_refresh ("After slices init")

    # create slices on plc1
    message ("CREATING SLICES on plc1")
    test04_slice ([1])

    check_slices (total_slices(),0,[1])
    check_slices (system_slices(),0,[2])
    test00_refresh ("after slice created on plc1")
    check_slices (total_slices(),0,[1])
    check_slices (system_slices(),number_slices,[2])
    # no slice has any node yet
    check_local_slice_nodes(0,[1])
    check_foreign_slice_nodes(0,[2])

    # insert local nodes in local slice on plc1
    message ("ADDING LOCAL NODES IN SLICES")
    test04_slice_add_lnode ([1])
    # of course the change is only local
    check_local_slice_nodes (number_nodes_per_slice,[1])
    check_foreign_slice_nodes(0,[2])

    # refreshing
    test00_refresh ("After local nodes were added on plc1")
    check_local_slice_nodes (number_nodes_per_slice,[1])
    check_foreign_slice_nodes (number_nodes_per_slice,[2])

    # now we add foreign nodes into local slice
    message ("ADDING FOREIGN NODES IN SLICES")
    test04_slice_add_fnode ([1])
    check_local_slice_nodes (2*number_nodes_per_slice,[1])
    check_foreign_slice_nodes (number_nodes_per_slice,[2])

    # refreshing
    test00_refresh ("After foreign nodes were added in plc1")
    # remember that foreign slices only know about LOCAL nodes
    # so this does not do anything
    check_local_slice_nodes (2*number_nodes_per_slice,[1])
    check_foreign_slice_nodes (2*number_nodes_per_slice,[2])

    check_slivers_1(total_slivers())

def test_all_delslices ():

    message ("DELETING FOREIGN NODES FROM SLICES")
    test04_slice_del_fnode([1])
    check_local_slice_nodes (number_nodes_per_slice,[1])
    check_foreign_slice_nodes (2*number_nodes_per_slice,[2])
    # mmh?
    check_slivers_1(total_slivers(),[1])

    test00_refresh ("After foreign nodes were removed on plc1")
    check_local_slice_nodes (number_nodes_per_slice,[1])
    check_foreign_slice_nodes (number_nodes_per_slice,[2])
    
    message ("DELETING LOCAL NODES FROM SLICES")
    test04_slice_del_lnode([1])
    check_local_slice_nodes (0,[1])
    check_foreign_slice_nodes (number_nodes_per_slice,[2])

    test00_refresh ("After local nodes were removed on plc1")
    check_local_slice_nodes (0,[1])
    check_foreign_slice_nodes (0,[2])

    message ("CHECKING SLICES CLEAN UP")
    clean_all_slices([1])
    check_slices (system_slices(),0,[1])
    check_slices (system_slices(),number_slices,[2])
    test00_refresh ("After slices clenaup")
    check_slices(system_slices(),0)

def test_all_slices ():
    test_all_addslices ()
    test_all_delslices ()
    
def test_all_sats ():
    test05_sat ()
    test00_refresh("after SliceAttributeType creation")                   

def test_all ():
    test_all_init ()
    timer_show()
    test_all_sites ()
    timer_show()
    test_all_persons ()
    timer_show()
    test_all_nodes ()
    timer_show()
    test_all_slices ()
    timer_show()
    test_all_sats ()
    timer_show()
    dump()
    timer_show()
    message("END")

### ad hoc test sequences
# we just create objects here so we can dump the DB
def populate ():
    timer_start()
    test_all_init()
    timer_show()
    test01_site()
    timer_show()
    test02_person()
    timer_show()
    test03_node()
    timer_show()
    test04_slice([1])
    timer_show()
    test04_slice_add_lnode([1])
    timer_show()
    test05_sat()
    timer_show()
    test05_sa([1])
    timer_show()
    message("END")

def populate_end():
    test00_init(builtin_person=False)
    test00_refresh ("Peer 1 for publishing foreign nodes from 2",[1])
    timer_show()
    test04_slice_add_fnode([1])
    timer_show()
    test00_refresh("populate: refresh all")
    timer_show()
    test00_refresh("empty refresh")
    dump()
    timer_show()
    message("END")

# temporary - scratch as needed
def test_now ():
    test_all_init()

#    populate()
#    test00_refresh('peer 1 gets plc2 nodes',[1])
#    test04_slice_add_fnode([1])
#    test00_refresh('final',[1])
#    
#    test_all_sites ()
#    clean_all_nodes()
#    clean_all_slices()
#    populate()

from optparse import OptionParser
def main ():
    usage = "Usage: %prog [options] [ [function1] .. fn]"

    parser=OptionParser(usage=usage,version="%prog "+subversion_id)
    parser.add_option("-m","--mini",action="store_const", const="mini",dest="size", 
		      help="run in mini mode (1 instance of each class)")
    parser.add_option("-n","--normal",action="store_const", const="normal",dest="size", 
		      default="normal",
		      help="performs big run")
    parser.add_option("-b","--big",action="store_const", const="big",dest="size", 
		      help="performs big run")
    parser.add_option("-H","--huge",action="store_const", const="huge",dest="size", 
		      help="performs huge run")
    parser.add_option("-f","--factor",action="store", dest="factor",default=1,
		      help="multiply size by FACTOR")

    parser.add_option("-l","--local",action="store", dest="local_peer",
		      help="tester runs locally for peer LOCAL_PEER, rather than through xmlrpc")
    parser.add_option("-1",action="store_const", const=1, dest="local_peer",
		      help="shortcut for -l 1")
    parser.add_option("-2",action="store_const", const=2, dest="local_peer",
		      help="shortcut for -l 2")

    parser.add_option("--plc1",action="store",dest="plc1", default="",
		      help="specifies plc1 hostname")
    parser.add_option("--plc2",action="store",dest="plc2", default="",
		      help="specifies plc2 hostname")

    parser.add_option("-d","--debug",dest="debug",action="store_true",default=False,
		      help="Just shows what would be done")

    (options,args) = parser.parse_args()

    print 'options',options,'args',args

    steps = []
    if len(args) > 0:
	steps=args
    else:
	steps = [ 'test_all']

    # perform size initialisation
    size_func=globals()[options.size]
    size_func()
    # apply factor
    apply_factor(int(options.factor))
    
    # support for the --plc options
    global plc
    if options.plc1:
	plc[1]['hostname']=options.plc1
    if options.plc2:
	plc[2]['hostname']=options.plc2

    # update global local_peer
    global local_peer
    local_peer=options.local_peer
    
    show_test()
		
    for funcname in steps:
	print 'funcname',funcname
	print 'dir()',dir()
	if funcname not in globals():
	    print 'Unknown step',funcname,'skipped'
	else:
	    if options.debug:
		print "Would invoke function",funcname
	    else:
		func = globals()[funcname]
		func()
		timer_show()
		epilogue()

if __name__ == '__main__':
    main()
    
