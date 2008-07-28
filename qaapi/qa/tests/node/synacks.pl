#!/usr/bin/perl
# Generate a ton of connections and check if we can see syn/ack packets via tcpdump

use strict;
use IO::Socket;
use threads;
use threads::shared;

my $guineapig='www.cs.princeton.edu';
my $targetfile='/~sapanb/small';
my $magic='3j4kl;1234kj341234jl1k234ljk123h4';
my $numiter=1000;
my $numsynacks:shared=0;
my $numthreads=4;
my $numpackets=$numthreads*$numiter;

sub fetch {
	my $sock = new IO::Socket::INET (
		PeerAddr => $guineapig,
		PeerPort => 80,
		Proto => 'tcp'
	);
	return 0 unless $sock;
	print $sock "GET $targetfile HTTP/1.0\r\n";
	print $sock "Host: www.cs.princeton.edu\r\n";
	print $sock "\r\n";

	my $success=0;
	while (<$sock>) {
		if (/$magic/g) {
			$success=1;
			last;
		}
	}
	close ($sock);
	if ($success==1) {
		$numsynacks=$numsynacks+1;
	}
	return $success;
}

sub mfetch {
	foreach (1..$numiter) {
		fetch;
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
	my $filter="'tcp[tcpflags]&tcp-syn !=0 and tcp[tcpflags]&tcp-ack !=0 and src $guineapig'";
	my $cmdline="/usr/sbin/tcpdump -c $numpackets $filter";
	my $p;
	
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
