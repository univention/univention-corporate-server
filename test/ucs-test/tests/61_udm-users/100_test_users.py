#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# -*- coding: utf-8 -*-
## desc: Test various things in users/user
## exposure: dangerous
## roles: [domaincontroller_master]
## packages: [python-univention-directory-manager]

import pytest
import time
import subprocess


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

		create(): 'krb5PrincipalName', 'krb5MaxLife', 'krb5MaxRenew' are set

		modlist_samba_privileges
		modlist_cn
		modlist_gecos
		modlist_display_name
		modlist_krb_principal
		modlist_password_change
		modlist_samba_bad_pw_count
		modlist_sambaAcctFlags
		modlist_shadowMax
		modlist_samba_kickoff_time
		modlist_krb5_valid_end
		modlist_shadow_expire
		modlist_mail_forward
		modlist_univention_person
		modlist_home_share
		modlist_samba_mungeddial
		modlist_samba_sid

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
