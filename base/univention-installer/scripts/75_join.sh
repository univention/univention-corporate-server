#!/bin/sh
#
# Univention Installer
#  Join a system in the UCS domain
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
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Joining system into domain")" >&9

. /tmp/installation_profile

if [ -n "$system_role" ]; then
	export server_role="$system_role"
fi
if [ -n "$call_master_joinscripts" ]; then
	export call_master_joinscripts="$(echo "$call_master_joinscripts" | tr '[:upper:]' '[:lower:]')"
fi

# copy installation profile
cat /tmp/installation_profile | sed -e "s|root_password=.*|#root_password=''|" | sed -e "s|domain_controller_password=.*|#domain_controller_password=''|" > /instmnt/etc/univention/installation_profile

sync

if [ ! -e /instmnt/var/lib/univention-ldap ]; then
	mkdir -p /instmnt/var/lib/univention-ldap
fi
echo -n "$root_password" >/instmnt/var/lib/univention-ldap/root.secret
chmod 600 /instmnt/var/lib/univention-ldap/root.secret

cat >/instmnt/join.sh <<__EOT__
#!/bin/sh
progress_filter () {
	# this pipe redirects stdout to read stdout (/proc/\$\$/fd/1) and modifys a copy
	# of stdout via sed and pushes the result to filedescriptor 9
	tee /proc/\$\$/fd/1 | sed -u -e 's/^Configure /__JOINSCRIPT__ /' >&9
}

if [ -d /var/lib/univention-ldap/ldap ]; then
	rm -f /var/lib/univention-ldap/ldap/*
fi

# be sure the network is up and running
test -x /etc/init.d/networking && invoke-rc.d networking restart

if [ "$server_role" != "domaincontroller_master" ] && [ -n "$domain_controller_account" -a -n "$domain_controller_password" ]; then
	if [ -z "$auto_join" ] || [ "$auto_join" != "FALSE" -a "$auto_join" != "false" -a "$auto_join" != "False" ]; then
		# send number of join scripts to progress dialog
		CNT="\$(ls -1 /usr/lib/univention-install/*.inst | wc -l)"
		echo "__STEPS__:\$CNT" >&9

		pwd_file=\`mktemp\`
		chmod 600 \$pwd_file
		echo "$domain_controller_password" >>\$pwd_file
		if [ -n "$domain_controller" ]; then
			/usr/share/univention-join/univention-join -dcname $domain_controller -dcaccount "$domain_controller_account" -dcpwd "\$pwd_file" -simplegui | progress_filter
		else
			/usr/share/univention-join/univention-join -dcaccount $domain_controller_account -dcpwd "\$pwd_file" -simplegui | progress_filter
		fi
	fi
fi

if [ "$server_role" = "domaincontroller_master" ]; then
    mkdir -p /var/univention-join/
    mkdir -p /usr/share/univention-join/

    if [ "$call_master_joinscripts" = "false" -o "$call_master_joinscripts" = "no" ] ; then
        echo "Warning: Join script execution has been disabled via call_master_joinscripts=$call_master_joinscripts"
    else
        touch /var/univention-join/joined
        touch /var/univention-join/status
        rm -rf /usr/lib/univention-install/.index.txt
        ln -s /var/univention-join/joined /usr/share/univention-join/.joined
        ln -s /var/univention-join/status /usr/lib/univention-install/.index.txt
        for i in /usr/lib/univention-install/*.inst; do
            echo "Configure \`basename \$i\`" | progress_filter
            echo "Configure \`basename \$i\`" >>/var/log/univention/join.log
            \$i >>/var/log/univention/join.log 2>&1;
        done
    fi
fi
__EOT__
chmod +x /instmnt/join.sh
chroot /instmnt ./join.sh

rm -f /instmnt/var/lib/univention-ldap/root.secret
