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
parser.add_option("-g", "--graph-only", action="store_true", dest="graph_only", help = "Only plot the current data, then exit")
parser.add_option("-l", "--plot-length", action="store", dest="plot_length", help = "Plot x-axis (time) length in seconds")
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
	else: config_file = '/usr/share/planetlab/tests/node-ssh/nst_config'
	
	try:
	    execfile(config_file, self.__dict__)
	except:
	    raise "Could not find nst config in " + config_file

	if options.url: self.url = self.NST_API_SERVER = options.url
	if options.slice: self.NST_SLICE = options.slice
	if options.key: self.NST_KEY_PATH = options.key
	if options.user: self.NST_USER = options.user
	if options.password: self.NST_PASSWORD = options.password
	if options.nodes: self.NST_NODES = options.nodes
	else: self.NST_NODES = None
	if options.plot_length: self.NST_PLOT_LENGTH = options.plot_length

	self.api = xmlrpclib.Server(self.NST_API_SERVER)
	self.auth = {}
	self.auth['Username'] = self.NST_USER
	self.auth['AuthString'] = self.NST_PASSWORD
	self.auth['AuthMethod'] = 'password'
	self.key = self.NST_KEY_PATH
	self.slice = self.NST_SLICE
	self.nodes = self.NST_NODES
	self.plot_length = self.NST_PLOT_LENGTH
	self.sleep_time = 900
	self.verbose = options.verbose 	
	
	# set up directories
	self.data_path = '/var/lib/planetlab/tests/node-ssh/data/'
	self.plots_path = '/var/lib/planetlab/tests/node-ssh/plots/'	
	
	# set up files
	self.all_nodes_filename = self.data_path + os.sep + "nodes"
	self.nodes_in_slice_filename = self.data_path + os.sep + "nodes_in_slice"
	self.nodes_can_ssh_filename = self.data_path + os.sep + "nodes_can_ssh"
	self.nodes_good_comon_filename = self.data_path + os.sep + "nodes_good"
	 	

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
def count_nodes_by_api(config, current_time, all_nodes):

	# count all nodes	
	all_nodes_output = "%d\t%d" % (current_time, len(all_nodes))

	# count all nodes in slice
	if config.slice == 'root':
	    nodes_in_slice = all_nodes
	    nodes_in_slice_output = all_nodes_output
	else:
	    slice_id =config.api.GetSlices(config.auth, {'name': config.slice}, ['slice_id'])[0]['slice_id']
	    nodes_in_slice = [row['node_id'] for row in \
		              all_nodes if slice_id in row['slice_ids']]
	    nodes_in_slice_output =  "%d\t%d" % (current_time, len(nodes_in_slice))

	# write result to datafiles
	all_nodes_file = open(config.all_nodes_filename, 'a')
	all_nodes_file.write(all_nodes_output + "\n")
	all_nodes_file.close()
	
	nodes_in_slice_file = open(config.nodes_in_slice_filename, 'a')
	nodes_in_slice_file.write(nodes_in_slice_output + "\n")
	nodes_in_slice_file.close()
	
	if config.verbose:
	    print "all node: " + all_nodes_output
	    print "nodes in slice: " + nodes_in_slice_output
 		

# count total number of "good" nodes, according to CoMon
def count_nodes_good_by_comon(config, current_time):
	
	
	comon = urllib.urlopen("http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeviewshort&format=nameonly&select='resptime%20%3E%200%20&&%20((drift%20%3E%201m%20||%20(dns1udp%20%3E%2080%20&&%20dns2udp%20%3E%2080)%20||%20gbfree%20%3C%205%20||%20sshstatus%20%3E%202h)%20==%200)'")
	good_nodes = comon.readlines()

	comon_output =  "%d\t%d" % (current_time, len(good_nodes))
	nodes_good_comon_file = open(config.nodes_good_comon_filename, 'a')
	nodes_good_comon_file.write(comon_output + "\n")
	nodes_good_comon_file.close()
	
	if config.verbose:
	    print "comon: " + comon_output 
	
# count total number of nodes reachable by ssh
def count_nodes_can_ssh(config, current_time, all_nodes):

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
	good_nodes= [result.split(':')[0] for result in ssh_results]
	
	# remove temp files 
	if os.path.exists(nodes_filename): os.unlink(nodes_filename)
	if os.path.exists(ssh_filename): os.unlink(ssh_filename)
	
	# count number of node we can ssh into
	ssh_count = len(good_nodes)
	
	# determine whince nodes are dead:
	dead_nodes = set(node_list).difference(good_nodes)
	
	# write dead nodes to file
	dead_node_count_output = "%d\t%d" % (current_time, len(dead_nodes))
	dead_nodes_file_name = config.data_path + os.sep + "dead_nodes"
	dead_nodes_file = open(dead_nodes_file_name, 'w')

	for hostname in dead_nodes:
	    boot_state = node_dict[hostname]['boot_state']
	    last_contact = 0
	    if node_dict[hostname]['last_contact']: 
		last_contact = node_dict[hostname]['last_contact'] 
	    dead_nodes_file.write("%(current_time)d\t%(hostname)s\t%(boot_state)s\t%(last_contact)d\n" % \
	   			  locals())	
	dead_nodes_file.close() 
 		
	# write good node count 
	ssh_result_output =  "%d\t%d" % (current_time, ssh_count)
	nodes_can_ssh_file = open(config.nodes_can_ssh_filename, 'a')
	nodes_can_ssh_file.write(ssh_result_output + "\n")
	nodes_can_ssh_file.close()
	
	if verbose:
	    print "nodes that can ssh: " + ssh_result_output
	    print "dead nodes: " + dead_node_count_output   
	
	
# remove all nodes from a slice
def empty_slice(config, all_nodes):

	if config.verbose:
	    print "Removing %s from all nodes" % config.slice

	all_node_ids = [row['node_id'] for row in all_nodes]
	config.api.DeleteSliceFromNodes(config.auth, config.slice, all_node_ids)

	
# add slice to all nodes. 
# make sure users key is up to date   
def init_slice(config, all_nodes):

    api  = config.api	
    auth = config.auth
    slice = config.slice 	
    key_path = config.key
    verbose = config.verbose 
    slices = api.GetSlices(auth, [slice], \
				  ['slice_id', 'name', 'person_ids', 'node_ids'])
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
        print "Generating list of all nodes not in slice" 
    all_node_ids = [row['node_id'] for row in all_nodes]
    
    new_nodes = set(all_node_ids).difference(slice['node_ids'])			
    if verbose:
        print "Adding %s to nodes: %r " % (slice['name'], new_nodes)

    api.AddSliceToNodes(auth, slice['slice_id'], list(new_nodes))
	
	
# create the fill/empty plot
def plot_fill_empty(config):
	#ticstep = 3600	# 1 hour
	#plotlength = 36000 # 10 hours
	ticstep = 1800
	plotlength = config.plot_length
	plots_path = config.plots_path
	
	all_nodes_filename = config.all_nodes_filename	
	nodes_in_slice_filename = config.nodes_in_slice_filename
	nodes_can_ssh_filename = config.nodes_can_ssh_filename
	nodes_good_comon_filename = config.nodes_good_comon_filename
	
	tmpfilename = tempfile.mktemp()
	tmpfile = open(tmpfilename, 'w')
	
	starttime = -1
	stoptime = -1
	for datafilename in [all_nodes_filename,
			     nodes_in_slice_filename, \
			     nodes_can_ssh_filename, \
			     nodes_good_comon_filename]: 
		datafile = open(datafilename, 'r')
		lines = datafile.readlines()
		if len(lines) > 0:
		    line_start = lines[0]
		    line_end = lines[len(lines) -1]
		else:
		    continue
		
		thisstarttime = int(line_start.split("\t")[0])
		if starttime == -1 or thisstarttime < starttime:
			starttime = thisstarttime
		thisstoptime = int(line_end.split("\t")[0])
		if stoptime == -1 or thisstoptime > stoptime:
			stoptime = thisstoptime
	
	stopx = stoptime
	startx = max(starttime, stopx - plotlength)
	starttime = startx
	
	tics = getTimeTicString(starttime, stoptime, ticstep)
	
	startdate = time.strftime("%b %m, %Y - %H:%M", time.localtime(startx))
	stopdate = time.strftime("%H:%M", time.localtime(stopx))

	if config.verbose:
	    print "plotting data with start date: %(startdate)s and stop date: %(stopdate)s" % locals()
		
	plot_output ="""
	set term png
	set output "%(plots_path)s/fill_empty.png"
	
	set title "Number of Nodes / Time - %(startdate)s to %(stopdate)s"
	set xlabel "Time"
	set ylabel "Number of Nodes"
	
	set xtics (%(tics)s)
	set xrange[%(startx)d:%(stopx)d]
	set yrange[0:950]
	
	plot "%(all_nodes_filename)s" u 1:2 w lines title "Total Nodes", \
	     "%(nodes_in_slice_filename)s" u 1:2 w lines title "Nodes in Slice", \
	     "%(nodes_good_comon_filename)s" u 1:2 w lines title \
			"Healthy Nodes (according to CoMon)", \
	     "%(nodes_can_ssh_filename)s" u 1:2 w lines title "Nodes Reachable by SSH"
	
	""" 
	tmpfile.write(plot_output % locals())
	tmpfile.close()

	if config.verbose:
	    print plot_output % locals()
	
	os.system("gnuplot %s" %  tmpfilename)
	
	if os.path.exists(tmpfilename): os.unlink(tmpfilename)



# load configuration
config = Config(options)

if options.graph_only:
    plot_fill_empty(config)
    sys.exit(0)

current_time = round(time.time())
all_nodes = config.api.GetNodes(config.auth, {}, \
                                ['node_id', 'boot_state', 'hostname', 'last_contact', 'slice_ids'])


# if root is specified we will ssh into root context, not a slice
# so no need to add a slice to all nodes
if config.slice == 'root':

    if config.verbose:
        print "Logging in as root"
else:
    # set up slice and add it to nodes
    init_slice(config, all_nodes)
   
    if config.verbose:
	print "Waiting %d seconds for nodes to update" % config.sleep_time	 

    # wait for nodes to get the data
    sleep(config.sleep_time)	  	


# gather data
count_nodes_can_ssh(config, current_time, all_nodes)	
count_nodes_by_api(config, current_time, all_nodes)
count_nodes_good_by_comon(config, current_time)
    
# update plots
plot_fill_empty(config)
#os.system("cp plots/*.png ~/public_html/planetlab/tests")		 		

# clean up
empty_slice(config, all_nodes)		

