#!/bin/sh
COMMAND=$(basename $0)

hostname=$1; shift
pids="$(ps $(pgrep qemu) | grep $hostname | awk '{print $1;}')"

if [ -z "$pids" ] ; then
    echo $COMMAND: no qemu instance for $hostname found on $(hostname)
else
    echo Killing $pids
    kill $pids
    sleep 2
    if [ -n "$(ps $pids)" ] ; then
	echo Killing -9 $pids
	kill -9 $pids
    fi
    echo Done
fi
