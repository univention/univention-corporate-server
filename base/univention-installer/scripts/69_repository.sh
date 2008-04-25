#!/bin/sh
#
# Univention Installer
#  setup repository
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

if [ -n "$system_role" ]; then
	export server_role="$system_role"
fi

eval `UNIVENTION_BASECONF=/instmnt/etc/univention/base.conf /bin/python2.4 /sbin/univention-config-registry shell`

sources_list ()
{
		host univention-repository.$domainname >/dev/null 2>&1 
		if [ $? = 0 ]; then
			echo "deb http://univention-repository.$domainname/univention-cdrom/packages/ ./">/instmnt/etc/apt/sources.list
			echo "# deb http://apt.univention.de/$version_version/maintained/ ${version_version}-${version_patchlevel}/all/" >>/instmnt/etc/apt/sources.list
			echo "# deb http://apt.univention.de/$version_version/maintained/ ${version_version}-${version_patchlevel}/i386/" >>/instmnt/etc/apt/sources.list
			echo "# deb http://apt.univention.de/$version_version/maintained/ ${version_version}-${version_patchlevel}/extern/" >>/instmnt/etc/apt/sources.list
			echo "# deb http://apt.univention.de/$version_version/unmaintained/ ${version_version}-${version_patchlevel}/all/" >>/instmnt/etc/apt/sources.list
			echo "# deb http://apt.univention.de/$version_version/unmaintained/ ${version_version}-${version_patchlevel}/i386/" >>/instmnt/etc/apt/sources.list
			echo "# deb http://apt.univention.de/$version_version/unmaintained/ ${version_version}-${version_patchlevel}/extern/" >>/instmnt/etc/apt/sources.list
			echo "# deb-src http://apt.univention.de/$version_version/unmaintained/ ${version_version}-${version_patchlevel}/source/" >>/instmnt/etc/apt/sources.list
		else
			echo "#deb http://univention-repository.$domainname/univention-cdrom/packages/ ./">/instmnt/etc/apt/sources.list
			echo "deb http://apt.univention.de/2.0/$version_version/ ${version_version}-${version_patchlevel}/all/" >>/instmnt/etc/apt/sources.list
			echo "deb http://apt.univention.de/2.0/$version_version/ ${version_version}-${version_patchlevel}/i386/" >>/instmnt/etc/apt/sources.list
			echo "deb http://apt.univention.de/2.0/$version_version/ ${version_version}-${version_patchlevel}/extern/" >>/instmnt/etc/apt/sources.list
			echo "# deb http://apt.univention.de/$version_version/unmaintained/ ${version_version}-${version_patchlevel}/all/" >>/instmnt/etc/apt/sources.list
			echo "# deb http://apt.univention.de/$version_version/unmaintained/ ${version_version}-${version_patchlevel}/i386/" >>/instmnt/etc/apt/sources.list
			echo "# deb http://apt.univention.de/$version_version/unmaintained/ ${version_version}-${version_patchlevel}/extern/" >>/instmnt/etc/apt/sources.list
			echo "# deb-src http://apt.univention.de/$version_version/unmaintained/ ${version_version}-${version_patchlevel}/source/" >>/instmnt/etc/apt/sources.list
		fi
}

if [ -n "$local_repository" ]; then

	if [ "$local_repository" = "true" ] || [ "$local_repository" = "yes" ]; then

		UNIVENTION_BASECONF=/instmnt/etc/univention/base.conf /bin/python2.4 /sbin/univention-config-registry set local/repository=yes

		eval `UNIVENTION_BASECONF=/instmnt/etc/univention/base.conf /bin/python2.4 /sbin/univention-config-registry shell`

		echo "Copy cdrom to /var/lib/univention-server-cdrom"
		mkdir -p /instmnt/var/lib/univention-server-cdrom
		cp -dpR /instmnt/sourcedevice/* /instmnt/var/lib/univention-server-cdrom/
		cp -dpR /instmnt/sourcedevice/.??* /instmnt/var/lib/univention-server-cdrom/
		if [ -e "/instmnt/var/lib/univention-server-cdrom/profiles" ]; then
			chmod -R o-rwx /instmnt/var/lib/univention-server-cdrom/profiles
			chmod -R ug+rwx /instmnt/var/lib/univention-server-cdrom/profiles
		fi
		if [ -e "/instmnt/var/lib/univention-server-cdrom/internal_profiles" ]; then
			chmod -R o-rwx /instmnt/var/lib/univention-server-cdrom/internal_profiles
			chmod -R ug+rwx /instmnt/var/lib/univention-server-cdrom/internal_profiles
		fi

		if [ "$server_role" = "basesystem" ]; then
			echo "deb file:/var/lib/univention-server-cdrom/packages/ ./" >/instmnt/etc/apt/sources.list
		else
			echo "deb http://$hostname.$domainname/univention-cdrom/packages/ ./" >/instmnt/etc/apt/sources.list
		fi

		touch /instmnt//var/lib/univention-server-cdrom/sources.list
		if [ -d "/instmnt//var/lib/univention-server-cdrom/packages" ]; then
			echo "deb http://$hostname.$domainname/univention-cdrom/packages/ ./">> /instmnt/var/lib/univention-server-cdrom/sources.list
		fi
		mkdir -p /instmnt/var/lib/univention-server-cdrom/ucs-updates
		echo "$version_version-$version_patchlevel" >>/instmnt/var/lib/univention-server-cdrom/ucs-updates/index.list
		echo "nextupdate=none" >>/instmnt/var/lib/univention-server-cdrom/ucs-updates/ucs_$version_version-$version_patchlevel.txt
		for dir in /instmnt/var/lib/univention-server-cdrom/ucs-updates/*; do
			if [ -d "$dir" ]; then
				echo "`basename $dir`" >>/instmnt/var/lib/univention-server-cdrom/ucs-updates/index.list
				echo "deb http://$hostname.$domainname/univention-cdrom/ucs-updates/`basename $dir`/ ./">> /instmnt/var/lib/univention-server-cdrom/sources.list
			fi
		done

		boot_version=`uname -r | grep ^2.4`
		mkdir -p /instmnt/var/lib/univention-server-cdrom/isolinux/
		if [ -n "$boot_version" ]; then
			ln -sf /var/lib/univention-server-cdrom/boot/linux24 /instmnt/var/lib/univention-server-cdrom/isolinux/linux
			ln -sf /var/lib/univention-server-cdrom/boot/linux24.bin /instmnt/var/lib/univention-server-cdrom/isolinux/linux.bin
		else
			ln -sf /var/lib/univention-server-cdrom/boot/linux26 /instmnt/var/lib/univention-server-cdrom/isolinux/linux
			ln -sf /var/lib/univention-server-cdrom/boot/linux26.bin /instmnt/var/lib/univention-server-cdrom/isolinux/linux.bin
		fi


	else
		sources_list
	fi

else
	sources_list
fi
