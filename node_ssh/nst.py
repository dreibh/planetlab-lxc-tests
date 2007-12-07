#!/usr/bin/python

import time, sys, urllib, os, tempfile, random
import xmlrpclib
from optparse import OptionParser
from getpass import getpass
from time import sleep

parser = OptionParser()
parser.add_option("-c", "--config", action="store", dest="config",  help="Path to alternate config file")
parser.add_option("-x", "--url", action="store", dest="url", help = "API URL")
parser.add_option("-s", "--slice", action="store", dest="slice", help = "Name of slice to use")
parser.add_option("-n", "--nodes", action="store", dest="nodes", help = "File that contains a list of nodes to try to access")
parser.add_option("-k", "--key", action="store", dest="key", help = "Path to alternate public key")
parser.add_option("-u", "--user", action="store", dest="user", help = "API user name")
parser.add_option("-p", "--password", action="store", dest="password", help = "API password") 
parser.add_option("-v", "--verbose", action="store_true",  dest="verbose", help="Be verbose (default: %default)")
(options, args) = parser.parse_args()

# If user is specified but password is not
if options.user is not None and options.password is None:
    try:
        options.password = getpass()
    except (EOFError, KeyboardInterrupt):
        print
        sys.exit(0)

class Config:
    
    def __init__(self, options):
	
	# if options are specified use them
        # otherwise use options from config file
	if options.config: config_file = options.config
	else: config_file = '/usr/share/planetlab/tests/nst/nst_config'
	
	try:
	    execfile(config_file, self.__dict__)
	except:
	    raise "Could not find nst config in " + config_file

	if options.url: self.NST_API_SERVER = options.url
	if options.slice: self.NST_SLICE = options.slice
	if options.key: self.NST_KEY_PATH = options.key
	if options.user: self.NST_USER = options.user
	if options.password: self.NST_PASSWORD = options.password
	if options.nodes: self.NST_NODES = options.nodes
	else: self.NST_NODES = None

	self.api = xmlrpclib.Server(self.NST_API_SERVER)
	self.auth = {}
	self.auth['Username'] = self.NST_USER
	self.auth['AuthString'] = self.NST_PASSWORD
	self.auth['AuthMethod'] = 'password'
	self.key = self.NST_KEY_PATH
	self.slice = self.NST_SLICE
	self.nodes = self.NST_NODES
	self.verbose = options.verbose 	
	
	self.data_path = '/usr/share/planetlab/tests/nst/data/'
	self.plots_path = '/usr/share/planetlab/tests/nst/plots/'	
	

# get formatted tic string for gnuplot
def getTimeTicString(t1, t2, step):
	first_hour = list(time.localtime(t1))
	if not first_hour[4] == first_hour[5] == 0:
		first_hour[4] = 0
		first_hour[5] = 0
	
	first_hour_time = int(time.mktime(first_hour))
	first_hour_time += 3600
	
	backsteps = (first_hour_time - t1)
	backsteps /= step
	start = first_hour_time - backsteps * step
	
	tics = []
	thistime = start
	while thistime < t2:
		tics.append("\"%s\" %d" % \
			(time.strftime("%H:%M", time.localtime(thistime)), thistime))
		thistime += step
	
	ticstr = ", ".join(tics)
	return ticstr


# count total number of nodes in PlanetLab, according to the api
# count total number  of nodes in slice, according to the api 
def count_nodes_by_api(config):

	# count all nodes	
	all_nodes = config.api.GetNodes(config.auth, {}, ['node_id', 'slice_ids'])
	all_nodes_output = "%d\t%d" % (round(time.time()), len(all_nodes))

	# count all nodes in slice
	if config.slice == 'root':
	    nodes_in_slice = all_nodes
	    nodes_in_slice_output = all_nodes_output
	else:
	    slice_id =config.api.GetSlices(config.auth, {'name': config.slice}, ['slice_id'])[0]['slice_id']
	    nodes_in_slice = [row['node_id'] for row in \
		              all_nodes if slice_id in row['slice_ids']]
	    nodes_in_slice_output =  "%d\t%d" % (round(time.time()), len(nodes_in_slice))

	# write result to datafiles
	all_nodes_file_name = config.data_path + os.sep + "nodes" 
	all_nodes_file = open(all_nodes_file_name, 'w')
	all_nodes_file.write(all_nodes_output)
	all_nodes_file.close()
	
	nodes_in_slice_file_name = config.data_path + os.sep + "nodes_in_slice"
	nodes_in_slice_file = open(nodes_in_slice_file_name, 'w')
	nodes_in_slice_file.write(nodes_in_slice_output)
	nodes_in_slice_file.close()
	
	if config.verbose:
	    print "all node: " + all_nodes_output
	    print "nodes in slice: " + nodes_in_slice_output
 		

# count total number of "good" nodes, according to CoMon
def count_nodes_good_by_comon(config):
	
	
	comon = urllib.urlopen("http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeviewshort&format=nameonly&select='resptime%20%3E%200%20&&%20((drift%20%3E%201m%20||%20(dns1udp%20%3E%2080%20&&%20dns2udp%20%3E%2080)%20||%20gbfree%20%3C%205%20||%20sshstatus%20%3E%202h)%20==%200)'")
	good_nodes = comon.readlines()

	comon_output =  "%d\t%d" % (round(time.time()), len(good_nodes))
	nodes_good_comon_file_name = config.data_path + os.sep + "nodes_good"
	nodes_good_comon_file = open(nodes_good_comon_file_name, 'a')
	nodes_good_comon_file.write(comon_output)
	nodes_good_comon_file.close()
	
	if config.verbose:
	    print "comon: " + comon_output 
	
# count total number of nodes reachable by ssh
def count_nodes_can_ssh(config):

	api = config.api
	slice = config.slice
	key = config.key
	verbose = config.verbose
	auth = config.auth
	nodes = config.nodes

	if verbose:
	    verbose_text = ""
	    print "Creating list of nodes to ssh to"
	else:
	    verbose_text = ">/dev/null 2>&1"
	
	# creaet node dict
	all_nodes = api.GetNodes(auth, {}, ['hostname', 'boot_state', 'last_updated'])
        node_dict = {}
        for node in all_nodes:
            node_dict[node['hostname']] = node

	# create node list
	if nodes:
	    nodes_file = open(nodes, 'r')
	    nodes_filename = nodes_file.name
	    lines = nodes_file.readlines()
	    node_list = [node.replace('\n', '') for node in lines]
	    nodes_file.close()
	    
	else:
	    node_list = node_dict.keys()
	    nodes_filename = tempfile.mktemp()
	    nodes_file = open(nodes_filename, 'w')
	    for node in node_list:
		nodes_file.write("%(node)s\n" % locals())
	    nodes_file.close()
	
	# creaet node dict
	node_dict = {}
        for node in all_nodes:
            node_dict[node['hostname']] = node

	private_key = key.split(".pub")[0] 
	
	# create ssh command
	if verbose:
	    print "Attemptng to ssh to nodes in " + nodes_filename

	ssh_filename = tempfile.mktemp()
	ssh_file = open(ssh_filename, 'w')
	ssh_file.write("""
	export MQ_SLICE="%(slice)s"
        export MQ_NODES="%(nodes_filename)s"

	eval `ssh-agent` >/dev/null 2>&1
        trap "kill $SSH_AGENT_PID" 0
        ssh-add %(private_key)s >/dev/null 2>&1	
	
	multiquery 'hostname' 2>/dev/null |
	grep "bytes" | 
        grep -v ": 0 bytes"		
	""" % locals())
	ssh_file.close()
	ssh_results = os.popen("bash %(ssh_filename)s" % locals()).readlines()
	from pprint import pprint
	pprint(ssh_results)
	if len(ssh_results) > 0: 
	    ssh_result = eval(ssh_results[0].replace('\\n', '')) 
	else:
	    ssh_result = []
	# remove temp files 
	#if os.path.exists(nodes_filename): os.unlink(nodes_filename)
	#if os.path.exists(ssh_filename): os.unlink(ssh_filename)
	
	# create a list of hostname out of results that are not empty
	good_nodes = []
	for result in ssh_result:
	    if result.find("bytes") > -1:
		result_parts = result.split(":")
		hostname = result_parts[0]
	    	good_nodes.append(hostname)

	# count number of node we can ssh into
	ssh_count = len(good_nodes)
	
	# determine whince nodes are dead:
	dead_nodes = set(node_list).difference(good_nodes)
	
	# write dead nodes to file
	curr_time = round(time.time())
	dead_node_count_output = "%d\t%d" % (curr_time, len(dead_nodes))
	dead_nodes_file_name = config.data_path + os.sep + "dead_nodes"
	dead_nodes_file = open(dead_nodes_file_name, 'a')
	for hostname in dead_nodes:
	    boot_state = node_dict[hostname]['boot_state']
	    last_updated = 0
	    if node_dict[hostname]['last_updated']: 
		last_updated = node_dict[hostname]['last_updated'] 
	    dead_nodes_file.write("%(curr_time)d\t%(hostname)s\t%(boot_state)s\t%(last_updated)d\n" % \
	   			  locals())	
	dead_nodes_file.close() 
 		
	# write good node count 
	ssh_result_output =  "%d\t%d" % (round(time.time()), ssh_count)
	nodes_can_ssh_file_name = config.data_path + os.sep + "nodes_can_ssh"
	nodes_can_ssh_file = open(nodes_can_ssh_file_name, 'a')
	nodes_can_ssh_file.write(ssh_result_output)
	nodes_can_ssh_file.close()
	
	if verbose:
	    print "nodes that can ssh: " + ssh_result_output
	    print "dead nodes: " + dead_node_count_output   
	
	
# remove all nodes from a slice
def empty_slice(config):

	if config.verbose:
	    print "Removing %s from all nodes" % config.slice

	all_nodes = [row['node_id'] for row in config.api.GetNodes(config.auth, {}, ['node_id'])]
	config.api.DeleteSliceFromNodes(config.auth, config.slice, all_nodes)

	
# add slice to all nodes. 
# make sure users key is up to date   
def init_slice(config):

    api  = config.api	
    auth = config.auth
    slice = config.slice 	
    key_path = config.key
    verbose = config.verbose 
    slices = api.GetSlices(auth, [slice], \
				  ['slice_id', 'name', 'person_ids'])
    if not slices:
        raise "No such slice %s" % slice
    slice = slices[0]

    # make sure user is in slice
    person = api.GetPersons(auth, auth['Username'], \
				   ['person_id', 'email', 'slice_ids', 'key_ids'])[0]
    if slice['slice_id'] not in person['slice_ids']:
        raise "%s not in %s slice. Must be added first" % \
	      (person['email'], slice['name'])
    	 
    # make sure user key is up to date	
    current_key = open(key_path, 'r').readline().strip()
    if len(current_key) == 0:
        raise "Key cannot be empty" 

    keys = api.GetKeys(auth, person['key_ids'])
    if not keys:
        if verbose:
 	    print "Adding new key " + key_path
        api.AddPersonKey(auth, person['person_id'], \
			        {'key_type': 'ssh', 'key': current_key})

    elif not filter(lambda k: k['key'] == current_key, keys):
        if verbose:
	    print "%s was modified or is new. Updating PLC"
        old_key = keys[0]
        api.UpdateKey(auth, old_key['key_id'], \
			     {'key': current_key})


	
    # add slice to all nodes  	 		
    if verbose:
        print "Generating list of all nodes " 
    all_nodes = [row['node_id'] for row in \
                 api.GetNodes(auth, {}, ['node_id'])]
    if verbose:
        print "Adding %s to all nodes" % slice['name']
    api.AddSliceToNodes(auth, slice['slice_id'], all_nodes)
	
	
# create the fill/empty plot
def plot_fill_empty():
	#ticstep = 3600	# 1 hour
	#plotlength = 36000 # 10 hours
	ticstep = 1800
	plotlength = 10800

	plots_path = config.plots_path
	
	all_nodes_file_name = config.data_path + os.sep + "nodes"	
	nodes_in_slice_file_name = config.data_path + os.sep + "nodes_in_slice"
	nodes_can_ssh_file_name = config.data_path + os.sep + "nodes_can_ssh"
	nodes_good_comon_file_name = config.data_path + os.sep + "nodes_good"
	
	tmpfilename = tempfile.mktemp()
	tmpfile = open(tmpfilename, 'w')
	
	starttime = -1
	stoptime = -1
	for datafilename in [all_nodes_file_name,
			     nodes_in_slice_file_name, \
			     nodes_can_ssh_file_name, \
			     nodes_good_comon_file_name]: 
		datafile = open(datafilename, 'r')
		line1 = datafile.readline()
		datafile.seek(-32,2)
		line2 = datafile.readlines().pop()
		thisstarttime = int(line1.split("\t")[0])
		if starttime == -1 or thisstarttime < starttime:
			starttime = thisstarttime
		thisstoptime = int(line2.split("\t")[0])
		if stoptime == -1 or thisstoptime > stoptime:
			stoptime = thisstoptime
	
	stopx = stoptime
	startx = max(starttime, stopx - plotlength)
	starttime = startx
	
	tics = getTimeTicString(starttime, stoptime, ticstep)
	
	startdate = time.strftime("%b %m, %Y - %H:%M", time.localtime(startx))
	stopdate = time.strftime("%H:%M", time.localtime(stopx))
	
	tmpfile.write("""
	set term png
	set output "%(plots_path)s/fill_empty.png"
	
	set title "Number of Nodes / Time - %(startdate)s to %(stopdate)s"
	set xlabel "Time"
	set ylabel "Number of Nodes"
	
	set xtics (%(tics)s)
	set xrange[%(startx)d:%(stopx)d]
	set yrange[0:950]
	
	plot "%(all_nodes_file_name)s" u 1:2 w lines title "Total Nodes", \
		"%(nodes_in_slice_file_name)s" u 1:2 w lines title "Nodes in Slice", \
		"%(nodes_good_comon_file_name)s" u 1:2 w lines title \
			"Healthy Nodes (according to CoMon)", \
		"%(nodes_can_ssh_file_name)s" u 1:2 w lines title "Nodes Reachable by SSH"
	
	""" % locals())
	
	tmpfile.close()
	
	os.system("%s %s" % (gnuplot_path, tmpfilename))
	
	if os.path.exists(tmpfilename):
		os.unlink(tmpfilename)



config = Config(options)
sleep_time = 30

if config.slice == 'root':

    if config.verbose:
        print "Logging in as root"
else:
    # set up slice and add it to nodes
    init_slice(config)
   
    if config.verbose:
	print "Waiting %(sleep_time)d seconds for nodes to update" % locals()	 
    # wait 15 mins for nodes to get the data
    sleep(sleep_time)	  	

# gather data
count_nodes_can_ssh(config)	
count_nodes_by_api(config)
count_nodes_good_by_comon(config)
    
# update plots
#plot_fill_empty()
#os.system("cp plots/*.png ~/public_html/planetlab/tests")		 		

# clean up
#empty_slice(config)		

