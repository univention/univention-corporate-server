#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# -*- coding: utf-8 -*-
## desc: Test various things in users/user
## exposure: dangerous
## roles: [domaincontroller_master]
## packages: [python-univention-directory-manager]

import pytest
import time
import subprocess

from univention.config_registry import handler_set
from univention.testing.strings import random_username


class TestUsers(object):
	"""
		# TODO: test open() method:

		2.
		if self.exists():
			self._unmap_mail_forward()
			self.sambaMungedDialUnmap()
			self.sambaMungedDialParse()

		3.
		self._load_groups(loadGroups)

		# TODO: test pre_create() / pre_modify() / pre_ready() method:
		primaryGroupWithoutSamba

		different password expiry interval values!

		is the locking of uidNumber still okay, what if limits are reached?

		what if pwdChangeNextLogin = 1 and password=foo at the same time?
	"""

	@pytest.mark.parametrize('shadowLastChange,shadowMax,pwd_change_next_login', [
		('0', '', '1'),
		('0', '0', '1'),
		('0', '1', '1'),
		('0', str(int(time.time()) + 86400), '1'),
		('', str(int(time.time()) + 86400), []),
		('', '', []),
		('', str(int(time.time()) - 86400 * 2), []),
		('1', str(int(time.time()) - 86400 * 2), []),
		('0', str(int(time.time()) - 86400 * 2), '1'),
	])
	def test_unmap_pwd_change_next_login(self, udm, lo, shadowLastChange, shadowMax, pwd_change_next_login):
		user = udm.create_user()[0]
		attr = lo.get(user)
		ml = []
		if shadowLastChange is not None:
			ml.append(('shadowLastChange', attr.get('shadowLastChange'), shadowLastChange))
		if shadowMax is not None:
			ml.append(('shadowMax', attr.get('shadowMax'), shadowMax))
		if ml:
			lo.modify(user, ml)
		udm.verify_udm_object("users/user", user, {"pwdChangeNextLogin": pwd_change_next_login})

	@pytest.mark.parametrize('path', ['/test', '/test2/'])
	def test_unmap_automount_information(self, udm, path, random_name, lo, verify_ldap_object, verify_udm_object):
		homeSharePath = random_name()
		host = random_name()
		share = udm.create_object('shares/share', name=random_name(), path=path, host=host)

		user = udm.create_user(homeShare=share, homeSharePath=homeSharePath)[0]
		udm.verify_udm_object("users/user", user, {"homeShare": share, "homeSharePath": homeSharePath})
		verify_ldap_object(user, {'automountInformation': ['-rw %s:%s/%s' % (host, path.rstrip('/'), homeSharePath)]})

	def test_unmap_user_certificate(self, udm, ucr):
		certificate = subprocess.check_output(['openssl', 'x509', '-inform', 'pem', '-in', '/etc/univention/ssl/%(hostname)s/cert.pem' % ucr, '-outform', 'der', '-out', '-']).encode('base64').replace('\n', '')
		user = udm.create_user(options=['pki'], userCertificate=certificate)[0]
		# FIXME: get the real values from the certificate!
		udm.verify_udm_object('users/user', user, {
			'userCertificate': certificate,
			'certificateDateNotAfter': '2022-12-17',
			'certificateDateNotBefore': '2017-12-18',
			# 'certificateIssuerCommonName': 'Univention Corporate Server Root CA (ID=YRkLWLDu)',
			'certificateIssuerCountry': 'DE',
			'certificateIssuerLocation': 'DE',
			'certificateIssuerMail': 'ssl@%s' % ucr.get('domainname'),
			'certificateIssuerOrganisation': 'DE',
			'certificateIssuerOrganisationalUnit': 'Univention Corporate Server',
			'certificateIssuerState': 'DE',
			'certificateSerial': '1',
			'certificateSubjectCommonName': '%(hostname)s.%(domainname)s' % ucr,
			'certificateSubjectCountry': 'DE',
			'certificateSubjectLocation': 'DE',
			'certificateSubjectMail': 'ssl@%s' % ucr.get('domainname'),
			'certificateSubjectOrganisation': 'DE',
			'certificateSubjectOrganisationalUnit': 'Univention Corporate Server',
			'certificateSubjectState': 'DE',
			'certificateVersion': '2',
		})

	def test_mail_primary_group_gets_lowercased(self):
		pass  # TODO: implement create() + modify()

	def test_uid_gid_number_conflict_is_detected(self):
		pass

	def test_locking(self):
		"""
		locks (change und create): uidNumber, uid, mailPrimaryAddress
		locks confirmed after creation/modification
		locks released after removal
		locks funktionieren mit case-insensitive
		"""

	def test_prohibited_username_are_checked(self, udm, random_username):
		username = random_username()
		udm.create_object('settings/prohibited_username', name='forbidden', usernames=[username])

		with pytest.raises(Exception):
			udm.create_user(username=username)

		user = udm.create_user()[0]
		with pytest.raises(Exception):
			udm.modify_object('user/user', dn=user, username=username)

	def test_modification_of_username(self, udm, random_username, verify_ldap_object, ucr):
		user, name = udm.create_user()
		username = random_username()
		assert name in user
		assert username not in user
		user = udm.modify_object('users/user', dn=user, username=username)
		assert name not in user
		assert username in user
		verify_ldap_object(user, {'krb5PrincipalName': ['%s@%s' % (username, ucr['domainname'].upper())]})

	def test_kerberos_values_are_set(self, udm, verify_ldap_object):
		user = udm.create_user()[0]
		verify_ldap_object(user, {
			'krb5MaxLife': ['86400'],
			'krb5MaxRenew': ['604800'],
		})

	@pytest.mark.parametrize('privileges', [
		['SeMachineAccountPrivilege'],
		['SeSecurityPrivilege'],
		['SeTakeOwnershipPrivilege'],
		['SeBackupPrivilege'],
		['SeRestorePrivilege'],
		['SeRemoteShutdownPrivilege'],
		['SePrintOperatorPrivilege'],
		['SeAddUsersPrivilege'],
		['SeDiskOperatorPrivilege'],
		[
			'SeMachineAccountPrivilege',
			'SeSecurityPrivilege',
			'SeTakeOwnershipPrivilege',
			'SeBackupPrivilege',
			'SeRestorePrivilege',
			'SeRemoteShutdownPrivilege',
			'SePrintOperatorPrivilege',
			'SeAddUsersPrivilege',
			'SeDiskOperatorPrivilege',
		]
	])
	def test_modlist_samba_privileges(self, udm, privileges, verify_ldap_object):
		self._test_modlist(udm, verify_ldap_object, {'sambaPrivileges': privileges}, {'univentionSambaPrivilegeList': privileges, 'objectClass': ['univentionSambaPrivileges']})

	@pytest.mark.parametrize('privileges', [
		pytest.mark.xfail(['SeMachineAccountPrivilege', 'foobar'], reason='https://forge.univention.org/bugzilla/show_bug.cgi?id=46020'),
		['foobar'],
	])
	def test_modlist_samba_privileges_invalid(self, udm, privileges):
		with pytest.raises(Exception):
			udm.create_user(sambaPrivileges=privileges)

		user = udm.create_user()[0]
		with pytest.raises(Exception):
			udm.modify_object('users/user', dn=user, sambaPrivileges=privileges)

	_modlist_cn_username = random_username()

	@pytest.mark.parametrize('form,props,cn', [
		('<firstname> <lastname>', {'firstname': 'X', 'lastname': 'Y'}, 'X Y'),
		('<username> <firstname> <lastname>', {'username': _modlist_cn_username, 'firstname': 'X', 'lastname': 'Y'}, '%s X Y' % (_modlist_cn_username,)),
	])
	def test_modlist_cn(self, udm, ucr, form, props, cn, verify_ldap_object):
		handler_set(['directory/manager/usercn/attributes=%s' % (form,)])
		udm.stop_cli_server()
		self._test_modlist(udm, verify_ldap_object, props, {'cn': [cn]})

	def _test_modlist(self, udm, verify_ldap_object, props, attrs):
		user = udm.create_user(**props)[0]
		verify_ldap_object(user, attrs, strict=False)
		udm.remove_object('users/user', dn=user)

		user = udm.create_user()[0]
		user = udm.modify_object('users/user', dn=user, **props)
		verify_ldap_object(user, attrs, strict=False)

	def test_modlist_gecos(self, udm):
		pass

	def test_modlist_display_name(self, udm):
		pass

	def test_modlist_krb_principal(self, udm):
		pass

	def test_modlist_password_change(self, udm):
		pass

	def test_modlist_samba_bad_pw_count(self, udm):
		pass

	def test_modlist_sambaAcctFlags(self, udm):
		pass

	def test_modlist_shadowMax(self, udm):
		pass

	def test_modlist_samba_kickoff_time(self, udm):
		pass

	def test_modlist_krb5_valid_end(self, udm):
		pass

	def test_modlist_shadow_expire(self, udm):
		pass

	def test_modlist_mail_forward(self, udm):
		pass

	def test_modlist_univention_person(self, udm):
		pass

	def test_modlist_home_share(self, udm):
		pass

	def test_modlist_samba_mungeddial(self, udm):
		pass

	def test_modlist_samba_sid(self, udm):
		pass
