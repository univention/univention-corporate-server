#!/bin/sh
#
# Univention Installer
#  basic system setup
#
# Copyright 2004-2012 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

# update progress message
. /tmp/progress.lib
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Configuring basesystem")" >&9

. /tmp/installation_profile

architecture=`/bin/uname -m`
mkdir -p /instmnt/etc/univention/
cp /etc/univention/base.conf /instmnt/etc/univention/

# preconfigure for nfs mounts
if [ -e /sbin/mount.nfs ]; then
	cp /sbin/mount.nfs /instmnt/sbin/
fi

if [ -e /sbin/rpc.statd ]; then
	cp /sbin/rpc.statd /instmnt/sbin/
fi

cat >/instmnt/preconfigure.sh <<__EOT__
#!/bin/sh

mount proc /proc -t proc
mount -t sysfs sysfs /sys/

# create devices file for xen and kvm
cd /sys/block
for d in xvd[a-z] vd[a-z] ; do
        if [ ! -d "/sys/block/\$d" ]; then
                continue
        fi
        cd "/sys/block/\$d"
        . ./uevent
        mknod "/dev/\$d" b "\$MAJOR" "\$MINOR"
        for i in 1 2 3 4 5 6 7 8 9; do
                if [ ! -e "/dev/\$d\$i" ]; then
                        mknod "/dev/\$d\$i" b "\$MAJOR" "\$((\$MINOR + \$i))"
                fi
        done
done

# create xen console
cd /sys/devices/virtual/tty
for d in hvc[0-9] ; do
        if [ ! -d "/sys/devices/virtual/tty/\$d" ]; then
                continue
        fi
        cd "/sys/devices/virtual/tty/\$d"
        . ./uevent
        if [ ! -e "/dev/\$d" ]; then
                mknod "/dev/\$d" c "\$MAJOR" "\$MINOR"
        fi
done

echo "Setting up devices, this may take a while."
mount devtmpfs -t devtmpfs /dev -o size=10M

mount -a

cp /proc/mounts /etc/mtab

shadowconfig on
if [ -n "$root_password_crypted" ]; then
	usermod -p "$root_password_crypted" root
else
	usermod -p '`mkpasswd -H sha-512 "$root_password"`' root
fi

export DEBIAN_FRONTEND=noninteractive

mkdir -p /var/log/univention
touch /var/log/univention/join.log
chown root:root /var/log/univention/join.log
chmod 600 /var/log/univention/join.log

nfs=`echo $cdrom_device | grep "nfs:"`
smbfs=`echo $cdrom_device | grep "smbfs:"`
if [ -n "\$nfs" ]; then
	/bin/mount -t nfs `echo $cdrom_device | sed -e 's|nfs:||'` /sourcedevice
elif [ -n "\$smbfs" ]; then
	/bin/mount -t smbfs `echo $cdrom_device | sed -e 's|smbfs:||'` /sourcedevice
else
	if ! grep -q " /sourcedevice " /proc/mounts ; then
		mount -r -t iso9660 $cdrom_device /sourcedevice 2>&1
	fi
fi
apt-get clean
apt-get update
__EOT__
chmod +x /instmnt/preconfigure.sh
chroot /instmnt ./preconfigure.sh
