#!/bin/sh
#
# Univention Installer
#  install kernel
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
if [ "$architecture" = "powerpc" -o "$architecture" = "ppc64" ]; then
	architecture="powerpc"
fi

PIPE="yes yes '' |"

cat >>/instmnt/install_initrd.sh <<__EOT__

export DEBIAN_FRONTEND=noninteractive

$PIPE apt-get install initrd-tools
$PIPE dpkg --configure -a

__EOT__

if [ "$architecture" != "powerpc" ]; then
	chmod +x /instmnt/install_initrd.sh
	chroot /instmnt ./install_initrd.sh
fi

loaded_modules=`cat /proc/modules | awk '{print $1}' | grep -v ^Module`
loaded_modules=$(echo $loaded_modules | sed -e 's| |;|g')

if [ -n "$modules" ]; then
	modules=$(echo $modules | sed -e 's| |;|g')
fi

if [ -n "$kernel_version" ]; then
	v=`echo $kernel_version | grep ^2.4`
	if [ -n "$v" ]; then
		kernel_package="univention-kernel-image"
	else
		kernel_package="univention-kernel-image-$kernel_version"
	fi
else
	boot_version=`uname -r | grep ^2.4`
	if [ -n "$boot_version" ]; then
		kernel_package="univention-kernel-image"
	else

		if [ "$system_role" = "managed_client" ]; then
			kernel_extension="-managedclient"
		elif [ "$system_role" = "mobile_client" ]; then
			kernel_extension="-mobileclient"
		fi

		boot_version=`uname -r | awk -F"." '{printf "%s.%s.%s\n",$1,$2,$3}'`
		if [ "$boot_version" = "2.6.14" ]; then
			# booting the default kernel image
			kernel_package="univention-kernel-image${kernel_extension}-2.6.18"
			fallback_kernel_package="univention-kernel-image-2.6-18"
		else
			kernel_package="univention-kernel-image${kernel_extension}-${boot_version}"
			fallback_kernel_package="univention-kernel-image-2.6.18"
		fi
			
	fi
fi

cat >>/instmnt/install_kernel.sh <<__EOT__

export DEBIAN_FRONTEND=noninteractive

if [ -n "$loaded_modules" ]; then
	univention-baseconfig set mkinird/modules="$loaded_modules"
fi
if [ -n "$module" ]; then
	univention-baseconfig set kernel/modules="$module"
fi

if [ "$architecture" = "powerpc" ]; then
	$PIPE apt-get install initramfs-tools parted
else
	$PIPE apt-get install univention-grub univention-initrd
fi

echo "do_initrd = Yes" >>/etc/kernel-img.conf
echo "do_bootfloppy = no" >>/etc/kernel-img.conf
echo "silent_loader = yes" >>/etc/kernel-img.conf
if [ "$architecture" = "powerpc" ]; then
	echo "ramdisk = mkinitramfs mkinitrd.yaird" >>/etc/kernel-img.conf
fi

$PIPE apt-get install $kernel_package
if [ "\$?" != "0" ]; then
	if [ -n "$fallback_kernel_package" ]; then
		$PIPE apt-get install $fallback_kernel_package
	fi
fi

univention-baseconfig commit

if [ "$architecture" = "powerpc" ]; then
	#TODO read PreP partition from profile
	for disk in vda vdb vdc vdd; do
		prep=\`parted --script /dev/iseries/\$disk p 2>/dev/null | grep "prep"\`;
		if [ -n "\$prep" ]; then
			prep_partition="/dev/iseries/\$disk\`echo \$prep | awk '{print \$1}'\`";
			break
		fi
	done

	if [ -n "\$prep_partition" ]; then
		dd if=/vmlinux of="\$prep_partition"
	else
		echo "Warning: no PreP Partition found"
	fi
fi

__EOT__

chmod +x /instmnt/install_kernel.sh
chroot /instmnt ./install_kernel.sh
