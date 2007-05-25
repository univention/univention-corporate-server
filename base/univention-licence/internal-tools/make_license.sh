#! /bin/sh -e
# Shell Script to generate Univention License Keys

# wenn nicht root, dann sudo versuchen
if [ $UID != 0 ]; then sudo $0 "$@"; exit; fi

help_and_exit () {
	local RC=0;
	if [ "$1" ]; then RC="$1"; fi; 
	echo "$0" [-d datespec] [-a maxaccounts] [-c maxclients] [-g maxgroupwareaccounts] [-u maxuniventiondesktops] [-p product\(s\)] [-o] [-i] [-e] [-H ldap-server]\\ 
	echo "     " -f outputfilename -D ldapbinddn -w ldappwd -t tempdn -k masterkeydir customername dn
	echo "use -o to create an old license (for systems before UGS/1.3-1)"
	exit $RC;
}

# paths to the key store, relativ to the directory of the master key
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

for i; do
	if [ -z "$1" ]; then break; fi; 
	case "$1" in

		"-d")   
			if [ -z "$2" ]; then help_and_exit 1; fi; 
			EXPDATE="$2";
			UNLIMITED=0;
			shift; shift; 
			;;
		"-f")
			filename="$2";
			shift;
			shift;
			;;
		"-e")
			shift;
			EVALKEY=1;
			;;
		"-i")
			shift;
			INTERNAL=1;
			;;
		"-h")
			help_and_exit 0;
			;;
		"-D")
			if [ -z "$2" ]; then help_and_exit 1; fi; 
			LDAPBINDDN="$2";
			shift; shift;
			;;
		"-w")
			if [ -z "$2" ]; then help_and_exit 1; fi; 
			LDAPPWD="$2";
			shift; shift;
			;;
		"-t")
			if [ -z "$2" ]; then help_and_exit 1; fi; 
			LDAPTMP="$2";
			shift; shift;
			;;
		"-k")   
			if [ -z "$2" ]; then help_and_exit 1; fi; 
			MASTERKEYDIR="$2";
			shift; shift;
			;;
		"-a")
			if [ -z "$2" ]; then help_and_exit 1; fi;
			MAXACCOUNTS="$2";
			shift; shift;
			;;
		"-c")
			if [ -z "$2" ]; then help_and_exit 1; fi;
			MAXCLIENTS="$2";
			shift; shift;
			;;
		"-g")
			if [ -z "$2" ]; then help_and_exit 1; fi;
			MAXGROUPWAREACCOUNTS="$2";
			shift; shift;
			;;
		"-u")
			if [ -z "$2" ]; then help_and_exit 1; fi;
			MAXDESKTOPS="$2";
			shift; shift;
			;;
		"-p")
			if [ -z "$2" ]; then help_and_exit 1; fi;
			PRODUCTS="$2";
			shift; shift;
			;;
		"-o")
			OLDLICENSE="1";
			shift;
			;;
		"-H")
			if [ -z "$2" ]; then help_and_exit 1; fi;
			LDAPSERVER="-h $2";
			shift; shift;
			;;
		*)
			if [ "$CUSTOMER" == "" ]; then
				CUSTOMER="$1";
			elif [ "$BASEDN" == "" ]; then 
				BASEDN="$1";
			else
				help_and_exit 1;
			fi;
			shift;
			;;
	esac;
done; 

if [ "$MASTERKEYDIR" == "" ]; then 
	help_and_exit 1;
fi;

if [ "$LDAPBINDDN" == "" -o "$LDAPPWD" == "" ]; then 
	help_and_exit 1;
fi;

if [ "$LDAPTMP" == "" ]; then
	help_and_exit 1;
fi;

if [ "$CUSTOMER" == "" -o "$BASEDN" == "" ]; then 
	help_and_exit 1; 
fi; 

if [ "$EXPDATE" != "" ]; then 
	if ! EXPDATE=$( date -d "$EXPDATE" +%d.%m.%Y 2>/dev/null ); then
		echo "E: can't parse date (see man date)"
		exit 1;
	fi;
fi;

if [ "$EVALKEY" -eq 1 -a "$EXPDATE" == "" ]; then
	echo "E: evaluation licenses require an expiration date." 1>&2
	exit 1;
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
cd "$MASTERKEYDIR" 

# create the ldap objekt
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
