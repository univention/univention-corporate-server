# vim:set filetype=sh tabstop=4 shiftwidth=4 noexpandtab:
set -e -u

NET='192.168.2.0'
router="${NET%.0}.1"

BASE="$(ucr get ldap/base)"
name="$(tr -d -c '[:alnum:]' </dev/urandom 2>/dev/null | head -c 20)"

policy () {
	univention-policy-result -D "$(ucr get ldap/hostdn)" -y /etc/machine.secret "$@"
}

pypolicy () {
	python2.7 -c 'import sys
from univention.uldap import getMachineConnection
c = getMachineConnection()
p = c.getPolicies(sys.argv[1])
v = p.get("univentionPolicyDhcpRouting", {}).get("univentionDhcpRouters", {})
print "v=", v
e = eval(sys.argv[2]).get("univentionDhcpRouters", {})
print "e=", e
r = 0 if all(value == v.get(key) for key, value in e.iteritems()) else 1
print "r=", r
sys.exit(r)
' "$@"
}

setup () {
	udm-test dhcp/service create \
		--position "$BASE" \
		--set service="$name"
	udm-test dhcp/subnet create \
		--superordinate "cn=$name,$BASE" \
		--set subnet="$NET" \
		--set subnetmask='255.255.255.0'
	udm-test policies/dhcp_routing create \
		--position "cn=$name,$BASE" \
		--set name="p1" \
		--set routers="${NET%.0}.1" \
		--set "$PROPERTY"="$PROPVAL"
	udm-test dhcp/service modify \
		--dn "cn=$name,$BASE" \
		--policy-reference "cn=p1,cn=$name,$BASE"
}

_toggle_case () {
	echo "$1" | tr '[:upper:][:lower:]' '[:lower:][:upper:]'
}
toggle_case () {
	case "$PROPVAL" in
	*=*) PROPVAL="${PROPVAL%%=*}=$(_toggle_case "${PROPVAL#*=}")" ;;
	*) PROPVAL="$(_toggle_case "$PROPVAL")" ;;
	esac
	udm-test policies/dhcp_routing modify \
		--dn "cn=p1,cn=$name,$BASE" \
		--set "$PROPERTY"="$PROPVAL"
}

die () {
	echo "E: $*" >&2
	exit 1
}

tmp="$(mktemp -d)"
cleanup () {
	local retval=$?
	[ $retval -eq 0 ] || univention-ldapsearch -LLLo ldif-wrap=no -b "cn=$name,$BASE"
	rm -rf "$tmp"
	udm-test dhcp/service remove --dn "cn=$name,$BASE"
	exit $retval
}
trap cleanup EXIT
