set -e
set -x

install_domain_join() {
	local branch=${2:?missing branch}
	wait_for_automatic_update
	if [ "$1" == "testing" ]; then
		install_testing_version $branch
	else
		install_released_version
	fi
}

wait_for_automatic_update() {
	for i in {0..10};do
		a=$(ps aux | grep -i apt | wc -l)
		if [ $a == 1 ];then
			break
		fi
		echo "Background update is running. Waiting 20 seconds"
		sleep 60
	done
}

install_testing_version () {
	local branch=${1:?missing branch}
	DEBIAN_FRONTEND=noninteractive apt install -y git curl build-essential dpkg-dev debhelper python3 dh-python python3-all python-setuptools expect
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

install_released_version() {
	add-apt-repository -y ppa:univention-dev/ppa
	apt-get update
	DEBIAN_FRONTEND=noninteractive apt-get -y install univention-domain-join univention-domain-join-cli expect
}

create_user () {
	local user=${1:?missing username}
	local lastname=${2:?missing lastname}
	local password=${3:?missing password}

	univention-directory-manager users/user create \
	--position "cn=users,$(ucr get ldap/base)" \
	--set username="$user" \
	--set lastname="$lastname" \
	--set password="$password"
}

test_univention_domain_join_cli () {
	local dc_ip=${1:?missing dc ip}
	local admin=${2:?missing admin account}
	local password=${3:?missing admin account password}
	univention-domain-join-cli --username "$admin" --password "$password" --dc-ip "$dc_ip" --force-ucs-dns
}

test_user () {
	local username=${1:?missing username}
	local password=${2:?missing password}
	local password_file=$(mktemp)
	# ldap users
	getent passwd | grep $username
	# kerberos, ldapsearch with krb5 ticket
	echo -n $password > $password_file
	kinit --password-file=$password_file $username
	ldapsearch uid=$username | grep "^dn: uid=$username"
	sshpass -p "$password" ssh -o StrictHostKeyChecking=no "$username@$(hostname)" "whoami"
	kdestroy
}

test_login () {
	local user=${1:?missing user}
	local password=${2:?missing password}
	echo "Login as User: $user"
	expect ~/product-tests/domain-join/login "$user" "$password"
}

test_change_password () {
	local user=${1:?missing user}
	local old_password=${2:?missing old password}
	local new_password=${3:?missing new password}
	echo "Changing password of User: $user"
	expect ~/product-tests/domain-join/kpasswd "$user" "$old_password" "$new_password"
}

test_home_directory () {
	local user=${1:?missing user}
	echo "Checking directory /home/$user/"
	[ -d "/home/$user/" ] && echo "Directory /home/$user/ found"
}

test_login_with_old_pw () {
	local user=${1:?missing user}
	local password=${2:?missing password}
	local password_file=$(mktemp)
	echo -n $password > $password_file
	! kinit --password-file=$password_file $user
}

run_tests () {
	local run_tests=${1:?missing run tests parameter}
	local dc_ip=${2:?missing dc ip}
	local admin=${3:?missing admin account}
	local admin_password=${4:?missing admin account password}
	local user=${5:?missing user account}
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
