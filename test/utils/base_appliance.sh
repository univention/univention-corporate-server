# shellcheck shell=bash
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2015-2024 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

appliance_default_password="zRMtAmGIb3"

set -x
set -e

die () {
	echo "$*" >&2
	exit 1
}

download_system_setup_packages () {  # [app_id]
	local app="${1:-}"

	# autoremove packages before updating package cache
	# there is an automatic autoremove after installing
	# u-server-ROLE, so anything removed there would not be
	# in the package cache
	apt-get -y autoremove

	/usr/share/univention-system-setup/download-packages -b
}

install_haveged () {
	univention-install -y haveged
}

uninstall_packages () {
	# if upgraded, u-basesystem will be installed by postup.sh
	state="$(dpkg --get-selections univention-basesystem 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		apt-get purge -y --assume-yes univention-basesystem
		apt-get -y --assume-yes autoremove
	fi

	univention-prune-kernels -v
}

setup_appliance () {  # [app_id]
	# Stop firefox. Not required to run, and resets some UCRv (e.g. system/setup/boot/start)
	# TODO is this necessary with UCS 5
	killall -9 firefox-esr || true

	# allow X11 login as normal user
	ucr set "auth/gdm/group/Domain Users"=yes

	# Disable xorg autodetection and set resolution to 800x600 for system setup
	ucr set xorg/autodetect=no xorg/resolution=800x600

	# Disable kernel mode set
	# ucr set grub/append="nomodeset $(ucr get grub/append)"

	# Disable interface renaming
	ucr set grub/append="$(ucr get grub/append) net.ifnames=0"

	# Show bootscreen in 800x600
	ucr set grub/gfxmode=800x600@16

	# generate all UMC languages
	ucr set locale/default="en_US.UTF-8:UTF-8" locale="en_US.UTF-8:UTF-8 de_DE.UTF-8:UTF-8"
	locale-gen

	install_haveged
	uninstall_packages
	univention-install -y --assume-yes --reinstall univention-system-setup-boot

	# shrink appliance image size
	rm -f /etc/apt/sources.list.d/05univention-system-setup.list
	rm -rf /var/cache/univention-system-setup/packages
	download_system_setup_packages

	# Cleanup apt archive
	apt-get -q update

	# set initial system uuid (set to new value in setup-join.sh)
	ucr set uuid/system="00000000-0000-0000-0000-000000000000"

	# Disable fancy output for serial console
	echo 'FANCYTTY=0' >>/etc/lsb-base-logging.sh
}

clear_dhcp_hostname () {
	# reset hostname and domainname in case it was set through dhcp
	local default_hostname="unassigned-hostname"
	local default_domainname="unassigned-domain"
	if [ "$(ucr get hostname)" != "$default_hostname" ] || [ "$(ucr get domainname)" != "$default_domainname" ]; then
		rm -f "/etc/univention/ssl/$(ucr get hostname)"
		rm -rf "/etc/univention/ssl/$(ucr get hostname).$(ucr get domainname)"
		ucr set hostname="$default_hostname" domainname="$default_domainname"
		univention-certificate new -name "$default_hostname.$default_domainname"
		ln -s "/etc/univention/ssl/$default_hostname.$default_domainname" "/etc/univention/ssl/$default_hostname"
	fi
}

appliance_cleanup () {
	# after system setup is finished, boot in 1024x768 (not 800x600)
	cat >/usr/lib/univention-system-setup/appliance-hooks.d/screenresolution <<__EOF__
#!/bin/sh
exec ucr set grub/gfxmode=1024x768@16 \
	xorg/resolution=1024x768
__EOF__
	chmod +x /usr/lib/univention-system-setup/appliance-hooks.d/screenresolution

	cat >/usr/lib/univention-system-setup/appliance-hooks.d/postfix_restart <<__EOF__
#!/bin/sh
systemctl -q list-unit-files postfix.service && systemctl try-restart postfix.service
exit 0
__EOF__
	chmod +x /usr/lib/univention-system-setup/appliance-hooks.d/postfix_restart

	# deactivate kernel module; prevents bootsplash from appearing/freezing in vmware and virtualbox
	ucr set kernel/blacklist="$(ucr get kernel/blacklist);vmwgfx;vboxvideo"

	# Do network stuff

	# set initial values for UCR ssl variables
	/usr/sbin/univention-certificate-check-validity

	clear_dhcp_hostname

	# Set official update server, deactivate online repository until system setup script 90_postjoin/20upgrade
	ucr set repository/online=false \
		repository/online/server='https://updates.software-univention.de'
	# ucr set repository/online/server=univention-repository.knut.univention.de

	rm -rf /root/shared-utils/

	# Cleanup apt archive
	apt-get clean
	apt-get -q update

	# do not restart network interfaces / reset UCR variables
	ucr set --forced interfaces/restart/auto=false
	# Remove all previous network setting
	ucr --keys-only search --non-empty --key '^(interfaces/|gateway$|nameserver|dns/forwarder)' |
		xargs -r ucr unset

	# Set a default nameserver and remove all local configured nameserver
	# Activate DHCP for eth0
	# in ec2 we use net.ifnames=0 so that the interface is always eth0
	ucr set \
		nameserver1=208.67.222.222 \
		interfaces/eth0/type=dhcp \
		dhclient/options/timeout=12

	# Manual cleanup
	rm -rf /tmp/*
	for dir in python-cherrypy3 libwibble-dev texlive-base texlive-lang-german texmf texlive-latex-recommended groff-base libept-dev texlive-doc; do
		rm -rf "/usr/share/doc/$dir"
	done

	[ -e /var/lib/logrotate/status ] && :> /var/lib/logrotate/status
	rm -f /var/mail/systemmail
	rm -rf /var/univention-backup/*

	# fill up HDD with ZEROs to maximize possible compression
	fstrim -av || dd if=/dev/zero of=/fill-it-up bs=1M || rm /fill-it-up

	# Remove persistent net rule
	rm -f /etc/udev/rules.d/70-persistent-net.rules

	ucr unset --forced interfaces/restart/auto
	ucr set system/setup/boot/start=true
}

setup_ec2 () {
	local DEV GRUB='(hd0)' append

	for DEV in /dev/xvda /dev/vda /dev/sda /dev/hda
	do
		[ -b "$DEV" ] && break
	done
	[ -b "$DEV" ] || exit 1
	echo "${GRUB} ${DEV}" >/boot/grub/device.map
	debconf-communicate <<<"set grub-pc/install_devices $DEV"

	append="$(ucr get grub/append |
		sed -re "s|/dev/[hsv]da|${DEV}|g;s|(no)?splash||g") console=tty0 console=ttyS0"
	ucr set server/amazon=true \
		updater/identify="UCS (EC2)" \
		locale="en_US.UTF-8:UTF-8 de_DE.UTF-8:UTF-8" \
		grub/bootsplash=no \
		grub/quiet=no \
		grub/append="${append}" \
		grub/boot=${DEV} \
		grub/root=${DEV}1 \
		grub/rootdelay=0 \
		grub/timeout=0 \
		grub/terminal="console serial" \
		grub/serialcommand="serial --unit=0 --speed=115200 --word=8 --parity=no --stop=1"

	# amazon has an internal timeserver for instances to use:
	ucr set timeserver=169.254.169.123

	rm -f /boot/grub/menu.lst # This still is evaluated by AWS-EC2 if it exists!
	update-grub

	apt-get purge -y univention-firewall ifplugd
	univention-install -y cloud-initramfs-growroot patch gdisk
	mv /usr/share/initramfs-tools/scripts/local-bottom/growroot /usr/share/initramfs-tools/scripts/init-premount/
	###### cp growroot.patch
	cat > /root/growroot.patch <<__EOF__
--- /usr/share/initramfs-tools/scripts/init-premount/growroot.orig      2024-06-04 12:36:47.808220276 +0200
+++ /usr/share/initramfs-tools/scripts/init-premount/growroot   2024-06-04 12:36:48.620183880 +0200
@@ -81,10 +81,6 @@
	*) exit 0;;
 esac

-# There was something to do, unmount and resize
-umount "\${rootmnt}" ||
-	fail "failed to umount \${rootmnt}";
-
 # Wait for any of the initial udev events to finish
 # This is to avoid any other processes using the block device that the
 # root partition is on, which would cause the sfdisk 'BLKRRPART' to fail.
@@ -106,20 +102,4 @@
 # so that the root partition is available when we try and mount it.
 udevadm settle --timeout \${ROOTDELAY:-30}

-# this is taken from 'mountroot' function
-#   see /usr/share/initramfs-tools/scripts/local
-#FSTYPE=\$(wait-for-root "\${ROOT}" \${ROOTDELAY:-30})
-if [ -z "\${ROOTFSTYPE}" ] || [ "\${ROOTFSTYPE}" = auto ]; then
-		FSTYPE=\$(get_fstype "\${ROOT}")
-else
-		FSTYPE=\${ROOTFSTYPE}
-fi
-roflag="-r"
-[ "\${readonly}" = "y" ] || roflag="-w"
-mount \${roflag} \${FSTYPE:+-t \${FSTYPE} }\${ROOTFLAGS} \${ROOT} \${rootmnt} ||
-	fail "failed to re-mount \${ROOT}. this is bad!"
-
-# write to /etc/grownroot-grown. most likely this wont work (readonly)
-{ date --utc > "\${rootmnt}/etc/growroot-grown" ; } >/dev/null 2>&1 || :
-
 # vi: ts=4 noexpandtab
__EOF__

	patch -p1 -d/ < growroot.patch
	rm -f growroot.patch /usr/share/initramfs-tools/scripts/init-premount/growroot.orig
	update-initramfs -uk all

	# resize2fs
	cat > /etc/init.d/resize2fs <<__EOF__
#!/bin/sh
### BEGIN INIT INFO
# Provides:          resize2fs
# Required-Start:    \$local_fs
# Required-Stop:
# Default-Start:     2
# Default-Stop:
# Short-Description: resize filesystem upon boot
### END INIT INFO

resize2fs /dev/xvda1 &
disown
__EOF__
	chmod +x /etc/init.d/resize2fs
	update-rc.d resize2fs defaults
}

# vim:set ts=8 sw=8 noexpandtab:
