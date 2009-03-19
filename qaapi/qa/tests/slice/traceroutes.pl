#!/usr/bin/perl

# Module: VNET+
# Description: 	Trace the route path to a node using two methods: TCP-related ICMP errors, and TTL expiry. 
# Then match the two paths to see that they concord. If there's a slight difference, it's probably OK given that
# some routers might support one type of error but not the other, and that the routes are not guaranteed to be the
# same.
# Dependencies: tcptraceroute, traceroute, which
# Author: sapanb@cs.princeton.edu

$|=1;
use strict;

# ********************************************************************************
# CONFIGURATION


# The node that we're going to trace route. It's probably a good idea to change it
# periodically so that we don't harass the same host.
my $guineapig="vini-veritas.net";

# Location of traceroute, tcptraceroute
my $ttraceroute=`which tcptraceroute 2>/dev/null`;
my $traceroute=`which traceroute 2>/dev/null`;

my %tr;

chop($ttraceroute);
chop($traceroute);

if ($traceroute !~ /^\//) {
	$traceroute=`which tracepath 2>/dev/null`;
	chop($traceroute);
}

if (!-e "$ttraceroute") {
	print $ttraceroute."\n";
	die("[FAILED] Please install tcptraceroute in the slice before running this test\n");
}	
else {
	print "Found tcptraceroute. Good.\n";
}

if ($traceroute !~ /^\//) {
	die("[FAILED] Please install traceroute in the slice before running this test\n");
}	

sub open_tcptraceroute {
	my $cmdline="sudo $ttraceroute $guineapig 2>&1";
	print $cmdline."\n";
	my $out='';
	open TT,"$cmdline|";

	while (<TT>) {
		if (/\((\d+\.\d+\.\d+\.\d+)\)/) {
            glob %tr;
            $tr{"IP$1"}++;
            print ">>>$1\n";
		}
	}
}

sub open_traceroute {
	my $ref=shift;
	my $cmdline="$traceroute $guineapig 2>&1";
	my $out='';
	print $cmdline."\n";
	open TT,"$cmdline|";

	while (<TT>) {
		if (/\((\d+\.\d+\.\d+\.\d+)\)/) {
            glob %tr;
            $tr{"IP$1"}++;
            print ">>>$1\n";
		}
	}
}

sub compare {
	my $ret=1;
	my $double=0;
	my $single=0;
	glob %tr;
	foreach (keys %tr) {
		if ($tr{$_}==1) {
			$single++;
		} elsif ($tr{$_}==2) {
			$double++;
		}
	}
	return ($single,$double);
}

sub alhandler {
	print "[FAILED] Timed out waiting.\n";
	exit(-1);
}

if (fork==0) {
	my %r1;
	my $s;
	my $d;
    glob %tr;

	open_tcptraceroute;
	open_traceroute;

    ($s,$d)=compare;

    if ($d>4) {
        print "[SUCCESS] traceroutes succeeded, singles: $s, doubles: $d\n";
    }
    else {
        print "[FAILED] traceroutes returned different results: $s, $d\n";
    }
}
else {
	print "Generating connections...\n";
	$SIG{ALRM}=\&alhandler;
	alarm(60);
	wait;
}
