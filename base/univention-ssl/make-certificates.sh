#! /bin/bash -e
#
# Univention SSL
#  gencertificate script
#
# Copyright 2004-2015 Univention GmbH
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
set -e -u

# See:
# http://www.ibiblio.org/pub/Linux/docs/HOWTO/other-formats/html_single/SSL-Certificates-HOWTO.html
# http://www.pca.dfn.de/dfnpca/certify/ssl/handbuch/ossl092/

SSLBASE="${sslbase:-/etc/univention/ssl}"
CA=ucsCA
DEFAULT_DAYS="$(/usr/sbin/univention-config-registry get ssl/default/days)"
: ${DEFAULT_DAYS:=1825}
DEFAULT_MD="$(/usr/sbin/univention-config-registry get ssl/default/hashfunction)"
: ${DEFAULT_MD:=sha256}
DEFAULT_BITS="$(/usr/sbin/univention-config-registry get ssl/default/bits)"
: ${DEFAULT_BITS:=2048}

if test -e "$SSLBASE/password"; then
	PASSWD=`cat "$SSLBASE/password"`
else
	PASSWD=""
fi

_check_ssl () {
	local var="$1" len="$2" val="${3:-}"
	[ -n "$val" ] || val=$(ucr get "$var")
	[ ${#val} -le $len ] && return 0
	echo "$var too long; max $len" >&2
	return 1
}

mk_config () {
	local outfile=${1:?Missing argument: outfile}
	local password=${2:-?Missing argument: password}
	local days=${3:?Missing argument: days}
	local name=${4:?Missing argument: common name}
	local subjectAltName=${5:-}

	_check_ssl ssl/country 2
	_check_ssl ssl/state 128
	_check_ssl ssl/locality 128
	_check_ssl ssl/organization 64
	_check_ssl ssl/organizationalunit 64
	_check_ssl common-name 64 "$name"
	_check_ssl ssl/email 128

	local SAN_txt= san IFS=' '
	for san in $5 # IFS
	do
		SAN_txt="${SAN_txt:+${SAN_txt}, }DNS:${san}"
	done

	rm -f "$outfile"
	touch "$outfile"
	chmod 0600 "$outfile"

	cat >"$outfile" <<EOF
# HOME			= .
# RANDFILE		= \$ENV::HOME/.rnd
# oid_section		= new_oids
#
# [ new_oids ]
#

path		= $SSLBASE

[ ca ]
default_ca	= CA_default

[ CA_default ]

dir                 = \$path/${CA}
certs               = \$dir/certs
crl_dir             = \$dir/crl
database            = \$dir/index.txt
new_certs_dir       = \$dir/newcerts

certificate         = \$dir/CAcert.pem
serial              = \$dir/serial
crl                 = \$dir/crl.pem
private_key         = \$dir/private/CAkey.pem
RANDFILE            = \$dir/private/.rand

x509_extensions     = ${CA}_ext
crl_extensions     = crl_ext
copy_extensions     = copy
default_days        = $days
default_crl_days    = 30
default_md          = ${DEFAULT_MD}
preserve            = no

policy              = policy_match

[ policy_match ]

countryName		= match
stateOrProvinceName	= supplied
localityName		= optional
organizationName	= supplied
organizationalUnitName	= optional
commonName		= supplied
emailAddress		= optional

[ policy_anything ]

countryName		= match
stateOrProvinceName	= optional
localityName		= optional
organizationName	= optional
organizationalUnitName	= optional
commonName		= supplied
emailAddress		= optional

[ req ]

default_bits		= $DEFAULT_BITS
default_keyfile 	= privkey.pem
default_md          = ${DEFAULT_MD}
distinguished_name	= req_distinguished_name
attributes		= req_attributes
x509_extensions		= v3_ca
prompt		= no
${password:+input_password = $password}
${password:+output_password = $password}
string_mask = nombstr
req_extensions = v3_req

[ req_distinguished_name ]

C	= $(ucr get ssl/country)
ST	= $(ucr get ssl/state)
L	= $(ucr get ssl/locality)
O	= $(ucr get ssl/organization)
OU	= $(ucr get ssl/organizationalunit)
CN	= $name
emailAddress	= $(ucr get ssl/email)

[ req_attributes ]

challengePassword		= A challenge password
unstructuredName	= Univention GmbH

[ ${CA}_ext ]

basicConstraints        = CA:FALSE
# keyUsage                = cRLSign, keyCertSign
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid,issuer:always
# subjectAltName          = email:copy
# issuerAltName           = issuer:copy
# nsCertType              = sslCA, emailCA, objCA
# nsComment               = signed by Univention Corporate Server Root CA

[ v3_req ]

basicConstraints = critical, CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
${SAN_txt:+subjectAltName = $SAN_txt}

[ v3_ca ]

basicConstraints        = critical, CA:TRUE
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always,issuer:always
keyUsage                = cRLSign, keyCertSign
nsCertType              = sslCA, emailCA, objCA
subjectAltName          = email:copy
issuerAltName           = issuer:copy
nsComment               = This certificate is a Root CA Certificate

[ crl_ext ]

issuerAltName           = issuer:copy
authorityKeyIdentifier  = keyid:always,issuer:always
EOF
	chmod 0600 "$outfile"
}

move_cert () {
	(
	cd "$SSLBASE"

	local i count
	for i in "$@"
	do
		if [ -f "$i" ]
		then
			local new="${SSLBASE}/${CA}/certs/$(basename "$i")"
			mv "$i" "$new"
			local hash=$(openssl x509 -hash -noout -in "$new")
			count=0
			while :
			do
				local linkname="${CA}/certs/${hash}.${count}"
				if [ -h "$linkname" ]
				then
					count=$((count + 1))
					continue
				else
					ln -s "$new" "$linkname"
					break
				fi
			done
		fi
	done
	)
}

init () {
	# remove old stuff
	rm -rf "$SSLBASE"

	# create the base directory
	mkdir -p "$SSLBASE"

	# make sure we have a password, generate one if we don't
	if ! test -e "$SSLBASE/password"; then
		touch "$SSLBASE/password"
		chmod 600 "$SSLBASE/password"
		. /usr/share/univention-lib/base.sh
		create_machine_password > "$SSLBASE/password"
	fi
	PASSWD=`cat "$SSLBASE/password"`

	(
	# create directory infrastructure
	cd "$SSLBASE"
	mkdir -m 700 -p "${CA}"
	mkdir -p "${CA}/certs"
	mkdir -p "${CA}/crl"
	mkdir -p "${CA}/newcerts,private"
	mkdir -p "${CA}/private"
	echo "01" >"${CA}/serial"
	touch "${CA}/index.txt"

	# make the root-CA configuration file
	mk_config openssl.cnf "$PASSWD" "$DEFAULT_DAYS" "$(ucr get ssl/common)"

	openssl genrsa -des3 -passout pass:"$PASSWD" -out "${CA}/private/CAkey.pem" "$DEFAULT_BITS"
	openssl req -batch -config openssl.cnf -new -x509 -days "$DEFAULT_DAYS" -key "${CA}/private/CAkey.pem" -out "${CA}/CAcert.pem"

	# copy the public key to a place, from where browsers can access it
	openssl x509 -in "${CA}/CAcert.pem" -out /var/www/ucs-root-ca.crt

	# mv the certificate to the certs dir and link it to its hash value
	cp "${CA}/CAcert.pem" "${CA}/newcerts/00.pem"
	move_cert "${CA}/newcerts/00.pem"

	# generate root ca request
	openssl x509 -x509toreq -in "${CA}/CAcert.pem" -signkey "${CA}/private/CAkey.pem" -out "${CA}/CAreq.pem" -passin pass:"$PASSWD"

	find "${CA}" -type f -exec chmod 600 {} +
	find "${CA}" -type d -exec chmod 700 {} +

	chmod 755 "${CA}"
	chmod 644 "${CA}/CAcert.pem"
	#generate empty crl at installation time
	openssl ca -config openssl.cnf -gencrl -out "${CA}/crl/crl.pem" -passin pass:"$PASSWD"
	openssl crl -in "${CA}/crl/crl.pem" -out "${CA}/crl/${CA}.crl" -inform pem -outform der
	cp "${CA}/crl/${CA}.crl" /var/www/

	if getent group 'DC Backup Hosts' >/dev/zero
	then
		chgrp -R 'DC Backup Hosts' -- "$SSLBASE"
		chmod -R g+rwX -- "$SSLBASE"
	fi
	)
}

list_cert_names () {
	awk -F '\t' '
	{
		if ( $1 == "V" ) {
			split ( $6, X, "/" );
			for ( i=2; X[i] != ""; i++ ) {
				if ( X[i] ~ /^CN=/ ) {
					split ( X[i], Y, "=" );
					print $4 "\t" Y[2];
				}
			}
		}
	}' <"${SSLBASE}/${CA}/index.txt"
}

has_valid_cert () { # returns 0 if yes, 1 if none found, 2 if expired
	local cn="${1:?Missing argument: common name}"

	awk -F '\t' -v name="$cn" '
	BEGIN { ret=1; seq=""; }
	{
		split ( $6, X, "/" );
		for ( i=2; X[i] != ""; i++ ) {
			if ( X[i] ~ /^CN=/ ) {
				split ( X[i], Y, "=" );
				if ( name == Y[2] ) {
					seq = $4;
					ret = ( $1 == "V" ) ? 0 : 2;
				}
			}
		}
	}
	END { print seq; exit ret; }' <"${SSLBASE}/${CA}/index.txt"
}

renew_cert () {
	local fqdn="${1:?Missing argument: common name}"
	local days="${2:-$DEFAULT_DAYS}"

	revoke_cert "$fqdn" || [ $? -eq 2 ] || return $?

	(
	cd "$SSLBASE"

	_common_gen_cert "$fqdn" "$fqdn"
	)
}

# Parameter 1: Name des CN dessen Zertifikat wiederufen werden soll

revoke_cert () {
	local fqdn="${1:?Missing argument: common name}"

	local cn NUM
	[ ${#fqdn} -gt 64 ] && cn="${fqdn%%.*}" || cn="$fqdn"

	if ! NUM="$(has_valid_cert "$cn")"
	then
		echo "no certificate for $1 registered" >&2
		return 2
	fi

	(
	cd "$SSLBASE"
	openssl ca -config openssl.cnf -revoke "${CA}/certs/${NUM}.pem" -passin pass:"$PASSWD"
	openssl ca -config openssl.cnf -gencrl -out "${CA}/crl/crl.pem" -passin pass:"$PASSWD"
	openssl crl -in "${CA}/crl/crl.pem" -out "${CA}/crl/${CA}.crl" -inform pem -outform der
	cp "${CA}/crl/${CA}.crl" /var/www/
	)
}


# Parameter 1: Name des Unterverzeichnisses, in dem das neue Zertifikat abgelegt werden soll
# Parameter 2: Name des CN für den das Zertifikat ausgestellt wird.

gencert () {
	local name="${1:?Missing argument: dirname}"
	local fqdn="${2:?Missing argument: common name}"

	local hostname=${fqdn%%.*} cn="$fqdn"
	if [ ${#hostname} -gt 64 ]
	then
		echo "FATAL: Hostname '$hostname' is longer than 64 characters" >&2
		return 2
	fi

	local days=$(/usr/sbin/univention-config-registry get ssl/default/days)
	: ${days:=$DEFAULT_DAYS}

	revoke_cert "$fqdn" || [ $? -eq 2 ] || return $?

	(
	cd "$SSLBASE"

	# generate a key pair
	mkdir -pm 700 "$name"
	if [ ${#fqdn} -gt 64 ]
	then
		echo "INFO: FQDN '$fqdn' is longer than 64 characters, using hostname '$hostname' as CN."
		cn="$hostname"
	fi
	mk_config "$name/openssl.cnf" "" "$days" "$cn" "$fqdn $hostname"
	openssl genrsa -out "$name/private.key" "$DEFAULT_BITS"
	openssl req -batch -config "$name/openssl.cnf" -new -key "$name/private.key" -out "$name/req.pem"

	_common_gen_cert "$name" "$fqdn"
	)
}

_common_gen_cert () {
	local name="$1" fqdn="$2"

	# get host extension file
	local extFile hostExt=$(ucr get ssl/host/extensions)
	if [ -s "$hostExt" ]; then
		set +e
		. "$hostExt"
		extFile=$(createHostExtensionsFile "$fqdn")
		set -e
	fi

	# process the request
	if [ -s "${extFile:-}" ]; then
		openssl ca -batch -config openssl.cnf -days $days -in "$name/req.pem" \
			-out "$name/cert.pem" -passin pass:"$PASSWD" -extfile "$extFile"
		rm -f "$extFile"
	else
		openssl ca -batch -config openssl.cnf -days $days -in "$name/req.pem" \
			-out "$name/cert.pem" -passin pass:"$PASSWD"
	fi

	# move the new certificate to its place
	move_cert "${CA}/newcerts/"*

	find "$name" -type f -exec chmod 600 {} +
	find "$name" -type d -exec chmod 700 {} +
}
