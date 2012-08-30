#!/bin/sh
#
# Univention Installer
#  Configure Univention Config Registry
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
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Configuring Univention base packages")" >&9

. /tmp/installation_profile

architecture=`/bin/uname -m`

acpi_off=`grep "acpi=off" /proc/cmdline`
pci_acpi_off=`grep "pci=noacpi" /proc/cmdline`
pci_acpi_on=`grep "pci=acpi" /proc/cmdline`
version_version=`sed -ne 's|VERSION=||p' </instmnt/sourcedevice/.univention_install`
version_patchlevel=`sed -ne 's|PATCHLEVEL=||p' </instmnt/sourcedevice/.univention_install`
case "${version_version}-${version_patchlevel}" in # Bug #27835
3.0-0) version_erratalevel=0 ;;
3.0-1) version_erratalevel=30 ;;
3.0-2) version_erratalevel=93 ;;
esac

# get x keyboard config
if [ -n "$locale_default" ]; then
	myLocale=$(echo "$locale_default" | awk -F : '{print $1}')

	xkbLayout=$(sh /lib/univention-installer/locale/locale2xkblayout.sh --layout "$myLocale")
	xkbVariant=$(sh /lib/univention-installer/locale/locale2xkblayout.sh --variant "$myLocale")
fi

if [ -n "$system_role" ]; then
	export server_role="$system_role"
fi
cat >/instmnt/hostname.sh <<__EOT__
#!/bin/sh
if [ -n "$to_scan" ] || [ -n "$scan" ]; then
	for ts in $to_scan $scan; do
		if [ "\$ts" = "hostname" ]; then
			ipcmd=\`sed -ne 's/.*ip=//gp' </proc/cmdline\`
			myip=\`echo \$ipcmd | awk -F ':' '{print \$1}'\`
			if [ -n "$nameserver1" ]; then
				host=\`host \$myip $nameserver1 |tail -1 | awk '{print \$5}' | awk -F '.' '{print \$1}'\`
			elif [ -n "$nameserver_1" ]; then
				host=\`host \$myip $nameserver_1 |tail -1 | awk '{print \$5}' | awk -F '.' '{print \$1}'\`
			fi
		fi
	done
fi
if [ -n "\$host" ]; then
	univention-config-registry set hostname=\$host
elif [ -n "$hostname" ]; then
	univention-config-registry set hostname=$hostname
fi
hostname \`univention-config-registry get hostname\`		# finally
__EOT__
chmod +x /instmnt/hostname.sh
chroot /instmnt ./hostname.sh

cat >/instmnt/postconfigure_config_registry.sh <<__EOT__
#!/bin/sh
univention-config-registry set \
	domainname="$domainname" \
	windows/domain="$windows_domain"
__EOT__

cat >>/instmnt/postconfigure_config_registry.sh <<__EOT__

if [ -n "$create_home_share" -a "$create_home_share" = "true" ]; then
	univention-config-registry set create/home/share=true
fi

if [ -n "$ldap_position" ]; then
	univention-config-registry set ldap/position="$ldap_position"
fi

if [ "$server_role" = "domaincontroller_master" ]; then
	if [ -n "$ldap_base" ]; then
		univention-config-registry set ldap/base="$ldap_base"
	fi
	univention-config-registry set \
	  ldap/server/ip="$eth0_ip" \
	  ldap/server/port=7389 \
	  ldap/server/name="$hostname.$domainname" \
	  ldap/master="$hostname.$domainname" \
	  ldap/master/port=7389 \
	  kerberos/adminserver="$hostname.$domainname" \
	  server/role=domaincontroller_master \
	  ldap/server/type=master
else
	if [ -n "$ldap_base" ]; then
		univention-config-registry set ldap/base="$ldap_base"
	fi

	univention-config-registry set ldap/master/port?7389 ## provide default for univention-join
	if [ -n "$domain_controller_ip" ]; then
		univention-config-registry set ldap/master/ip="$domain_controller_ip"
	fi

	univention-config-registry set ldap/server/type=slave

	if [ $server_role = "domaincontroller_slave" ]; then
		univention-config-registry set server/role=domaincontroller_slave
	elif [ $server_role = "memberserver" ]; then
		univention-config-registry set server/role=memberserver
	elif [ $server_role = "managed_client" ]; then
		univention-config-registry set server/role=fatclient
	elif [ $server_role = "mobile_client" ]; then
		univention-config-registry set server/role=mobileclient
	elif [ $server_role = "domaincontroller_backup" ]; then
		univention-config-registry set server/role=domaincontroller_backup
	elif [ $server_role = "basesystem" ]; then
		univention-config-registry set server/role=basesystem
	fi
fi

if [ -n "$acpi_off" ]; then
	univention-config-registry set "\$(univention-config-registry get grub/append) acpi=off"
fi

if [ -n "$pci_acpi_off" ]; then
	univention-config-registry set "\$(univention-config-registry get grub/append) pci=noacpi"
fi

univention-config-registry set locale="$locales"

if [ -n "$locale_default" ]; then
	short_form=`echo $locale_default | awk -F ':' '{print $1}'`

	univention-config-registry set \
	  locale/default="$locale_default"
fi

echo "$timezone" >/etc/timezone
ln -sf "/usr/share/zoneinfo/$timezone" /etc/localtime

mkdir -p /etc/console

univention-config-registry set locale/keymap="$keymap"

if [ -n "$xkbVariant" ]; then
	univention-config-registry set xorg/keyboard/options/XkbVariant="$xkbVariant"
fi

if [ -n "$xkbLayout" ]; then
	univention-config-registry set xorg/keyboard/options/XkbLayout="$xkbLayout"
fi

if [ -n "$ox_primary_maildomain" ] ; then
	univention-config-registry set ox/mail/domain/primary="$ox_primary_maildomain"
fi

univention-config-registry set \
	version/version="$version_version" \
	version/patchlevel="$version_patchlevel" \
	${version_erratalevel:+version/erratalevel=$version_erratalevel} \
	${version_erratalevel:+repository/online/errata/start=$((1 + $version_erratalevel))}

univention-config-registry commit

# Start syslogd
/etc/init.d/sysklogd start
__EOT__

# get all profile variables with leading "ssl_" and set them as UCR variables with leading "ssl/"
set | grep ^ssl_ | while read line ; do
    echo "univention-config-registry set $(echo "$line" | sed -e 's,^ssl_,ssl/,')" >> /instmnt/postconfigure_config_registry.sh
done

chmod +x /instmnt/postconfigure_config_registry.sh
chroot /instmnt ./postconfigure_config_registry.sh
