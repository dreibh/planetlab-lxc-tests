#!/usr/bin/perl

# Module: VNET+
# Description: 	Trace the route path to a node using two methods: TCP-related ICMP errors, and TTL expiry. 
# Then match the two paths to see that they concord. If there's a slight difference, it's probably OK given that
# some routers might support one type of error but not the other, and that the routes are not guaranteed to be the
# same.
# Dependencies: tcptraceroute, traceroute, which
# Author: sapanb@cs.princeton.edu

$|=1;

# ********************************************************************************
# CONFIGURATION


# The node that we're going to trace route. It's probably a good idea to change it
# periodically so that we don't harass the same host.
my $guineapig="vini-veritas.net";

# Location of traceroute, tcptraceroute
my $ttraceroute=`which tcptraceroute 2>/dev/null`;
my $traceroute=`which traceroute 2>/dev/null`;

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
	print "Found rcptraceroute. Good.\n";
}

if ($traceroute !~ /^\//) {
	die("[FAILED] Please install traceroute in the slice before running this test\n");
}	

my %hash;

sub open_tcptraceroute {
	my $cmdline="$ttraceroute $guineapig";
	my $out='';
	open TT,"$cmdline|";

	while (<TT>) {
		if (/\((\d+\.\d+\.\d+\.\d+)\)/) {
			$hash{$1}++;
		}
	}
}

sub open_traceroute {
	my $ref=shift;
	my $cmdline="$traceroute $guineapig";
	my $out='';
	open TT,"$cmdline|";
	glob %hash;

	while (<TT>) {
		if (/\((\d+\.\d+\.\d+\.\d+)\)/) {
			if ($ref->{$1}) {print $ref->{$1};}
			$hash{$1}=$hash{$1}+1;
			if ($ref->{$1}) {print $ref->{$1};}
		}
	}
}

sub compare {
	my $ref=shift;
	my $ret=1;
	my $double=0;
	my $single=0;
	foreach (keys %hash) {
		print "$_->".$a1{$_}."\n";
		if ($hash{$_}==1) {
			$single++;
		} elsif ($hash{$_}==2) {
			print "Concorded on $_\n";
			$double++;
		}
		else { die ("[FAILED] bug in test script (sorry!).\n");}

	}
	return ($single,$double);
}

sub alhandler {
	print "[FAILED] Timed out waiting.\n";
	exit(-1);
}

print "Starting tcptraceroute...\n";
if (fork==0) {
	my %r1;
	my $s;
	my $d;

	open_tcptraceroute;
	open_traceroute;
	($s,$d)=compare;
	if ($s==0 && $d>2) {
		print "[SUCCESS] traceroute and tcptraceroute reported the same result. $d hops.\n";
		exit(0);
	}
	elsif ($s && $d>2) {
		print "[PARTIAL SUCCESS] traceroute and tcptraceroute reported $s different hops out of $d.\n";
	}
	else {
		print "[FAILED] traceroute and tcptraceroute reported different results\n";
	}
}
else {
	print "Generating connections...\n";
	$SIG{ALRM}=\&alhandler;
	alarm(60);
	wait;
}
