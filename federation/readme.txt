==== requirements
you need to have 
(*) one master test machine (abbreved 'test') - this is where you
trigger everything from
(*) two servers with myplc installed (abbreved 'plc1' and 'plc2')
at this stage the myplc configuration needs to be done by hand
you also need root ssh access from the test box to the two plc boxes in both boxes

-- configuring the plc servers:
(*) set their names in the Makefile (PLC1 and PLC2) 
(*) edit TestPeers.py too -- xxx should be improved

To some extent this stuff can be ran to control a single plc.

==== concepts
right now, 4 tests sizes are supported, they are named
* m (minimal)	   1 object of each kind is created
* n (normal)	   a few of each kind
* b (big)	     	   a few hundreds
* h (huge)	   a few thousands

two modes are supported:

(1) single run mode: everything is ran from the 'test' box
this is a convenient, but very slow mode, especially for large sizes
because each individual object is created in a single xmlrpc command 
>>> xxx btw, I did not know about begin/commit at that time, but I do not
       think it can speed up to the point where the second mode does
In this mode, both DB's are populated together, and various checks can
be done on the fly

(2) populate-and-run mode
where the DB populating parts are done beforehand, and separately,
from each plc's chroot jail for direct access to the DB
This mode allows for dump&restore of the populated DB

==== preparation

(*) manually install both myplc, do the configs manually (once and for
good, see upgrades below)

(*) initial setup
- check Makefile and TestPeers.py for correct identification of 

(*) push the stuff
$ make push
so the local repository gets synced on all nodes.

(*) get and push peers information
$ make peers 
(at least once) so the gpg and other authentication materials get pushed to both nodes

==== use cases

IMPORTANT:  for cleaning up previous tests if needed

$ make db-clean.3
=> cleans up both databases if needed
<<< xxx this uses the initscripts to perform the job, it's a bit slow on
old boxes, could probably be improved by snapshotting the db right
after plc gets started>>>

(1) 

$ make testpeers.help

$ make testpeers-m.run
assumes the dbs are clean, and runs the test locally

$ make testpeers-b.all
cleans both dbs and runs .run

$ make testpeers-m.diff
checks the output agaist the .ref file that chould be under subversion

$ make testpeers-m.ckp
adopts the current .out as a reference for that test - does *not*
commit under subversion, just copies the .out into .ref

(2)

$ make populate.help

$ make populate-m.all
cleans both dbs, cleans any former result, then runs .init and .run

$ make populate-b.init
assumes both dbs are clean, populates both databases and dumps database in the .sql files

$ make populate-b.run
performs the populate_end part of the test from the populated database

$ make populate-b.restore
restores the database from the stage where it just populated

$ make populate-b.clean
cleans everything except the sql files

$ make populate-b.sqlclean
cleans the .sql files

==== various utilities

(*) upgrading both plcs (xxx could be improved):
- log as root on both plc servers and manually curl the myplc rpm you
want, in /root/new_plc_api/tests
- back to the server node:
$ make upgrade.3

if you want to upgrade only one, of course just use targets upgrade.1
or upgrade.2

(*) cleaning the database
$ make db-clean.1 (or .2 or .3)



==== implementation notes
I've designed this thing so everything can be invoked from the test
server, even when things need to be actually triggered from a chroot

For this reason the same pieces of code (namely Makefile and
TestPeers.py) needs to be accessible from
(*) the test server
(*) root's homedir on both plc's, namely in /root/new_plc_api/tests
(*) chroot jail on both plc's, namely in /plc/root/usr/share/plc_api/tests

This is where the 'push' target comes in
xxx at this stage the push target pushes the whole API, because I used this 
to test the code that I was patching on the test node. this can be improved

TARGET structure

If you need to invoke something on a given plc, append '.1' or '.2' to the target name
$ make db-clean.1
Will run the 'db-clean' target on the plc1 node

for convenience:
$ make db-clean.3
will run db-clean on both plc's

When something needs to be ran in the chroot jail, run
$ make sometarget.chroot
that will make sometarget from the chroot jail

So from the test server
$ make sometarget.chroot.3
runs in both chroot jails

