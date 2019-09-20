#! /bin/bash -e
#
# Univention License
#  Shell Script to generate Univention License Keys
#
# Copyright 2004-2019 Univention GmbH
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

# wenn nicht root, dann sudo versuchen
if [ $UID != 0 ]
then
	sudo "$0" "$@"
	exit
fi

help_and_exit () {
	local RC=0;
	if [ -n "$1" ]
	then
		exec 1>&2
		echo "E: $1"
		echo ""
		RC=1
	fi
	echo "usage: $0 [-h | --help] [-d datespec] \\"
	echo "  [-u maxusers] [-s maxservers] [-m maxmanagedclients] [-c maxcorporateclients] \\"
	echo "  [-v maxdvsusers] [-V maxdvsclients] [-S maxstandardsupport] [-P maxpremiumsupport] \\"
	echo "  [-U uuid|generate] \\"
	echo "  [-p product\(s\)] [ -O oemproduct\(s\)] [-o] [-i] [-e] [-H ldap-server] \\"
	echo "  -f outputfilename -D ldapbinddn -w ldappwd -t tempdn -k masterkeydir customername dn"
	if [ -z "$1" ]
	then
		echo ""
		echo "  -h	show this help"
		echo "  -d	expiration date"
		echo "  -u	maximum number of users"
		echo "  -s	maximum number of servers"
		echo "  -m	maximum number of managedclients"
		echo "  -c	maximum number of corporateclients"
		echo "  -v	maximum number of DVS users"
		echo "  -V	maximum number of DVS clients"
		echo "  -S	maximum number of servers with standard support"
		echo "  -P	maximum number of servers with premium support"
		echo "  -U	customer ID, use generate to generate a new UUID"
		echo "  -p	comma separated list of procuts: Univention Corporate Server,..."
		echo "  -O	comma separated list of OEM products"
		echo "  -i	create license for internal use only"
		echo "  -e	create evaluation license"
		echo "  -H	specify LDAP server (default: ldap/master)"
		echo "  -f	file name for output file"
		echo "  -D	bind-dn for LDAP authentication"
		echo "  -w	password for LDAP authentication"
		echo "  -t	base-dn for storing the temporary license"
		echo "  -k	directory containing private key for license signing"
		echo "  dn	base-dn of licensee"
	fi
	exit $RC
}

# paths to the key store, relative to the directory of the master key
INTERNALKEYS="../eigene";
EVALUATIONKEYS="../evaluation";
CUSTOMERKEYS="../kunden";
filename="/dev/null"

# parameter checking

EXPDATE="";
UNLIMITED=1;
EVALKEY=0;
INTERNAL=0;
CUSTOMER="";
BASEDN=""
LDAPSERVER=""

LDAPBINDDN=""
LDAPPWD=""
LDAPTMP=""

MASTERKEYDIR=""


# defaults
MAXDESKTOPS="1000";
MAXGROUPWAREACCOUNTS="1000";
MAXCLIENTS="1000";
MAXACCOUNTS="1000";
PRODUCTS="UCS";

# load defaults
if [ -r /etc/univention/make_license.config ]; then 
	. /etc/univention/make_license.config
fi;

for i in "$@"
do
	if [ -z "$1" ]; then break; fi; 
	case "$1" in
		"-d")   
			EXPDATE="$2";
			UNLIMITED=0;
			shift 2 || help_and_exit '-d expects date'
			;;
		"-f")
			filename="$2";
			shift 2 || help_and_exit '-f expects file name'
			;;
		"-e")
			EVALKEY=1;
			shift
			;;
		"-i")
			INTERNAL=1;
			shift
			;;
		-h|--help)
			help_and_exit
			;;
		"-D")
			LDAPBINDDN="$2";
			shift 2 || help_and_exit '-D expects bind-dn'
			;;
		"-w")
			LDAPPWD="$2";
			shift 2 || help_and_exit '-w expects password'
			;;
		"-t")
			LDAPTMP="$2";
			shift 2 || help_and_exit '-t expects dn'
			;;
		"-k")   
			MASTERKEYDIR="$2";
			shift 2 || help_and_exit '-k expects directory'
			;;
		"-u")
			MAXUSERS="$2";
			shift 2 || help_and_exit '-u expects number of users'
			;;
		"-s")
			MAXSERVERS="$2";
			shift 2 || help_and_exit '-s expects number of servers'
			;;
		"-m")
			MAXMANAGEDCLIENTS="$2";
			shift 2 || help_and_exit '-m expects number of managed clients'
			;;
		"-c")
			MAXCORPORATECLIENTS="$2";
			shift 2 || help_and_exit '-c expects number of corporate clients'
			;;
		"-v")
			MAXDVSUSERS="$2";
			shift 2 || help_and_exit '-v expects number of DVS users'
			;;
		"-V")
			MAXDVSCLIENTS="$2";
			shift 2 || help_and_exit '-V expects number of DVS clients'
			;;
		"-S")
			MAXSTANDARDSUPPORT="$2";
			shift 2 || help_and_exit '-s expects number of servers with standard support'
			;;
		"-P")
			MAXPREMIUMSUPPORT="$2";
			shift 2 || help_and_exit '-s expects number of servers with premium support'
			;;
		"-U")
			KEYID="$2";
			shift 2 || help_and_exit '-U expects a UUID or the keyword generate'
			;;
		"-p")
			PRODUCTS="$2";
			shift 2 || help_and_exit '-p expects list of products'
			;;
		"-O")
			OEMPRODUCTS="$2";
			shift 2 || help_and_exit '-O expects list of OEM products'
			;;
		"-o")
			OLDLICENSE="1";
			shift;
			;;
		"-H")
			LDAPSERVER="-h $2";
			shift 2 || help_and_exit '-H expects LDAP host'
			;;
		*)
			if [ "$CUSTOMER" == "" ]; then
				CUSTOMER="$1";
			elif [ "$BASEDN" == "" ]; then 
				BASEDN="$1";
			else
				help_and_exit "additional argument $1"
			fi;
			shift;
			;;
	esac;
done; 

if [ "$MASTERKEYDIR" == "" ]; then 
	help_and_exit 'Missing master directory -k'
fi;

if [ "$LDAPBINDDN" == "" -o "$LDAPPWD" == "" ]; then 
	help_and_exit 'Missing LDAP bind-dn -D and password -w'
fi;

if [ "$LDAPTMP" == "" ]; then
	help_and_exit 'Missing LDAP temp-dn -t'
fi;

if [ "$CUSTOMER" == "" -o "$BASEDN" == "" ]; then 
	help_and_exit 'Missing customer name and base-dn'
fi; 

if [ "$EXPDATE" != "" ]; then 
	if ! EXPDATE=$( date -d "$EXPDATE" +%d.%m.%Y 2>/dev/null ); then
		help_and_exit "can't parse date (see man date)"
	fi;
fi;

if [ "$EVALKEY" -eq 1 -a "$EXPDATE" == "" ]; then
	help_and_exit "evaluation licenses require an expiration date."
fi; 

if [ "$EXPDATE" == "" ]; then 
	EXPDATE="unlimited";
fi; 

if [ -z "$MAXUSERS" ]; then
	MAXUSERS="unlimited";
fi;
if [ -z "$MAXSERVERS" ]; then
	MAXSERVERS="unlimited";
fi;
if [ -z "$MAXMANAGEDCLIENTS" ]; then
	MAXMANAGEDCLIENTS="unlimited";
fi;
if [ -z "$MAXCORPORATECLIENTS" ]; then
	MAXCORPORATECLIENTS="unlimited";
fi;
if [ -z "$MAXDVSUSERS" ]; then
	MAXDVSUSERS="unlimited";
fi;
if [ -z "$MAXDVSCLIENTS" ]; then
	MAXDVSCLIENTS="unlimited";
fi;
if [ -z "$MAXSTANDARDSUPPORT" ]; then
	MAXSTANDARDSUPPORT="0";
fi;
if [ -z "$MAXPREMIUMSUPPORT" ]; then
	MAXPREMIUMSUPPORT="0";
fi;

if [ "$KEYID" = "generate" ]; then
	UUID=$(uuid)
elif [ -n "$KEYID" ]; then
	UUID="$KEYID"
fi

# parameter checking done
# change to the master key directory
cd "$MASTERKEYDIR" || help_and_exit "Can't change to directory $MASTERKEYDIR"

# create the ldap object
(
	echo dn: cn="$CUSTOMER","$LDAPTMP";
	echo objectClass: top;
	echo objectClass: univentionLicense;
	echo objectClass: univentionObject;
	echo univentionObjectType: settings/license;
	echo univentionLicenseEndDate: "$EXPDATE";
	echo univentionLicenseModule: admin;
	echo univentionLicenseSignature: empty;
	echo cn: "$CUSTOMER";
	echo univentionLicenseBaseDN: "$BASEDN";
	echo univentionLicenseUsers: "$MAXUSERS";
	echo univentionLicenseServers: "$MAXSERVERS";
	echo univentionLicenseManagedClients: "$MAXMANAGEDCLIENTS";
	echo univentionLicenseCorporateClients: "$MAXCORPORATECLIENTS";
	echo univentionLicenseVirtualDesktopUsers: "$MAXDVSUSERS";
	echo univentionLicenseVirtualDesktopClients: "$MAXDVSCLIENTS";
	echo univentionLicenseSupport: "$MAXSTANDARDSUPPORT";
	echo univentionLicensePremiumSupport: "$MAXPREMIUMSUPPORT";
	echo univentionLicenseVersion: 2;
	if [ -n "$UUID" ]; then
		echo univentionLicenseKeyID: "$UUID";
	fi
	if [ -n "$PRODUCTS" ]; then
		IFS=$','
		for product in $PRODUCTS
		do
			echo univentionLicenseType: "$product"
		done
		unset IFS
	fi
	if [ -n "$OEMPRODUCTS" ]; then
		IFS=$','
		for oemproduct in $OEMPRODUCTS
		do
			echo univentionLicenseOEMProduct: "$oemproduct"
		done
		unset IFS
	fi;
) | ldapadd -x $LDAPSERVER -D "$LDAPBINDDN" -w "$LDAPPWD" 1>/dev/null 

# wait for replication, if we are operating on a remote server
# this could and should be handled more efficiently

if [ -n "$LDAPSERVER" ]; then
	sleep 5
fi

# sign the license
LICENSEKEY=`univentionLicenseCreateSignature -d cn="$CUSTOMER","$LDAPTMP" -k key.privat -p $( cat passwort.txt ) 2>/dev/null | grep ^univentionLicenseSignatur;`

# add the key
(
	echo dn: cn="$CUSTOMER","$LDAPTMP";
	echo changetype: modify
	echo replace: univentionLicenseSignature;
	echo "$LICENSEKEY"
) | ldapmodify -x $LDAPSERVER -D "$LDAPBINDDN" -w "$LDAPPWD" 1>/dev/null

# get the complete license
LICENSEKEY=`ldapsearch -LLL -x $LDAPSERVER -s base -D "$LDAPBINDDN" -w "$LDAPPWD" -b cn="$CUSTOMER","$LDAPTMP" | ldapsearch-wrapper`;

# delete it from ldap
ldapdelete -x $LDAPSERVER -D "$LDAPBINDDN" -w "$LDAPPWD" cn="$CUSTOMER","$LDAPTMP";

# adjust it
LICENSEKEY=$( 
	echo "# extended LDIF";
	echo "#";
	echo "# LDAP V3";
	echo "#";
	echo "# Univention Product License"
	echo "# PRODUCT: UNIVENTION CORPORATE SERVER"
	echo "# MODULE: Admin"
	echo "#"
	echo "# ISSUED TO: $CUSTOMER"
	echo "# VALID UNTIL: $EXPDATE"
	echo "# Users: $MAXUSERS";
	echo "# Servers:  $MAXSERVERS";
	echo "# Managed clients: $MAXMANAGEDCLIENTS";
	echo "# Corporate clients: $MAXCORPORATECLIENTS";
	echo "# DVS users: $MAXDVSUSERS";
	echo "# DVS clients: $MAXDVSCLIENTS";
	echo "# Servers with standard support: $MAXSTANDARDSUPPORT";
	echo "# Servers with premium support: $MAXPREMIUMSUPPORT";
	echo "# Version:  2";
	if [ -n "$UUID" ]; then
		echo "# KeyID: $UUID";
	fi;
	echo "# UCS BASEDN: $BASEDN"
	echo "#"
	echo "# To install this license use the following command on your UCS DC Master:"
	echo "#"
	echo "# univention-license-import name_of_this_file";
	echo "#"
	echo "dn: cn=admin,cn=license,cn=univention,$BASEDN";
	echo "$LICENSEKEY" | sed -e '1d' -e 's/^cn: '"$CUSTOMER"'$/cn: admin/1';
)

# store it

if [ "$INTERNAL" == 1 ]; then
	mkdir -p "$INTERNALKEYS";
	echo "$LICENSEKEY" > "$INTERNALKEYS"/"$CUSTOMER"-$( date +%y%m%d-%H%M%S ).ldif
elif [ "$EVALKEY" == 1 ]; then 
	mkdir -p "$EVALUATIONKEYS"/"$CUSTOMER";
	echo "$LICENSEKEY" > "$EVALUATIONKEYS"/"$CUSTOMER"/"$CUSTOMER"-$( date +%y%m%d-%H%M%S ).ldif
else
	mkdir -p "$CUSTOMERKEYS"/"$CUSTOMER";
	echo "$LICENSEKEY" > "$CUSTOMERKEYS"/"$CUSTOMER"/"$CUSTOMER"-$( date +%y%m%d-%H%M%S ).ldif
fi;

# store it to the chosen file;
echo "$LICENSEKEY" > "$filename"

# echo the license

echo "$LICENSEKEY";
