#!/usr/bin/python

import time, sys, urllib, os, tempfile, random

# set up the api
import xmlrpclib
api = xmlrpclib.Server('https://www.planet-lab.org/PLCAPI/')

# create auth struct
auth = {}
auth['Username'] = "USERNAME GOES HERE"
auth['AuthMethod'] = "password"
auth['AuthString'] = "PASSWORD GOES HERE"
auth['Role'] = "user"

multiquery_path = "PATH/TO/CODEPLOY/multiquery"
gnuplot_path = "/PATH/TO/gnuplot"

# create plots
def make_plots():
	plot_fill_empty()
	plot_keys()
	#os.system("cp plots/*.png ~/public_html/planetlab/tests")


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
def count_nodes_by_api():
	all_nodes = [row['node_id'] for row in api.GetNodes(auth, {}, ['node_id'])]
	print "%d\t%d" % (round(time.time()), len(all_nodes))


# count total number of nodes in slice, according to the api
def count_nodes_in_slice_by_api(slice=None):
	if slice is None:
		return
	
	slice_id = [row['slice_id'] for row in \
		api.GetSlices(auth, {'name': slice}, ['slice_id'])][0]
		
	all_nodes = [row['node_id'] for row in \
		api.GetNodes(auth, {}, ['node_id', 'slice_ids']) \
		if slice_id in row['slice_ids']]
	
	print "%d\t%d" % (round(time.time()), len(all_nodes))


# count total number of "good" nodes, according to CoMon
def count_nodes_good_by_comon():
	comon = urllib.urlopen("http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeviewshort&format=nameonly&select='resptime%20%3E%200%20&&%20((drift%20%3E%201m%20||%20(dns1udp%20%3E%2080%20&&%20dns2udp%20%3E%2080)%20||%20gbfree%20%3C%205%20||%20sshstatus%20%3E%202h)%20==%200)'")
	good_nodes = comon.readlines()

	print "%d\t%d" % (round(time.time()), len(good_nodes))
	
# estimate total number of nodes reachable by ssh
def count_nodes_can_ssh(slice=None, key=None):
	if slice is None:
		return
	if key is None:
		return
		
	pollnum = 20
	
	all_nodes = ["%s\n" % row['hostname'] for row in \
	        api.GetNodes(auth, {}, ['hostname'])]

	rand_nodes = []
	for i in range(pollnum):
	        rand_nodes.append(all_nodes[random.randint(0,len(all_nodes)-1)])

	tmpfilename = tempfile.mktemp()
	tmpfile = open(tmpfilename, 'w')
	tmpfile.writelines(rand_nodes)
	tmpfile.close()
	
	tmpfilename2 = tempfile.mktemp()
	tmpfile2 = open(tmpfilename2, 'w')
	tmpfile2.writelines("""
	export MQ_SLICE="$1"
	export MQ_NODES="$2"
	
	eval `ssh-agent` >/dev/null 2>&1
	trap "kill $SSH_AGENT_PID" 0
	ssh-add ./keys/$3 >/dev/null 2>&1
	
	%s 'uname' 2>/dev/null |
	grep "bytes" |
	grep -v ": 0 bytes" |
	wc -l	
	""" % multiquery_path)
	tmpfile2.close()
	
	ssh_result = os.popen("bash %s %s %s %s 2>/dev/null" % (tmpfilename2, slice, tmpfilename, key)).readlines()
	if len(ssh_result) > 0:
		ssh_count = float(ssh_result[0].strip()) * len(all_nodes) / pollnum
		print "%d\t%d" % (round(time.time()), round(ssh_count))
	
	if os.path.exists(tmpfilename):
		os.unlink(tmpfilename)

	
	
	
# remove all nodes from a slice
def empty_slice(slice=None):
	if slice is None:
		return
	
	all_nodes = [row['node_id'] for row in api.GetNodes(auth, {}, ['node_id'])]
	api.DeleteSliceFromNodes(auth, slice, all_nodes)

	
# add all nodes to a slice
def fill_slice(slice=None):
	all_nodes = [row['node_id'] for row in api.GetNodes(auth, {}, ['node_id'])]
	api.AddSliceToNodes(auth, slice, all_nodes)

	
# add a key to a user
def add_key(key=None):
	if key is None:
		return
	
	key_value = open("keys/%s.pub" % key).readline()
		
	api.AddPersonKey(auth, auth['Username'], {'key_type': 'ssh', 'key': key_value})

	
# update a user's key
def update_key(oldkey=None, newkey=None):
	if oldkey is None:
		return
	if newkey is None:
		return
	
	oldkeyval = open("keys/%s.pub" % oldkey).readline()
	newkeyval = open("keys/%s.pub" % newkey).readline()
	keyid = [row['key_id'] for row in api.GetKeys(auth) if row['key'] == oldkeyval]
	if len(keyid) == 0:
		return
	keyid = keyid[0]
	api.UpdateKey(auth, keyid, {'key_type': 'ssh', 'key': newkeyval})	


# delete a key from the user
def delete_key(delkey=None):
	if delkey is None:
		return
	
	delkeyval = open("keys/%s.pub" % delkey).readline()
	delkeyid = [row['key_id'] for row in api.GetKeys(auth) if row['key'] == delkeyval]
	if len(delkeyid) == 0:
		return
	delkeyid = delkeyid[0]
	api.DeleteKey(auth, delkeyid)

	
# create the fill/empty plot
def plot_fill_empty():
	#ticstep = 3600	# 1 hour
	#plotlength = 36000 # 10 hours
	ticstep = 1800
	plotlength = 10800
	
	tmpfilename = tempfile.mktemp()
	tmpfile = open(tmpfilename, 'w')
	
	starttime = -1
	stoptime = -1
	for datafilename in ['data/nodes', 'data/nodes_in_slice', \
			'data/nodes_can_ssh', 'data/nodes_good']:
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
	set output "plots/fill_empty.png"
	
	set title "Number of Nodes / Time - %s to %s"
	set xlabel "Time"
	set ylabel "Number of Nodes"
	
	set xtics (%s)
	set xrange[%d:%d]
	set yrange[0:950]
	
	plot "data/nodes" u 1:2 w lines title "Total Nodes", \
		"data/nodes_in_slice" u 1:2 w lines title "Nodes in Slice", \
		"data/nodes_good" u 1:2 w lines title \
			"Healthy Nodes (according to CoMon)", \
		"data/nodes_can_ssh" u 1:2 w lines title "Nodes Reachable by SSH"
	
	""" % (startdate, stopdate, tics, startx, stopx))
	
	tmpfile.close()
	
	os.system("%s %s" % (gnuplot_path, tmpfilename))
	
	if os.path.exists(tmpfilename):
		os.unlink(tmpfilename)



# create the keys plot
def plot_keys():
	#ticstep = 3600	# 1 hour
	#plotlength = 36000 # 10 hours
	ticstep = 1800
	plotlength = 10800
	
	tmpfilename = tempfile.mktemp()
	tmpfile = open(tmpfilename, 'w')

	starttime = -1
	stoptime = -1
	for datafilename in ['data/nodes', 'data/nodes_in_slice2', \
			'data/nodes_good', 'data/nodes_can_ssh2_key0', 'data/nodes_can_ssh2_key1', \
			'data/nodes_can_ssh2_key2']:
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
	set output "plots/keys.png"

	set title "Number of Nodes / Time - %s to %s"
	set xlabel "Time"
	set ylabel "Number of Nodes"

	set xtics (%s)
	set xrange[%d:%d]
	set yrange[0:1000]

	plot "data/nodes" u 1:2 w lines title "Total Nodes", \
		"data/nodes_in_slice2" u 1:2 w lines title "Nodes in Slice", \
		"data/nodes_good" u 1:2 w lines title \
			"Healthy Nodes (according to CoMon)", \
		"data/nodes_can_ssh2_key0" u 1:2 w lines title "Nodes Accepting Key 0", \
		"data/nodes_can_ssh2_key1" u 1:2 w lines title "Nodes Accepting Key 1", \
		"data/nodes_can_ssh2_key2" u 1:2 w lines title "Nodes Accepting Key 2"

	""" % (startdate, stopdate, tics, startx, stopx))

	tmpfile.close()

	os.system("%s %s" % (gnuplot_path, tmpfilename))
	
	if os.path.exists(tmpfilename):
		os.unlink(tmpfilename)
	
