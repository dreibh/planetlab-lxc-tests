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
	system("ping $guineapig");
	}

sub mfetch {
	foreach (1..$numiter) {
		run;
	}
}

sub launch {
	my @tarray;
	foreach (1..$numthreads) {
		my $thr = threads->create(\&mfetch);
		push @tarray,$thr;
	}

	for (@tarray) {
		$_->join;
	}
}

sub open_tcpdump {
	my $filter="icmp and src $guineapig";
	my $cmdline="/usr/sbin/tcpdump -c $numpackets $filter";
	
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
launch;
$SIG{ALRM}=\&alhandler;
alarm(60);
$tcpdthr->join;
$numsynacks++;
print "[SUCCESS] Test completed OK. $numsynacks SYN/ACK packets intercepted.\n";
