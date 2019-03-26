#!/bin/bash

set -x
set -e

prepare_on_master () {

	echo -e "UserKnownHostsFile=/dev/null\nStrictHostKeyChecking=no" > ~/.ssh/config
	service slapd stop

	# type 1 - provide database backend
	sshpass -p "univention" ssh "$slave1_IP" "mkdir -p /opt/type1"
	cat /var/lib/univention-directory-listener/notifier_id | sshpass -p "univention" ssh "$slave1_IP" "cat - > /opt/type1/notifier_id"
	cd /var/lib/univention-ldap/ldap && tar -Sc data.mdb | sshpass -p "univention" ssh "$slave1_IP" "tar -Sx -C /opt/type1/"

	# type 2 - provide ldif file
	sshpass -p "univention" ssh "$backup_IP" "mkdir -p /opt/type2"
	cat /var/lib/univention-directory-listener/notifier_id | sshpass -p "univention" ssh "$backup_IP" "cat - > /opt/type2/notifier_id"
	slapcat | gzip | sshpass -p "univention" ssh "$backup_IP" "cat - > /opt/type2/ldif.gz"

	# type 3 - let the join handle the provisioning (ldapsearch)
	# nothing todo here

	service slapd start
}

type1_listener_fake () {

	# type1 fake for replication and nss with additional listener/init/fake/helper for nss

	echo -n "$DOMAIN_PWD" > /tmp/join_secret
	test -f /usr/share/univention-directory-listener/resync-objects.py
	test -f /usr/share/univention-directory-listener/univention-get-ldif-from-master.py
	cat << EOF > /tmp/fake_helper
fake_nss () {
        touch /tmp/fake_nss
}
EOF
	ucr set listener/init/fake/helper=/tmp/fake_helper
	ucr set listener/init/fake="replication nss"
	ucr set listener/init/fake/replication/mdb="/opt/type1/data.mdb"
	ucr set listener/init/fake/notifierid="$(cat /opt/type1/notifier_id)"
	univention-join -dcaccount "$DOMAIN_ACCOUNT" -dcpwd /tmp/join_secret
	univention-ldapsearch uid="$DOMAIN_ACCOUNT"
	univention-check-join-status
	grep "faking listener initialization" /var/log/univention/join.log
	grep "faking handler 'replication'" /var/log/univention/join.log
	grep "faking handler 'nss'" /var/log/univention/join.log
	grep "Installing database file /opt/type1/data.mdb" /var/log/univention/join.log
	grep "resync from master: cn=$slave1_NAME," /var/log/univention/join.log
	test -f /tmp/fake_nss
}

type2_listener_fake () {


	# type2 fake for replication and nss without listener/init/fake/helper

	echo -n "$DOMAIN_PWD" > /tmp/join_secret
	test -f /usr/share/univention-directory-listener/resync-objects.py
	test -f /usr/share/univention-directory-listener/univention-get-ldif-from-master.py
	ucr set listener/init/fake="replication nss"
	ucr set listener/init/fake/replication/ldif="/opt/type2/ldif.gz"
	ucr set listener/init/fake/notifierid="$(cat /opt/type2/notifier_id)"
	univention-join -dcaccount "$DOMAIN_ACCOUNT" -dcpwd /tmp/join_secret
	univention-ldapsearch uid="$DOMAIN_ACCOUNT"
	univention-check-join-status
	grep "faking listener initialization" /var/log/univention/join.log
	grep "faking handler 'replication'" /var/log/univention/join.log
	grep "faking handler 'nss'" /var/log/univention/join.log
	grep "slapadd /opt/type2/ldif.gz" /var/log/univention/join.log
	grep "resync from master: cn=$backup_NAME," /var/log/univention/join.log
}

type3_listener_fake () {

	# type3 fake for replication

	echo -n "$DOMAIN_PWD" > /tmp/join_secret
	test -f /usr/share/univention-directory-listener/resync-objects.py
	test -f /usr/share/univention-directory-listener/univention-get-ldif-from-master.py
	ucr set listener/init/fake="replication"
	univention-join -dcaccount "$DOMAIN_ACCOUNT" -dcpwd /tmp/join_secret
	univention-ldapsearch uid="$DOMAIN_ACCOUNT"
	univention-check-join-status
	grep "faking listener initialization" /var/log/univention/join.log
	grep "faking handler 'replication'" /var/log/univention/join.log
	grep "searching ldap on master and slapadd " /var/log/univention/join.log
	grep "resync from master: cn=$slave2_NAME," /var/log/univention/join.log
}
