#!/bin/sh
#
# Univention Installer
#  reboot system
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

#copy installation profile
cat /tmp/installation_profile | sed -e "s|root_password=.*|#root_password=''|" | sed -e "s|domain_controller_password=.*|#domain_controller_password=''|" >/instmnt/etc/univention/installation_profile

sync


chmod -R 700 /instmnt/root
chmod 1777 /instmnt/tmp

#cleanup
rm -f /instmnt/*.sh
rm -f /instmnt/.log
rm -f /instmnt/start
rm -Rf /instmnt/srv
rm -Rf /instmnt/initrd
rm -Rf /instmnt/dead.letter
/bin/sync

if [ -n "$auto_reboot" ] && [ "$auto_reboot" = "Yes" -o "$auto_reboot" = "yes" -o "$auto_reboot" = "True" -o "$auto_reboot" = "true" ]; then
	echo "Auto reboot"
else
	if [ "$architecture" = "powerpc" -o "$architecture" = "ppc64" ]; then
		echo "Press enter to halt the system"
	else
		echo "Press enter to reboot the system"
	fi
	read foobar
fi

sync

cat >/instmnt/tmp/cleanup.sh <<__EOT__
umount -a >/dev/null 2>&1
__EOT__
chmod +x /instmnt/tmp/cleanup.sh
chroot /instmnt ./tmp/cleanup.sh

cat >/instmnt/tmp/cleanup.sh <<__EOT__
if [ -x /etc/init.d/nscd ]; then
	/etc/init.d/nscd stop
fi

umount -a >/dev/null 2>&1
echo -n "Sending all processes the TERM signal... "
killall5 -15 >/dev/null 2>&1
echo "done."

sleep 5
echo -n "Sending all processes the KILL signal... "
killall5 -9 >/dev/null 2>&1
echo "done."

umount -a >/dev/null 2>&1
rm -Rf /sourcedevice >/dev/null 2>&1
__EOT__

chmod +x /instmnt/tmp/cleanup.sh
chroot /instmnt ./tmp/cleanup.sh

echo "Rebooting in 10 seconds - Please remove the install media in order to prevent install rerun"
for i in 0 1 2 3 4 5 6 7 8 9 ; do echo -n . ; sleep 1 ; done

if [ "$architecture" = "powerpc" -o "$architecture" = "ppc64" ]; then
	halt
else
	reboot
fi
