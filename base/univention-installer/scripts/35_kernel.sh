#!/bin/sh
#
# Univention Installer
#  install kernel
#
# Copyright 2004-2013 Univention GmbH
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
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Installing kernel and bootloader")" >&9

. /tmp/installation_profile

if [ -e /tmp/installation_profile_scanned ]; then
	. /tmp/installation_profile_scanned
fi

PIPE="yes yes '' |"

#loaded_modules=`cat /proc/modules | awk '{print $1}' | grep -v ^Module`
#loaded_modules=$(echo $loaded_modules | sed -e 's| |;|g')

if [ -n "$modules" ]; then
	modules=$(echo $modules | sed -e 's| |;|g')
fi

kernel_package="univention-kernel-image"

# 486 legacy kernel
if [ "486" = "$(uname -r | awk -F - '{print $NF}')" ]; then
	kernel_package="univention-kernel-image-486"
fi

cat >/instmnt/install_kernel.sh <<__EOT__
#!/bin/sh
export DEBIAN_FRONTEND=noninteractive

echo "PROGRESS: $0: Calculating number of packages"
PKGCNT="\$(apt-get -y -o APT::Get::AllowUnauthenticated=1 install -s -y --ignore-missing univention-initrd \$kernel_package \$xen_kernel univention-grub | grep "^Inst " | wc -l)"
echo "__STEPS__:\$((\$PKGCNT * 3))" >&9

if [ -n "$modules" ]; then
	univention-config-registry set kernel/modules="$modules"
fi

apt-get -y -o APT::Status-FD=9 -o APT::Get::AllowUnauthenticated=1 install univention-initrd

apt-get -y -o APT::Status-FD=9 -o APT::Get::AllowUnauthenticated=1 install $kernel_package
if [ "\$?" != "0" ]; then
	if [ -n "$fallback_kernel_package" ]; then
		apt-get -y -o APT::Status-FD=9 -o APT::Get::AllowUnauthenticated=1 install $fallback_kernel_package
	fi
fi

if [ -n "$xen_kernel" ]; then
	apt-get -y -o APT::Status-FD=9 -o APT::Get::AllowUnauthenticated=1 install $xen_kernel
fi

univention-config-registry commit
__EOT__
chmod +x /instmnt/install_kernel.sh
chroot /instmnt ./install_kernel.sh

export grub_package="grub-pc"
if [ "$use_efi" = "yes" ] ; then
	export grub_package="univention-uefi"
	eval "$(ucr shell grub/efi/secureboot)"
	if [ "$grub_efi_secureboot" = "yes" ] ; then
		export grub_package="univention-uefi-secureboot"
	fi
fi

# install mdadm if necessary and then grub
cat >/instmnt/install_mdadm.sh <<__EOT__
#!/bin/sh
export DEBIAN_FRONTEND=noninteractive

mount | grep /dev/md 2>&1 1>/dev/null
if [ 0 -eq \$? ]; then
	apt-get -y -o APT::Status-FD=9 -o APT::Get::AllowUnauthenticated=1 install mdadm
fi

ucr set grub/efi="${use_efi}"
apt-get -y -o APT::Status-FD=9 -o APT::Get::AllowUnauthenticated=1 install univention-grub ${grub_package}
__EOT__
chmod +x /instmnt/install_mdadm.sh
chroot /instmnt ./install_mdadm.sh
