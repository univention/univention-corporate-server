
check_parameter ()
{
	if [ $# != 1 ]; then
		usage
		exit 2
	fi

	if [ ! -e "$1" ]; then
		echo "$1 does not exist"
		usage
		exit 2
	fi
}

usage ()
{
	echo "Usage $0 <ldif file>"
	echo "For example: $0 /usr/share/ucs-test-tools/customer5000.ldif"
}

get_sambaSID ()
{
	univention-ldapsearch sambaDomainName=$windows_domain -LLL | sed -ne 's|^sambaSID: ||p'
}

prepare_ldif_for_slapadd ()
{
	cat "$1" | sed -e "s|%%SID%%|$sambaSID|g;s|%%LDAP_BASE%%|$ldap_base|g;s|%%DNS%%|$domainname|g"
}

prepare_ldif_for_ldapadd ()
{
	cat "$1" | sed -e "s|%%SID%%|$sambaSID|g;s|%%LDAP_BASE%%|$ldap_base|g;s|%%DNS%%|$domainname|g" | egrep -v "(^modifyTimestamp:|^modifiersName:|^entryCSN:|^entryUUID:|^creatorsName:|^createTimestamp:|^structuralObjectClass:)"
}


stop_slapd ()
{
	/etc/init.d/slapd stop
}

start_slapd ()
{
	/etc/init.d/slapd start
}

sync_groupmemberships ()
{
	/usr/share/univention-directory-manager-tools/proof_uniqueMembers
}

change_performance_settings ()
{
	echo "Disable autosearch, to reset use: ucr set directory/manager/web/modules/autosearch=1"
	ucr set directory/manager/web/modules/autosearch=0

	echo "Change group_to_file settings, to reset use: ucr set nss/group/cachefile/check_member=yes nss/group/cachefile/invalidate_interval='*/15 * * * *'"
	ucr set nss/group/cachefile/check_member=no
	ucr set nss/group/cachefile/invalidate_interval="#*/15 * * * *"
}

backup_and_remove_ldap_objects ()
{
	for dn in "cn=Windows Hosts,cn=groups,$ldap_base" \
		"cn=Domain Users,cn=groups,$ldap_base" \
		"cn=DC Backup Hosts,cn=groups,$ldap_base" \
		"cn=DC Slave Hosts,cn=groups,$ldap_base" \
		"cn=Computers,cn=groups,$ldap_base" \
		"cn=default containers,cn=univention,$ldap_base"
	do
		univention-ldapsearch -b "$dn" >>/var/univention-backup/import-backup.ldif
		ldapdelete -x -D cn=admin,$ldap_base -y /etc/ldap.secret "$dn"
	done
}
