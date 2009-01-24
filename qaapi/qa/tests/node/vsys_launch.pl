#!/usr/bin/perl
use strict;

my $prefix;

if ($#ARGV>0) {
		$prefix=$ARGV[0];
		print "Setting prefix = $prefix\n";
}
else {
    # Setting temporarily for Thierry's test environment
	$prefix="pl";
}


my $slice="$prefix"."_netflow";
my $slicedir="/vservers/$slice";

# Subtest #1 Create new vsys entry
print "Creating entries...\t";

my $vsys_entry="#!/bin/bash\n\ncat /etc/passwd";
my $vsys_entry_acl = "$slice";

open ACL,">/vsys/test.acl" || die ("Could not create acl for test entry.");
print ACL $vsys_entry_acl;
close ACL;

open FIL,">/vsys/test" || die ("Could not create test entry.");
print FIL $vsys_entry;
close $vsys_entry;

chmod 0755,"/vsys/test";

# Check if it has shown up
sleep(2);

(-p "/vservers/$slice/vsys/test.in") || die ("in file didn't show up in the slice");
(-p "/vservers/$slice/vsys/test.out") || die ("out file didn't show up in the slice");

# OK, SUBTEST #1 SUCCEEDED
print "[SUCCESS] The new entried appeared OK\n";

# Subtest #2 

print "Multiple-connection test...\t";
mkdir ("/vservers/$slice/support");
system("cp vsys_conctest /vservers/$slice/support");
system("su -c '/support/vsys_conctest $slice' $slice -");
($? && die ("[FAILED] Multiple-connection test failed\n"));


# OK, SUBTEST #2 SUCCEEDED
print "[SUCCESS])\n";

# Subtest #3
unlink "/vsys/test.acl";
unlink "/vsys/test";

(-f "$slicedir/test.in" || -f "$slicedir/test.out") && die ("cleanup failed");

