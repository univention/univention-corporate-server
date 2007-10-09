#!/bin/bash -e
#
# Univention Client Devices
#  exports local devices of a thin client
#
# Copyright (C) 2001, 2002, 2003, 2004, 2005, 2006 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA


DEVICE_ROOT="/ramdisk/devices"
DEVICE_TMP="/ramdisk/devices.mnt"
DRIVE_LETTERS=(K L M N O P Q R S T U V W X Y Z)

drive_index="0"
DEVICES=""
if [ -e "/dev/.udev" ]; then
	# detect floppy drives
	for d in `ls -1 /dev/fd[0-9]`; do
		b=$(basename $d)
		if [ "$b" == "fd0" ]; then
			DEVICES="$DEVICES floppy:$d:vfat:rw:${DRIVE_LETTERS[$drive_index]}"
			drive_index=$[$drive_index + 1]
		else
			DEVICES="$DEVICES floppy$b:$d:vfat:rw:${DRIVE_LETTERS[$drive_index]}"
			drive_index=$[$drive_index + 1]
		fi
	done
	# detect cdrom drives
	for d in `ls -1 /dev/cdrom*`; do
		b=$(basename $d)
		DEVICES="$DEVICES $b:$d:iso9660:ro:${DRIVE_LETTERS[$drive_index]}"
		drive_index=$[$drive_index + 1]
	done
else
	DEVICES="floppy:/dev/fd0:vfat:rw:K cdrom:/dev/hda:iso9660:ro:L"
fi

eval `univention-baseconfig shell`

ACTION="$1"
USER="$2"
HOME=`getent passwd $USER | cut -d : -f 6`

cleanup() {
	/etc/init.d/samba stop 2>/dev/null || true
	killall -9 smbd 2>/dev/null || true
	killall -9 nmbd 2>/dev/null || true
	rm -f /tmp/etc/samba/smb.conf;
	rm -f $HOME/.winstartup.cmd;
	rm -f /tmp/etc/samba/smbpasswd
}

cleanup_device() {
	local name=$1
	local device=$2
	local filesystem=$3
	local mode=$4
	local options=$5
	local drive=$6

	umount "$DEVICE_ROOT/$name" 2>/dev/null || true
	umount "$DEVICE_TMP/$name" 2>/dev/null || true
	rmdir "$DEVICE_ROOT/$name" "$DEVICE_TMP/$name" 2>/dev/null || true
}

setup() {
	modprobe fuse
	cat <<-EOF > /etc/samba/smb.conf
	[global]

		debug level = 0
		netbios name = ${hostname}
		server string = %h Client ${hostname}

		syslog = 1
		syslog only = yes
		log file = /tmp/samba
		max log size = 100

		; ldap'

		;passdb backend = ldapsam:ldap://${ldap_server_name} guest
		auth methods = guest sam winbind

		;ldap suffix = "${ldap/base}"

		; idmap/winbind
		;idmap backend = ldap:ldap://${ldap_server_name}
		;idmap uid = 55000-64000
		;idmap gid = 55000-64000

		;winbind enum users = yes
		;winbind enum groups = yes
		;winbind separator = .
		; winbind use default domain = yes
		; winbind enable local accounts = yes
		template shell = /bin/bash
		template homedir = /home/%D-%U


		oplocks = yes
		kernel oplocks = yes
		large readwrite = yes
	#       socket options = TCP_NODELAY IPTOS_LOWDELAY
		socket options = TCP_NODELAY IPTOS_LOWDELAY SO_SNDBUF=8192 SO_RCVBUF=8192
		deadtime = 15
		wide links = no
		read raw = yes
		write raw = yes
		max xmit = 65536
		getwd cache = yes

		#load printers = yes
		#printing = cups

		guest account = nobody

		workgroup = ${hostname}

		security = user
		#password server = ${univentionDesktopServer}

		domain logons = no
		encrypt passwords = yes

		os level = 0
		domain master = no
		prefered master = no
		local master = yes
		#wins server = ${univentionDesktopServer}
		wins support = no
		preserve case = yes
		short preserve case = yes

		invalid users = daemon bin sys sync games man lp mail news uucp proxy majordom postgres www-data backup msql operator list irc gnats alias qmaild qmails qmailr qmailq qmaill qmailp telnetd identd ftp rwhod gdm fetchmail faxmaster
EOF
	touch "$HOME/.winstartup.cmd"
	if [ -e "/tmp/passwd" ]; then
		PASSWD=`cat /tmp/passwd`
		echo -e "$PASSWD\n$PASSWD"|smbpasswd -s -a "$USER"
	else
		echo "password not found"
		exit 1
	fi
}

setup_device() {
	local name=$1
	local device=$2
	local filesystem=$3
	local mode=$4
	local options=$5
	local drive=$6

	mkdir -p "$DEVICE_ROOT/$name" "$DEVICE_TMP/$name" 2>/dev/null || true
	/usr/lib/univention-automount/autofs $device "$DEVICE_ROOT/$name" "$DEVICE_TMP/$name" $filesystem $mode $options allow_other 2>&1|logger
        logger "/usr/lib/univention-automount/autofs $device $DEVICE_ROOT/$name $DEVICE_TMP/$name $filesystem $mode $options allow_other"

	#fusermount -p -x "$DEVICE_ROOT/$name" \
	#	/usr/lib/univention-automount/autofs \
	#	$device "$DEVICE_TMP/$name" $filesystem $mode $options \
	#	> /tmp/fuse-$name.log 2>&1 &

	if [ "$mode" = "rw" ]; then
		writable="yes";
	else
		writable="no";
	fi

	cat <<-EOF >> /etc/samba/smb.conf
	[$name]
		comment = $device
		writable = $writable
		path = $DEVICE_ROOT/$name
		public = no
		browsable = no
		#only user = yes
		locking = no
		sync always = yes
		user = $USER
EOF

	cat <<-EOF >> "$HOME/.winstartup.cmd"
	net use ${drive}: \\\\${hostname}\\$name /persistent:no
EOF

	chown `id -u $USER`.`id -g $USER` "$HOME/.winstartup.cmd"
}


if [ "$ACTION" = "start" ]; then
	cleanup
	setup
elif [ "$ACTION" = "stop" ]; then
	cleanup
fi

options="uid=`id -u $USER`,gid=`id -g $USER`"
for DEVICE in $DEVICES; do
	IFS=":"
	set $DEVICE
	name=$1
	device=$2
	filesystem=$3
	mode=$4
	drive=$5

	if [ "$ACTION" = "start" ]; then
		setup_device $name $device $filesystem $mode $options $drive
	elif [ "$ACTION" = "stop" ]; then
		cleanup_device $name $device $filesystem $mode $options $drive
	fi
done

/etc/init.d/samba start
