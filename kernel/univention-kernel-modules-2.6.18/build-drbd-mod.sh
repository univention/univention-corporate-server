#! /bin/sh -x 

rm -rf /tmp/drbd-built
mkdir /tmp/drbd-built

for i in /usr/src/linux-headers-*; do \
    kversion=$(basename $i | sed -e 's|linux-headers-||')
    echo $kversion

    rm -rf /tmp/drbd-build
    mkdir /tmp/drbd-build
    debtmp=/tmp/drbd-build

    mkdir -p $debtmp/drbd/debian
    ko=`find /tmp/usr_src/modules/drbd8/debian/-$kversion -name 'drbd.ko'`
    cp $ko $debtmp/drbd/

    cp templates/* $debtmp/drbd/debian/
    sed -i -e 's|KVERSION|'$kversion'|' $debtmp/drbd/debian/postinst
    sed -i -e 's|KVERSION|'$kversion'|' $debtmp/drbd/debian/control
    sed -i -e 's|KVERSION|'$kversion'|' $debtmp/drbd/debian/rules
    sed -i -e 's|KVERSION|'$kversion'|' $debtmp/drbd/debian/dirs
    cd $debtmp/drbd
    dpkg-buildpackage
    mv $debtmp/*deb /tmp/drbd-built
done;