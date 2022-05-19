# shellcheck shell=sh
set -e -x

setup_owncloud_with_oidc () {
	local backup_ip=${1:?missing ip}
	univention-app configure owncloud --set OWNCLOUD_OPENID_LOGIN_ENABLED=true
	udm dns/host_record modify --dn relativeDomainName=ucs-sso,zoneName=autotest.local,cn=dns,dc=autotest,dc=local --set a="$backup_ip"
}

test_oidc_provider () {
	if [ "$1" == "true" ] ; then
		python3 product-tests/component/openid_connect_test.py
	fi
}
