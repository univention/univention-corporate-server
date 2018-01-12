#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# -*- coding: utf-8 -*-
## desc: Test various things in users/user
## exposure: dangerous
## roles: [domaincontroller_master]
## packages: [python-univention-directory-manager]

import pytest
import time


class TestUsers(object):
	"""
		# TODO: test open() method:
		1. self.is_auth_saslpassthrough = self.__pwd_is_auth_saslpassthrough(self['password'] or '')

		2.
		if self.exists():
			self._unmap_mail_forward()
			self.sambaMungedDialUnmap()
			self.sambaMungedDialParse()
			self.reload_certificate()

		3.
		self._load_groups(loadGroups)

		# TODO: test pre_create() / pre_modify() / pre_ready() method:
		mail primary address gets lowered
		primaryGroupWithoutSamba
		check uid/gidnumber conflict

		locks (change und create): uidNumber, uid, mailPrimaryAddress
		locks confirmed after creation/modification
		locks released after removal
		prohibited usernames are checked during create(), modify()

		locks funktionieren mit case-insensitive

		create(): 'krb5PrincipalName', 'krb5MaxLife', 'krb5MaxRenew' are set

		modification of username → correct DN, correct krb principal name

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
