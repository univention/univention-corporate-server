set -x
set -e

. product-tests/samba/utils.sh
eval "$(ucr shell ldap/base windows/domain)"
#for i in $(seq 1 40); do
#	udm groups/group list --filter name="gruppe$i" | grep "^DN: "
##done
#for i in $(seq 1 1500); do
#	udm users/user create --position "cn=users,$ldap_base" --set username="benutzer$i" \
#					--set lastname="newuser01" --set password="Univention.99"
#udm groups/group modify --dn "cn=Domain Admins,cn=groups,$ldap_base" --append users="uid=newuser01,cn=users,dc=sambatest,dc=local"
for i in $(seq 1 1050); do
	udm groups/group create --position "cn=groups,$ldap_base" --set name="gruppe$i"
	for j in $(seq 1 50); do
		newindex="$j"
		newindex+="ing$i"
		udm users/user create --position "cn=users,$ldap_base" --set username="benutzer$newindex" \
						--set lastname="newuser01" --set password="Univention.99"
		udm groups/group modify --dn "cn=gruppe$i,cn=groups,$ldap_base" \
						--append users="uid=benutzer$newindex,cn=users,$ldap_base"
	done
done





