#!/bin/bash

path=/vservers

#################### work on all containers - only deal with the ones that have a timestamp
function sense_all () {
    virsh -c lxc:/// list 2> /dev/null | grep running | while read line; do
        pid=$(echo $line | cut -d' ' -f1)
        lxc_name=$(echo $line | cut -d' ' -f2)
	# ignore regular vservers like testmaster and the like
        timestamp_file=$path/$lxc_name/$lxc_name.timestamp
	[ -f $timestamp_file ] || continue
        timestamp=$(cat $timestamp_file 2> /dev/null)
        echo "$lxc_name;$pid;$timestamp" 
    done  
}

function start_all () {
    virsh -c lxc:/// list --inactive | grep " - "| while read line; do
        lxc_name=$(echo $line | cut -d' ' -f2)
	# ignore regular vservers like testmaster and the like
        timestamp_file=$path/$lxc_name/$lxc_name.timestamp
	[ -f $timestamp_file ] || continue
        virsh -c lxc:/// start $lxc_name
    done    
}

function stop_all () {
    virsh -c lxc:/// list | grep running | while read line; do
        lxc_name=$(echo $line | cut -d' ' -f2)
	# ignore regular vservers like testmaster and the like
        timestamp_file=$path/$lxc_name/$lxc_name.timestamp
	[ -f $timestamp_file ] || continue
        virsh -c lxc:/// destroy $lxc_name
    done   
}

function destroy_all () {
    
    stop_all
    virsh -c lxc:/// list --all | while read line; do
        lxc_name=$(echo $line | cut -d' ' -f2)
	# ignore regular vservers like testmaster and the like
        timestamp_file=$path/$lxc_name/$lxc_name.timestamp
	[ -f $timestamp_file ] || continue
        virsh -c lxc:/// undefine $lxc_name
        rm -fr $path/$lxc_name 
    done
}

function restart_all () {

    stop_all 
    start_all
}

#################### deal with one user-specified container
function sense_lxc () {

    lxc_name=$1; shift
    if [ "$(virsh -c lxc:/// dominfo $lxc_name | grep State| cut -d' ' -f11)" == "running" ] ; then
       pid=$(virsh -c lxc:/// dominfo $lxc_name| grep Id | cut -d' ' -f14)
        timestamp_file=$path/$lxc_name/$lxc_name.timestamp
       timestamp=$(cat $timestamp_file)
       echo "$lxc_name;$pid;$timestamp"
    fi
}

function start_lxc () {

    lxc_name=$1; shift
    if [ "$(virsh -c lxc:/// dominfo $lxc_name | grep State| cut -d' ' -f11)" != "running" ] ; then
       virsh -c lxc:/// start $lxc_name
    fi
}

function stop_lxc () {

    lxc_name=$1; shift
    if [ "$(virsh -c lxc:/// dominfo $lxc_name | grep State| cut -d' ' -f11)" != "shut off" ] ; then
       virsh -c lxc:/// destroy $lxc_name
    fi
}

function restart_lxc () {

    lxc_name=$1; shift
    stop_lxc $lxc_name
    start_lxc $lxc_name
}

function destroy_lxc () {

    lxc_name=$1; shift
    stop_lxc $lxc_name
    virsh -c lxc:/// undefine $lxc_name
    rm -fr $path/$lxc_name
}

####################
commands="sense_all|start_all|stop_all|restart_all|destroy_all|sense_lxc|start_lxc|stop_lxc|restart_lxc|destroy_lxc"

function usage () {
    echo "Usage: lxc-driver.sh [options]"
    echo "Description:"
    echo "   This command is used to manage and retreive information on existing lxc containers "
    echo "lxc-driver.sh -c <COMMAND>_all"
    echo "lxc-driver.sh -c <COMMAND>_lxc -n <LXCNAME>"
    echo "<COMMAND> in {$commands}"

}

function main () {

    #set -x

    while getopts "c:n:" opt ; do
        case $opt in
            c) command=$OPTARG;;
            n) lxc=$OPTARG;;
            *) usage && exit 1;;
        esac
    done

    
    case $command in
  	sense_all|start_all|stop_all|restart_all|destroy_all|sense_lxc|start_lxc|stop_lxc|restart_lxc|destroy_lxc) $command ;;
	*) usage
    esac


}

main "$@"

