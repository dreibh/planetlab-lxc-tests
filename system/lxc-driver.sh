#!/bin/bash

function sense_all () {

    for i in $(lxc-ls -1|sort|uniq); do 
	[ "$(lxc-info -n $i | grep state| awk '{print $2;}' )" == "RUNNING" ] && echo "$i;$(lxc-info -n $i | grep pid | awk '{print $2;}');$(cat /var/lib/lxc/$i/$i.timestamp)" || :
    done    
}

function start_all () {

    for i in $(lxc-ls -1|sort|uniq); do 
        [ "$(lxc-info -n $i | grep state| awk '{print $2;}' )" != "RUNNING" ] && lxc-start -d -n $i || :
    done
   
    #sense_all
}

function stop_all () {
   
    for i in $(lxc-ls -1|sort|uniq); do
        [ "$(lxc-info -n $i | grep state| awk '{print $2;}' )" != "STOPPED" ] && lxc-stop -n $i
    done
    
    #sense_all
}

function sense_lxc () {

    lxc=$1; shift
    [ "$(lxc-info -n $lxc | grep state | awk '{print $2;}')" == "RUNNING" ] && echo "$lxc;$(lxc-info -n $lxc | grep pid | awk '{print $2;}');$(cat /var/lib/lxc/$lxc/$lxc.timestamp)" || :
}

function start_lxc () {

    lxc=$1; shift
    [ "$(lxc-info -n $lxc | grep state| awk '{print $2;}' )" != "RUNNING" ] && lxc-start -d -n $lxc ||:
    
    #sense_lxc $lxc
}

function stop_lxc () {

    lxc=$1; shift
    [ "$(lxc-info -n $lxc | grep state| awk '{print $2;}' )" != "STOPPED" ] && lxc-stop -n $lxc

    #sense_lxc $lxc
}

function restart_all () {

    stop_all 
    start_all
}

function restart_lxc () {

    lxc=$1; shift
    stop_lxc $lxc
    start_lxc $lxc
}

function destroy_all () {
    
    stop_all
    for i in $(lxc-ls -1|sort|uniq); do
        lxc-destroy -n $i
    done

}

function destroy_lxc () {

    lxc=$1; shift
    stop_lxc $lxc
    lxc-destroy -n $lxc
}

function usage () {
    echo "Usage: lxc-driver.sh [options]"
    echo "Description:"
    echo "   This command is used to manage and retreive information on existing lxc containers "
    echo "lxc-driver.sh -c <COMMAND>_all"
    echo "lxc-driver.sh -c <COMMAND>_lxc -l <LXCNAME>"
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

