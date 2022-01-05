createHostExtensionsFile () {
	local fqdn="$1"
	local hostname=${fqdn%%.*}
	local extFile=$(mktemp)
	. /usr/share/univention-lib/base.sh
	local ipaddr=$(get_default_ip_address)
	cat <<EOF >>"$extFile"
extensions = myx509v3
[ myx509v3 ]

# ucs defaults
basicConstraints = CA:FALSE
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer:always

# alternative name
subjectAltName = DNS:$fqdn, DNS:$hostname, IP:127.0.0.1, DNS:localhost, IP:$ipaddr
EOF

	echo "$extFile"
}


