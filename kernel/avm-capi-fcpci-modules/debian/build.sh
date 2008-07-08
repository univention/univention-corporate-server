#! /bin/sh

KVERS=2.6.18-ucs57-686

origdir=`pwd`

mkdir -p /usr/src
cd /usr/src/
pwd
tar xfj /usr/src/linux-source-2.6.18.tar.bz2
mv /usr/src/linux-source-2.6.18 /usr/src/linux
cp $origdir/debian/kernel-config /usr/src/linux/.config
cd /usr/src/linux
make oldconfig
make prepare
make modules

cd $origdir
tar -zxf fcpci-suse*.tar.gz
sh -c "cd fritz; sed 's|^KDIR.*|KDIR		:= /usr/src/linux|' <Makefile >Makefile.tmp; mv Makefile.tmp Makefile; sed 's|^KDIR.*|KDIR		:= /usr/src/linux|' <src/Makefile >src/Makefile.tmp; mv src/Makefile.tmp src/Makefile; make clean; make"
mkdir -p debian/avm-capi-fcpci-modules-2.6.18-ucs57-686/lib/modules/2.6.18-ucs57-686/kernel/drivers/isdn/capi/
cp fritz/src/fcpci.ko debian/avm-capi-fcpci-modules-2.6.18-ucs57-686/lib/modules/2.6.18-ucs57-686/kernel/drivers/isdn/capi/
