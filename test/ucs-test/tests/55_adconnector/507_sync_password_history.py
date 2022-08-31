#!/usr/share/ucs-test/runner pytest-3 -s -l -v
# coding: utf-8
## desc: "Test the UCS<->AD NT password history sync"
## exposure: dangerous
## packages:
## - univention-ad-connector
## bugs:
##  - 52230
## tags:
##  - skip_admember

import ldap
import pytest
import subprocess
import os
import struct
import binascii
import Crypto
import hashlib
from tempfile import NamedTemporaryFile

import adconnector
from adconnector import connector_running_on_this_host, connector_setup
from univention.connector.ad import kerberosAuthenticationFailed, netbiosDomainnameNotFound
from univention.connector.ad.password import decrypt, decrypt_history, calculate_krb5keys

import univention.testing.connector_common as tcommon
from univention.testing.connector_common import delete_con_user
from univention.testing.connector_common import (
	create_udm_user, to_unicode, NormalUser
)

import univention.config_registry
import univention.testing.strings as tstrings

from samba.dcerpc import drsuapi, misc, security, drsblobs, nbt
from samba.ndr import ndr_unpack
from samba.param import LoadParm
from samba.net import Net
from samba.credentials import Credentials, DONT_USE_KERBEROS
from samba import drs_utils

# This is something weird. The `adconnector.ADConnection()` MUST be
# instantiated, before `UCSTestUDM` is imported.
AD = adconnector.ADConnection()

from univention.testing.udm import UCSTestUDM, UCSTestUDM_ModifyUDMObjectFailed  # noqa: E402

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()


class ADHistSync_Exception(Exception):
	def __str__(self):
		if self.args and len(self.args) == 1 and isinstance(self.args[0], dict):
			return '\n'.join('%s=%s' % (key, value) for key, value in self.args[0].items())
		else:
			return Exception.__str__(self)
	__repr__ = __str__


class ADCreateUser_Exception(ADHistSync_Exception):
	pass


class ADSetPassword_Exception(ADHistSync_Exception):
	pass


def open_drs_connection():

	ad_ldap_host = configRegistry.get("connector/ad/ldap/host")
	ad_ldap_port = configRegistry.get('connector/ad/ldap/port')
	ad_ldap_base = configRegistry.get('connector/ad/ldap/base')
	ad_ldap_certificate = configRegistry.get('connector/ad/ldap/certificate')

	tls_mode = 2 if configRegistry.is_true('connector/ad/ldap/ssl', True) else 0
	ldaps = configRegistry.is_true('connector/ad/ldap/ldaps', False)  # tls or ssl

	lo_ad = univention.uldap.access(
		host=ad_ldap_host, port=int(ad_ldap_port),
		base='', binddn=None, bindpw=None, start_tls=tls_mode,
		use_ldaps=ldaps, ca_certfile=ad_ldap_certificate,
	)

	ad_ldap_binddn = configRegistry.get('connector/ad/ldap/binddn')
	ad_ldap_bindpw_file = configRegistry.get('connector/ad/ldap/bindpw')
	with open(ad_ldap_bindpw_file) as fd:
		ad_ldap_bindpw = fd.read().rstrip()

	def get_kerberos_ticket(ad_ldap_bindpw, ad_ldap_binddn):
		p1 = subprocess.Popen(['kdestroy', ], close_fds=True)
		p1.wait()
		with NamedTemporaryFile('w') as fd:
			fd.write(ad_ldap_bindpw)
			fd.flush()
			cmd_block = ['kinit', '--no-addresses', '--password-file=%s' % (fd.name,), ad_ldap_binddn]
			p1 = subprocess.Popen(cmd_block, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
			stdout, stderr = p1.communicate()
		if p1.returncode != 0:
			raise kerberosAuthenticationFailed('The following command failed: "%s" (%s): %s' % (' '.join(cmd_block), p1.returncode, stdout.decode('UTF-8', 'replace')))

	lo_ad.lo.set_option(ldap.OPT_REFERRALS, 0)

	if configRegistry.is_true('connector/ad/ldap/kerberos'):
		os.environ['KRB5CCNAME'] = '/var/cache/univention-ad-connector/krb5.cc'
		get_kerberos_ticket(ad_ldap_bindpw, ad_ldap_binddn)
		auth = ldap.sasl.gssapi("")
		lo_ad = univention.uldap.access(host=ad_ldap_host, port=int(ad_ldap_port), base=ad_ldap_base, binddn=None, bindpw=ad_ldap_bindpw, start_tls=tls_mode, use_ldaps=ldaps, ca_certfile=ad_ldap_certificate)
		get_kerberos_ticket(ad_ldap_bindpw, ad_ldap_binddn)
		lo_ad.lo.sasl_interactive_bind_s("", auth)
	else:
		lo_ad = univention.uldap.access(host=ad_ldap_host, port=int(ad_ldap_port), base=ad_ldap_base, binddn=ad_ldap_binddn, bindpw=ad_ldap_bindpw, start_tls=tls_mode, use_ldaps=ldaps, ca_certfile=ad_ldap_certificate)

	if lo_ad.binddn:
		try:
			result = lo_ad.search(base=lo_ad.binddn, scope='base')
			ad_ldap_bind_username = result[0][1]['sAMAccountName'][0].decode('UTF-8')
		except ldap.LDAPError as msg:
			print("Failed to get SID from AD: %s" % msg)
	else:
		ad_ldap_bind_username = configRegistry.get('connector/ad/ldap/binddn')

	bindpw = lo_ad.bindpw

	lp = LoadParm()
	Net(creds=None, lp=lp)

	repl_creds = Credentials()
	repl_creds.guess(lp)
	repl_creds.set_kerberos_state(DONT_USE_KERBEROS)
	repl_creds.set_username(ad_ldap_bind_username)
	repl_creds.set_password(bindpw)

	# binding_options = "seal,print"
	drs, drsuapi_handle, bind_supported_extensions = drs_utils.drsuapi_connect(ad_ldap_host, lp, repl_creds)

	dcinfo = drsuapi.DsGetDCInfoRequest1()
	dcinfo.level = 1
	ad_netbios_domainname = configRegistry.get('connector/ad/netbiosdomainname', None)
	if not ad_netbios_domainname:
		lp = LoadParm()
		net = Net(creds=None, lp=lp)
		try:
			cldap_res = net.finddc(address=ad_ldap_host, flags=nbt.NBT_SERVER_LDAP | nbt.NBT_SERVER_DS | nbt.NBT_SERVER_WRITABLE)
			ad_netbios_domainname = cldap_res.domain_name
		except RuntimeError:
			raise
	if not ad_netbios_domainname:
		raise netbiosDomainnameNotFound('Failed to find Netbios domain name from AD server. Please configure it manually: "ucr set connector/ad/netbiosdomainname=<AD NetBIOS Domainname>"')
	dcinfo.domain_name = ad_netbios_domainname

	i, o = drs.DsGetDomainControllerInfo(drsuapi_handle, 1, dcinfo)
	computer_dn = o.array[0].computer_dn

	req = drsuapi.DsNameRequest1()
	names = drsuapi.DsNameString()
	names.str = computer_dn
	req.format_offered = drsuapi.DRSUAPI_DS_NAME_FORMAT_FQDN_1779
	req.format_desired = drsuapi.DRSUAPI_DS_NAME_FORMAT_GUID
	req.count = 1
	req.names = [names]
	i, o = drs.DsCrackNames(drsuapi_handle, 1, req)
	source_dsa_guid = o.array[0].result_name
	computer_guid = source_dsa_guid.replace('{', '').replace('}', '').encode('utf8')

	return (drs, drsuapi_handle, computer_guid)


def get_ad_password(computer_guid, dn, drs, drsuapi_handle):

	req8 = drsuapi.DsGetNCChangesRequest8()
	req8.destination_dsa_guid = misc.GUID(computer_guid)
	req8.source_dsa_invocation_id = misc.GUID(computer_guid)
	req8.naming_context = drsuapi.DsReplicaObjectIdentifier()
	req8.naming_context.dn = dn
	req8.replica_flags = 0
	req8.max_object_count = 402
	req8.max_ndr_size = 402116
	req8.extended_op = drsuapi.DRSUAPI_EXOP_REPL_SECRET
	req8.fsmo_info = 0

	def _decrypt_supplementalCredentials(user_session_key, spl_crypt):
		assert len(spl_crypt) >= 20

		confounder = spl_crypt[0:16]
		enc_buffer = spl_crypt[16:]

		m5 = hashlib.md5()
		m5.update(user_session_key)
		m5.update(confounder)
		enc_key = m5.digest()

		rc4 = Crypto.Cipher.ARC4.new(enc_key)
		plain_buffer = rc4.decrypt(enc_buffer)

		(crc32_v) = struct.unpack("<L", plain_buffer[0:4])
		attr_val = plain_buffer[4:]
		crc32_c = binascii.crc32(attr_val) & 0xffffffff
		assert int(crc32_v[0]) == int(crc32_c), "CRC32 0x%08X != 0x%08X" % (crc32_v[0], crc32_c)
		return ndr_unpack(drsblobs.supplementalCredentialsBlob, attr_val)

	while True:
		(level, ctr) = drs.DsGetNCChanges(drsuapi_handle, 8, req8)
		rid = None
		unicode_blob = None
		history_blob = None
		keys = []
		if ctr.first_object is None:
			break

		for i in ctr.first_object.object.attribute_ctr.attributes:
			if i.attid == 589970:
				# DRSUAPI_ATTID_objectSid
				if i.value_ctr.values:
					for j in i.value_ctr.values:
						sid = ndr_unpack(security.dom_sid, j.blob)
						_tmp, rid = sid.split()
			if i.attid == 589914:
				# DRSUAPI_ATTID_unicodePwd
				if i.value_ctr.values:
					for j in i.value_ctr.values:
						unicode_blob = j.blob
			if i.attid == drsuapi.DRSUAPI_ATTID_ntPwdHistory:
				if i.value_ctr.values:
					for j in i.value_ctr.values:
						history_blob = j.blob
			if i.attid == drsuapi.DRSUAPI_ATTID_supplementalCredentials and configRegistry.is_true('connector/ad/mapping/user/password/kerberos/enabled', False):
				if i.value_ctr.values:
					for j in i.value_ctr.values:
						spl = _decrypt_supplementalCredentials(drs.user_session_key, j.blob)
						keys = calculate_krb5keys(spl)

		if rid and unicode_blob:
			nt_hash = decrypt(drs.user_session_key, unicode_blob, rid).upper()

		if rid and history_blob:
			nt_hashes = decrypt_history(drs.user_session_key, history_blob, rid)

		if ctr.more_data == 0:
			break

	return nt_hash, keys, nt_hashes


def create_ad_user(username, password, **kwargs):
	#  use samba-tool
	host = configRegistry.get("connector/ad/ldap/host")
	admin = ldap.dn.explode_rdn(configRegistry.get("connector/ad/ldap/binddn"), notypes=True)[0]
	passw = open(configRegistry.get("connector/ad/ldap/bindpw"), 'r').read()
	cmd = ["samba-tool", "user", "create", "--use-username-as-cn", username.decode('UTF-8'), password, "--URL=ldap://%s" % host, "-U'%s'%%'%s'" % (admin, passw)]

	print(" ".join(cmd))
	child = subprocess.Popen(" ".join(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	(stdout, stderr) = child.communicate()
	stdout, stderr = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')

	if child.returncode:
		raise ADCreateUser_Exception({'module': 'users/user', 'kwargs': kwargs, 'returncode': child.returncode, 'stdout': stdout, 'stderr': stderr})

	new_position = 'cn=users,%s' % configRegistry.get('connector/ad/ldap/base')
	con_user_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(tcommon.to_unicode(username)), new_position)

	udm_user_dn = ldap.dn.dn2str([
		[("uid", to_unicode(username), ldap.AVA_STRING)],
		[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(configRegistry.get('ldap/base')))
	adconnector.wait_for_sync()
	return (con_user_dn, udm_user_dn)


def modify_password_ad(username, password):
	host = configRegistry.get("connector/ad/ldap/host")
	admin = ldap.dn.explode_rdn(configRegistry.get("connector/ad/ldap/binddn"), notypes=True)[0]
	passw = open(configRegistry.get("connector/ad/ldap/bindpw"), 'r').read()
	cmd = ["samba-tool", "user", "setpassword", "--newpassword='%s'" % password, username.decode('UTF-8'), "--URL=ldap://%s" % host, "-U'%s'%%'%s'" % (admin, passw)]

	child = subprocess.Popen(" ".join(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	(stdout, stderr) = child.communicate()
	stdout, stderr = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')

	if child.returncode:
		raise ADSetPassword_Exception({'module': 'users/user', 'returncode': child.returncode, 'stdout': stdout, 'stderr': stderr})

	adconnector.wait_for_sync()


def udm_modify(udm, **kwargs):
	udm._cleanup.setdefault('users/user', []).append(kwargs['dn'])
	udm.modify_object(modulename='users/user', **kwargs)
	adconnector.wait_for_sync()


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_initial_AD_pwd_is_synced():
	with connector_setup("sync"), UCSTestUDM() as udm:
		(ad_user_dn, udm_user_dn) = create_ad_user(tstrings.random_username().encode('UTF-8'), "Univention.2-")

		drs, drs_handle, computer_guid = open_drs_connection()
		nt_hash, keys, nt_hist = get_ad_password(computer_guid, ad_user_dn, drs, drs_handle)
		ucs_result = udm._lo.search(base=udm_user_dn, attr=['sambaNTPassword', 'pwhistory'])[0][1]
		print("- Check udm and ad nt_hash.")
		assert ucs_result["sambaNTPassword"][0] == nt_hash, "UDM sambaNTPassword and AD nt_hash should be equal"
		print("Ok")
		print("- Check udm and ad pwd history.")
		pwhist = ucs_result["pwhistory"][0].decode('ASCII').strip().split(" ")
		assert len(nt_hist) == len(pwhist), "AD and UCS password histories have a different number of entries. Check PwdHistoryLength configuration."
		assert nt_hist[0].decode('ASCII') == pwhist[-1][len("{NT}$"):], "Error verifying last AD and UDM password entry"
		print("Ok")
		delete_con_user(AD, ad_user_dn, udm_user_dn, adconnector.wait_for_sync)


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_initial_UCS_pwd_is_synced():
	with connector_setup("sync"), UCSTestUDM() as udm:
		udm_user = NormalUser()
		(udm_user_dn, ad_user_dn) = create_udm_user(udm, AD, udm_user, adconnector.wait_for_sync)

		drs, drs_handle, computer_guid = open_drs_connection()
		nt_hash, keys, nt_hist = get_ad_password(computer_guid, ad_user_dn, drs, drs_handle)
		ucs_result = udm._lo.search(base=udm_user_dn, attr=['sambaNTPassword', 'pwhistory'])[0][1]
		print("- Check udm and ad nt_hash.")
		assert ucs_result["sambaNTPassword"][0] == nt_hash, "UDM sambaNTPassword and AD nt_hash should be equal"
		print("Ok")
		print("- Check udm and ad pwd history.")
		pwhist = ucs_result["pwhistory"][0].decode('ASCII').strip().split(" ")
		assert len(nt_hist) == len(pwhist), "AD and UCS password histories have a different number of entries. Check PwdHistoryLength configuration."
		assert nt_hist[0] == ucs_result["sambaNTPassword"][0], "Error verifying last AD and UDM password entry"
		print("Ok")


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_create_user_in_AD_set_same_pwd_in_UDM():
	with connector_setup("sync"), UCSTestUDM() as udm:
		(ad_user_dn, udm_user_dn) = create_ad_user(tstrings.random_username().encode('UTF-8'), "Univention.2-")

		print("- Try to set original AD password in UDM. (Should Raise)")
		with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
			udm_modify(udm, dn=udm_user_dn, password="Univention.2-")
		print("Ok")
		drs, drs_handle, computer_guid = open_drs_connection()
		nt_hash, keys, nt_hist = get_ad_password(computer_guid, ad_user_dn, drs, drs_handle)
		ucs_result = udm._lo.search(base=udm_user_dn, attr=['sambaNTPassword', 'pwhistory'])[0][1]
		print("- Check udm and ad nt_hash.")
		assert ucs_result["sambaNTPassword"][0] == nt_hash, "UDM sambaNTPassword and AD nt_hash should be equal"
		print("Ok")
		print("- Check udm and ad pwd history.")
		pwhist = ucs_result["pwhistory"][0].decode('ASCII').strip().split(" ")
		assert len(nt_hist) == len(pwhist), "AD and UCS password histories have a different number of entries. Check PwdHistoryLength configuration."
		assert nt_hist[0].decode('ASCII') == pwhist[-1][len("{NT}$"):], "Error verifying last AD and UDM password entry"
		print("Ok")
		delete_con_user(AD, ad_user_dn, udm_user_dn, adconnector.wait_for_sync)


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_set_already_used_password_set_in_AD():
	with connector_setup("sync"), UCSTestUDM() as udm:
		udm_user = NormalUser()
		(udm_user_dn, ad_user_dn) = create_udm_user(udm, AD, udm_user, adconnector.wait_for_sync)

		print("- Set password in AD.")
		modify_password_ad(ldap.dn.explode_rdn(ad_user_dn, notypes=True)[0].encode('UTF-8'), "Njkxsa12.qad")
		print("Ok")
		print("- Set the same password in UCS. (Should Raise)")
		with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
			udm_modify(udm, dn=udm_user_dn, password="Njkxsa12.qad")
		print("Ok")
		drs, drs_handle, computer_guid = open_drs_connection()
		nt_hash, keys, nt_hist = get_ad_password(computer_guid, ad_user_dn, drs, drs_handle)
		ucs_result = udm._lo.search(base=udm_user_dn, attr=['sambaNTPassword', 'pwhistory'])[0][1]
		print("- Check udm and ad nt_hash.")
		assert ucs_result["sambaNTPassword"][0] == nt_hash, "UDM sambaNTPassword and AD nt_hash should be equal"
		print("Ok")
		print("- Check udm and ad pwd history.")
		pwhist = ucs_result["pwhistory"][0].decode('ASCII').strip().split(" ")
		assert len(nt_hist) == len(pwhist), "AD and UCS password histories have a different number of entries. Check PwdHistoryLength configuration."
		assert nt_hist[0].decode('ASCII') == pwhist[-1][len("{NT}$"):], "Error verifying last AD and UDM password entry"
		print("Ok")
