# shellcheck shell=sh
set -e -x

install_domain_join() {
	local branch=${2:?missing branch}
	wait_for_automatic_update
	if [ "$1" == "testing" ]; then
		install_testing_version "$branch"
	else
		install_released_version
	fi
}

wait_for_automatic_update() {
	# shellcheck disable=SC2034
	for i in $(seq 10)
	do
		pgrep apt || return 0
		echo "Background update is running. Waiting 60 seconds"
		sleep 60
	done
	return 1
}

install_testing_version () {
	local branch=${1:?missing branch}
	DEBIAN_FRONTEND=noninteractive apt-get -q --assume-yes install --no-install-recommends git build-essential expect
	git clone --single-branch --branch "$branch" --depth 1 -c http.sslVerify=false https://git.knut.univention.de/univention/univention-domain-join.git
	cd univention-domain-join
	DEBIAN_FRONTEND=noninteractive apt-get -q --assume-yes build-dep .
	dpkg-buildpackage -uc -us -b
	cd ..
	DEBIAN_FRONTEND=noninteractive apt-get -q --assume-yes install ./python3-univention-domain-join_*_all.deb ./univention-domain-join_*_all.deb ./univention-domain-join-cli_*_all.deb
}

install_released_version() {
	add-apt-repository -y ppa:univention-dev/ppa
	apt-get -q update
	DEBIAN_FRONTEND=noninteractive apt-get -y install univention-domain-join univention-domain-join-cli expect
}

create_user () {
	local user=${1:?missing username} lastname=${2:?missing lastname} password=${3:?missing password}

	univention-directory-manager users/user create \
	--position "cn=users,$(ucr get ldap/base)" \
	--set username="$user" \
	--set lastname="$lastname" \
	--set password="$password"
}

test_univention_domain_join_cli () {
	local dc_ip=${1:?missing dc ip} admin=${2:?missing admin account} password=${3:?missing admin account password}
	univention-domain-join-cli --username "$admin" --password "$password" --dc-ip "$dc_ip" --force-ucs-dns
}

test_user () {
	local username=${1:?missing username} password=${2:?missing password} password_file
	password_file=$(mktemp)
	# ldap users
	getent passwd "$username"
	# kerberos, ldapsearch with krb5 ticket
	echo -n "$password" > "$password_file"
	kinit --password-file="$password_file" "$username"
	ldapsearch uid="$username" | grep "^dn: uid=$username"
	sshpass -p "$password" ssh -o StrictHostKeyChecking=no "$username@$(hostname)" "whoami"
	kdestroy
}

test_login () {
	local user=${1:?missing user} password=${2:?missing password}
	echo "Login as User: $user"
	expect ~/product-tests/domain-join/login "$user" "$password"
}

test_change_password () {
	local user=${1:?missing user} old_password=${2:?missing old password} new_password=${3:?missing new password}
	echo "Changing password of User: $user"
	expect ~/product-tests/domain-join/kpasswd "$user" "$old_password" "$new_password"
}

test_home_directory () {
	local user=${1:?missing user}
	echo "Checking directory /home/$user/"
	[ -d "/home/$user/" ] && echo "Directory /home/$user/ found"
}

test_login_with_old_pw () {
	local user=${1:?missing user} password=${2:?missing password} password_file
	password_file=$(mktemp)
	echo -n "$password" > "$password_file"
	! kinit --password-file="$password_file" "$user"
}

run_tests () {
	local run_tests=${1:?missing run tests parameter}
	local dc_ip=${2:?missing dc ip}
	local admin=${3:?missing admin account}
	local admin_password=${4:?missing admin account password}
	local user=${5:?missing user account}
	# shellcheck disable=SC2034
	local user_lastname=${6:?missing user lastname}
	local user_password=${7:?missing user password}
	local new_user_password=${8:?missing new user password}

	if $run_tests; then
		test_univention_domain_join_cli "$dc_ip" "$admin" "$admin_password"
		test_user "$admin" "$admin_password"
		test_login "$user" "$user_password"
		test_home_directory "$user"
		test_change_password "$user" "$user_password" "$new_user_password"
		test_login "$user" "$new_user_password"
		test_login_with_old_pw "$user" "$user_password"
	fi
}
