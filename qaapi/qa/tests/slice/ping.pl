#!/usr/bin/perl

# Module: VNET+
# Description: Generate ping packets and count the responses
# Author: sapanb@cs.princeton.edu

use strict;
use threads;

#please change to something local
my $guineapig='planetlab-1.cs.princeton.edu';
my $numiter=1000;

sub run {
	system("sudo ping -c $numiter -i 0.1 $guineapig");
	}


sub open_tcpdump {
	my $filter="icmp and src $guineapig";
	my $cmdline="/usr/sbin/tcpdump -c $numiter $filter";
	
	system($cmdline);
}

sub alhandler {
	print "[FAILED] tcpdump apparently did not intercept all SYN/ACK packets\n";
	exit(-1);
}

print "Starting tcpdump...\n";
my $tcpdthr=threads->create(\&open_tcpdump);
sleep 10;
print "Generating connections...\n";
run;
$SIG{ALRM}=\&alhandler;
alarm(60);

$tcpdthr->join;
print "[SUCCESS] Test completed OK.\n";
