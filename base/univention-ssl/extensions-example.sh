createHostExtensionsFile () {
	local fqdn="$1"
	local hostname=${fqdn%%.*}
	local extFile=$(mktemp)
  local ipaddr=`ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'`
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


