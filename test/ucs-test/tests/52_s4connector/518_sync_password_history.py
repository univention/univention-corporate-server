#!/usr/share/ucs-test/runner pytest-3 -s -l -v
# coding: utf-8
## desc: "Test the UCS<->S4 NT password history sync"
## exposure: dangerous
## packages:
## - univention-s4-connector
## bugs:
##  - 52230


import ldap
import pytest
import subprocess
import binascii

import univention.testing.connector_common as tcommon
from univention.testing.connector_common import delete_con_user
from univention.testing.connector_common import (
	create_udm_user, to_unicode, NormalUser
)
from univention.testing.udm import UCSTestUDM, UCSTestUDM_ModifyUDMObjectFailed

import univention.config_registry
import univention.testing.strings as tstrings

import s4connector
from s4connector import connector_running_on_this_host, connector_setup

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()


class S4HistSync_Exception(Exception):
	def __str__(self):
		if self.args and len(self.args) == 1 and isinstance(self.args[0], dict):
			return '\n'.join('%s=%s' % (key, value) for key, value in self.args[0].items())
		else:
			return Exception.__str__(self)
	__repr__ = __str__


class S4CreateUser_Exception(S4HistSync_Exception):
	pass


class S4SetPassword_Exception(S4HistSync_Exception):
	pass


def create_s4_user(username, password, **kwargs):
	cmd = ["samba-tool", "user", "create", "--use-username-as-cn", username.decode('UTF-8'), password]

	print(" ".join(cmd))
	child = subprocess.Popen(" ".join(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	(stdout, stderr) = child.communicate()
	stdout, stderr = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')

	if child.returncode:
		raise S4CreateUser_Exception({'module': 'users/user', 'kwargs': kwargs, 'returncode': child.returncode, 'stdout': stdout, 'stderr': stderr})

	new_position = 'cn=users,%s' % configRegistry.get('connector/s4/ldap/base')
	con_user_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(tcommon.to_unicode(username)), new_position)

	udm_user_dn = ldap.dn.dn2str([
		[("uid", to_unicode(username), ldap.AVA_STRING)],
		[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(configRegistry.get('ldap/base')))
	s4connector.wait_for_sync()
	return (con_user_dn, udm_user_dn)


def modify_password_s4(username, password):
	cmd = ["samba-tool", "user", "setpassword", "--newpassword='%s'" % password, username.decode('UTF-8')]

	child = subprocess.Popen(" ".join(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	(stdout, stderr) = child.communicate()
	stdout, stderr = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')

	if child.returncode:
		raise S4SetPassword_Exception({'module': 'users/user', 'returncode': child.returncode, 'stdout': stdout, 'stderr': stderr})

	s4connector.wait_for_sync()


def udm_modify(udm, **kwargs):
	udm._cleanup.setdefault('users/user', []).append(kwargs['dn'])
	udm.modify_object(modulename='users/user', **kwargs)
	s4connector.wait_for_sync()


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention S4 Connector not configured.")
def test_initial_S4_pwd_is_synced():
	with connector_setup("sync") as s4, UCSTestUDM() as udm:
		(s4_user_dn, udm_user_dn) = create_s4_user(tstrings.random_username().encode('UTF-8'), "Univention.2-")

		s4_results = s4.get(s4_user_dn, attr=['unicodePwd'])
		nt_hash = binascii.b2a_hex(s4_results['unicodePwd'][0])
		ucs_result = udm._lo.search(base=udm_user_dn, attr=['sambaNTPassword', 'pwhistory'])[0][1]
		print("- Check udm and S4 nt_hash.")
		assert ucs_result["sambaNTPassword"][0] == nt_hash.upper(), "UDM sambaNTPassword and S4 nt_hash should be equal"
		print("Ok")
		print("- Check udm and S4 pwd history.")
		pwhist = ucs_result["pwhistory"][0].decode('ASCII').strip().split(" ")
		assert nt_hash.decode('ASCII').upper() == pwhist[-1][len("{NT}$"):].upper(), "Error verifying last S4 and UDM password entry"
		print("Ok")

		print("- Try to set original S4 password in UDM. (Should Raise, the password is in the history)")
		with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
			udm_modify(udm, dn=udm_user_dn, password="Univention.2-")
		print("Ok")

		print("- Set a different password in in UDM.")
		udm_modify(udm, dn=udm_user_dn, password="Univention.3-")
		print("Ok")

		delete_con_user(s4, s4_user_dn, udm_user_dn, s4connector.wait_for_sync)


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention S4 Connector not configured.")
def test_UCS_pwd_in_s4_history_synced():
	with connector_setup("sync") as s4, UCSTestUDM() as udm:
		udm_user = NormalUser()
		(udm_user_dn, s4_user_dn) = create_udm_user(udm, s4, udm_user, s4connector.wait_for_sync)

		print("- Set a different password in in S4.")
		modify_password_s4(ldap.dn.explode_rdn(s4_user_dn, notypes=True)[0].encode("UTF-8"), "Univention.5-")
		print("Ok")

		print("- Try to set the same password in UDM. (Should Raise, the password is in the history)")
		with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
			udm_modify(udm, dn=udm_user_dn, password="Univention.5-")
		print("Ok")

		s4_results = s4.get(s4_user_dn, attr=['unicodePwd', 'ntPwdHistory'])
		nt_hash = binascii.b2a_hex(s4_results['unicodePwd'][0])
		ucs_result = udm._lo.search(base=udm_user_dn, attr=['sambaNTPassword', 'pwhistory'])[0][1]
		print("- Check udm and S4 nt_hash.")
		assert ucs_result["sambaNTPassword"][0] == nt_hash.upper(), "UDM sambaNTPassword and S4 nt_hash should be equal"
		print("Ok")
		print("- Check udm and S4 pwd history.")
		pwhist = ucs_result["pwhistory"][0].decode('ASCII').strip().split(" ")
		assert nt_hash.decode('ASCII').upper() == pwhist[-1][len("{NT}$"):].upper(), "Error verifying last S4 and UDM password entry"
		print("Ok")

		delete_con_user(s4, s4_user_dn, udm_user_dn, s4connector.wait_for_sync)
