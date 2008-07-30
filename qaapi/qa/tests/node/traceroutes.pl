#!/usr/bin/perl
# Generate a ton of connections and check if we can see syn/ack packets via tcpdump

my $guineapig="vini-veritas.net";
my $ttraceroute="/usr/sbin/tcptraceroute";
my $traceroute="/usr/sbin/tracepath";

sub open_tcptraceroute {
	if (!-e "$ttraceroute") {
		die("[FAILED] Please install tcptraceroute in the slice before running this test\n");
	}	
	my $cmdline="$ttraceroute $guineapig";
	my $out='';
	my %result;
	open TT,"$cmdline|";

	while (<TT>) {
		if (/\((\d+\.\d+\.\d+\.\d+)\)/) {
			$result{$1}=$result{$1}+1;
		}
	}
	return %result;

}

sub open_traceroute {
	if (!-e "$traceroute") {
		die("[FAILED] Please install tcptraceroute in the slice before running this test\n");
	}	
	my $ref=shift;
	my $cmdline="$traceroute $guineapig";
	my $out='';
	my %result=%$ref;;
	open TT,"$cmdline|";

	while (<TT>) {
		if (/\((\d+\.\d+\.\d+\.\d+)\)/) {
			$result{$1}=$results{$1}+1;
		}
	}
	return %result;

}

sub compare {
	my $ref=shift;
	my %a1=%$ref;
	my $ret=1;
	my $double=0;
	my $single=0;
	foreach (keys %a1) {
		print "$_->".$a1{$_}."\n";
		if ($a1{$_}==1) {
			print "Single: $_\n";
			$single++;
		} elsif ($a1{$_}==2) {
			print "Double: $_\n";
			$double++;
		}
		else { die ("bug in test script");}

	}
	return ($single,$double);
}

sub alhandler {
	print "[FAILED] Timed out waiting\n";
	exit(-1);
}

print "Starting tcptraceroute...\n";
if (fork==0) {
	my %r1;
	my $s;
	my $d;

	%r1=open_tcptraceroute;
	%r1=open_traceroute %r1;
	($s,$d)=compare(\%r1);
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
