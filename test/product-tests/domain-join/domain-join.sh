set -e
set -x

install_testing_version () {
	local branch=${1:?missing branch}
	DEBIAN_FRONTEND=noninteractive apt install -y git curl build-essential dpkg-dev debhelper python3 dh-python python3-all python-setuptools
	curl -k  https://billy.knut.univention.de/ucs-root-ca.crt > /usr/local/share/ca-certificates/billy.crt
	update-ca-certificates -f
	git clone https://git.knut.univention.de/univention/univention-domain-join.git
	cd univention-domain-join
	git checkout "$branch"
	dpkg-buildpackage
	cd ..
	dpkg -i python3-univention-domain-join_*_all.deb  univention-domain-join_*_all.deb  univention-domain-join-cli_*_all.deb || true
	DEBIAN_FRONTEND=noninteractive apt-get -y -f install
}

install_released_version () {
	TODO
}

univention_domain_join_cli () {
	local master=${1:?missing master ip}
	local admin=${2:?missing admin account}
	local password=${3:?missing admin account password}
	univention-domain-join-cli --username "$admin" --password "$password" --master-ip "$master"
}

check_user () {
	local username=${1:?missing username}
	local password=${2:?missing password}
	local password_file=$(mktemp)
	# ldap users
	getent passwd | grep $username
	# kerberos, ldapsearch with krb5 ticket
	echo -n $password > $password_file
	kinit --password-file=$password_file $username
	ldapsearch uid=$username | grep "^dn: uid=$username"
}
