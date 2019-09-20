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
	echo "  [-a maxaccounts] [-c maxclients] [-g maxgroupwareaccounts] [-u maxuniventiondesktops] \\"
	echo "  [-p product\(s\)] [ -O oemproduct\(s\)] [-o] [-i] [-e] [-H ldap-server] \\"
	echo "  -f outputfilename -D ldapbinddn -w ldappwd -t tempdn -k masterkeydir customername dn"
	if [ -z "$1" ]
	then
		echo ""
		echo "  -h	show this help"
		echo "  -d	expiration date"
		echo "  -a	maximum number of accounts"
		echo "  -c	maximum number of hosts"
		echo "  -g	maximum number of groupware accounts"
		echo "  -u	maximum number of desktop hosts"
		echo "  -p	comma separated list of procuts: UCS,UCD,TCS,DVS,..."
		echo "  -O	comma separated list of OEM products"
		echo "  -o	create old license for systems before UGS/1.3-1"
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
		"-a")
			MAXACCOUNTS="$2";
			shift 2 || help_and_exit '-a expects number of accounts'
			;;
		"-c")
			MAXCLIENTS="$2";
			shift 2 || help_and_exit '-c expects number of clients'
			;;
		"-g")
			MAXGROUPWAREACCOUNTS="$2";
			shift 2 || help_and_exit '-g expects number of groupware accounts'
			;;
		"-u")
			MAXDESKTOPS="$2";
			shift 2 || help_and_exit '-u expects number of desktop hosts'
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

if [ -z "$MAXACCOUNTS" ]; then
	MAXACCOUNTS="unlimited";
fi;
if [ -z "$MAXCLIENTS" ]; then
	MAXCLIENTS="unlimited";
fi;
if [ -z "$MAXGROUPWAREACCOUNTS" ]; then
	MAXGROUPWAREACCOUNTS="unlimited";
fi;
if [ -z "$MAXDESKTOPS" ]; then
	MAXDESKTOPS="unlimited";
fi;

# parameter checking done


# change to the master key directory
cd "$MASTERKEYDIR" || help_and_exit "Can't change to directory $MASTERKEYDIR"

# create the ldap object
(
	echo dn: cn="$CUSTOMER","$LDAPTMP";
	echo objectClass: top;
	echo objectClass: univentionLicense;
	echo univentionLicenseEndDate: "$EXPDATE";
	echo univentionLicenseModule: admin;
	echo univentionLicenseSignature: empty;
	echo cn: "$CUSTOMER";
	echo univentionLicenseBaseDN: "$BASEDN";
	echo univentionLicenseAccounts: "$MAXACCOUNTS"
	echo univentionLicenseClients: "$MAXCLIENTS"
	echo univentionLicenseGroupwareAccounts: "$MAXGROUPWAREACCOUNTS"
	echo univentionLicenseuniventionDesktops: "$MAXDESKTOPS"
	if [ -z "$OLDLICENSE" ]; then
	    for product in `echo "$PRODUCTS"|sed -e 's|,| |'`
	      do
	      echo univentionLicenseType: "$product"
	    done
		if [ -n "$OEMPRODUCTS" ]; then
			IFS=$','
			for oemproduct in $OEMPRODUCTS
			do
				echo univentionLicenseOEMProduct: "$oemproduct"
			done
			unset IFS
		fi;
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
	if [ -z "$OLDLICENSE" ]; then
		echo "# ACCOUNTS: $MAXACCOUNTS"
		echo "# GROUPWARE ACCOUNTS: $MAXGROUPWAREACCOUNTS"
		echo "# CLIENTS: $MAXCLIENTS"
		echo "# UNIVENTION DESKTOPS: $MAXDESKTOPS"
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
