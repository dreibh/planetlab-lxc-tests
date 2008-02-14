#!/bin/sh
# $Id$
COMMAND=$(basename $0)

hostname=$1; shift

# -l option 
if [ "$hostname" = "-l" ] ; then
    echo $COMMAND - listing qemu processes on $(hostname)
    pids="$(pgrep -x qemu) $(pgrep -x start-qemu-node)"
    [ -n "$(echo $pids)" ] && ps $pids
    exit 0
fi

# locate only the actual qemu 
qemu_pids="$(pgrep -x start-qemu-node) $(pgrep -x qemu)"

if [ -z "$(echo $qemu_pids)" ] ; then
    echo $COMMAND - no qemu found on $(hostname)
    exit 0
fi

pids="$(ps $qemu_pids | grep $hostname | awk '{print $1;}')"

if [ -z "$pids" ] ; then
    echo $COMMAND: no qemu instance for $hostname found on $(hostname)
    exit 0
fi

echo Killing $pids
kill $pids
(sleep 1; 
 if ps $pids &> /dev/null ; then
     echo still alive - killing -9 $pids
     kill -9 $pids
 fi ) &
echo Done
exit 0
