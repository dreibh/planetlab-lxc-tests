#!/bin/bash

# =============================================================================
# Author: Marco Yuen
# $Date$
# $Revision$
# $Author$
# =============================================================================
# README
# ------
# Make sure you have the rights to run SUDO. Otherwise, this script will not
# work.
# =============================================================================

###############################################################################
# Configurations
###############################################################################

# Directory where VDE and QEMU are installed
# Only needed when not in path or when you want to override
#VDEROOT="/usr/local/bin/"
#QEMUROOT="/usr/local/bin/"

# The network info for tun0 (private interface)
PRIVATE_IP="10.0.2.1"
PRIVATE_NETMASK="255.255.255.0"

# The network info for tun1 (public interface)
PUBLIC_IP="172.20.0.1"
PUBLIC_NETMASK="255.255.0.0"

# The default memory size
MEGS="512"

# The default #CPUS size
CPUS="1"

# By default do not specify the disk, cdrom, floppy, or boot
DISK1=""
DISK2=""
DISK3=""
DISK4=""
CDROM=""
FLOPPY=""
BOOT=""

# If VDE is off, use tap/tun by default. Otherwise use ``user''.
MULTIHOMED="no"
TYPE="vde"

# Which QEMU executable to use
#QEMUEXE="qemu-system_x86_64"
QEMUEXE="qemu"



###############################################################################
# Functions 
# Please, DO NOT modify anything below this line, unless you know what you are
# doing.
###############################################################################

NETWORK_SET=""
function network_set {
    if [[ ! -z ${NETWORK_SET} ]]; then
        echo "Don't mix -u, -v, -t. Use only one"
        exit 1
    fi
}

function image_check {
    IMG=${1}
    if [[ ! -w ${IMG} ]]; then
        echo "The disk image '${IMG}' doesn't exist or not writtable"
        exit 1
    fi
}

function kill_or_start_vde {
    # For good measure, let's kill all the existing vde_switch(es)
    if [[ -S /tmp/private.ctl && -S /tmp/public.ctl ]]; then
        echo -n "Existing public and private switches found. Kill them?(yes or no) "
        read KILLTHEM

        if [[ ${KILLTHEM} == "yes" ]]; then
            create_switches
        elif [[ ${KILLTHEM} == "no" ]]; then
            echo "You are exposing weakness ..."
        fi
    else
	create_switches
    fi
}

function create_switches {
    sudo killall -9 vde_switch
    echo "Creating new sockets ..."
    # Create the private switch
    sudo ${VDEROOT}vde_switch -tap tun0 \
        -sock /tmp/private.ctl -daemon
    # Create the public switch
    sudo ${VDEROOT}vde_switch -tap tun1 \
        -sock /tmp/public.ctl -daemon
    # Correct the permissions
    sudo chmod 666 /tmp/private.ctl
    sudo chmod 666 /tmp/public.ctl
    # Setting up network info
    sudo ifconfig tun0 ${PRIVATE_IP} netmask ${PRIVATE_NETMASK}
    sudo ifconfig tun1 ${PUBLIC_IP} netmask ${PUBLIC_NETMASK}
    # Turn on ip forwarding and set up IPTABLE
    sudo sysctl -w net.ipv4.ip_forward=1
    # Disable IPTABLES first
    sudo /etc/init.d/iptables stop
    # XXX Define some rules.
    sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
    sudo /etc/init.d/iptables save
    sudo /etc/init.d/iptables start
}

###############################################################################
# Main
###############################################################################

function usage() {
    echo `basename $0` "file"
    echo "      start qemu with file as hard disk 0 image"
    echo "-b  [a|c|d]"
    echo "      Boot on floppy (a), hard disk (c) or CD-ROM (d). Hard disk boot is the default."
    echo "-c  file"
    echo "      Use file as CD-ROM image. You can use the host CD-ROM by using /dev/cdrom as filename."
    echo "-f  file"
    echo "      Use file as fda floppy disk image.  You can use the host floppy by using /dev/fd0 as filename."
    echo "-m  megs"
    echo "      Set virtual RAM size to megs megabytes. Default is ${MEGS} MB."
    echo "-s  #CPUS"
    echo "      Set the number of CPUs. Default is ${CPUS} MB."
    echo "-n  [user|tap|vde]"
    echo "      vde == VDE based networking. (default = ON)"
    echo "      tap == tun/tap networking. (default = OFF)"
    echo "      user == user mode stack for networking. (default = OFF)"
    echo "-p  mac"
    echo "      Set the mac address of the nic to specified mac"
    echo "-l vmsnapshot"
    echo "      load vm snapshot"
    echo "-o"
    echo "      Multihome this machine"
    echo "-x"
    echo "      serial console"
    echo "-h  print help"
}

MAC="52:54:00:12:34:56"
GRAPHIC=
SNAPSHOT=
while getopts "b:c:f:l:m:n:s:hp:ox" opt ; do
    case ${opt} in
        # Boot mode options
        b)
            BOOT=${OPTARG}
            ;;
	c)
	    CDROM=${OPTARG}
	    ;;
	f)
	    FLOPPY=${OPTARG}
	    ;;
	m)
	    MEGS=${OPTARG}
	    ;;
	s)
	    CPUS=${OPTARG}
	    ;;
        n)
            network_set
            [ "${TYPE}" != "${OPTARG}" ] && NETWORK_SET="yes"
            TYPE=${OPTARG}
            ;;
	o)
	    MULTIHOMED="yes"
	    ;;
	p)
	    MAC=${OPTARG}
	    ;;
	l)
	    SNAPSHOT=${OPTARG}
	    ;;
	x)
	    GRAPHIC=-nographic
	    ;;
        h)
            usage
            exit 0
            ;;
        ?)
            usage
            exit 1
            ;;
    esac
done

shift $(($OPTIND - 1))
DISK1=$1
if [ -z "$DISK1" ]; then
    usage
    exit 1
fi
image_check ${DISK1}

shift
DISK2=$1
shift
DISK3=$1
shift
DISK4=$1
if [ ! -z "${CDROM}" -a ! -z "${DISK4}" ]; then
    echo "canot specify cdrom and 4th ide drive (${DISK4})"
    exit 1
fi

echo "Checking if the kqemu module is loaded ..."
module=$(lsmod | grep kqemu | awk '{print $1}')

if [[ ${module} == "" ]]; then
    echo "Loading kqemu module ... "
    #sudo modprobe kqemu
    [[ $? != 0 ]] && exit 1
    echo "kqemu loaded."
elif [[ ${module} == "kqemu" ]]; then
    echo "kqemu already loaded. Continue ..."
fi

if [ ! -c /dev/kqemu ] ; then
    mknod /dev/kqemu c 250 0 
    chmod 600 /dev/kqemu   
fi

QEMU_CMD="${QEMUROOT}${QEMUEXE} ${GRAPHIC} -m ${MEGS} -smp ${CPUS}"
[ ! -z "${SNAPSHOT}" ] && QEMU_CMD="${QEMU_CMD} -loadvm ${SNAPSHOT}"
[ ! -z "${FLOPPY}" ] && QEMU_CMD="${QEMU_CMD} -fda ${FLOPPY}"
[ ! -z "${CDROM}" ] && QEMU_CMD="${QEMU_CMD} -cdrom ${CDROM}"
[ ! -z "${BOOT}" ] && QEMU_CMD="${QEMU_CMD} -boot ${BOOT}"

[ ! -z "${DISK1}" ] && QEMU_CMD="${QEMU_CMD} -hda ${DISK1}"
[ ! -z "${DISK2}" ] && QEMU_CMD="${QEMU_CMD} -hdb ${DISK2}"
[ ! -z "${CDROM}" -a ! -z "${DISK3}" ] && QEMU_CMD="${QEMU_CMD} -hdd ${DISK3}"
[   -z "${CDROM}" -a ! -z "${DISK3}" ] && QEMU_CMD="${QEMU_CMD} -hdc ${DISK3}"

case ${TYPE} in
    vde)
	QEMU_CMD="${VDEROOT}vdeq ${QEMU_CMD}"
	echo "Running with VDE ..."
	kill_or_start_vde
	QEMU_CMD="${QEMU_CMD} -net nic,vlan=0,macaddr=${MAC}"
	QEMU_CMD="${QEMU_CMD} -net vde,vlan=0,sock=/tmp/private.ctl"
	if [ "${MULTIHOMED}" == "yes" ]; then
	    QEMU_CMD="${QEMU_CMD} -net nic,vlan=1"
	    QEMU_CMD="${QEMU_CMD} -net vde,vlan=1,sock=/tmp/public.ctl"
	fi
	;;
    tap)
	echo "still have to fix code -- mef"
	exit 1
	;;
    user)
	QEMU_CMD="${QEMU_CMD} -net nic -net user"
	;;
    *)
	echo "invalid networking type"
	;;
esac

# Executing frontend.
echo ${QEMU_CMD}
if [ -z "${GRAPHIC}" ]; then
    ${QEMU_CMD} &
else
    ${QEMU_CMD}
fi
