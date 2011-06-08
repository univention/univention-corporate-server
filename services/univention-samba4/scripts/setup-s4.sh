#!/bin/bash

usage(){ echo "$0 [-h|--help] [-w <samba4-admin password file>] [-W]"; exit 1; }

SCRIPTDIR=/usr/share/univention-samba4/scripts
LOGFILE="/var/log/univention/samba4-provision.log"

touch $LOGFILE
chmod 600 $LOGFILE

adminpw="$(pwgen -1 -s -c -n 16)"
adminpw2="$adminpw"

while getopts  "h-:W:" option; do
	case "${option}" in
		h) usage;;
		-)
		case "${OPTARG}" in
			help) usage;;
			*) echo "$0: illegal option -- --${OPTARG}"; exit 1;;
		esac;;
		w) if [ -r "$OPTARG" ]; then adminpw="$(< $OPTARG)"; adminpw2="$adminpw"; fi ;;
		W) adminpw2='!unset';;
	esac
done

while [ "$adminpw" != "$adminpw2" ]; do
	read -p "Choose Samba4 admin password: " adminpw
	if [ "${#adminpw}" -lt 8 ]; then
		echo "Password too short, Samba4 minimal requirements: 8 characters, one digit, one uppercase"
		continue
	fi
	read -p "Confirm password: " adminpw2
	if [ "$adminpw" != "$adminpw2" ]; then
		echo "Passwords don't match, please try again"
	fi
done

pwfile="/etc/samba4.secret"
if [ -e "$pwfile" ]; then
	cat "$pwfile" >>"$pwfile".SAVE
fi
touch "$pwfile"
chmod 600 "$pwfile"
echo -n "$adminpw" >> "$pwfile"

univention-config-registry set ldap/server/port=7389 ldap/master/port=7389 ldap/port=7389 ldap/port/ldaps=7636 >>$LOGFILE 2>&1
# univention-config-registry commit /etc/init.d/slapd /etc/libnss-ldap.conf /etc/pam_ldap.conf /etc/ldap/ldap.conf \
#           /etc/runit/univention-directory-listener/run /etc/dhcp3/dhcpd.conf

## restart processes with adjusted ports
pkill -f /usr/share/univention-directory-manager-tools/univention-cli-server
/etc/init.d/slapd restart >>$LOGFILE 2>&1
/etc/init.d/univention-directory-listener restart >>$LOGFILE 2>&1
/etc/init.d/univention-management-console-server restart >>$LOGFILE 2>&1

## commit univention-bind zones in /etc/bind/univention.conf.d/ to use new port
univention-directory-listener-ctrl resync bind >>$LOGFILE 2>&1

## Provision Samba4
eval "$(univention-config-registry shell)"

if [ -x /etc/init.d/samba ]; then
	/etc/init.d/samba stop >>$LOGFILE 2>&1
fi
if [ -x /etc/init.d/winbind ]; then
	/etc/init.d/winbind stop >>$LOGFILE 2>&1
fi
univention-config-registry set samba/autostart=no winbind/autostart=no >>$LOGFILE 2>&1

/etc/init.d/heimdal-kdc stop >>$LOGFILE 2>&1
univention-config-registry set kerberos/autostart=no >>$LOGFILE 2>&1

if [ ! -e /usr/modules ]; then
	ln -s /usr/lib /usr/modules		# somehow MODULESDIR is set to /usr/modules in samba4 source despite --enable-fhs
fi

S3_DOMAIN_SID="$(ldapsearch -x objectclass=sambadomain sambaSID | sed -n 's/sambaSID: \(.*\)/\1/p')"

# /usr/sbin/upgradeprovision --full --realm="$kerberos_realm" -s /etc/samba/smb.conf.samba3
/usr/sbin/provision --realm="$kerberos_realm" --domain="$windows_domain" --domain-sid="$S3_DOMAIN_SID" \
					--adminpass="$adminpw" --server-role='domain controller'	\
					--machinepass=="$(</etc/machine.secret)" >>$LOGFILE 2>&1
# the code in /usr/share/pyshared/samba/provision.py derives the 'domaindn' from the realm, save it for later use
univention-config-registry set samba4/ldap/base="DC=${kerberos_realm/./,DC=}" >>$LOGFILE 2>&1

if [ ! -d /etc/phpldapadmin ]; then
	mkdir /etc/phpldapadmin
fi
if [ ! -e /etc/phpldapadmin/config.php ]; then
	cp /var/lib/samba/private/phpldapadmin-config.php /etc/phpldapadmin/config.php
fi

# provide a TLS-enabled smb.conf
# cp /etc/samba/smb.conf /etc/samba/smb.conf.provision
# cat "${SCRIPTDIR}/tls_for_smb.conf" | univention-config-registry filter >> /etc/samba/smb.conf

## TODO: Join-Script candidate: DNS-Setup
"${SCRIPTDIR}/setup-dns-in-ucsldap.sh" >>$LOGFILE 2>&1

# Copy keytab
if [ -e /etc/krb5.keytab ]; then
	mv /etc/krb5.keytab /etc/krb5.keytab.BACKUP_UCS_INSTALLATION
fi

ln -sf /var/lib/samba/private/secrets.keytab /etc/krb5.keytab

# Create kerberos service entries for sshd and slapd (ssh and ldapsearch -Y GSSAPI)
ldbmodify -H /var/lib/samba/private/secrets.ldb -b "flatname=$windows_domain,cn=Primary Domains" <<%EOF
dn: flatname=$windows_domain,cn=Primary Domains
changetype: modify
add: servicePrincipalName
servicePrincipalName: host/$hostname.$domainname
servicePrincipalName: ldap/$hostname.$domainname
-
%EOF

/etc/init.d/samba4 restart >>$LOGFILE 2>&1	# somehow this currently is necessary to avoid 'Failed to listen on 0.0.0.0:445 - NT_STATUS_ADDRESS_ALREADY_ASSOCIATED'

exit 0
