#! /bin/bash
#
# Univention SSL
#  gencertificate script
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

# See:
# http://www.ibiblio.org/pub/Linux/docs/HOWTO/other-formats/html_single/SSL-Certificates-HOWTO.html
# http://www.pca.dfn.de/dfnpca/certify/ssl/handbuch/ossl092/

SSLBASE="${sslbase:-/etc/univention/ssl}"
case "$SSLBASE" in /*) ;; *) echo "$0: FATAL: Invalid SSLBASE=$SSLBASE" >&2 ; exit 2 ;; esac
CA=ucsCA
case "$CA" in /*) echo "$0: FATAL: Invalid CA=$CA" >&2 ; exit 2 ;; esac

DEFAULT_CRL_DAYS="$(/usr/sbin/univention-config-registry get ssl/crl/validity)"
: "${DEFAULT_CRL_DAYS:=10}"
DEFAULT_DAYS="$(/usr/sbin/univention-config-registry get ssl/default/days)"
: "${DEFAULT_DAYS:=1825}"
DEFAULT_MD="$(/usr/sbin/univention-config-registry get ssl/default/hashfunction)"
: "${DEFAULT_MD:=sha256}"
DEFAULT_BITS="$(/usr/sbin/univention-config-registry get ssl/default/bits)"
: "${DEFAULT_BITS:=2048}"
export DEFAULT_MD DEFAULT_BITS DEFAULT_CRL_DAYS

if test -e "$SSLBASE/password"; then
	PASSWD="$(cat "$SSLBASE/password")"
else
	PASSWD=""
fi

_check_ssl () {
	local var="$1" len="$2" val="${3:-}"
	[ -n "$val" ] || val=$(ucr get "$var")
	[ "${#val}" -le "$len" ] && return 0
	echo "$var too long; max $len" >&2
	return 1
}
check_ssl_parameters () {
	_check_ssl ssl/country 2 || return $?
	_check_ssl ssl/state 128 || return $?
	_check_ssl ssl/locality 128 || return $?
	_check_ssl ssl/organization 64 || return $?
	_check_ssl ssl/organizationalunit 64 || return $?
	_check_ssl common-name 64 "$1" || return $?
	_check_ssl ssl/email 128 || return $?
	return 0
}

mk_config () {
	local outfile="${1:?Missing argument: outfile}"
	local password="${2?Missing argument: password}"
	local days="${3:?Missing argument: days}"
	local name="${4:?Missing argument: common name}"
	local subjectAltName="${5:-}"

	check_ssl_parameters "$name" || return $?

	local SAN_txt san IFS=' '
	for san in $subjectAltName # IFS
	do
		SAN_txt="${SAN_txt:+${SAN_txt}, }DNS:${san}"
	done

	rm -f "$outfile"
	touch "$outfile"
	chmod 0600 "$outfile"

	_escape () {
		sed 's/["$]/\\\0/g'
	}

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
default_crl_days    = \$ENV::DEFAULT_CRL_DAYS
default_md          = \$ENV::DEFAULT_MD
preserve            = no

policy              = policy_match

unique_subject      = no

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

default_bits		= \$ENV::DEFAULT_BITS
default_keyfile 	= privkey.pem
default_md          = \$ENV::DEFAULT_MD
distinguished_name	= req_distinguished_name
attributes		= req_attributes
x509_extensions		= v3_ca
prompt		= no
${password:+input_password = $password}
${password:+output_password = $password}
string_mask = nombstr
req_extensions = v3_req

[ req_distinguished_name ]

C	= $(ucr get ssl/country | _escape)
ST	= $(ucr get ssl/state | _escape)
L	= $(ucr get ssl/locality | _escape)
O	= $(ucr get ssl/organization | _escape)
OU	= $(ucr get ssl/organizationalunit | _escape)
CN	= $(echo -en "$name" | _escape)
emailAddress	= $(ucr get ssl/email | _escape)

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
}

move_cert () {
	local hash i dir="${SSLBASE}/${CA}/certs"
	for i in "$@"
	do
		if [ -f "$i" ]
		then
			hash="$(openssl x509 -hash -noout -in "$i")"
			mv "$i" "${dir}/${i##*/}"
			local count=0
			while :
			do
				local linkname="${dir}/${hash}.${count}"
				[ -h "$linkname" ] || break
				count=$((count + 1))
			done
			ln -snf "${i##*/}" "$linkname"
		fi
	done
}

init () {
	local cn cipher
	cn="$(ucr get ssl/common)"
	cipher="$(/usr/sbin/univention-config-registry get ssl/ca/cipher)"
	check_ssl_parameters "$cn" || return $?

	# remove old stuff
	rm -rf "$SSLBASE"

	# create the base directory
	install -m 0755 -d "$SSLBASE"

	# make sure we have a password, generate one if we don't
	if ! test -e "$SSLBASE/password"; then
		touch "$SSLBASE/password"
		chmod 600 "$SSLBASE/password"
		# shellcheck source=/dev/null
		. /usr/share/univention-lib/base.sh
		create_machine_password > "$SSLBASE/password"
	fi
	PASSWD="$(cat "$SSLBASE/password")"

	# create directory infrastructure
	install -m 755 -d "${SSLBASE}/${CA}"
	install -m 700 -d "${SSLBASE}/${CA}/certs"
	install -m 700 -d "${SSLBASE}/${CA}/crl"
	install -m 700 -d "${SSLBASE}/${CA}/newcerts"
	install -m 700 -d "${SSLBASE}/${CA}/private"
	echo "01" >"${SSLBASE}/${CA}/serial"
	touch "${SSLBASE}/${CA}/index.txt"

	# make the root-CA configuration file
	mk_config "${SSLBASE}/openssl.cnf" "$PASSWD" "$DEFAULT_DAYS" "$cn" || return $?

	openssl genrsa -"${cipher:-aes256}" -passout pass:"$PASSWD" -out "${SSLBASE}/${CA}/private/CAkey.pem" "$DEFAULT_BITS" || return $?
	openssl req -batch -config "${SSLBASE}/openssl.cnf" -new -x509 -days "$DEFAULT_DAYS" -key "${SSLBASE}/${CA}/private/CAkey.pem" -out "${SSLBASE}/${CA}/CAcert.pem" || return $?

	ln -snf "${SSLBASE}/${CA}/CAcert.pem" "/usr/local/share/ca-certificates/${CA}.crt" || return $?
	update-ca-certificates --fresh || return $?

	# copy the public key to a place, from where browsers can access it
	if [ -w /var/www ]; then
	openssl x509 -in "${SSLBASE}/${CA}/CAcert.pem" -out /var/www/ucs-root-ca.crt || return $?
	fi

	# copy the certificate to the certs dir and link it to its hash value
	install -m 0600 "${SSLBASE}/${CA}/CAcert.pem" "${SSLBASE}/${CA}/newcerts/00.pem"
	move_cert "${SSLBASE}/${CA}/newcerts/00.pem"

	# generate root ca request
	openssl x509 -x509toreq -in "${SSLBASE}/${CA}/CAcert.pem" -signkey "${SSLBASE}/${CA}/private/CAkey.pem" -out "${SSLBASE}/${CA}/CAreq.pem" -passin pass:"$PASSWD" || return $?

	find "${SSLBASE}/${CA}" -type f -exec chmod 600 {} + , -type d -exec chmod 700 {} +

	chmod 755 "${SSLBASE}/${CA}"
	chmod 644 "${SSLBASE}/${CA}/CAcert.pem"

	# generate empty crl at installation time
	gencrl

	if getent group 'DC Backup Hosts' >/dev/zero
	then
		chgrp -R 'DC Backup Hosts' -- "$SSLBASE"
		chmod -R g+rwX -- "$SSLBASE"
	fi
}

gencrl () {
	local pem="${SSLBASE}/${CA}/crl/crl.pem"
	local der="${SSLBASE}/${CA}/crl/${CA}.crl"
	openssl ca -config "${SSLBASE}/openssl.cnf" -gencrl -out "${pem}" -passin pass:"$PASSWD" || return $?
	openssl crl -in "${pem}" -out "${der}" -inform pem -outform der || return $?
	if [ -w /var/www ]; then
	install -m 0644 "${der}" /var/www/
	fi
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

list_cert_names_all () {
	awk -F '\t' '
	{
		split ( $6, X, "/" );
		for ( i=2; X[i] != ""; i++ ) {
			if ( X[i] ~ /^CN=/ ) {
				split ( X[i], Y, "=" );
				print $4 "\t" Y[2] " (" $1 ")";
			}
		}
	}' <"${SSLBASE}/${CA}/index.txt"
}

get_cert_name_from_id () {
	if ! [ -z "$1" ]; then
		list_cert_names_all | awk -v id="$1" '$1 == id {print $2}'
	fi
}

update_db () {
	openssl ca -updatedb -config "${SSLBASE}/openssl.cnf" -passin "file:${SSLBASE}/password"
}

# parameter 1: id of cert to check
# exits 0 if yes, 1 if not found, 2 if revoked, 3 if expired

is_valid () {
	local id="${1:?Missing argument: number}"
	tac "${SSLBASE}/${CA}/index.txt" | awk -F '\t' -v id="$id" -v now="$(TZ=UTC date +%y%m%d%H%M%S)" '
	BEGIN { ret=1; }
	$4 == id {
		ret = ( $1 != "R" ) ? ( $1 == "V" && $2 >= now ? 0 : 3 ) : 2;
		exit;
	}
	END { exit ret; }'
}

# parameter 1: cn whose certs to look for
# exits 0 if cert exists and is not revoked, 1 if not found or revoked; prints certs of cn

has_cert () {
	local cn="${1:?Missing argument: common name}"
	cn="${cn//'*'/'\*'}"
	awk -F '\t' -v cn="$cn" '
	BEGIN { ret=1; seq=""; }
	$6 ~ cn {
		seq = seq $4 "\n";
		if ($1 == "V") {
			ret = 0;
		}
	}
	END {
		print seq;
		exit ret;
	}' <"${SSLBASE}/${CA}/index.txt"
}

# parameter 1: cn whose certs to look for
# exits 0 if yes, 1 if not found, 2 if revoked, 3 if expired; prints newest valid cert of cn

has_valid_cert () {
	local cn="${1:?Missing argument: common name}"
	cn="${cn//'*'/'\*'}"
	tac "${SSLBASE}/${CA}/index.txt" | awk -F '\t' -v cn="$cn" -v now="$(TZ=UTC date +%y%m%d%H%M%S)" '
	BEGIN { ret=1; seq=""; }
	$6 ~ cn {
		if ($1 == "V") {
			seq = $4;
			ret = 0;
			exit;
		} else {
			ret = ( $1 != "R" ) ? ( $1 == "V" && $2 >= now ? 0 : 3 ) : 2;
		}
	}
	END { print seq; exit ret; }'
}

renew_cert () {
	local fqdn="${1:?Missing argument: common name}"
	local days="${2:-$DEFAULT_DAYS}"

	(
	cd "$SSLBASE" || exit $?
	_common_gen_cert "$fqdn" "$fqdn"
	)
}

# Parameter 1: Name of the CN whose certs are to be revoked

revoke_cert () {
	local fqdn="${1:?Missing argument: common name}"

	local cn NUM line
	[ ${#fqdn} -gt 64 ] && cn="${fqdn%%.*}" || cn="$fqdn"

	if ! NUM="$(has_cert "$cn")"
	then
		echo "no certificate for $1 registered" >&2
		return 2
	fi

	for line in $NUM  # IFS
	do
		if is_valid "$line"; then
			openssl ca -config "${SSLBASE}/openssl.cnf" -revoke "${SSLBASE}/${CA}/certs/${line}.pem" -passin pass:"$PASSWD"
		fi
	done
	gencrl
}

# Parameter 1: id of the cert to be revoked

revoke_cert_id () {
	local id="${1:?Missing argument: serial number}"

	openssl ca -config "${SSLBASE}/openssl.cnf" -revoke "${SSLBASE}/${CA}/certs/${id}.pem" -passin pass:"$PASSWD"
	gencrl
}

# Parameter 1: Request file

getcnreq () {
	local request="${1:?Missing argument: request}"
	if ! openssl req -noout -verify -in "$request" 2>/dev/null
	then
		echo "FATAL: could not verify request '$request'" >&2
		return 1
	fi
	# CN=blabla/bla/emailAddress
	# CN=blablabla/bla/OU=youknow/email
	# Corporate Server/CN=dummy.bla.bla/emailAddress=ssl@w2k12.test
	# Corporate Server/CN=dummy.bla.bla
python -c '
try:
	import sys
	import M2Crypto
	name = sys.argv[1]
	req = M2Crypto.X509.load_request(name)
	subject = req.get_subject()
	cn = subject.CN
	if cn: print cn.replace("/", ".")
except Exception as err:
	sys.stderr.write("FATAL: could not get CN from request %s (%s)\n" % (name, err))
	sys.exit(1)
' "$request"
}

# Parameter 1: Name des Unterverzeichnisses, in dem das neue Zertifikat abgelegt werden soll
# Parameter 2: Name des CN für den das Zertifikat ausgestellt wird.
# Parameter 3: Optionale Anzahl der Tage für die Gültigkeit.

gencert () {
	local name="${1:?Missing argument: dirname}"
	local fqdn="${2:?Missing argument: common name}"
	local days="${3:-$DEFAULT_DAYS}"

	local hostname="${fqdn%%.*}" cn="$fqdn"
	if [ ${#hostname} -gt 64 ]
	then
		echo "FATAL: Hostname '$hostname' is longer than 64 characters" >&2
		return 2
	fi
	name=$(cd "$SSLBASE" && readlink -f "$name")

	install -m 700 -d "$name"
	if [ ${#fqdn} -gt 64 ]
	then
		echo "INFO: FQDN '$fqdn' is longer than 64 characters, using hostname '$hostname' as CN."
		cn="$hostname"
	fi
	if [ -n "$EXTERNAL_REQUEST_FILE" ]
	then
		cp "$EXTERNAL_REQUEST_FILE" "$name/req.pem"
		[ -n "$EXTERNAL_REQUEST_FILE_KEY" ] && cp "$EXTERNAL_REQUEST_FILE_KEY" "$name/private.key"
	else
		# Add DNS alias names
		local san
		san="$(univention-ldapsearch -LLLo ldif-wrap=no "(cNAMERecord=${fqdn%.}.)" 1.1 | sed -rne 's/^dn: relativeDomainName=([^,]+),zoneName=([^,]+),.*/\1 \1.\2/p' | tr '\n' ' ')"
		# generate config, ignore san for wildcard certs
		if [ "$hostname" = '*' ]; then
			mk_config "$name/openssl.cnf" "" "$days" "$cn" ""
		else
			mk_config "$name/openssl.cnf" "" "$days" "$cn" "$fqdn $hostname $san"
		fi
		# generate a key pair
		openssl genrsa -out "$name/private.key" "$DEFAULT_BITS"
		openssl req -batch -config "$name/openssl.cnf" -new -key "$name/private.key" -out "$name/req.pem"
	fi

	_common_gen_cert "$name" "$fqdn"
}

_common_gen_cert () {
	local name="$1" fqdn="$2"

	# get host extension file
	local extFile hostExt
	hostExt=$(ucr get ssl/host/extensions)
	if [ -s "$hostExt" ]; then
		# shellcheck source=/dev/null
		. "$hostExt"
		extFile=$(createHostExtensionsFile "$fqdn")
	fi

	# process the request
	if [ -s "${extFile:-}" ]; then
		openssl ca -batch -config "${SSLBASE}/openssl.cnf" -days "$days" -in "$name/req.pem" \
			-out "$name/cert.pem" -passin pass:"$PASSWD" -extfile "$extFile"
		rm -f "$extFile"
	else
		openssl ca -batch -config "${SSLBASE}/openssl.cnf" -days "$days" -in "$name/req.pem" \
			-out "$name/cert.pem" -passin pass:"$PASSWD"
	fi

	# move the new certificate to its place
	move_cert "${SSLBASE}/${CA}/newcerts/"*

	find "$name" -type f -exec chmod 600 {} + , -type d -exec chmod 700 {} +
}
