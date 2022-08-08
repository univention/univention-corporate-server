#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  control the password sync communication with the ad password service
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2022 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

import ldap
import univention.debug2 as ud
import univention.connector.ad

import hashlib
import binascii
import time

from Crypto.Cipher import DES, ARC4
import Crypto
from samba.dcerpc import drsuapi, lsa, misc, security, drsblobs
from samba.ndr import ndr_unpack
from samba import NTSTATUSError
from struct import pack
import struct
import traceback
import samba.dcerpc.samr
import heimdal


def nt_password_to_arcfour_hmac_md5(nt_password):
	# all arcfour-hmac-md5 keys begin this way
	key = b'0\x1d\xa1\x1b0\x19\xa0\x03\x02\x01\x17\xa1\x12\x04\x10'

	for i in range(0, 16):
		o = nt_password[2 * i:2 * i + 2]
		key += chr(int(o, 16)).encode('ISO8859-1')
	return key


def transformKey(InputKey):
	# Section 5.1.3
	InputKey = list(InputKey)
	OutputKey = []
	OutputKey.append(chr(InputKey[0] >> 0x01))
	OutputKey.append(chr(((InputKey[0] & 0x01) << 6) | (InputKey[1] >> 2)))
	OutputKey.append(chr(((InputKey[1] & 0x03) << 5) | (InputKey[2] >> 3)))
	OutputKey.append(chr(((InputKey[2] & 0x07) << 4) | (InputKey[3] >> 4)))
	OutputKey.append(chr(((InputKey[3] & 0x0F) << 3) | (InputKey[4] >> 5)))
	OutputKey.append(chr(((InputKey[4] & 0x1F) << 2) | (InputKey[5] >> 6)))
	OutputKey.append(chr(((InputKey[5] & 0x3F) << 1) | (InputKey[6] >> 7)))
	OutputKey.append(chr(InputKey[6] & 0x7F))
	for i in range(8):
		OutputKey[i] = chr((ord(OutputKey[i]) << 1) & 0xfe)
	return "".join(OutputKey).encode('ISO8859-1')


def mySamEncryptNTLMHash(hash, key):
	# [MS-SAMR] Section 2.2.11.1.1
	Block1 = hash[:8]
	Block2 = hash[8:]
	Key1 = key[:7]
	Key1 = transformKey(Key1)
	Key2 = key[7:14]
	Key2 = transformKey(Key2)
	Crypt1 = DES.new(Key1, DES.MODE_ECB)
	Crypt2 = DES.new(Key2, DES.MODE_ECB)
	plain1 = Crypt1.encrypt(Block1)
	plain2 = Crypt2.encrypt(Block2)
	return plain1 + plain2


def deriveKey(baseKey):
	# 2.2.11.1.3 Deriving Key1 and Key2 from a Little-Endian, Unsigned Integer Key
	# Let I be the little-endian, unsigned integer.
	# Let I[X] be the Xth byte of I, where I is interpreted as a zero-base-index array of bytes.
	# Note that because I is in little-endian byte order, I[0] is the least significant byte.
	# Key1 is a concatenation of the following values: I[0], I[1], I[2], I[3], I[0], I[1], I[2].
	# Key2 is a concatenation of the following values: I[3], I[0], I[1], I[2], I[3], I[0], I[1]
	key = pack('<L', baseKey)
	key1 = (key[0], key[1], key[2], key[3], key[0], key[1], key[2])
	key2 = (key[3], key[0], key[1], key[2], key[3], key[0], key[1])
	return transformKey(key1), transformKey(key2)


def removeDESLayer(cryptedHash, rid):
	Key1, Key2 = deriveKey(rid)
	Crypt1 = DES.new(Key1, DES.MODE_ECB)
	Crypt2 = DES.new(Key2, DES.MODE_ECB)
	decryptedHash = Crypt1.decrypt(cryptedHash[:8]) + Crypt2.decrypt(cryptedHash[8:])
	return decryptedHash


def decrypt(key, data, rid):
	salt = data[0:16]
	# check_sum = data[16:]
	md5 = hashlib.new('md5')
	md5.update(key)
	md5.update(salt)
	finalMD5 = md5.digest()
	cipher = ARC4.new(finalMD5)
	plainText = cipher.decrypt(data[16:])
	hash = removeDESLayer(plainText[4:], rid)
	return binascii.hexlify(hash)


def calculate_krb5keys(supplementalCredentialsblob):
	spl = supplementalCredentialsblob
	#cleartext_hex = None
	keys = []
	keytypes = []
	kvno = 0
	context = heimdal.context()
#	for i in range(0, spl.sub.num_packages):
#		pkg = spl.sub.packages[i]
#		if pkg.name != "Primary:CLEARTEXT":
#			continue
#		cleartext_hex = pkg.data

	krb5_old_hex = None

	for i in range(0, spl.sub.num_packages):
		pkg = spl.sub.packages[i]
		if pkg.name != "Primary:Kerberos":
			continue
		krb5_old_hex = pkg.data

	if krb5_old_hex is not None:
		krb5_old_raw = binascii.a2b_hex(krb5_old_hex)
		krb5_old = ndr_unpack(drsblobs.package_PrimaryKerberosBlob, krb5_old_raw, allow_remaining=True)
		assert krb5_old.version == 3
		for k in krb5_old.ctr.keys:
			if k.keytype not in keytypes:
				ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: ctr3.key.keytype: %s" % k.keytype)
				try:
					key = heimdal.keyblock_raw(context, k.keytype, k.value)
					krb5SaltObject = heimdal.salt_raw(context, krb5_old.ctr.salt.string)
					keys.append(heimdal.asn1_encode_key(key, krb5SaltObject, kvno))
					keytypes.append(k.keytype)
				except Exception:
					if k.keytype == 4294967156:  # in all known cases W2k8 AD uses keytype 4294967156 (=-140L) for this
						ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: ignoring unknown key with special keytype %s in %s" % (k.keytype, pkg.name))
					else:
						ud.debug(ud.LDAP, ud.ERROR, "calculate_krb5key: krb5Key with keytype %s could not be parsed in %s. Ignoring this keytype." % (k.keytype, pkg.name))
						ud.debug(ud.LDAP, ud.ERROR, traceback.format_exc())

	krb5_new_hex = None

	for i in range(0, spl.sub.num_packages):
		pkg = spl.sub.packages[i]
		if pkg.name != "Primary:Kerberos-Newer-Keys":
			continue
		krb5_new_hex = pkg.data

	if krb5_new_hex is not None:
		krb_blob = binascii.unhexlify(krb5_new_hex)
		krb = ndr_unpack(drsblobs.package_PrimaryKerberosBlob, krb_blob)
		assert krb.version == 4

		for k in krb.ctr.keys:
			if k.keytype not in keytypes:
				ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: ctr4.key.keytype: %s" % k.keytype)
				try:
					key = heimdal.keyblock_raw(context, k.keytype, k.value)
					krb5SaltObject = heimdal.salt_raw(context, krb.ctr.salt.string)
					keys.append(heimdal.asn1_encode_key(key, krb5SaltObject, kvno))
					keytypes.append(k.keytype)
				except Exception:
					if k.keytype == 4294967156:  # in all known cases W2k8 AD uses keytype 4294967156 (=-140L) for this
						ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: ignoring unknown key with special keytype %s in %s" % (k.keytype, pkg.name))
					else:
						ud.debug(ud.LDAP, ud.ERROR, "calculate_krb5key: krb5Key with keytype %s could not be parsed in %s. Ignoring this keytype." % (k.keytype, pkg.name))
						ud.debug(ud.LDAP, ud.ERROR, traceback.format_exc())
	return keys


def set_password_in_ad(connector, samaccountname, pwd, reconnect=False):

	# print "Static Session Key: %s" % (samr.session_key,)

	if reconnect:
		if connector.dom_handle:
			connector.samr.Close(connector.dom_handle)
		connector.samr = None

	if not connector.samr:
		connector.open_samr()

	user_handle = None
	info = None
	try:
		sam_accountname = lsa.String()
		sam_accountname.string = samaccountname
		(rids, types) = connector.samr.LookupNames(connector.dom_handle, [sam_accountname, ])

		rid = rids.ids[0]
		user_handle = connector.samr.OpenUser(connector.dom_handle, security.SEC_FLAG_MAXIMUM_ALLOWED, rid)

		userinfo18 = samba.dcerpc.samr.UserInfo18()
		bin_hash = binascii.a2b_hex(pwd)
		enc_hash = mySamEncryptNTLMHash(bin_hash, connector.samr.session_key)

		samr_Password = samba.dcerpc.samr.Password()
		samr_Password.hash = list(enc_hash)

		userinfo18.nt_pwd = samr_Password
		userinfo18.nt_pwd_active = 1
		userinfo18.password_expired = 0
		info = connector.samr.SetUserInfo(user_handle, 18, userinfo18)
	finally:
		if user_handle:
			connector.samr.Close(user_handle)

	return info


def decrypt_supplementalCredentials(connector, spl_crypt):
	assert len(spl_crypt) >= 20

	confounder = spl_crypt[0:16]
	enc_buffer = spl_crypt[16:]

	m5 = hashlib.md5()
	m5.update(connector.drs.user_session_key)
	m5.update(confounder)
	enc_key = m5.digest()

	rc4 = Crypto.Cipher.ARC4.new(enc_key)
	plain_buffer = rc4.decrypt(enc_buffer)

	(crc32_v) = struct.unpack("<L", plain_buffer[0:4])
	attr_val = plain_buffer[4:]
	crc32_c = binascii.crc32(attr_val) & 0xffffffff
	assert int(crc32_v[0]) == int(crc32_c), "CRC32 0x%08X != 0x%08X" % (crc32_v[0], crc32_c)

	return ndr_unpack(drsblobs.supplementalCredentialsBlob, attr_val)


def get_password_from_ad(connector, user_dn, reconnect=False):
	ud.debug(ud.LDAP, ud.INFO, "get_password_from_ad: Read password from AD: %s" % user_dn)
	nt_hash = None

	if not connector.drs or reconnect:
		connector.open_drs_connection()

	req8 = drsuapi.DsGetNCChangesRequest8()
	req8.destination_dsa_guid = misc.GUID(connector.computer_guid)
	req8.source_dsa_invocation_id = misc.GUID(connector.computer_guid)
	req8.naming_context = drsuapi.DsReplicaObjectIdentifier()
	req8.naming_context.dn = user_dn
	req8.replica_flags = 0
	req8.max_object_count = 402
	req8.max_ndr_size = 402116
	req8.extended_op = drsuapi.DRSUAPI_EXOP_REPL_SECRET
	req8.fsmo_info = 0

	while True:
		(level, ctr) = connector.drs.DsGetNCChanges(connector.drsuapi_handle, 8, req8)
		rid = None
		unicode_blob = None
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
						ud.debug(ud.LDAP, ud.INFO, "get_password_from_ad: Found unicodePwd blob")
			if i.attid == drsuapi.DRSUAPI_ATTID_supplementalCredentials and connector.configRegistry.is_true('%s/ad/mapping/user/password/kerberos/enabled' % connector.CONFIGBASENAME, False):
				if i.value_ctr.values:
					for j in i.value_ctr.values:
						ud.debug(ud.LDAP, ud.INFO, "get_password_from_ad: Found supplementalCredentials blob")
						spl = decrypt_supplementalCredentials(connector, j.blob)
						keys = calculate_krb5keys(spl)

		if rid and unicode_blob:
			nt_hash = decrypt(connector.drs.user_session_key, unicode_blob, rid).upper()

		if ctr.more_data == 0:
			break

	ud.debug(ud.LDAP, ud.INFO, "get_password_from_ad: AD Hash: %s" % nt_hash)

	return nt_hash, keys


def password_sync_ucs(connector, key, object):
	# externes Programm zum Überptragen des Hash aufrufen
	# per ldapmodify pwdlastset auf -1 setzen

	ud.debug(ud.LDAP, ud.INFO, "Object DN=%r" % (object['dn'],))

	ucs_object = connector._object_mapping(key, object, 'con')

	ud.debug(ud.LDAP, ud.INFO, "   UCS DN = %r" % (ucs_object['dn'],))

	try:
		res = connector.lo.lo.search(base=ucs_object['dn'], scope='base', attr=['sambaLMPassword', 'sambaNTPassword', 'sambaPwdLastSet'])
	except ldap.NO_SUCH_OBJECT:
		ud.debug(ud.LDAP, ud.PROCESS, "password_sync_ucs: The UCS object (%s) was not found. The object was removed." % ucs_object['dn'])
		return

	sambaPwdLastSet = None
	if 'sambaPwdLastSet' in res[0][1]:
		sambaPwdLastSet = int(res[0][1]['sambaPwdLastSet'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: sambaPwdLastSet: %s" % sambaPwdLastSet)

	pwd = None
	if 'sambaNTPassword' in res[0][1]:
		pwd = res[0][1]['sambaNTPassword'][0]
	else:
		ud.debug(ud.LDAP, ud.WARN, "password_sync_ucs: Failed to get NT Hash from UCS")

	res = connector.lo_ad.lo.search_s(object['dn'], ldap.SCOPE_BASE, '(objectClass=*)', ['pwdLastSet', 'objectSid'])
	pwdLastSet = None
	if 'pwdLastSet' in res[0][1]:
		pwdLastSet = int(res[0][1]['pwdLastSet'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: pwdLastSet from AD : %s" % pwdLastSet)
	if 'objectSid' in res[0][1]:
		str(univention.connector.ad.decode_sid(res[0][1]['objectSid'][0]).split('-')[-1])

	# Only sync passwords from UCS to AD when the password timestamp in UCS is newer
	if connector.configRegistry.is_true('%s/ad/password/timestamp/check' % connector.CONFIGBASENAME, False):
		ad_password_last_set = 0
		# If sambaPwdLast was set to 1 the password must be changed on next login. In this
		# case the timestamp is ignored and the password will be synced. This behavior can
		# be disabled by setting connector/ad/password/timestamp/syncreset/ucs to false. This
		# might be necessary if the connector is configured in read mode and the password will be
		# synced in two ways: Bug #22653
		if sambaPwdLastSet > 1 or (sambaPwdLastSet <= 2 and connector.configRegistry.is_false('%s/ad/password/timestamp/syncreset/ucs' % connector.CONFIGBASENAME, False)):
			ad_password_last_set = univention.connector.ad.ad2samba_time(pwdLastSet)
			if sambaPwdLastSet:
				if int(ad_password_last_set) >= int(sambaPwdLastSet):
					# skip
					ud.debug(ud.LDAP, ud.PROCESS, "password_sync: Don't sync the password from UCS to AD because the AD password equal or is newer.")
					ud.debug(ud.LDAP, ud.INFO, "password_sync:  AD pwdlastset: %s (original (%s))" % (ad_password_last_set, pwdLastSet))
					ud.debug(ud.LDAP, ud.INFO, "password_sync: UCS pwdlastset: %s" % (sambaPwdLastSet))
					return

		ud.debug(ud.LDAP, ud.INFO, "password_sync: Sync the passwords from UCS to AD.")
		ud.debug(ud.LDAP, ud.INFO, "password_sync:  AD pwdlastset: %s (original (%s))" % (ad_password_last_set, pwdLastSet))
		ud.debug(ud.LDAP, ud.INFO, "password_sync: UCS pwdlastset: %s" % (sambaPwdLastSet))

	pwd_set = False
	try:
		nt_hash, krb5Key = get_password_from_ad(connector, object['dn'])
	except NTSTATUSError as exc:
		ud.debug(ud.LDAP, ud.PROCESS, "password_sync_ucs: get_password_from_ad failed with %s, retry with reconnect" % (exc,))
		nt_hash, krb5Key = get_password_from_ad(connector, object['dn'], reconnect=True)

	if not nt_hash:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: No password hash could be read from AD")
	res = ''

	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: Hash AD: %s Hash UCS: %s" % (nt_hash, pwd))
	if not pwd or pwd.startswith(b'NO PASSWORD'):
		# There are variations of "NO PASSWORD" in customer environments:
		# 1. "NO PASSWORD*********************" (password_sync_kinit, see below)
		# 2. "NO PASSWORDXXXXXX"                (old AD-Connector password service?)
		# 3. "NO PASSWORDXXXXXXX"               (Ticket #2020121821000706)
		# 4. "NO PASSWORDXXXXXXXXXXXXXXXXXXXXX" (/usr/share/univention-heimdal/kerberos_now)
		# see https://forge.univention.org/bugzilla/buglist.cgi?longdesc=NO%20PASSWORD&longdesc_type=casesubstring
		ud.debug(ud.LDAP, ud.PROCESS, "The sambaNTPassword hash is set to %s. Skip the synchronisation of this hash to AD." % pwd)
	elif pwd != nt_hash:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: Hash AD and Hash UCS differ")
		pwd_set = True

		try:
			res = set_password_in_ad(connector, object['attributes']['sAMAccountName'][0], pwd)
		except NTSTATUSError as exc:
			ud.debug(ud.LDAP, ud.PROCESS, "password_sync: set_password_in_ad failed with %s, retry with reconnect" % (exc,))
			res = set_password_in_ad(connector, object['attributes']['sAMAccountName'][0], pwd, reconnect=True)

	newpwdlastset = "-1"  # if pwd was set in ad we need to set pwdlastset to -1 or it will be 0
	# if sambaPwdMustChange >= 0 and sambaPwdMustChange < time.time():
	# password expired, must be changed on next login
	#	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: samba pwd expired, set newpwdLastSet to 0")
	#	newpwdlastset = "0"
	if sambaPwdLastSet <= 1:
		newpwdlastset = "0"  # User must change his password
	elif pwdLastSet and int(pwdLastSet) > 0 and not pwd_set:
		newpwdlastset = "1"
	if int(newpwdlastset) != 1:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: pwdlastset in modlist: %s" % newpwdlastset)
		connector.lo_ad.lo.modify_s(object['dn'], [(ldap.MOD_REPLACE, 'pwdlastset', newpwdlastset.encode('ASCII'))])
	else:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: don't modify pwdlastset")


def password_sync_kinit(connector, key, ucs_object):

	connector._object_mapping(key, ucs_object, 'ucs')

	attr = {'userPassword': b'{KINIT}', 'sambaNTPassword': b'NO PASSWORD*********************', 'sambaLMPassword': b'NO PASSWORD*********************'}

	ucs_result = connector.lo.search(base=ucs_object['dn'], attr=attr.keys())

	modlist = []
	for attribute in attr.keys():
		expected_value = attr[attribute]
		if attribute in ucs_result[0][1]:
			userPassword = ucs_result[0][1][attribute][0]
			if userPassword != expected_value:
				modlist.append((ldap.MOD_REPLACE, attribute, expected_value))

	if modlist:
		connector.lo.lo.modify_s(ucs_object['dn'], modlist)


def password_sync(connector, key, ucs_object):
	# externes Programm zum holen des Hash aufrufen
	# "kerberos_now"

	object = connector._object_mapping(key, ucs_object, 'ucs')
	res = connector.lo_ad.lo.search_s(object['dn'], ldap.SCOPE_BASE, '(objectClass=*)', ['objectSid', 'pwdLastSet'])

	if connector.isInCreationList(object['dn']):
		connector.removeFromCreationList(object['dn'])
		ud.debug(ud.LDAP, ud.INFO, "password_sync: Synchronisation of password has been canceled. Object was just created.")
		return

	pwdLastSet = None
	if 'pwdLastSet' in res[0][1]:
		pwdLastSet = int(res[0][1]['pwdLastSet'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync: pwdLastSet from AD: %s (%s)" % (pwdLastSet, res))

	if 'objectSid' in res[0][1]:
		str(univention.connector.ad.decode_sid(res[0][1]['objectSid'][0]).split('-')[-1])

	ucs_result = connector.lo.search(base=ucs_object['dn'], attr=['sambaPwdLastSet', 'sambaNTPassword', 'krb5PrincipalName', 'krb5Key', 'shadowLastChange', 'shadowMax', 'krb5PasswordEnd'])

	sambaPwdLastSet = None
	if 'sambaPwdLastSet' in ucs_result[0][1]:
		sambaPwdLastSet = ucs_result[0][1]['sambaPwdLastSet'][0]
	ud.debug(ud.LDAP, ud.INFO, "password_sync: sambaPwdLastSet: %s" % sambaPwdLastSet)

	if connector.configRegistry.is_true('%s/ad/password/timestamp/check' % connector.CONFIGBASENAME, False):
		# Only sync the passwords from AD to UCS when the pwdLastSet timestamps in AD are newer
		ad_password_last_set = 0

		# If pwdLastSet was set to 0 the password must be changed on next login. In this
		# case the timestamp is ignored and the password will be synced. This behavior can
		# be disabled by setting connector/ad/password/timestamp/syncreset/ad to false. This
		# might be necessary if the connector is configured in read mode and the password will be
		# synced in two ways: Bug #22653
		if (pwdLastSet > 1) or (pwdLastSet in [0, 1] and connector.configRegistry.is_false('%s/ad/password/timestamp/syncreset/ad' % connector.CONFIGBASENAME, False)):
			ad_password_last_set = univention.connector.ad.ad2samba_time(pwdLastSet)
			if sambaPwdLastSet:
				if int(sambaPwdLastSet) >= int(ad_password_last_set) and int(sambaPwdLastSet) != 1:
					# skip
					ud.debug(ud.LDAP, ud.PROCESS, "password_sync: Don't sync the passwords from AD to UCS because the UCS password is equal or newer.")
					ud.debug(ud.LDAP, ud.INFO, "password_sync:  AD pwdlastset: %s (original (%s))" % (ad_password_last_set, pwdLastSet))
					ud.debug(ud.LDAP, ud.INFO, "password_sync: UCS pwdlastset: %s" % (sambaPwdLastSet))
					return

		ud.debug(ud.LDAP, ud.INFO, "password_sync: Sync the passwords from AD to UCS.")
		ud.debug(ud.LDAP, ud.INFO, "password_sync:  AD pwdlastset: %s (original (%s))" % (ad_password_last_set, pwdLastSet))
		ud.debug(ud.LDAP, ud.INFO, "password_sync: UCS pwdlastset: %s" % (sambaPwdLastSet))

	try:
		nt_hash, krb5Key = get_password_from_ad(connector, object['dn'])
	except Exception as exc:
		ud.debug(ud.LDAP, ud.PROCESS, "password_sync: get_password_from_ad failed with %s, retry with reconnect" % (exc,))
		nt_hash, krb5Key = get_password_from_ad(connector, object['dn'], reconnect=True)

	old_krb5end = ucs_result[0][1].get('krb5PasswordEnd', [None])[0]
	old_shadowMax = ucs_result[0][1].get('shadowMax', [None])[0]
	old_shadowLastChange = ucs_result[0][1].get('shadowLastChange', [None])[0]
	modlist = []

	if nt_hash:
		ntPwd_ucs = b''
		krb5Principal = b''

		ntPwd = nt_hash

		if 'sambaNTPassword' in ucs_result[0][1]:
			ntPwd_ucs = ucs_result[0][1]['sambaNTPassword'][0]
		if 'krb5PrincipalName' in ucs_result[0][1]:
			krb5Principal = ucs_result[0][1]['krb5PrincipalName'][0]

		pwd_changed = False

		if ntPwd.upper() != ntPwd_ucs.upper():
			if ntPwd in [b'00000000000000000000000000000000', b'NO PASSWORD*********************']:
				ud.debug(ud.LDAP, ud.WARN, "password_sync: AD connector password daemon returned 0 for the nt hash. Please check the AD settings.")
			else:
				pwd_changed = True
				modlist.append(('sambaNTPassword', ntPwd_ucs, ntPwd.upper()))
				if krb5Principal:
					connector.lo.lo.modify_s(ucs_object['dn'], [(ldap.MOD_REPLACE, 'krb5Key', nt_password_to_arcfour_hmac_md5(ntPwd.upper()))])

		if pwd_changed:
			if krb5Key:
				krb5Key_ucs = ucs_result[0][1]['krb5Key'][0]
				modlist.append(('krb5Key', krb5Key_ucs, krb5Key))

			connector.lo.lo.modify_s(ucs_object['dn'], [(ldap.MOD_REPLACE, 'userPassword', b'{K5KEY}')])

			# update shadowLastChange
			new_shadowLastChange = str(int(time.time()) // 3600 // 24).encode('ASCII')
			if pwdLastSet != 0:
				modlist.append(('shadowLastChange', old_shadowLastChange, new_shadowLastChange))
				ud.debug(ud.LDAP, ud.INFO, "password_sync: update shadowLastChange to %s for %s" % (new_shadowLastChange, ucs_object['dn']))

			# get pw policy
			new_shadowMax = None
			new_krb5end = None
			policies = connector.lo.getPolicies(ucs_object['dn'])
			policy = policies.get('univentionPolicyPWHistory', {}).get('univentionPWExpiryInterval')
			if policy:
				ud.debug(ud.LDAP, ud.INFO, "password_sync: password expiry for %s is %s" % (ucs_object['dn'], policy))
				policy_value = policy.get('value', [None])[0]
				if policy_value:
					new_shadowMax = policy_value
					new_krb5end = time.strftime("%Y%m%d000000Z", time.gmtime((int(time.time()) + (int(policy_value) * 3600 * 24)))).encode('ASCII')

			# update shadowMax (set to value of univentionPWExpiryInterval, otherwise delete) and
			# krb5PasswordEnd (set to today + univentionPWExpiryInterval, otherwise delete)
			if (old_shadowMax or new_shadowMax) and (pwdLastSet != 0):
				ud.debug(ud.LDAP, ud.INFO, "password_sync: update shadowMax to %s for %s" % (new_shadowMax, ucs_object['dn']))
				modlist.append(('shadowMax', old_shadowMax, new_shadowMax))
			if (old_krb5end or new_krb5end) and (pwdLastSet != 0):
				ud.debug(ud.LDAP, ud.INFO, "password_sync: update krb5PasswordEnd to %s for %s" % (new_krb5end, ucs_object['dn']))
				modlist.append(('krb5PasswordEnd', old_krb5end, new_krb5end))
	else:
		ud.debug(ud.LDAP, ud.ERROR, "password_sync: sync failed, no result from AD")

	# update sambaPwdLastSet
	if pwdLastSet or pwdLastSet == 0:
		newSambaPwdLastSet = str(univention.connector.ad.ad2samba_time(pwdLastSet)).encode('ASCII')
		if sambaPwdLastSet:
			if sambaPwdLastSet != newSambaPwdLastSet:
				modlist.append(('sambaPwdLastSet', sambaPwdLastSet, newSambaPwdLastSet))
				ud.debug(ud.LDAP, ud.INFO, "password_sync: sambaPwdLastSet in modlist (replace): %s" % newSambaPwdLastSet)
		else:
			modlist.append(('sambaPwdLastSet', b'', newSambaPwdLastSet))
			ud.debug(ud.LDAP, ud.INFO, "password_sync: sambaPwdLastSet in modlist (set): %s" % newSambaPwdLastSet)
		if pwdLastSet == 0:
			expiry = int(time.time())
			new_krb5end = time.strftime("%Y%m%d000000Z", time.gmtime(expiry)).encode('ASCII')
			if old_krb5end:
				ud.debug(ud.LDAP, ud.INFO, "password_sync: krb5PasswordEnd in modlist (replace): %s" % new_krb5end)
				modlist.append(('krb5PasswordEnd', old_krb5end, new_krb5end))
			else:
				ud.debug(ud.LDAP, ud.INFO, "password_sync: krb5PasswordEnd in modlist (set): %s" % new_krb5end)
				modlist.append(('krb5PasswordEnd', b'', new_krb5end))
			if old_shadowMax:
				ud.debug(ud.LDAP, ud.INFO, "password_sync: shadowMax in modlist (replace): 0")
				modlist.append(('shadowMax', old_shadowMax, b'1'))
			else:
				ud.debug(ud.LDAP, ud.INFO, "password_sync: shadowMax in modlist (set): 0")
				modlist.append(('shadowMax', b'', b'1'))
			two_days_ago = int(time.time()) - (86400 * 2)
			new_shadowLastChange = str(two_days_ago // 3600 // 24).encode('ASCII')
			if old_shadowLastChange:
				ud.debug(ud.LDAP, ud.INFO, "password_sync: shadowLastChange in modlist (replace): %s" % new_shadowLastChange)
				modlist.append(('shadowLastChange', old_shadowLastChange, new_shadowLastChange))
			else:
				ud.debug(ud.LDAP, ud.INFO, "password_sync: shadowMax in modlist (set): %s" % new_shadowLastChange)
				modlist.append(('shadowLastChange', b'', new_shadowLastChange))

	if len(modlist) > 0:
		connector.lo.lo.modify(ucs_object['dn'], modlist)
