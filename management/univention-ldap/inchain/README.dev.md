make all LDAP_BUILD=../../../debian/build && ../../../debian/build/libtool --mode=install install -c inchain.la /usr/lib/ldap/inchain.la


univention-ldapsearch -LLL '(uniqueMember:1.2.840.113556.1.4.1941:=uid=user1,cn=users,dc=school,dc=dev)' dn


ldapadd -x -H "ldap://$ldap_master:$ldap_master_port" -ZZ -D "cn=admin,$ldap_base" -y /etc/ldap.secret -f test.ldif

# time univention-ldapsearch -LLL '(uniqueMember:1.2.840.113556.1.4.1941:=uid=user1,cn=users,dc=school,dc=dev)' dn
dn: cn=group1,cn=groups,dc=school,dc=dev

dn: cn=group2,cn=groups,dc=school,dc=dev

dn: cn=group3,cn=groups,dc=school,dc=dev

dn: cn=group4,cn=groups,dc=school,dc=dev

dn: cn=group5,cn=groups,dc=school,dc=dev


real    0m0,393s
user    0m0,264s
sys     0m0,035s
# time univention-ldapsearch -LLL   '(uniqueMember=uid=user1,cn=users,dc=school,dc=dev)' dn
dn: cn=group1,cn=groups,dc=school,dc=dev


real    0m0,407s
user    0m0,333s
sys     0m0,047s

# univention-ldapsearch -LLLb cn=group1,cn=groups,dc=school,dc=dev uniqueMember
dn: cn=group1,cn=groups,dc=school,dc=dev
uniqueMember: uid=user1,cn=users,dc=school,dc=dev

# univention-ldapsearch -LLLb cn=group2,cn=groups,dc=school,dc=dev uniqueMember
dn: cn=group2,cn=groups,dc=school,dc=dev
uniqueMember: cn=group1,cn=groups,dc=school,dc=dev

# univention-ldapsearch -LLLb cn=group3,cn=groups,dc=school,dc=dev uniqueMember
dn: cn=group3,cn=groups,dc=school,dc=dev
uniqueMember: cn=group2,cn=groups,dc=school,dc=dev

# univention-ldapsearch -LLLb cn=group4,cn=groups,dc=school,dc=dev uniqueMember
dn: cn=group4,cn=groups,dc=school,dc=dev
uniqueMember: cn=group3,cn=groups,dc=school,dc=dev

# univention-ldapsearch -LLLb cn=group5,cn=groups,dc=school,dc=dev uniqueMember
dn: cn=group5,cn=groups,dc=school,dc=dev
uniqueMember: cn=group4,cn=groups,dc=school,dc=dev
