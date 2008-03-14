#!/usr/bin/perl

# Subtest #1 Create new vsys entry

print "Creating entries...\t";

$vsys_entry="#!/bin/bash\n\ncat /etc/passwd";
$vsys_entry_acl = "/vservers/pl_netflow pl_netflow";

open ACL,">/vsys/test.acl" || die ("Could not create acl for test entry.");
print ACL $vsys_entry_acl;
close ACL;

open FIL,">/vsys/test" || die ("Could not create test entry.");
print FIL $vsys_entry;
close $vsys_entry;

chmod 0755,"/vsys/test";

# Check if it has shown up

(-f "/vservers/pl_netflow/test.in") || die ("in file didn't show up in the slice");
(-f "/vservers/pl_netflow/test.out") || die ("out file didn't show up in the slice");

# OK, SUBTEST #1 SUCCEEDED
print "(success)\n";

# Subtest #2 

print "Multiple-connection test...\t";
system("su -c support/vsys_conctest pl_netflow -");
($? && die ("Multiple-connection test failed\n"));


# OK, SUBTEST #2 SUCCEEDED
print "(success)\n";

# Subtest #3
unlink "/vsys/test.acl";
unlink "/vsys/test";

(-f "/vservers/pl_netflow/test.in" || -f "/vservers/pl_netflow/test.out") && die ("cleanup failed");

