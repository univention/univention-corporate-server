#!/usr/share/ucs-test/runner /usr/bin/pytest-3 -s -vvv
# -*- coding: utf-8 -*-
## desc: Test that school replica server can't create a Samba Administrator on the primary server
## tags: [samba4,apptest]
## roles: [domaincontroller_slave]
## exposure: dangerous
## packages:
##   - univention-config
##   - ucs-school-replica

import pytest
import subprocess

import univention.admin
import univention.testing.strings as uts
import univention.testing.utils as utils
import univention.testing.udm as udm_test


# I only want the user to be created once
@pytest.fixture(scope="session")
def udm_session():
	with udm_test.UCSTestUDM() as udm:
		yield udm


@pytest.fixture(scope='session')
def user1(udm_session, ucr_session):
	hn = ucr_session.get("samba4/join/site")
	base = ucr_session.get("ldap/base")
	# only users in the schoolservers ou can be modified by the schoolserver account
	user_dn, username = udm_session.create_user(position=f'ou={hn},{base}', wait_for_replication=True, wait_for=True)
	return user_dn, username


@pytest.fixture
def lo(ucr):
	ldap_server = ucr.get('ldap/master')
	port = ucr.get('ldap/server/port')
	binddn = ucr.get('ldap/hostdn')
	bindpw = open('/etc/machine.secret').read()
	lo = univention.admin.uldap.access(host=ldap_server, port=port, base=ucr.get('ldap/base'), binddn=binddn, bindpw=bindpw, start_tls=2, follow_referral=True)
	return lo


@pytest.fixture
def ldif(ucr):
	def_admin = 'cn=Administrator,cn=users,%s' % (ucr.get('ldap/base'),)
	attribute = 'description'
	new_attribute_val = uts.random_name()
	filename = "/tmp/%s.ldif" % (uts.random_name())
	with open(filename, 'w+') as f:
		f.write(f"dn: {def_admin}\nchangetype: modify\nreplace: {attribute}\n{attribute}: {new_attribute_val}")
	return filename


def check_primarys4_access(username, primary_ip, ucr, ldif, password="univention"):
	try:
		# i can get around the ldapi requirement of samba4 on the primary by using ldbmodify
		# because i want a simple bind to test the access rights of the testuser
		subprocess.check_output(['ldbmodify', '-H', f'ldap://{primary_ip}', f'-U{username}%{password}', ldif], stderr=subprocess.PIPE)
	except subprocess.CalledProcessError as e:
		assert b'LDAP_INVALID_CREDENTIALS' not in e.stderr
		assert b'LDAP_INSUFFICIENT_ACCESS_RIGHTS' in e.stderr
		pass
	else:
		raise AssertionError("Non Administrator user1 was able to modify Samba4 LDAP data")


# test that the school replica can't modify groupmemberships
def test_group_modification(udm, ucr, lo, user1, ldif):
	user_dn, username = user1[0].encode('utf-8'), user1[1].encode('utf-8')
	group_dn, attrs = lo.search(filter='cn=Domain Admins', attr=['memberUid', 'uniqueMember'])[0]
	with pytest.raises(univention.admin.uexceptions.permissionDenied):
		lo.modify(group_dn, (('memberUid', b'', username), ('uniqueMember', b'', user_dn)))


@pytest.mark.parametrize('attr,rid', [('sambaSID', b'-500'), ('sambaPrimaryGroupSID', b'-512')])
def test_sid_modification(udm, ucr, lo, user1, ldif, attr, rid):
	user_dn, username = user1
	primary_ip = lo.search(filter='univentionObjectType=computers/domaincontroller_master', attr=['aRecord'])[0][1].get('aRecord')[0].decode('utf-8')
	old_pgsid = lo.get(user_dn, [attr]).get(attr)[0]
	# change rid of sid to resemble the default administrator attributes
	new_pgsid = old_pgsid.rsplit(b'-', 1)[0] + rid

	lo.modify(user_dn, ((attr, old_pgsid, new_pgsid),))
	utils.wait_for_replication_and_postrun()
	utils.wait_for_s4connector_replication()

	check_primarys4_access(username, primary_ip, ucr, ldif)
