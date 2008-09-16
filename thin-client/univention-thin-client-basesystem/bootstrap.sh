#!/bin/sh -e
#
# Univention Thin Client Basesystem
#  bootstrap script for the univention-thin-client-basesystem debian package
#
# Copyright (C) 2001, 2002, 2003, 2004, 2005, 2006, 2007 Univention GmbH
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

export suite=univention
mirror=http://192.168.0.10/build2/ucs_2.0-0/

export packages="univention-config-registry python-support python-univention libnss-ldap libpam-ldap nfs-common heimdal-clients openssh-client python2.4 bind9-host pam-runasroot ntpdate ntp less univention-automount dhcp-client libpam-heimdal heimdal-clients univention-policy-tools libunivention-policy0 libldap2 ldap-utils python-dns kudzu-2.6 lynx locales univention-home-mounter rdate netcat univention-automount univention-bootsplash univention-kde-setdirs console-data univention-client-session gawk iproute  whiptail dialog file libmagic1 libidl0"
export exclude="lilo,pcmcia-cs,base-config,exim,mailx,at,logrotate,cpio,ipchains,dhcp-client,manpages,modconf,mbr,man-db,makedev,telnet,libdb4.0,info,diff,syslinux"
export remove_packages="apt-utils"
export disable_init="bootmisc.sh hostname.sh cron atd samba mountall.sh checkroot.sh nfs-common hwclock.sh hwclockfirst.sh kudzu winbind console-screen.sh"
export remove_files="etc/pam.d/chsh etc/pam.d/passwd usr/doc usr/games usr/share/man usr/share/man-db usr/share/info usr/share/doc usr/share/doc-base usr/share/apps usr/share/common_licenses usr/share/dict usr/share/calendar"

case "$1" in

    setup)

	destdir="$2"
	test -z "$destdir" && exit 1
	test "$destdir" = "/" && exit 1

	if test -z "$3"; then
	    rm -rf "$destdir"
	    mkdir -p "$destdir"

	    /usr/sbin/debootstrap --exclude="$exclude" "$suite" "$destdir" "$mirror"
	fi

	mkdir -p $destdir/etc/apt/
	cp -a "etc/apt/sources.list" "$destdir/etc/apt/"
	cp -a "etc/apt/apt.conf" "$destdir/etc/apt/"

	install -m755 bootstrap.sh "$destdir/bootstrap.sh"
	touch "$destdir/.univention-bootstrap"
	chroot "$destdir" /bootstrap.sh install

	find etc usr -type d ! -path '*/.svn*' | while read d; do
	    mkdir -p "$destdir/$d"
	done
	find etc usr -type f ! -path '*/.svn*' ! -name '.cvsignore' | while read f; do
	    cp -a "$f" "$destdir/$f"
	done

	# setup univention-baseconfig
	mkdir -p "$destdir/etc/univention/templates/info" \
		"$destdir/etc/univention/templates/files" \
		"$destdir/etc/univention/templates/scripts"
	install -m644 univention-thin-client-basesystem.info "$destdir/etc/univention/templates/info"
	find conffiles -type d ! -path '*/.svn*' | while read d; do
	    n=${d#conffiles}
	    mkdir -p "$destdir/etc/univention/templates/files/$n"
	done
	find conffiles -type f ! -path '*/.svn*' ! -name '.cvsignore' | while read f; do
	    n=${f#conffiles}
	    cp -a "$f" "$destdir/etc/univention/templates/files/$n"
	done

	touch "$destdir/etc/network/interfaces"

	chroot "$destdir" /bootstrap.sh configure

	;;

    install)

	if ! test -f "/.univention-bootstrap"; then
	    echo "Cannot configure outside basesystem"
	    exit 1
	fi

	mkdir -p /etc/univention
	touch /etc/univention/disable_baseconfig

	usermod -p '!' root

	export DEBIAN_FRONTEND=noninteractive
	apt-get update
	yes ''|apt-get -o DPkg::Options=--force-confdef --yes dist-upgrade
	yes ''|apt-get -o DPkg::Options=--force-confdef --yes -f install
	mv "/sbin/start-stop-daemon" "/sbin/start-stop-daemon.REAL"
	echo \
"#!/bin/sh
echo
echo \"Warning: Fake start-stop-daemon called, doing nothing\"" > "/sbin/start-stop-daemon"
chmod 755 "/sbin/start-stop-daemon"

	mount /proc
	export LC_ALL=C
	yes ''|apt-get -o DPkg::Options=--force-confdef --yes install $packages

	# remove unwanted stuff
	for f in $remove_files; do
		if [ -f "$f" ] ; then
			rm -fR "$f"
		elif [ -d "$f" ] ; then
			find $f -type f -print0 | xargs -0 -r -n10 rm -f
		fi
	done
	yes ''|apt-get -o DPkg::Options=--force-confdef --yes remove $remove_packages

	for f in `find usr/share/locale -type d -maxdepth 1`
	  do
	  if [ `basename $f` != 'C' -a `basename $f` != 'de' -a `basename $f` != 'locale' ]
		  then
		  rm -Rf $f
	  fi
	done

	;;

    configure)

	if ! test -f "/.univention-bootstrap"; then
	    echo "Cannot configure outside basesystem"
	    exit 1
	fi

	# setup symlinks
	if ! test -d /ramdisk; then
	    mkdir /ramdisk
	fi

	if test -f /etc/mtab; then
	    rm -f /etc/mtab
	    ln -s /proc/mounts /etc/mtab
	fi

	for i in /tmp /var /root /home; do
	    if test -d "$i"; then
		mv "$i" "/ramdisk$i"
		ln -s "ramdisk$i" "$i"
	    fi
	done
	if ! test -d /etc/univention; then
	    mkdir /etc/univention
	fi

	if ! test -L /etc/univention/base.conf; then
	    test -d /ramdisk/etc/univention || mkdir -p /ramdisk/etc/univention
	    test -d /ramdisk/etc/default || mkdir -p /ramdisk/etc/default
	    test -d /ramdisk/etc/init.d || mkdir -p /ramdisk/etc/init.d
		for f in base.conf base-ldap.conf base-forced.conf ; do
	    	ln -fs /ramdisk/etc/univention/${f} /etc/univention/${f}
	    	ln -fs /ramdisk/etc/univention/${f}.bak /etc/univention/${f}.bak
		done

	    touch /ramdisk/etc/mtab.fuselock
	    touch /ramdisk/etc/hosts

	    ln -fs /ramdisk/etc/mtab.fuselock /etc/mtab.fuselock
	    ln -fs /ramdisk/etc/hosts /etc/hosts
	fi
	mkdir -p /ramdisk/etc/network/run

	if test -e /etc/network/run; then rm -rf /etc/network/run; fi
	ln -fs /ramdisk/etc/network/run /etc/network/run
	ln -fs /ramdisk/etc/udev/rules.d/z25_persistent-net.rules /etc/udev/rules.d/z25_persistent-net.rules

	rm -f /etc/univention/disable_baseconfig

	touch /etc/univention/ramdisk.dirs
	for dir in "/home" "/root" "/etc/udev/rules.d" "/etc/network/run" "/var/lib/univention-home-mounter" "/tmp" "/var/tmp"; do
		if [ `grep -c "$dir" /etc/univention/ramdisk.dirs` = "0" ]; then
			echo "$dir" >> /etc/univention/ramdisk.dirs
		fi
	done
	find etc/univention/templates/files -type d | while read dir; do
	    n=${dir#etc/univention/templates/files}
		if [ `grep -c "$n" /etc/univention/ramdisk.dirs` = "0" ]; then
			echo "$n" >> /etc/univention/ramdisk.dirs
		fi
	done
	find etc/univention/templates/files -type f | while read f; do
	    n=${f#etc/univention/templates/files}
	    if test "$n" = "/.templates" -o "$n" = "/.not-templates"; then
			continue
	    fi

	    echo "installing $n..."
	    if ! test -L "$n"; then
			mkdir -p "/ramdisk`dirname \"$n\"`"
			if [ -f "$n" ]; then
				mv "$n" "/ramdisk$n"
			else
				touch "/ramdisk$n"
			fi
			mkdir -p "`dirname \"$n\"`"
			ln -s "/ramdisk$n" "$n"
	    fi
	done

	for i in $disable_init; do
	    update-rc.d -f $i remove
	done

	chmod 0755 /etc/dhcp3/dhclient-script
	update-rc.d thin-client-base start 02 S .
	update-rc.d thin-client-network start 40 S .
	update-rc.d thin-client-ldap start 45 S .
	update-rc.d thin-client-policies start 50 S .

	ln -sf /etc/init.d/portmap /etc/rc2.d/S80portmap

	mv "/sbin/start-stop-daemon.REAL" "/sbin/start-stop-daemon"
	# set keyboard to German
	ln -sf ../../usr/share/keymaps/i386/qwertz/de-latin1.kmap.gz /etc/console/boottime.kmap.gz || true
	ln -sf ../../usr/share/zoneinfo/Europe/Berlin /etc/localtime || true
	apt-get clean

	# reset dpkg status (currently installed packages are part of univention-thin-client-basesystem)
	#dpkg --clear-avail
	#echo -n > /var/lib/dpkg/status
	#yes ''|apt-get -o DPkg::Options=--force-confdef --yes install dpkg

	umount -f -n /proc || true
	rm -f /bootstrap.sh /.univention-bootstrap

	;;

    *)
	echo "Usage: $0 {setup,install,configure}"
esac
