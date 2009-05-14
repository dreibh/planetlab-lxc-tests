#!/usr/bin/perl

$netflow_slice="pl_netflow";

print "Warning! This test runs only once. I.e., it will usually not run twice in succession till syslog sees some new activitt\n";
print "Preparing...";


system("cp /var/log/messages /tmp/pf2_test");


# Wait for pl_netflow to come up

$timeout=600;

until ((-f "/var/run/vservers/pl_netflow" && -d "/home/pl_netflow") || ($timeout==0)) {sleep (15);print "Waiting for pl_netflow to show up...\n";$timeout-=15;}

if ($timeout>0) {
# ping magic IP address
print "Sending out packet...\n";
system("su -c \"ping -I eth0 -c 1 10.0.0.8\" $netflow_slice -"); 

print "Waiting for flow to appear...\n";
sleep(10);

open PIP,"|/usr/bin/diff -u /tmp/pf2_test /var/log/messages";

while (<PIP>) {
	if (/Received test flow to corewars.org from slice ([0-9]+)/) {
		$xid = int($1);
		print "Slice id: $xid\n";
        $success=1;
		($xid==0 || $xid==-1) && die("Slice id incorrect");
	}
}

if ($success) {
        print "[SUCCESS]";
}
else {
        print "[FAILED]";
}
}
else {
    die("[FAILED] Timed out.. pl_netflow didn't come up for 10 minutes...\n");
}


close PIP;

