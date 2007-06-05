#!/bin/sh -e
#
# Univention Client Basesystem
#  bootstrap script for the univention-client-basesystem debian package
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

export suite=univention
mirror=http://192.168.0.10/build2/ucs_2.0-0/

# fixme: univention-python
export packages="univention-config python-univention libnss-ldap libpam-ldap nfs-common rsh-client gdm samba samba-common univention-x-core univention-fonts python2.4 bind9-host pam-runasroot ntpdate ntp less rdesktop fuse-utils univention-automount arts kcontrol dhcp3-client libpam-heimdal heimdal-clients cupsys univention-policy-tools libunivention-policy0 libldap2 ldap-utils python-dns kudzu-2.6 univention-gdm lynx locales univention-xnumlock univention-home-mounter rdate netcat fuse-utils smbfs univention-automount univention-client-devices-client univention-bootsplash univention-kde-setdirs"
export reinstall_packages="univention-client-session univention-gdm univention-gdm-sessions"
# adduser, e2fsprogs
export exclude="lilo,pcmcia-cs,base-config,exim,mailx,at,logrotate,cpio,ipchains,dhcp-client,manpages,modconf,mbr,man-db,makedev,telnet,libdb4.0,info,diff,whiptail,syslinux,libsepol1"
export remove_packages="apt-utils postfix"
export disable_init="bootmisc.sh hostname.sh cron atd samba mountall.sh checkroot.sh portmap nfs-common hwclock.sh hwclockfirst.sh kudzu winbind console-screen.sh"
export remove_files="etc/gdm/Sessions/* etc/pam.d/* etc/cups/ppd usr/X11R6/man usr/doc usr/games usr/share/man usr/share/man-db usr/share/info usr/share/doc usr/share/doc-base usr/share/gtk-doc usr/share/apps usr/share/icons usr/share/common_licenses usr/share/dict usr/share/calendar usr/share/applnk usr/share/applications usr/share/application-registry usr/share/wallpapers usr/share/cups/doc-root etc/network/if-up.d/postfix etc/network/if-down.d/postfix"

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

	install -m755 bootstrap.sh "$destdir/bootstrap.sh"
	touch "$destdir/.univention-bootstrap"
	chroot "$destdir" /bootstrap.sh install

	find etc usr -type d ! -path '*/CVS*' | while read d; do
	    mkdir -p "$destdir/$d"
	done
	find etc usr -type f ! -path '*/CVS*' ! -name '.cvsignore' | while read f; do
	    cp -a "$f" "$destdir/$f"
	done

	# setup univention-baseconfig
	mkdir -p "$destdir/etc/univention/templates/info" \
		"$destdir/etc/univention/templates/files" \
		"$destdir/etc/univention/templates/scripts"
	install -m644 univention-client-basesystem.info "$destdir/etc/univention/templates/info"
	find conffiles -type d ! -path '*/CVS*' | while read d; do
	    n=${d#conffiles}
	    mkdir -p "$destdir/etc/univention/templates/files/$n"
	done
	find conffiles -type f ! -path '*/CVS*' ! -name '.cvsignore' | while read f; do
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
		rm -fR "$f"
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

	yes ''|apt-get -o DPkg::Options=--force-confdef --yes install $reinstall_packages

	# Removed the purge packages loop because we want the KDE-Sounds to be in the Client Basesystem


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
		ln -s "/ramdisk$i" "$i"
	    fi
	done
	if ! test -d /etc/univention; then
	    mkdir /etc/univention
	fi

	if ! test -L /etc/univention/base.conf; then
	    test -d /ramdisk/etc/univention || mkdir -p /ramdisk/etc/univention
	    test -d /ramdisk/etc/default || mkdir -p /ramdisk/etc/default
	    touch /ramdisk/etc/univention/base.conf
	    touch /ramdisk/etc/univention/base.conf.bak
	    touch /ramdisk/etc/mtab.fuselock
	    touch /ramdisk/etc/hosts
	    ln -fs /ramdisk/etc/univention/base.conf /etc/univention/base.conf
	    ln -fs /ramdisk/etc/univention/base.conf.bak /etc/univention/base.conf.bak
	    ln -fs /ramdisk/etc/mtab.fuselock /etc/mtab.fuselock
	    ln -fs /ramdisk/etc/hosts /etc/hosts
	fi
	mkdir -p /ramdisk/etc/network/run
	mkdir -p /ramdisk/var/run/cups
	mkdir -p /ramdisk/var/spool/postfix

	if test -e /etc/network/run; then rm -rf /etc/network/run; fi
	ln -fs /ramdisk/etc/network/run /etc/network/run
	ln -fs /ramdisk/var/run/cups /var/run/cups
	ln -fs /ramdisk/var/spool/postfix /var/spool/postfix
	ln -fs /ramdisk/etc/X11/X /etc/X11/X

	rm -f /etc/univention/disable_baseconfig

	adduser --system --home /tmp --shell "/bin/bash" --disabled-password autostart

	find etc/univention/templates/files -type f | while read f; do
	    n=${f#etc/univention/templates/files}
	    if test "$n" = "/.templates" -o "$n" = "/.not-templates"; then
		continue
	    fi

	    echo "installing $n..."
	    if ! test -L "$n"; then
		rm -f "$n"
		mkdir -p "`dirname \"$n\"`"
		ln -s "/ramdisk$n" "$n"
	    fi
	done


	for i in $disable_init; do
	    update-rc.d -f $i remove
	done

	chmod 0755 /etc/init.d/diskless*.sh /etc/dhcp3/dhclient-script
	update-rc.d diskless.sh start 02 S .
	update-rc.d disklesshardware.sh start 12 2 .
	update-rc.d disklessfinish.sh start 98 2 .
	update-rc.d portmap start 80 2 .
	update-rc.d ntpdate start 98 2 .
	update-rc.d xsession start 99 2 .


	mv "/sbin/start-stop-daemon.REAL" "/sbin/start-stop-daemon"
	# set keyboard to German
	ln -fs ../../usr/share/keymaps/i386/quertz/de-latin1.kmap.gz /etc/console/boottime.kmap.gz
	ln -sf ../../usr/share/zoneinfo/Europe/Berlin /etc/localtime
	/usr/sbin/univention-baseconfig set locale='de_DE@euro:ISO-8859-15'; locale-gen
	apt-get clean

	umount -f -n /proc || true
	rm -f /bootstrap.sh /.univention-bootstrap

	;;

    *)
	echo "Usage: $0 {setup,install,configure}"
esac
