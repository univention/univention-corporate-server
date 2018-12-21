setup_user_and_groups () {
	set -x
	set -e

	. product-tests/samba/utils.sh
	eval "$(ucr shell ldap/base windows/domain)"
	#5000 benutzer 1050 gruppen je 50 zufällig benutzer
	#start : 15:08
	#finish : 20:23
	#ca. 5 hours
	START=$(date +%s.%N)
	for i in $(seq 1 5000); do
		newindex="$i"
		udm users/user create --position "cn=users,$ldap_base" --set username="benutzer$newindex" \
					--set lastname="newuser" --set password="Univention.99"
	done

	for i in $(seq 1 1050); do
		udm groups/group create --position "cn=groups,$ldap_base" --set name="gruppe$i"
		for j in $(seq 1 50); do
			newindex=$(shuf -i 1-5000 -n 1)
			udm groups/group modify --dn "cn=gruppe$i,cn=groups,$ldap_base" \
						--append users="uid=benutzer$newindex,cn=users,$ldap_base"
		done
	done
	END=$(date +%s.%N)
	DIFF=$(echo "$END - $START" | bc)
	echo "Group and user creation time: /n" >> timestamps.log
	echo $DIFF >> timestamps.log

}

login_user () {
	
	set -x
	set -e

	. product-tests/samba/utils.sh
	python shared-utils/ucs-winrm.py domain-join --domain sambatest.local --dnsserver "$UCS" --domainuser "Administrator" --domainpassword $ADMIN_PASSWORD
	python shared-utils/ucs-winrm.py domain-user-validate-password --domainuser "Administrator" --domainpassword $ADMIN_PASSWORD
	START=$(date +%s.%N)
	python shared-utils/ucs-winrm.py run-ps --cmd ipconfig --impersonate --run-as-user "Administrator"
	END=$(date +%s.%N)
	DIFF=$(echo "$END - $START" | bc)
	echo "Login time" >> timestamps.log
	echo $DIFF >> timestamps.log
}
