#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: check if service specific password works as expected
## tags: [apptest, radius]
## packages:
##   - univention-radius
## join: true
## exposure: dangerous

import ldap
import pytest
import subprocess
import univention.uldap as uldap


def radius_auth(username, password):
	subprocess.check_call([
		'radtest',
		'-t',
		'mschap',
		username,
		password,
		'127.0.0.1:18120',
		'0',
		'testing123',
	])


def test_acl_user_may_not_read(rad_user, lo, ssp):
	dn, name, password = rad_user
	lo.modify_ext_s(dn, ((ldap.MOD_REPLACE, 'univentionRadiusPassword', ssp[1]),))
	output = subprocess.check_output(['univention-ldapsearch', '-D', dn, '-w', password, '-b', dn, 'univentionRadiusPassword'])
	output = output.decode('utf-8')
	if 'univentionRadiusPassword:' in output:
		print(output)
		raise RuntimeError('%s should not be able to see univentionRadiusPassword' % dn)


def test_acl_user_may_not_write(rad_user, ssp, ucr):
	dn, name, password = rad_user
	lo = uldap.access(host=ucr.get('ldap/master'), port=ucr.get('ldap/server/port'), base=ucr.get('ldap/base'), binddn=dn, bindpw=password, start_tls=2, follow_referral=True)
	with pytest.raises(ldap.INSUFFICIENT_ACCESS):
		lo.modify_ext_s(dn, ((ldap.MOD_REPLACE, 'univentionRadiusPassword', ssp[1]),))


def test_acl_computer_may_read(rad_user, lo, ssp, ucr_session):
	dn, name, password = rad_user
	lo.modify_ext_s(dn, ((ldap.MOD_REPLACE, 'univentionRadiusPassword', ssp[1]),))
	output = subprocess.check_output(['univention-ldapsearch', '-D', ucr_session.get('ldap/hostdn'), '-y', '/etc/machine.secret', '-b', dn, 'univentionRadiusPassword'])
	output = output.decode('utf-8')
	if 'univentionRadiusPassword:' not in output:
		print(output)
		raise RuntimeError('%s needs to be able to see univentionRadiusPassword' % dn)


def test_acl_computer_may_not_write(rad_user, ssp, ucr):
	dn, name, password = rad_user
	bindpw = open('/etc/machine.secret').read()
	lo = uldap.access(host=ucr.get('ldap/master'), port=ucr.get('ldap/server/port'), base=ucr.get('ldap/base'), binddn=ucr.get('ldap/host'), bindpw=bindpw, start_tls=2, follow_referral=True)
	with pytest.raises(ldap.INSUFFICIENT_ACCESS):
		lo.modify_ext_s(dn, ((ldap.MOD_REPLACE, 'univentionRadiusPassword', ssp[1]),))


def test_acl_admin_may_read(rad_user, lo, ssp, ucr):
	dn, name, password = rad_user
	output = subprocess.check_output(['univention-ldapsearch', '-D', ucr.get('tests/domainadmin/account'), '-w', ucr.get('tests/domainadmin/pwd'), '-b', dn, 'univentionRadiusPassword'])
	output = output.decode('utf-8')
	if 'univentionRadiusPassword:' not in output:
		print(output)
		raise RuntimeError('Admin should be able to see univentionRadiusPassword')


def test_acl_admin_may_write(rad_user, ssp, ucr):
	dn, name, password = rad_user
	lo = uldap.access(host=ucr.get('ldap/master'), port=ucr.get('ldap/server/port'), base=ucr.get('ldap/base'), binddn=ucr.get('tests/domainadmin/account'), bindpw=ucr.get('tests/domainadmin/pwd'), start_tls=2, follow_referral=True)
	lo.modify_ext_s(dn, ((ldap.MOD_REPLACE, 'univentionRadiusPassword', ssp[1]),))
