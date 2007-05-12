#!/bin/sh
#
# Univention Installer
#  basic system setup
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

. /tmp/installation_profile

architecture=`/bin/uname -m`
mkdir -p /instmnt/etc/univention/
cp /etc/univention/base.conf /instmnt/etc/univention/

cat >>/instmnt/preconfigure.sh <<__EOT__
#!/bin/sh

if [ "$architecture" = "powerpc" -o "$architecture" = "ppc64" ]; then
	mkdir -p /dev/iseries
	mknod /dev/iseries/vcda b 113 0
	mknod /dev/iseries/vda b 112 0
	mknod /dev/iseries/vdb b 112 8
	mknod /dev/iseries/vdc b 112 16

	for((i=1;i<8;i++)); do
		mknod /dev/iseries/vda\$i b 112 \$i
	done

	for((i=9;i<16;i++)); do
		mknod /dev/iseries/vdb\$((i-8)) b 112 \$i
	done

	for((i=17;i<24;i++)); do
		mknod /dev/iseries/vdc\$((i-16)) b 112 \$i
	done
fi


mount -a
#mount /mnt/installation

shadowconfig on
usermod -p `mkpasswd $root_password` root
mount proc /proc -t proc

#create parport devices
cd /dev
./MAKEDEV parport
cd -

export DEBIAN_FRONTEND=noninteractive

#syslogd $LOG
#/etc/init.d/sysklogd

#tail -f /var/log/syslog >/dev/tty3 2>&1 &

mkdir -p /var/log/univention
touch /var/log/univention/join.log
chmod 600 /var/log/univention/join.log
tail -f /var/log/syslog >/dev/tty3 2>&1 &
tail -f /var/log/univention/join.log >/dev/tty4 2>&1 &

nfs=`echo $cdrom_device | grep "nfs:"`
smbfs=`echo $cdrom_device | grep "smbfs:"`
if [ -n "\$nfs" ]; then
	mount -t nfs `echo $cdrom_device | sed -e 's|nfs:||'` /sourcedevice
elif [ -n "\$smbfs" ]; then
	mount -t smbfs `echo $cdrom_device | sed -e 's|smbfs:||'` /sourcedevice
else
	mount $cdrom_device /sourcedevice
fi
apt-get clean
apt-get update

__EOT__

chmod +x /instmnt/preconfigure.sh
chroot /instmnt ./preconfigure.sh
