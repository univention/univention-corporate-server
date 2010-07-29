#!/bin/sh
#
# Univention Installer
#  install kernel
#
# Copyright 2004-2010 Univention GmbH
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

. /tmp/installation_profile
architecture=`/bin/uname -m`
if [ "$architecture" = "powerpc" -o "$architecture" = "ppc64" ]; then
	architecture="powerpc"
fi

PIPE="yes yes '' |"

cat >>/instmnt/install_initrd.sh <<__EOT__

export DEBIAN_FRONTEND=noninteractive

apt-get -y -o APT::Get::AllowUnauthenticated=1 install initrd-tools
$PIPE dpkg --configure -a

__EOT__

if [ "$architecture" != "powerpc" ]; then
	chmod +x /instmnt/install_initrd.sh
	chroot /instmnt ./install_initrd.sh
fi

#loaded_modules=`cat /proc/modules | awk '{print $1}' | grep -v ^Module`
#loaded_modules=$(echo $loaded_modules | sed -e 's| |;|g')

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

		boot_version=`uname -r | awk -F"-" '{print $1}'`
		if uname -r | grep -iq bigmem; then 
			boot_version="$boot_version-64gb"
		fi

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

# install xen kernel on xen virtualization server
boot_version=`uname -r | awk -F"-" '{print $1}'`
echo $packages | grep -qi univention-virtual-machine-manager-node-xen
if [ 0 -eq $? ]; then
	xen_kernel="univention-kernel-image-${boot_version}-xen"
fi 
	

cat >>/instmnt/install_kernel.sh <<__EOT__

export DEBIAN_FRONTEND=noninteractive

if [ -n "$modules" ]; then
	univention-config-registry set kernel/modules="$modules"
fi

if [ "$architecture" = "powerpc" ]; then
	apt-get -y -o APT::Get::AllowUnauthenticated=1 install initramfs-tools parted
else
	apt-get -y -o APT::Get::AllowUnauthenticated=1 install univention-initrd
fi

apt-get -y -o APT::Get::AllowUnauthenticated=1 install $kernel_package
if [ "\$?" != "0" ]; then
	if [ -n "$fallback_kernel_package" ]; then
		apt-get -y -o APT::Get::AllowUnauthenticated=1 install $fallback_kernel_package
	fi
fi

if [ -n "$xen_kernel" ]; then
	apt-get -y -o APT::Get::AllowUnauthenticated=1 install $xen_kernel
fi

univention-config-registry commit

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

# install mdadm if necessary and then grub
cat >>/instmnt/install_mdadm.sh <<__EOT__
export DEBIAN_FRONTEND=noninteractive

mount | grep /dev/md 2>&1 1>/dev/null
if [ 0 -eq \$? ]; then
	apt-get -y -o APT::Get::AllowUnauthenticated=1 install mdadm
fi

apt-get -y -o APT::Get::AllowUnauthenticated=1 install univention-grub

__EOT__

chmod +x /instmnt/install_mdadm.sh
chroot /instmnt ./install_mdadm.sh

