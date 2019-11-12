#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  control the password sync communication with the ad password service
#
# Copyright 2004-2019 Univention GmbH
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

from struct import pack
from Crypto.Cipher import DES, ARC4

from samba.dcerpc import drsuapi, lsa, misc, security
from samba.ndr import ndr_unpack
import samba.dcerpc.samr


def nt_password_to_arcfour_hmac_md5(nt_password):
	# all arcfour-hmac-md5 keys begin this way
	key = '0\x1d\xa1\x1b0\x19\xa0\x03\x02\x01\x17\xa1\x12\x04\x10'

	for i in range(0, 16):
		o = nt_password[2 * i:2 * i + 2]
		key += chr(int(o, 16))
	return key


def transformKey(InputKey):
	# Section 5.1.3
	OutputKey = []
	OutputKey.append(chr(ord(InputKey[0]) >> 0x01))
	OutputKey.append(chr(((ord(InputKey[0]) & 0x01) << 6) | (ord(InputKey[1]) >> 2)))
	OutputKey.append(chr(((ord(InputKey[1]) & 0x03) << 5) | (ord(InputKey[2]) >> 3)))
	OutputKey.append(chr(((ord(InputKey[2]) & 0x07) << 4) | (ord(InputKey[3]) >> 4)))
	OutputKey.append(chr(((ord(InputKey[3]) & 0x0F) << 3) | (ord(InputKey[4]) >> 5)))
	OutputKey.append(chr(((ord(InputKey[4]) & 0x1F) << 2) | (ord(InputKey[5]) >> 6)))
	OutputKey.append(chr(((ord(InputKey[5]) & 0x3F) << 1) | (ord(InputKey[6]) >> 7)))
	OutputKey.append(chr(ord(InputKey[6]) & 0x7F))
	for i in range(8):
		OutputKey[i] = chr((ord(OutputKey[i]) << 1) & 0xfe)
	return "".join(OutputKey)


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
	key1 = key[0] + key[1] + key[2] + key[3] + key[0] + key[1] + key[2]
	key2 = key[3] + key[0] + key[1] + key[2] + key[3] + key[0] + key[1]
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


def set_password_in_ad(connector, samaccountname, pwd):
	_d = ud.function('ldap.ad.set_password_in_ad')  # noqa: F841

	# print "Static Session Key: %s" % (samr.session_key,)
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
		samr_Password.hash = map(ord, enc_hash)

		userinfo18.nt_pwd = samr_Password
		userinfo18.nt_pwd_active = 1
		userinfo18.password_expired = 0
		info = connector.samr.SetUserInfo(user_handle, 18, userinfo18)
	finally:
		if user_handle:
			connector.samr.Close(user_handle)

	return info


def get_password_from_ad(connector, user_dn, reconnect=False):
	_d = ud.function('ldap.ad.get_password_from_ad')  # noqa: F841
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
		if ctr.first_object is None:
			break
		for i in ctr.first_object.object.attribute_ctr.attributes:
			if str(i.attid) == "589970":
				# DRSUAPI_ATTID_objectSid
				if i.value_ctr.values:
					for j in i.value_ctr.values:
						sid = ndr_unpack(security.dom_sid, j.blob)
						_tmp, rid = sid.split()
			if str(i.attid) == "589914":
				# DRSUAPI_ATTID_unicodePwd
				if i.value_ctr.values:
					for j in i.value_ctr.values:
						unicode_blob = j.blob
						ud.debug(ud.LDAP, ud.INFO, "get_password_from_ad: Found unicodePwd blob")
		if rid and unicode_blob:
			nt_hash = decrypt(connector.drs.user_session_key, unicode_blob, rid).upper()

		if ctr.more_data == 0:
			break

	ud.debug(ud.LDAP, ud.INFO, "get_password_from_ad: AD Hash: %s" % nt_hash)

	return nt_hash


def password_sync_ucs(connector, key, object):
	_d = ud.function('ldap.ad.password_sync_ucs')  # noqa: F841
	# externes Programm zum Überptragen des Hash aufrufen
	# per ldapmodify pwdlastset auf -1 setzen

	compatible_modstring = univention.connector.ad.compatible_modstring
	try:
		ud.debug(ud.LDAP, ud.INFO, "Object DN=%s" % object['dn'])
	except:  # FIXME: which exception is to be caught?
		ud.debug(ud.LDAP, ud.INFO, "Object DN not printable")

	ucs_object = connector._object_mapping(key, object, 'con')

	try:
		ud.debug(ud.LDAP, ud.INFO, "   UCS DN = %s" % ucs_object['dn'])
	except:  # FIXME: which exception is to be caught?
		ud.debug(ud.LDAP, ud.INFO, "   UCS DN not printable")

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
		pwd = 'NO PASSWORDXXXXXX'
		ud.debug(ud.LDAP, ud.WARN, "password_sync_ucs: Failed to get NT Hash from UCS")

	if pwd in ['NO PASSWORDXXXXXX', 'NO PASSWORD*********************']:
		ud.debug(ud.LDAP, ud.PROCESS, "The sambaNTPassword hash is set to %s. Skip the synchronisation of this hash to AD." % pwd)

	res = connector.lo_ad.lo.search_s(univention.connector.ad.compatible_modstring(object['dn']), ldap.SCOPE_BASE, '(objectClass=*)', ['pwdLastSet', 'objectSid'])
	pwdLastSet = None
	if 'pwdLastSet' in res[0][1]:
		pwdLastSet = int(res[0][1]['pwdLastSet'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: pwdLastSet from AD : %s" % pwdLastSet)
	if 'objectSid' in res[0][1]:
		str(univention.connector.ad.decode_sid(res[0][1]['objectSid'][0]).split('-')[-1])

	# Only sync passwords from UCS to AD when the password timestamp in UCS is newer
	if connector.baseConfig.is_true('%s/ad/password/timestamp/check' % connector.CONFIGBASENAME, False):
		ad_password_last_set = 0
		# If sambaPwdLast was set to 1 the password must be changed on next login. In this
		# case the timestamp is ignored and the password will be synced. This behavior can
		# be disabled by setting connector/ad/password/timestamp/syncreset/ucs to false. This
		# might be necessary if the connector is configured in read mode and the password will be
		# synced in two ways: Bug #22653
		if sambaPwdLastSet > 1 or (sambaPwdLastSet <= 2 and connector.baseConfig.is_false('%s/ad/password/timestamp/syncreset/ucs' % connector.CONFIGBASENAME, False)):
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
		pwd_ad = get_password_from_ad(connector, univention.connector.ad.compatible_modstring(object['dn']))
	except Exception as e:
		ud.debug(ud.LDAP, ud.PROCESS, "password_sync_ucs: get_password_from_ad failed with %s, retry with reconnect" % str(e))
		pwd_ad = get_password_from_ad(connector, univention.connector.ad.compatible_modstring(object['dn']), reconnect=True)

	if not pwd_ad:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: No password hash could be read from AD")
	res = ''

	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: Hash AD: %s Hash UCS: %s" % (pwd_ad, pwd))
	if not pwd == pwd_ad:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: Hash AD and Hash UCS differ")
		pwd_set = True
		res = set_password_in_ad(connector, object['attributes']['sAMAccountName'][0], pwd)

	if not pwd_set or pwd_ad:
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
			connector.lo_ad.lo.modify_s(compatible_modstring(object['dn']), [(ldap.MOD_REPLACE, 'pwdlastset', newpwdlastset)])
		else:
			ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: don't modify pwdlastset")


def password_sync_kinit(connector, key, ucs_object):
	_d = ud.function('ldap.ad.password_sync_kinit')  # noqa: F841

	connector._object_mapping(key, ucs_object, 'ucs')

	attr = {'userPassword': '{KINIT}', 'sambaNTPassword': 'NO PASSWORD*********************', 'sambaLMPassword': 'NO PASSWORD*********************'}

	ucs_result = connector.lo.search(base=ucs_object['dn'], attr=attr.keys())

	modlist = []
	for attribute in attr.keys():
		expected_value = attr[attribute]
		if attribute in ucs_result[0][1]:
			userPassword = ucs_result[0][1][attribute][0]
			if userPassword != expected_value:
				modlist.append((ldap.MOD_REPLACE, attribute, expected_value))

	if modlist:
		connector.lo.lo.modify_s(univention.connector.ad.compatible_modstring(ucs_object['dn']), modlist)


def password_sync(connector, key, ucs_object):
	_d = ud.function('ldap.ad.password_sync')  # noqa: F841
	# externes Programm zum holen des Hash aufrufen
	# "kerberos_now"

	object = connector._object_mapping(key, ucs_object, 'ucs')
	res = connector.lo_ad.lo.search_s(univention.connector.ad.compatible_modstring(object['dn']), ldap.SCOPE_BASE, '(objectClass=*)', ['objectSid', 'pwdLastSet'])

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

	ucs_result = connector.lo.search(base=ucs_object['dn'], attr=['sambaPwdLastSet', 'sambaNTPassword', 'krb5PrincipalName', 'shadowLastChange', 'shadowMax', 'krb5PasswordEnd'])

	sambaPwdLastSet = None
	if 'sambaPwdLastSet' in ucs_result[0][1]:
		sambaPwdLastSet = ucs_result[0][1]['sambaPwdLastSet'][0]
	ud.debug(ud.LDAP, ud.INFO, "password_sync: sambaPwdLastSet: %s" % sambaPwdLastSet)

	if connector.baseConfig.is_true('%s/ad/password/timestamp/check' % connector.CONFIGBASENAME, False):
		# Only sync the passwords from AD to UCS when the pwdLastSet timestamps in AD are newer
		ad_password_last_set = 0

		# If pwdLastSet was set to 0 the password must be changed on next login. In this
		# case the timestamp is ignored and the password will be synced. This behavior can
		# be disabled by setting connector/ad/password/timestamp/syncreset/ad to false. This
		# might be necessary if the connector is configured in read mode and the password will be
		# synced in two ways: Bug #22653
		if (pwdLastSet > 1) or (pwdLastSet in [0, 1] and connector.baseConfig.is_false('%s/ad/password/timestamp/syncreset/ad' % connector.CONFIGBASENAME, False)):
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
		res = get_password_from_ad(connector, univention.connector.ad.compatible_modstring(object['dn']))
	except Exception as e:
		ud.debug(ud.LDAP, ud.PROCESS, "password_sync: get_password_from_ad failed with %s, retry with reconnect" % str(e))
		res = get_password_from_ad(connector, univention.connector.ad.compatible_modstring(object['dn']), reconnect=True)

	if res:
		ntPwd_ucs = ''
		krb5Principal = ''

		ntPwd = res
		modlist = []

		if 'sambaNTPassword' in ucs_result[0][1]:
			ntPwd_ucs = ucs_result[0][1]['sambaNTPassword'][0]
		if 'krb5PrincipalName' in ucs_result[0][1]:
			krb5Principal = ucs_result[0][1]['krb5PrincipalName'][0]

		pwd_changed = False

		if ntPwd.upper() != ntPwd_ucs.upper():
			if ntPwd in ['00000000000000000000000000000000', 'NO PASSWORD*********************']:
				ud.debug(ud.LDAP, ud.WARN, "password_sync: AD connector password daemon returned 0 for the nt hash. Please check the AD settings.")
			else:
				pwd_changed = True
				modlist.append(('sambaNTPassword', ntPwd_ucs, str(ntPwd.upper())))
				if krb5Principal:
					connector.lo.lo.modify_s(univention.connector.ad.compatible_modstring(ucs_object['dn']), [(ldap.MOD_REPLACE, 'krb5Key', nt_password_to_arcfour_hmac_md5(ntPwd.upper()))])

		if pwd_changed:

			connector.lo.lo.modify_s(univention.connector.ad.compatible_modstring(ucs_object['dn']), [(ldap.MOD_REPLACE, 'userPassword', '{K5KEY}')])

			# update shadowLastChange
			old_shadowLastChange = ucs_result[0][1].get('shadowLastChange', [None])[0]
			new_shadowLastChange = str(int(time.time()) / 3600 / 24)
			modlist.append(('shadowLastChange', old_shadowLastChange, new_shadowLastChange))
			ud.debug(ud.LDAP, ud.INFO, "password_sync: update shadowLastChange to %s for %s" % (new_shadowLastChange, ucs_object['dn']))

			# get pw policy
			new_shadowMax = None
			new_krb5end = None
			old_shadowMax = ucs_result[0][1].get('shadowMax', [None])[0]
			old_krb5end = ucs_result[0][1].get('krb5PasswordEnd', [None])[0]
			policies = connector.lo.getPolicies(ucs_object['dn'])
			policy = policies.get('univentionPolicyPWHistory', {}).get('univentionPWExpiryInterval')
			if policy:
				ud.debug(ud.LDAP, ud.INFO, "password_sync: password expiry for %s is %s" % (ucs_object['dn'], policy))
				policy_value = policy.get('value', [None])[0]
				if policy_value:
					new_shadowMax = policy_value
					new_krb5end = time.strftime("%Y%m%d000000Z", time.gmtime((int(time.time()) + (int(policy_value) * 3600 * 24))))

			# update shadowMax (set to value of univentionPWExpiryInterval, otherwise delete) and
			# krb5PasswordEnd (set to today + univentionPWExpiryInterval, otherwise delete)
			if old_shadowMax or new_shadowMax:
				ud.debug(ud.LDAP, ud.INFO, "password_sync: update shadowMax to %s for %s" % (new_shadowMax, ucs_object['dn']))
				modlist.append(('shadowMax', old_shadowMax, new_shadowMax))
			if old_krb5end or new_krb5end:
				ud.debug(ud.LDAP, ud.INFO, "password_sync: update krb5PasswordEnd to %s for %s" % (new_krb5end, ucs_object['dn']))
				modlist.append(('krb5PasswordEnd', old_krb5end, new_krb5end))

			# update sambaPwdLastSet
			if pwdLastSet or pwdLastSet == 0:
				newSambaPwdLastSet = str(univention.connector.ad.ad2samba_time(pwdLastSet))
				if sambaPwdLastSet:
					if sambaPwdLastSet != newSambaPwdLastSet:
						modlist.append(('sambaPwdLastSet', sambaPwdLastSet, newSambaPwdLastSet))
						ud.debug(ud.LDAP, ud.INFO, "password_sync: sambaPwdLastSet in modlist (replace): %s" % newSambaPwdLastSet)
				else:
					modlist.append(('sambaPwdLastSet', '', newSambaPwdLastSet))
					ud.debug(ud.LDAP, ud.INFO, "password_sync: sambaPwdLastSet in modlist (set): %s" % newSambaPwdLastSet)

		if len(modlist) > 0:
			connector.lo.lo.modify(ucs_object['dn'], modlist)

	else:
		ud.debug(ud.LDAP, ud.ERROR, "password_sync: sync failed, no result from AD")
