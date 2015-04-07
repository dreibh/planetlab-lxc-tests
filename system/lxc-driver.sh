#!/bin/bash

path=/vservers

function sense_all () {
    virsh -c lxc:/// list 2> /dev/null | grep running | while read line; do
        pid=$(echo $line | cut -d' ' -f1)
        lxc_name=$(echo $line | cut -d' ' -f2)
        timestamp=$(cat $path/$lxc_name/$lxc_name.timestamp 2> /dev/null)
        echo "$lxc_name;$pid;$timestamp" 
    done  
}

function start_all () {
    virsh -c lxc:/// list --inactive | grep " - "| while read line; do
        lxc_name=$(echo $line | cut -d' ' -f2)
        virsh -c lxc:/// start $lxc_name
    done    
}

function stop_all () {
    virsh -c lxc:/// list | grep running | while read line; do
        lxc_name=$(echo $line | cut -d' ' -f2)
        virsh -c lxc:/// destroy $lxc_name
    done   
}

function sense_lxc () {

    lxc_name=$1; shift
    if [ "$(virsh -c lxc:/// dominfo $lxc_name | grep State| cut -d' ' -f11)" == "running" ] ; then
       pid=$(virsh -c lxc:/// dominfo $lxc_name| grep Id | cut -d' ' -f14)
       timestamp=$(cat $path/$lxc_name/$lxc_name.timestamp)
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

function restart_all () {

    stop_all 
    start_all
}

function restart_lxc () {

    lxc_name=$1; shift
    stop_lxc $lxc_name
    start_lxc $lxc_name
}

function destroy_all () {
    
    stop_all
    virsh -c lxc:/// list --all | while read line; do
        lxc_name=$(echo $line | cut -d' ' -f2)
        virsh -c lxc:/// undefine $lxc_name
        rm -fr $path/$lxc_name 
    done
}

function destroy_lxc () {

    lxc_name=$1; shift
    stop_lxc $lxc_name
    virsh -c lxc:/// undefine $lxc_name
    rm -fr $path/$lxc_name
}

function usage () {
    echo "Usage: lxc-driver.sh [options]"
    echo "Description:"
    echo "   This command is used to manage and retreive information on existing lxc containers "
    echo "lxc-driver.sh -c <COMMAND>_all"
    echo "lxc-driver.sh -c <COMMAND>_lxc -n <LXCNAME>"
    echo "<COMMAND> in {sense,start,stop,restart,destroy}"

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
  	sense_all) sense_all ;;
      	start_all) start_all ;;
	 stop_all) stop_all ;;
      restart_all) restart_all ;;
      destroy_all) destroy_all ;;
	sense_lxc) sense_lxc $lxc;;
        start_lxc) start_lxc $lxc;;
         stop_lxc) stop_lxc $lxc;;
      restart_lxc) restart_lxc $lxc;;
      destroy_lxc) destroy_lxc $lxc;;
		*) usage
    esac


}

main "$@"

