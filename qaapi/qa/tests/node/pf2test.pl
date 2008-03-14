#!/usr/bin/perl

print "Warning! This test runs only once. I.e., it will usually not run twice in succession till syslog sees some new activitt\n";
print "Preparing...";

system("cp /var/log/messages /tmp/pf2_test");

# ping magic IP address
print "Sending out packet...\n";
system("su -c \"ping -c 1 64.34.177.39\" pl_netflow -"); # hm. Sapan doesn't own this IP anymore. We should change it at some point.

print "Waiting for flow to appear...\n";
sleep(10);

open PIP,"|/usr/bin/diff -u /tmp/pf2_test /var/log/messages";

while (<PIP>) {
	if (/Received test flow to corewars.org from slice ([0-9]+)/) {
		$xid = int($1);
		print "Slice id: $xid";
		($xid==0 || $xid==-1) && die("Slice id incorrect");
	}
}

close PIP;

print "Test successful.";

