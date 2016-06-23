createHostExtensionsFile () {
	local fqdn="$1"
	local hostname=${fqdn%%.*}
	local extFile=$(mktemp)

	cat <<EOF >>"$extFile"
extensions = myx509v3
[ myx509v3 ]

# ucs defaults
basicConstraints = CA:FALSE
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer:always

# alternative name
subjectAltName = DNS:$fqdn, DNS:$hostname
EOF

	echo "$extFile"
}
