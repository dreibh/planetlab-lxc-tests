# setup

I have a myplc running f14 with foreign nodes running (so far)
* f18
* f20
* f21

# install syslinux

in the f14 myplc:

	rpm --import http://mirror.onelab.eu/keys/RPM-GPG-KEY-fedora-21-primary
	
	yum localinstall http://mirror.onelab.eu/fedora/releases/21/Everything/x86_64/os/Packages/s/syslinux-6.03-1.fc21.x86_64.rpm \
      http://mirror.onelab.eu/fedora/releases/21/Everything/x86_64/os/Packages/s/syslinux-nonlinux-6.03-1.fc21.noarch.rpm \
      http://mirror.onelab.eu/fedora/releases/21/Everything/x86_64/os/Packages/s/syslinux-perl-6.03-1.fc21.x86_64.rpm


# checking

## F14 native node

	run restart-node wait-node

OK

## F18 node
	bond18
	rung 
	rung node restart-node wait-node
OK

## F20 node
OK

## F21 node
OK
