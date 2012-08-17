#!/bin/sh
#
# Univention Installer
#  install packages
#
# Copyright 2004-2012 Univention GmbH
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
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Installing selected software components")" >&9

. /tmp/installation_profile

default_packages="isc-dhcp-client openssh-client"

if [ -n "$system_role" ]; then
	export server_role="$system_role"

	# always install univention-mail-postfix, except for base systems
	if [ ! "$server_role" = "basesystem" ]; then
		default_packages="$default_packages univention-mail-postfix"
	fi
fi

PIPE="yes yes '' |"

if [ -n "$components" ]; then
	for i in $components; do
			if [ "$i" = "Samba" ]; then
				packages="$packages univention-samba "
			elif [ "$i" = "Windows-Installer" ]; then
				packages="$packages univention-windows-installer "
			elif [ "$i" = "DHCP" ]; then
				packages="$packages univention-dhcp "
			elif [ "$i" = "DNS" ]; then
				packages="$packages univention-bind univention-bind-proxy "
			elif [ "$i" = "ThinClient" ]; then
				packages="$packages univention-thin-client "
			elif [ "$i" = "X-Client" ]; then
				packages="$packages univention-application-server "
			elif [ "$i" = "KDE" ]; then
				packages="$packages univention-kde "
			elif [ "$i" = "OpenOffice.org" ]; then
				packages="$packages univention-ooffice "
			elif [ "$i" = "Mozilla" ]; then
				packages="$packages univention-mozilla univention-mozilla-german "
			elif [ "$i" = "Evolution" ]; then
				packages="$packages evolution "
			elif [ "$i" = "FaxClient" ]; then
				packages="$packages univention-fax-client "
			elif [ "$i" = "FaxServer" ]; then
				packages="$packages univention-fax-server "
			elif [ "$i" = "Mail" ]; then
				packages="$packages univention-mail-postfix univention-mail-cyrus "
			elif [ "$i" = "Proxy" ]; then
				packages="$packages univention-squid "
			elif [ "$i" = "Spamfilter" ]; then
				packages="$packages univention-spamassassin"
			elif [ "$i" = "Admin" ]; then
				packages="$packages univention-directory-manager "
			elif [ "$i" = "SoftwareMonitor" ]; then
				packages="$packages univention-pkgdb "
			elif [ "$i" = "Backup" ]; then
				packages="$packages unidump "
			elif [ "$i" = "PrintServer" ]; then
				packages="$packages univention-printserver "
			elif [ "$i" = "PrintQuota" ]; then
				packages="$packages univention-printquota "
			elif [ "$i" = "X" ]; then
				packages="$packages univention-x-core univention-kde"
			elif [ "$i" = "NetInstaller" ]; then
				packages="$packages univention-net-installer"
			elif [ "$i" = "ISDN-Administration" ]; then
				packages="$packages univention-isdn"
			elif [ "$i" = "VNC-Server" ]; then
				packages="$packages vncserver"
			fi
	done
fi

# install all firmware packages if dummy network interface is used
if [ -f "/tmp/dummy-network-interface.txt" ] ; then
	export extra_packages="${extra_packages} firmware-linux"
fi

kolab=`echo $packages | grep "univention-kolab2"`
if [ -n "$kolab" ]; then
	export packages=`echo $packages | sed -e 's|univention-mail-postfix ||g;s|univention-mail-cyrus-imap ||g;s|univention-mail-cyrus-pop ||g;s|univention-mail-cyrus ||g;s|univention-spamassassin ||g'`
fi

# install firefox-de if desktop is selected
echo "$packages" | grep -iq univention-kde
if [ $? -eq 0 -a -n "$language" -a "$language" = "de" ]; then
	packages="firefox-de $packages"
fi

# default packages
packages="$packages $default_packages"

cat >/instmnt/install_packages.sh <<__EOT__
#!/bin/sh
echo "PROGRESS: $0: Calculating number of packages"
case "$server_role" in
	domaincontroller_master) pkglist="univention-server-master" ;;
	domaincontroller_backup) pkglist="univention-server-backup" ;;
	domaincontroller_slave) pkglist="univention-server-slave" ;;
	memberserver) pkglist="univention-server-member" ;;
	managed_client) pkglist="univention-managed-client" ;;
	mobile_client) pkglist="univention-mobile-client" ;;
	basesystem) pkglist="univention-basesystem" ;;
	*) echo "PROGRESS: $server_role not found" ;;
esac
# pkglist is set within chroot environment ==> \$pkglist
# packages is set by 50_packages.sh ==> $packages
pkglist="\$pkglist $packages $extra_packages"
PKGCNT="\$(apt-get -y -o APT::Get::AllowUnauthenticated=1 install -s -y --ignore-missing \$pkglist | grep "^Inst " | wc -l)"
echo "__STEPS__:\$((\$PKGCNT * 3))" >&9

export DEBIAN_FRONTEND=noninteractive

if [ "$server_role" = "domaincontroller_master" ]; then
	apt-get -y -o APT::Status-FD=9 -o DPkg::Options::=--force-confold -o APT::Get::AllowUnauthenticated=1 install univention-server-master --yes
elif [ "$server_role" = "domaincontroller_backup" ]; then
	apt-get -y -o APT::Status-FD=9 -o DPkg::Options::=--force-confold -o APT::Get::AllowUnauthenticated=1 install univention-server-backup --yes
elif [ "$server_role" = "domaincontroller_slave" ]; then
	apt-get -y -o APT::Status-FD=9 -o DPkg::Options::=--force-confold -o APT::Get::AllowUnauthenticated=1 install univention-server-slave --yes
elif [ "$server_role" = "memberserver" ]; then
	apt-get -y -o APT::Status-FD=9 -o DPkg::Options::=--force-confold -o APT::Get::AllowUnauthenticated=1 install univention-server-member --yes
elif [ "$server_role" = "managed_client" ]; then
	apt-get -y -o APT::Status-FD=9 -o DPkg::Options::=--force-confold -o APT::Get::AllowUnauthenticated=1 install univention-managed-client --yes
elif [ "$server_role" = "mobile_client" ]; then
	apt-get -y -o APT::Status-FD=9 -o DPkg::Options::=--force-confold -o APT::Get::AllowUnauthenticated=1 install univention-mobile-client univention-network-manager --yes
elif [ "$server_role" = "basesystem" ]; then
	apt-get -y -o APT::Status-FD=9 -o DPkg::Options::=--force-confold -o APT::Get::AllowUnauthenticated=1 install univention-basesystem --yes
fi

$PIPE dpkg --configure -a

if [ -n "$packages" ]; then
	for p in $packages; do
		apt-get -y -o APT::Status-FD=9 -o DPkg::Options::=--force-confold -o APT::Get::AllowUnauthenticated=1 install \$p
		$PIPE dpkg --configure -a
	done
fi

if [ -n "$extra_packages" ]; then
	for p in $extra_packages; do
		apt-get -y -o APT::Status-FD=9 -o DPkg::Options::=--force-confold -o APT::Get::AllowUnauthenticated=1 install \$p
		$PIPE dpkg --configure -a
	done
fi
__EOT__
chmod +x /instmnt/install_packages.sh
chroot /instmnt ./install_packages.sh </dev/tty1
