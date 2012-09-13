#!/bin/bash
# Test univention-dnsedit
eval "$(ucr shell)"

cleanup () {
	set +e
	univention-ldapsearch -xLLLb "zoneName=123.168.192.in-addr.arpa,cn=dns,$ldap_base" dn
	univention-ldapsearch -xLLLb "zoneName=test.$domainname,cn=dns,$ldap_base" dn
	udm dns/reverse_zone remove --dn "zoneName=123.168.192.in-addr.arpa,cn=dns,$ldap_base"
	udm dns/forward_zone remove --dn "zoneName=test.$domainname,cn=dns,$ldap_base"
}
trap cleanup EXIT
trap "echo ERROR" ERR
set -e

prog () {
	echo ">>> $*"
	../univention-dnsedit "$@"
}
prog_old () { # Wrapper around old dnsedit to resort --options to front
	declare -a OPT=() ARG=()
	while [ $# -ge 1 ]
	do
		case "$1" in
		--*) OPT+=("$1") ;;
		*) ARG+=("$1") ;;
		esac
		shift
	done
	set -- "${OPT[@]}" "${ARG[@]}"
	echo ">>> $*"
	/usr/share/univention-directory-manager-tools/univention-dnsedit "$@"
}

# Create reverse zone
  prog --reverse 192.168.123 add zone "root@$domainname" 1 28800 7200 25200 10800 "$hostname.$domainname"
! prog --reverse 192.168.123 add zone "root@$domainname" 1 28800 7200 25200 10800 "$hostname.$domainname"
  prog --reverse 192.168.123 add zone "root@$domainname" 1 28800 7200 25200 10800 "$hostname.$domainname" --ignore-exists
# Test PTR
  prog  --reverse 192.168.123 add    ptr   42  host.fqdn.
! prog  --reverse 192.168.123 add    ptr   42  host.fqdn.
  prog  --reverse 192.168.123 add    ptr   42  host.fqdn. --ignore-exists
  prog  --reverse 192.168.123 add    ptr   42  host2.fqdn. --overwrite
# Create forward zone
  prog "test.$domainname" add zone "root@$domainname" 1 28800 7200 25200 10800 "$hostname.$domainname"
! prog "test.$domainname" add zone "root@$domainname" 1 28800 7200 25200 10800 "$hostname.$domainname"
  prog "test.$domainname" add zone "root@$domainname" 1 28800 7200 25200 10800 "$hostname.$domainname" --ignore-exists
# Test SRV
  prog "test.$domainname" add    srv   ldap tcp 0 100 7389 master.fqdn.
  prog "test.$domainname" add    srv   ldap tcp 0 100 7389 master.fqdn.
! prog "test.$domainname" remove srv   ldap tcp 0 100 7389 master.fqdn.
  prog "test.$domainname" add    srv   ldap tcp 1 100 7389 backup.fqdn.
  prog "test.$domainname" remove srv   ldap tcp 0 100 7389 master.fqdn.
# Test TXT
  prog "test.$domainname" add    txt   entry-name  "Some text"
  prog "test.$domainname" add    txt   entry-name  "Some text"
  prog "test.$domainname" add    txt   entry-name  "Some other text"
# Test CNAME
  prog "test.$domainname" add    cname univention-repository apt.knut.univention.de.
! prog "test.$domainname" add    cname univention-repository apt.knut.univention.de.
  prog "test.$domainname" add    cname univention-repository apt.knut.univention.de. --overwrite
# Test A
  prog "test.$domainname" add    a     host  1.2.3.4
  prog "test.$domainname" add    a     host  1.2.3.4
  prog "test.$domainname" add    a     host  1.2.3.4  5.6.7.8
echo "SUCCESS"
