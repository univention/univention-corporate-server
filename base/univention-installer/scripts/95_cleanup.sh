#!/bin/sh
#
# Univention Installer
#  cleanup system
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
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Performing cleanup")" >&9

. /tmp/installation_profile

if [ -e /tmp/installation_profile_scanned ]; then
	. /tmp/installation_profile_scanned
fi

sync

chmod -R 700 /instmnt/root
chmod 1777 /instmnt/tmp
# Bug 29450:
chmod 0755 /instmnt/var/cache/apt/archives/partial /instmnt/var/lib/apt/lists/partial

#cleanup
rm -f /instmnt/*.sh
rm -f /instmnt/.log
rm -f /instmnt/start
rm -Rf /instmnt/initrd
rm -Rf /instmnt/dead.letter
/bin/sync

sync

cat >/instmnt/tmp/cleanup.sh <<__EOT__
#!/bin/sh
umount -a >/dev/null 2>&1
__EOT__
chmod +x /instmnt/tmp/cleanup.sh
chroot /instmnt ./tmp/cleanup.sh

cat >/instmnt/tmp/cleanup.sh <<__EOT__
#!/bin/sh

for service in nscd \
			nfs-kernel-server \
			nfs-common \
			univention-directory-listener \
			univention-directory-notifier \
			winbind \
			samba4 \
			samba \
			slapd;
do
	test -x "/etc/init.d/\$service" && invoke-rc.d "\$service" stop
done

# Bug 28473: reenable automatic configuration of interfaces
ucr unset --force interfaces/restart/auto
ucr unset interfaces/restart/auto

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
