#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  control the password sync communication with the s4 password service
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


import time
import ldap
import univention.debug2 as ud
import univention.s4connector.s4
from univention.s4connector.s4 import compatible_modstring
from univention.s4connector.s4 import format_escaped
import binascii

from samba.ndr import ndr_unpack, ndr_pack, ndr_print
from samba.dcerpc import drsblobs
import heimdal
from ldap.controls import LDAPControl
import traceback


class Krb5Context(object):
	def __init__(self):
		self.ctx = heimdal.context()
		self.etypes = self.ctx.get_permitted_enctypes()
		self.etype_ids = [et.toint() for et in self.etypes]


krb5_context = Krb5Context()


def calculate_krb5key(unicodePwd, supplementalCredentials, kvno=0):
	up_blob = unicodePwd
	sc_blob = supplementalCredentials

	keys = []
	keytypes = []
	context = heimdal.context()

	if up_blob:
		# ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: up_blob: %s" % binascii.b2a_base64(up_blob))
		assert len(up_blob) == 16
		key = heimdal.keyblock_raw(context, 23, up_blob)
		keys.append(heimdal.asn1_encode_key(key, None, kvno))

	if sc_blob:
		# ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: sc_blob: %s" % binascii.b2a_base64(sc_blob))
		try:
			sc = ndr_unpack(drsblobs.supplementalCredentialsBlob, sc_blob)
			for p in sc.sub.packages:
				krb = None
				ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: parsing %s blob" % p.name)
				if p.name == "Primary:Kerberos":
					krb_blob = binascii.unhexlify(p.data)
					krb = ndr_unpack(drsblobs.package_PrimaryKerberosBlob, krb_blob)
					assert krb.version == 3

					for k in krb.ctr.keys:
						if k.keytype not in keytypes:
							ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: ctr3.key.keytype: %s" % k.keytype)
							try:
								key = heimdal.keyblock_raw(context, k.keytype, k.value)
								krb5SaltObject = heimdal.salt_raw(context, krb.ctr.salt.string)
								keys.append(heimdal.asn1_encode_key(key, krb5SaltObject, kvno))
								keytypes.append(k.keytype)
							except:
								if k.keytype == 4294967156:  # in all known cases W2k8 AD uses keytype 4294967156 (=-140L) for this
									if k.value == up_blob:  # the known case
										ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: ignoring arc4 NThash with special keytype %s in %s" % (k.keytype, p.name))
									else:  # unknown special case
										ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: ignoring unknown key with special keytype %s in %s" % (k.keytype, p.name))
								else:
									traceback.print_exc()
									ud.debug(ud.LDAP, ud.ERROR, "calculate_krb5key: krb5Key with keytype %s could not be parsed in %s. Ignoring this keytype." % (k.keytype, p.name))

				elif p.name == "Primary:Kerberos-Newer-Keys":
					krb_blob = binascii.unhexlify(p.data)
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
							except:
								if k.keytype == 4294967156:  # in all known cases W2k8 AD uses keytype 4294967156 (=-140L) for this
									if k.value == up_blob:  # the known case
										ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: ignoring arc4 NThash with special keytype %s in %s" % (k.keytype, p.name))
									else:  # unknown special case
										ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: ignoring unknown key with special keytype %s in %s" % (k.keytype, p.name))
								else:
									traceback.print_exc()
									ud.debug(ud.LDAP, ud.ERROR, "calculate_krb5key: krb5Key with keytype %s could not be parsed in %s. Ignoring this keytype." % (k.keytype, p.name))

		except Exception:
			import sys
			exc = sys.exc_info()[1]
			if isinstance(exc.args, type(())) and len(exc.args) == 2 and exc.args[1] == 'Buffer Size Error':
				ud.debug(ud.LDAP, ud.WARN, "calculate_krb5key: '%s' while unpacking supplementalCredentials:: %s" % (exc, binascii.b2a_base64(sc_blob)))
				ud.debug(ud.LDAP, ud.WARN, "calculate_krb5key: the krb5Keys from the PrimaryKerberosBlob could not be parsed. Continuing anyway.")
			else:
				traceback.print_exc()
				ud.debug(ud.LDAP, ud.ERROR, "calculate_krb5key: the krb5Keys from the PrimaryKerberosBlob could not be parsed. Continuing anyway.")

	return keys


def calculate_supplementalCredentials(ucs_krb5key, old_supplementalCredentials):

	old_krb = {}
	if old_supplementalCredentials:
		sc = ndr_unpack(drsblobs.supplementalCredentialsBlob, old_supplementalCredentials)

		for p in sc.sub.packages:
			ud.debug(ud.LDAP, ud.INFO, "calculate_supplementalCredentials: parsing %s blob" % p.name)
			if p.name == "Primary:Kerberos":
				krb_blob = binascii.unhexlify(p.data)
				try:
					krb = ndr_unpack(drsblobs.package_PrimaryKerberosBlob, krb_blob)
					assert krb.version == 3
					old_krb['ctr3'] = krb.ctr
					for k in krb.ctr.keys:
						ud.debug(ud.LDAP, ud.INFO, "calculate_supplementalCredentials: ctr3.key.keytype: %s" % k.keytype)
				except:
					ud.debug(ud.LDAP, ud.ERROR, "calculate_supplementalCredentials: ndr_unpack of S4 Primary:Kerberos blob failed. Traceback:")
					traceback.print_exc()
					ud.debug(ud.LDAP, ud.ERROR, "calculate_supplementalCredentials: Continuing anyway, Primary:Kerberos (DES keys) blob will be missing in supplementalCredentials ctr3.old_keys.")
			elif p.name == "Primary:Kerberos-Newer-Keys":
				krb_blob = binascii.unhexlify(p.data)
				try:
					krb = ndr_unpack(drsblobs.package_PrimaryKerberosBlob, krb_blob)
					assert krb.version == 4
					old_krb['ctr4'] = krb.ctr
					for k in krb.ctr.keys:
						ud.debug(ud.LDAP, ud.INFO, "calculate_supplementalCredentials: ctr4.key.keytype: %s" % k.keytype)
				except:
					ud.debug(ud.LDAP, ud.ERROR, "calculate_supplementalCredentials: ndr_unpack of S4 Primary:Kerberos-Newer-Keys blob failed. Traceback:")
					traceback.print_exc()
					ud.debug(ud.LDAP, ud.ERROR, "calculate_supplementalCredentials: Continuing anyway, Primary:Kerberos-Newer-Keys (AES and DES keys) blob will be missing in supplementalCredentials ctr4.old_keys.")

	krb5_aes256 = ''
	krb5_aes128 = ''
	krb5_des_md5 = ''
	krb5_des_crc = ''
	krb_ctr3_salt = ''
	krb_ctr4_salt = ''
	for k in ucs_krb5key:
		(keyblock, salt, kvno) = heimdal.asn1_decode_key(k)
		key_data = keyblock.keyvalue()
		saltstring = salt.saltvalue()
		enctype = keyblock.keytype()
		enctype_id = enctype.toint()
		if enctype_id not in krb5_context.etype_ids:
			ud.debug(ud.LDAP, ud.WARN, "calculate_supplementalCredentials: ignoring unsupported krb5_keytype: (%d)" % (enctype_id,))
			continue

		ud.debug(ud.LDAP, ud.INFO, "calculate_supplementalCredentials: krb5_keytype: %s (%d)" % (enctype, enctype_id))
		if enctype_id == 18:
			krb5_aes256 = key_data
			if not krb_ctr4_salt:
				krb_ctr4_salt = saltstring
		elif enctype_id == 17:
			krb5_aes128 = key_data
			if not krb_ctr4_salt:
				krb_ctr4_salt = saltstring
		elif enctype_id == 3:
			krb5_des_md5 = key_data
			if not krb_ctr3_salt:
				krb_ctr3_salt = saltstring
		elif enctype_id == 1:
			krb5_des_crc = key_data
			if not krb_ctr3_salt:
				krb_ctr3_salt = saltstring

	# build new drsblobs.supplementalCredentialsBlob

	sc_blob = None
	cred_List = []
	package_names = []

	# Primary:Kerberos-Newer-Keys : AES keys
	if krb5_aes256 or krb5_aes128:
		ud.debug(ud.LDAP, ud.INFO, "calculate_supplementalCredentials: building Primary:Kerberos-Newer-Keys blob")
		kerberosKey4list = []

		if krb5_aes256:
			assert len(krb5_aes256) == 32
			next_key = drsblobs.package_PrimaryKerberosKey4()
			next_key.keytype = 18
			next_key.value = krb5_aes256
			next_key.value_len = len(krb5_aes256)
			kerberosKey4list.append(next_key)
		if krb5_aes128:
			assert len(krb5_aes128) == 16
			next_key = drsblobs.package_PrimaryKerberosKey4()
			next_key.keytype = 17
			next_key.value = krb5_aes128
			next_key.value_len = len(krb5_aes128)
			kerberosKey4list.append(next_key)
		if krb5_des_md5:
			assert len(krb5_des_md5) == 8
			next_key = drsblobs.package_PrimaryKerberosKey4()
			next_key.keytype = 3
			next_key.value = krb5_des_md5
			next_key.value_len = len(krb5_des_md5)
			kerberosKey4list.append(next_key)
		if krb5_des_crc:
			assert len(krb5_des_crc) == 8
			next_key = drsblobs.package_PrimaryKerberosKey4()
			next_key.keytype = 1
			next_key.value = krb5_des_crc
			next_key.value_len = len(krb5_des_crc)
			kerberosKey4list.append(next_key)

		salt4 = drsblobs.package_PrimaryKerberosString()
		salt4.string = krb_ctr4_salt

		ctr4 = drsblobs.package_PrimaryKerberosCtr4()
		ctr4.salt = salt4
		ctr4.num_keys = len(kerberosKey4list)
		ctr4.keys = kerberosKey4list

		if old_krb.get('ctr4'):
			# Backup old_keys to s4_old_keys
			s4_num_old_keys = old_krb['ctr4'].num_old_keys
			s4_old_keys = []
			for key in old_krb['ctr4'].old_keys:
				s4_old_keys.append(key)

			# keys -> old_keys
			if len(old_krb['ctr4'].keys) != ctr4.num_keys:
				cleaned_old_keys = []
				for key in old_krb['ctr4'].keys:
					if key.keytype == 4294967156:  # in all known cases W2k8 AD uses keytype 4294967156 (=-140L) to include the arc4 hash
						ud.debug(ud.LDAP, ud.INFO, "calculate_supplementalCredentials: Primary:Kerberos-Newer-Keys filtering keytype %s from old_keys" % key.keytype)
						continue
					else:  # TODO: can we do something better at this point to make old_keys == num_keys ?
						cleaned_old_keys.append(key)

				ctr4.old_keys = cleaned_old_keys
				ctr4.num_old_keys = len(cleaned_old_keys)
			else:
				ctr4.old_keys = old_krb['ctr4'].keys
				ctr4.num_old_keys = old_krb['ctr4'].num_keys

			# s4_old_keys -> older_keys
			if ctr4.num_old_keys != ctr4.num_older_keys:
				cleaned_older_keys = []
				for key in s4_old_keys:
					if key.keytype == 4294967156:  # in all known cases W2k8 AD uses keytype 4294967156 (=-140L) to include the arc4 hash
						ud.debug(ud.LDAP, ud.INFO, "calculate_supplementalCredentials: Primary:Kerberos-Newer-Keys filtering keytype %s from older_keys" % key.keytype)
						continue
					else:  # TODO: can we do something better at this point to make old_keys == num_keys ?
						cleaned_older_keys.append(key)

				ctr4.older_keys = cleaned_older_keys
				ctr4.num_older_keys = len(cleaned_older_keys)
			else:
				ctr4.older_keys = s4_old_keys
				ctr4.num_older_keys = s4_num_old_keys

		if ctr4.num_old_keys != 0 and ctr4.num_old_keys != ctr4.num_keys:
			# TODO: Recommended policy is to fill up old_keys to match num_keys, this will result in a traceback, can we do something better?
			ud.debug(ud.LDAP, ud.WARN, "calculate_supplementalCredentials: Primary:Kerberos-Newer-Keys num_keys = %s" % ctr4.num_keys)
			for k in ctr4.keys:
				ud.debug(ud.LDAP, ud.WARN, "calculate_supplementalCredentials: ctr4.key.keytype: %s" % k.keytype)
			ud.debug(ud.LDAP, ud.WARN, "calculate_supplementalCredentials: Primary:Kerberos-Newer-Keys num_old_keys = %s" % ctr4.num_old_keys)
			for k in ctr4.old_keys:
				ud.debug(ud.LDAP, ud.WARN, "calculate_supplementalCredentials: ctr4.old_key.keytype: %s" % k.keytype)

		if ctr4.num_older_keys != 0 and ctr4.num_older_keys != ctr4.num_old_keys:
			# TODO: Recommended policy is to fill up old_keys to match num_keys, this will result in a traceback, can we do something better?
			ud.debug(ud.LDAP, ud.WARN, "calculate_supplementalCredentials: Primary:Kerberos-Newer-Keys num_old_keys = %s" % ctr4.num_old_keys)
			for k in ctr4.old_keys:
				ud.debug(ud.LDAP, ud.WARN, "calculate_supplementalCredentials: ctr4.old_key.keytype: %s" % k.keytype)
			ud.debug(ud.LDAP, ud.WARN, "calculate_supplementalCredentials: Primary:Kerberos-Newer-Keys num_older_keys = %s" % ctr4.num_older_keys)
			for k in ctr4.older_keys:
				ud.debug(ud.LDAP, ud.WARN, "calculate_supplementalCredentials: ctr4.older_key.keytype: %s" % k.keytype)

		krb_Primary_Kerberos_Newer = drsblobs.package_PrimaryKerberosBlob()
		krb_Primary_Kerberos_Newer.version = 4
		krb_Primary_Kerberos_Newer.ctr = ctr4

		krb_blob_Primary_Kerberos_Newer = ndr_pack(krb_Primary_Kerberos_Newer)
		creddata_Primary_Kerberos_Newer = binascii.hexlify(krb_blob_Primary_Kerberos_Newer)
		credname_Primary_Kerberos_Newer = "Primary:Kerberos-Newer-Keys"

		cred_Primary_Kerberos_Newer = drsblobs.supplementalCredentialsPackage()
		cred_Primary_Kerberos_Newer.name = credname_Primary_Kerberos_Newer
		cred_Primary_Kerberos_Newer.name_len = len(credname_Primary_Kerberos_Newer)
		cred_Primary_Kerberos_Newer.data = creddata_Primary_Kerberos_Newer
		cred_Primary_Kerberos_Newer.data_len = len(creddata_Primary_Kerberos_Newer)
		cred_Primary_Kerberos_Newer.reserved = 1
		cred_List.append(cred_Primary_Kerberos_Newer)
		package_names.append('Kerberos-Newer-Keys')

	# Primary:Kerberos : MD5 and CRC keys
	if krb5_des_md5 or krb5_des_crc:
		ud.debug(ud.LDAP, ud.INFO, "calculate_supplementalCredentials: building Primary:Kerberos blob")
		kerberosKey3list = []

		if krb5_des_md5:
			next_key = drsblobs.package_PrimaryKerberosKey3()
			next_key.keytype = 3
			next_key.value = krb5_des_md5
			next_key.value_len = len(krb5_des_md5)
			kerberosKey3list.append(next_key)
		if krb5_des_crc:
			next_key = drsblobs.package_PrimaryKerberosKey3()
			next_key.keytype = 1
			next_key.value = krb5_des_crc
			next_key.value_len = len(krb5_des_crc)
			kerberosKey3list.append(next_key)

		salt = drsblobs.package_PrimaryKerberosString()
		salt.string = krb_ctr3_salt

		ctr3 = drsblobs.package_PrimaryKerberosCtr3()
		ctr3.salt = salt
		ctr3.num_keys = len(kerberosKey3list)
		ctr3.keys = kerberosKey3list

		if old_krb.get('ctr3'):
			# keys -> old_keys
			if len(old_krb['ctr3'].keys) != ctr3.num_keys:
				cleaned_ctr3_old_keys = []
				for key in old_krb['ctr3'].keys:
					if key.keytype == 4294967156:  # in all known cases W2k8 AD uses keytype 4294967156 (=-140L) to include the arc4 hash
						ud.debug(ud.LDAP, ud.INFO, "calculate_supplementalCredentials: Primary:Kerberos filtering keytype %s from old_keys" % key.keytype)
						continue
					else:  # TODO: can we do something better at this point to make old_keys == num_keys ?
						cleaned_ctr3_old_keys.append(key)

				ctr3.old_keys = cleaned_ctr3_old_keys
				ctr3.num_old_keys = len(cleaned_ctr3_old_keys)
			else:
				ctr3.old_keys = old_krb['ctr3'].keys
				ctr3.num_old_keys = old_krb['ctr3'].num_keys

		if ctr3.num_old_keys != 0 and ctr3.num_old_keys != ctr3.num_keys:
			# TODO: Recommended policy is to fill up old_keys to match num_keys, this will result in a traceback, can we do something better?
			ud.debug(ud.LDAP, ud.WARN, "calculate_supplementalCredentials: Primary:Kerberos num_keys = %s" % ctr3.num_keys)
			for k in ctr3.keys:
				ud.debug(ud.LDAP, ud.WARN, "calculate_supplementalCredentials: ctr3.key.keytype: %s" % k.keytype)
			ud.debug(ud.LDAP, ud.WARN, "calculate_supplementalCredentials: Primary:Kerberos num_old_keys = %s" % ctr3.num_old_keys)
			for k in ctr3.old_keys:
				ud.debug(ud.LDAP, ud.WARN, "calculate_supplementalCredentials: ctr3.old_key.keytype: %s" % k.keytype)

		krb = drsblobs.package_PrimaryKerberosBlob()
		krb.version = 3
		krb.ctr = ctr3
		krb3_blob = ndr_pack(krb)

		creddata_Primary_Kerberos = binascii.hexlify(krb3_blob)
		credname_Primary_Kerberos = "Primary:Kerberos"

		cred_Primary_Kerberos = drsblobs.supplementalCredentialsPackage()
		cred_Primary_Kerberos.name = credname_Primary_Kerberos
		cred_Primary_Kerberos.name_len = len(credname_Primary_Kerberos)
		cred_Primary_Kerberos.data = creddata_Primary_Kerberos
		cred_Primary_Kerberos.data_len = len(creddata_Primary_Kerberos)
		cred_Primary_Kerberos.reserved = 1
		cred_List.append(cred_Primary_Kerberos)
		package_names.append('Kerberos')

	if package_names:
		krb_blob_Packages = '\0'.join(package_names).encode('utf-16le')
		cred_PackagesBlob_data = binascii.hexlify(krb_blob_Packages).upper()
		cred_PackagesBlob_name = "Packages"
		cred_PackagesBlob = drsblobs.supplementalCredentialsPackage()
		cred_PackagesBlob.name = cred_PackagesBlob_name
		cred_PackagesBlob.name_len = len(cred_PackagesBlob_name)
		cred_PackagesBlob.data = cred_PackagesBlob_data
		cred_PackagesBlob.data_len = len(cred_PackagesBlob_data)
		cred_PackagesBlob.reserved = 2
		cred_List.insert(-1, cred_PackagesBlob)

		sub = drsblobs.supplementalCredentialsSubBlob()
		sub.num_packages = len(cred_List)
		sub.packages = cred_List
		sub.signature = drsblobs.SUPPLEMENTAL_CREDENTIALS_SIGNATURE
		sub.prefix = drsblobs.SUPPLEMENTAL_CREDENTIALS_PREFIX

		sc = drsblobs.supplementalCredentialsBlob()
		sc.sub = sub
		sc_blob = ndr_pack(sc)
		ud.debug(ud.LDAP, ud.ALL, "calculate_supplementalCredentials: sc:\n%s" % ndr_print(sc))

	return sc_blob


def extract_NThash_from_krb5key(ucs_krb5key):

	NThash = None

	for k in ucs_krb5key:
		(keyblock, salt, kvno) = heimdal.asn1_decode_key(k)

		enctype = keyblock.keytype()
		enctype_id = enctype.toint()
		if enctype_id == 23:
			krb5_arcfour_hmac_md5 = keyblock.keyvalue()
			NThash = binascii.b2a_hex(krb5_arcfour_hmac_md5)
			break

	return NThash


def _append_length(a, str):
	l = len(str)
	a.append(chr((l & 0xff)))
	a.append(chr((l & 0xff00) >> 8))
	a.append(chr((l & 0xff0000) >> 16))
	a.append(chr((l & 0xff000000) >> 24))


def password_sync_ucs_to_s4(s4connector, key, object):
	_d = ud.function('ldap.s4.password_sync_ucs_to_s4')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4 called")

	modify = False
	old_ucs_object = object.get('old_ucs_object', {})
	new_ucs_object = object.get('new_ucs_object', {})
	if old_ucs_object or new_ucs_object:
		for attr in ['sambaLMPassword', 'sambaNTPassword', 'sambaPwdLastSet', 'sambaPwdMustChange', 'krb5PrincipalName', 'krb5Key', 'shadowLastChange', 'shadowMax', 'krb5PasswordEnd', 'univentionService']:
			old_values = set(old_ucs_object.get(attr, []))
			new_values = set(new_ucs_object.get(attr, []))
			if old_values != new_values:
				modify = True
				break
	else:
		# add mode
		modify = True

	if not modify:
		ud.debug(ud.LDAP, ud.INFO, 'password_sync_ucs_to_s4: the password for %s has not been changed. Skipping password sync.' % (object['dn']))
		return

	try:
		ud.debug(ud.LDAP, ud.INFO, "Object DN=%s" % object['dn'])
	except:  # FIXME: which exception is to be caught?
		ud.debug(ud.LDAP, ud.INFO, "Object DN not printable")

	ucs_object = s4connector._object_mapping(key, object, 'con')

	try:
		ud.debug(ud.LDAP, ud.INFO, "   UCS DN = %s" % ucs_object['dn'])
	except:  # FIXME: which exception is to be caught?
		ud.debug(ud.LDAP, ud.INFO, "   UCS DN not printable")

	try:
		ucs_object_attributes = s4connector.lo.get(ucs_object['dn'], ['sambaLMPassword', 'sambaNTPassword', 'sambaPwdLastSet', 'sambaPwdMustChange', 'krb5PrincipalName', 'krb5Key', 'shadowLastChange', 'shadowMax', 'krb5PasswordEnd', 'univentionService'], required=True)
	except ldap.NO_SUCH_OBJECT:
		ud.debug(ud.LDAP, ud.PROCESS, "password_sync_ucs_to_s4: The UCS object (%s) was not found. The object was removed." % ucs_object['dn'])
		return

	services = ucs_object_attributes.get('univentionService', [])
	if 'Samba 4' in services:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: %s is a S4 server, skip password sync" % ucs_object['dn'])
		return

	sambaPwdLastSet = None
	if 'sambaPwdLastSet' in ucs_object_attributes:
		sambaPwdLastSet = int(ucs_object_attributes['sambaPwdLastSet'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: sambaPwdLastSet: %s" % sambaPwdLastSet)

	if 'sambaPwdMustChange' in ucs_object_attributes:
		sambaPwdMustChange = int(ucs_object_attributes['sambaPwdMustChange'][0])
		ud.debug(ud.LDAP, ud.WARN, "password_sync_ucs_to_s4: Ignoring sambaPwdMustChange: %s" % sambaPwdMustChange)

	ucsLMhash = ucs_object_attributes.get('sambaLMPassword', [None])[0]
	ucsNThash = ucs_object_attributes.get('sambaNTPassword', [None])[0]
	krb5Principal = ucs_object_attributes.get('krb5PrincipalName', [None])[0]
	krb5Key = ucs_object_attributes.get('krb5Key', [])

	if not ucsNThash:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: sambaNTPassword missing in UCS LDAP, trying krb5Key")
		ucsNThash = extract_NThash_from_krb5key(krb5Key)

	if not ucsNThash:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: Failed to get NT Password-Hash from UCS LDAP")

	# ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: Password-Hash from UCS: %s" % ucsNThash)

	s4_object_attributes = s4connector.lo_s4.get(compatible_modstring(object['dn']), ['pwdLastSet', 'objectSid'])
	pwdLastSet = None
	if 'pwdLastSet' in s4_object_attributes:
		pwdLastSet = int(s4_object_attributes['pwdLastSet'][0])
	objectSid = univention.s4connector.s4.decode_sid(s4_object_attributes['objectSid'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: pwdLastSet from S4 : %s" % pwdLastSet)
	# rid = None
	# if s4_object_attributes.has_key('objectSid'):
	# 	rid = str(univention.s4connector.s4.decode_sid(s4_object_attributes['objectSid'][0]).split('-')[-1])

	pwd_set = False
	filter_expr = format_escaped('(objectSid={0!e})', objectSid)
	res = s4connector.lo_s4.search(filter=filter_expr, attr=['unicodePwd', 'userPrincipalName', 'supplementalCredentials', 'msDS-KeyVersionNumber', 'dBCSPwd'])
	s4_search_attributes = res[0][1]

	unicodePwd_attr = s4_search_attributes.get('unicodePwd', [None])[0]
	dBCSPwd_attr = s4_search_attributes.get('dBCSPwd', [None])[0]
	userPrincipalName_attr = s4_search_attributes.get('userPrincipalName', [None])[0]
	supplementalCredentials = s4_search_attributes.get('supplementalCredentials', [None])[0]
	msDS_KeyVersionNumber = s4_search_attributes.get('msDS-KeyVersionNumber', [0])[0]
	# ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: Password-Hash from S4: %s" % unicodePwd_attr)

	s4NThash = None
	if unicodePwd_attr:
		s4NThash = binascii.b2a_hex(unicodePwd_attr).upper()
	else:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: Failed to get NT Password-Hash from S4")

	s4LMhash = None
	if dBCSPwd_attr:
		s4LMhash = binascii.b2a_hex(dBCSPwd_attr).upper()
	else:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: Failed to get LM Password-Hash from S4")

	modlist = []
	if krb5Principal != userPrincipalName_attr:
		if krb5Principal:
			if not userPrincipalName_attr:  # new and not old
				modlist.append((ldap.MOD_ADD, 'userPrincipalName', krb5Principal))
			else:  # new and old differ
				if krb5Principal.lower() != userPrincipalName_attr.lower():
					ud.debug(ud.LDAP, ud.WARN, "password_sync_ucs_to_s4: userPrincipalName != krb5Principal: '%s' != '%s'" % (userPrincipalName_attr, krb5Principal))
				modlist.append((ldap.MOD_REPLACE, 'userPrincipalName', krb5Principal))
		else:
			if userPrincipalName_attr:  # old and not new
				modlist.append((ldap.MOD_DELETE, 'userPrincipalName', userPrincipalName_attr))

	if not ucsNThash == s4NThash:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: NT Hash S4: %s NT Hash UCS: %s" % (s4NThash, ucsNThash))
		# Now if ucsNThash is empty there should at least some timestamp in UCS,
		# otherwise it's probably not a good idea to remove the unicodePwd.
		# Usecase: LDB module on ucs_3.0-0-ucsschool slaves creates XP computers/windows in UDM without password
		if ucsNThash or sambaPwdLastSet:
			pwd_set = True
			unicodePwd_new = None
			if ucsNThash:
				try:
					unicodePwd_new = binascii.a2b_hex(ucsNThash)
				except TypeError as exc:
					if ucsNThash.startswith("NO PASSWORD"):
						pwd_set = False
					else:
						raise
			if pwd_set and unicodePwd_new:
				modlist.append((ldap.MOD_REPLACE, 'unicodePwd', unicodePwd_new))

	if not ucsLMhash == s4LMhash:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: LM Hash S4: %s LM Hash UCS: %s" % (s4LMhash, ucsLMhash))
		pwd_set = True
		if ucsLMhash:
			dBCSPwd_new = binascii.a2b_hex(ucsLMhash)
			modlist.append((ldap.MOD_REPLACE, 'dBCSPwd', dBCSPwd_new))
		else:
			modlist.append((ldap.MOD_DELETE, 'dBCSPwd', None))

	if pwd_set or not supplementalCredentials:
		if krb5Principal:
			# encoding of Samba4 supplementalCredentials
			if krb5Key:
				supplementalCredentials_new = calculate_supplementalCredentials(krb5Key, supplementalCredentials)
				if supplementalCredentials_new:
					modlist.append((ldap.MOD_REPLACE, 'supplementalCredentials', supplementalCredentials_new))
				else:
					ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: no supplementalCredentials_new")
				# if supplementalCredentials:
				#	modlist.append((ldap.MOD_REPLACE, 'msDS-KeyVersionNumber', krb5KeyVersionNumber))
				# else:
				#	modlist.append((ldap.MOD_ADD, 'msDS-KeyVersionNumber', krb5KeyVersionNumber))

		if sambaPwdLastSet is None:
			sambaPwdLastSet = int(time.time())
			newpwdlastset = str(univention.s4connector.s4.samba2s4_time(sambaPwdLastSet))
		elif sambaPwdLastSet in [0, 1]:
			ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: samba pwd expired, set newpwdLastSet to 0")
			newpwdlastset = 0
		else:
			newpwdlastset = univention.s4connector.s4.samba2s4_time(sambaPwdLastSet)
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: pwdLastSet in modlist: %s" % newpwdlastset)
		modlist.append((ldap.MOD_REPLACE, 'pwdLastSet', str(newpwdlastset)))
		modlist.append((ldap.MOD_REPLACE, 'badPwdCount', '0'))
		modlist.append((ldap.MOD_REPLACE, 'badPasswordTime', '0'))
		modlist.append((ldap.MOD_REPLACE, 'lockoutTime', '0'))

	else:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: No password change to sync to S4 ")

		# check pwdLastSet
		if sambaPwdLastSet is not None:
			if sambaPwdLastSet in [0, 1]:
				newpwdlastset = 0
			else:
				newpwdlastset = univention.s4connector.s4.samba2s4_time(sambaPwdLastSet)
			ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: sambaPwdLastSet: %d" % sambaPwdLastSet)
			ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: newpwdlastset  : %s" % newpwdlastset)
			ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: pwdLastSet (AD): %s" % pwdLastSet)
			if newpwdlastset != pwdLastSet and abs(newpwdlastset - pwdLastSet) >= 10000000:
				modlist.append((ldap.MOD_REPLACE, 'pwdLastSet', str(newpwdlastset)))

	# TODO: Password History
	ctrl_bypass_password_hash = LDAPControl('1.3.6.1.4.1.7165.4.3.12', criticality=0)
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: modlist: %s" % modlist)
	if modlist:
		s4connector.lo_s4.lo.modify_ext_s(compatible_modstring(object['dn']), modlist, serverctrls=[ctrl_bypass_password_hash])


def password_sync_s4_to_ucs(s4connector, key, ucs_object, modifyUserPassword=True):
	_d = ud.function('ldap.s4.password_sync_s4_to_ucs')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs called")

	if ucs_object['modtype'] == 'modify':
		if 'pwdLastSet' not in ucs_object.get('changed_attributes', []):
			ud.debug(ud.LDAP, ud.INFO, 'password_sync_s4_to_ucs: the password for %s has not been changed. Skipping password sync.' % (ucs_object['dn']))
			return

	object = s4connector._object_mapping(key, ucs_object, 'ucs')
	s4_object_attributes = s4connector.lo_s4.get(compatible_modstring(object['dn']), ['objectSid', 'pwdLastSet'])

	if s4connector.isInCreationList(object['dn']):
		s4connector.removeFromCreationList(object['dn'])
		ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: Synchronisation of password has been canceled. Object was just created.")
		return

	pwdLastSet = None
	if 'pwdLastSet' in s4_object_attributes:
		pwdLastSet = int(s4_object_attributes['pwdLastSet'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: pwdLastSet from S4: %s (%s)" % (pwdLastSet, s4_object_attributes))
	objectSid = univention.s4connector.s4.decode_sid(s4_object_attributes['objectSid'][0])

	# rid = None
	# if s4_object_attributes.has_key('objectSid'):
	# 	rid = str(univention.s4connector.s4.decode_sid(s4_object_attributes['objectSid'][0]).split('-')[-1])

	filter_expr = format_escaped('(objectSid={0!e})', objectSid)
	res = s4connector.lo_s4.search(filter=filter_expr, attr=['unicodePwd', 'supplementalCredentials', 'msDS-KeyVersionNumber', 'dBCSPwd'])
	s4_search_attributes = res[0][1]

	unicodePwd_attr = s4_search_attributes.get('unicodePwd', [None])[0]
	if unicodePwd_attr:
		ntPwd = binascii.b2a_hex(unicodePwd_attr).upper()

		lmPwd = ''
		dBCSPwd = s4_search_attributes.get('dBCSPwd', [None])[0]
		if dBCSPwd:
			lmPwd = binascii.b2a_hex(dBCSPwd).upper()

		supplementalCredentials = s4_search_attributes.get('supplementalCredentials', [None])[0]
		msDS_KeyVersionNumber = s4_search_attributes.get('msDS-KeyVersionNumber', [0])[0]

		ntPwd_ucs = ''
		lmPwd_ucs = ''
		krb5Principal = ''
		userPassword = ''
		modlist = []
		ucs_object_attributes = s4connector.lo.get(ucs_object['dn'], ['sambaPwdMustChange', 'sambaPwdLastSet', 'sambaNTPassword', 'sambaLMPassword', 'krb5PrincipalName', 'krb5Key', 'krb5KeyVersionNumber', 'userPassword', 'shadowLastChange', 'shadowMax', 'krb5PasswordEnd', 'univentionService'])

		services = ucs_object_attributes.get('univentionService', [])
		if 'S4 SlavePDC' in services:
			ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: %s is a S4 SlavePDC server, skip password sync" % ucs_object['dn'])
			return

		if 'sambaNTPassword' in ucs_object_attributes:
			ntPwd_ucs = ucs_object_attributes['sambaNTPassword'][0]
		if 'sambaLMPassword' in ucs_object_attributes:
			lmPwd_ucs = ucs_object_attributes['sambaLMPassword'][0]
		if 'krb5PrincipalName' in ucs_object_attributes:
			krb5Principal = ucs_object_attributes['krb5PrincipalName'][0]
		if 'userPassword' in ucs_object_attributes:
			userPassword = ucs_object_attributes['userPassword'][0]
		sambaPwdLastSet = None
		if 'sambaPwdLastSet' in ucs_object_attributes:
			sambaPwdLastSet = ucs_object_attributes['sambaPwdLastSet'][0]
		ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: sambaPwdLastSet: %s" % sambaPwdLastSet)
		sambaPwdMustChange = ''
		if 'sambaPwdMustChange' in ucs_object_attributes:
			sambaPwdMustChange = ucs_object_attributes['sambaPwdMustChange'][0]
			ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: Found sambaPwdMustChange: %s" % sambaPwdMustChange)
		krb5Key_ucs = ucs_object_attributes.get('krb5Key', [])
		userPassword_ucs = ucs_object_attributes.get('userPassword', [None])[0]
		krb5KeyVersionNumber = ucs_object_attributes.get('krb5KeyVersionNumber', [None])[0]

		pwd_changed = False
		if ntPwd != ntPwd_ucs:
			pwd_changed = True
			modlist.append(('sambaNTPassword', ntPwd_ucs, str(ntPwd)))

		if lmPwd != lmPwd_ucs:
			pwd_changed = True
			modlist.append(('sambaLMPassword', lmPwd_ucs, str(lmPwd)))

		if pwd_changed:
			if krb5Principal:
				# decoding of Samba4 supplementalCredentials
				krb5Key_new = calculate_krb5key(unicodePwd_attr, supplementalCredentials, int(msDS_KeyVersionNumber))

				modlist.append(('krb5Key', krb5Key_ucs, krb5Key_new))
				if int(msDS_KeyVersionNumber) != int(krb5KeyVersionNumber):
					modlist.append(('krb5KeyVersionNumber', krb5KeyVersionNumber, msDS_KeyVersionNumber))

			# Append modification as well to modlist, to apply in one transaction
			if modifyUserPassword:
				modlist.append(('userPassword', userPassword_ucs, '{K5KEY}'))
		else:
			ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: No password change to sync to UCS")

		try:
			old_pwdLastSet = object['old_s4_object']['pwdLastSet'][0]
		except (KeyError, IndexError):
			old_pwdLastSet = None

		if pwdLastSet != old_pwdLastSet:
			ud.debug(ud.LDAP, ud.ALL, "password_sync_s4_to_ucs: updating shadowLastChange")
			old_shadowLastChange = ucs_object_attributes.get('shadowLastChange', [None])[0]
			new_shadowLastChange = old_shadowLastChange

			# shadowMax (set to value of univentionPWExpiryInterval, otherwise delete)
			# krb5PasswordEnd (set to today + univentionPWExpiryInterval, otherwise delete)
			old_shadowMax = ucs_object_attributes.get('shadowMax', [None])[0]
			new_shadowMax = old_shadowMax
			old_krb5end = ucs_object_attributes.get('krb5PasswordEnd', [None])[0]
			new_krb5end = old_krb5end

			pwdLastSet_unix = univention.s4connector.s4.s42samba_time(pwdLastSet)
			newSambaPwdLastSet = str(pwdLastSet_unix)

			if pwdLastSet == 0:  # pwd change on next login
				new_shadowMax = '1'
				expiry = int(time.time())
				new_krb5end = time.strftime("%Y%m%d000000Z", time.gmtime(expiry))
			else:                # not pwd change on next login
				new_shadowLastChange = str(pwdLastSet_unix / 3600 / 24)
				userobject = s4connector.get_ucs_object(key, ucs_object['dn'])
				if not userobject:
					ud.debug(ud.LDAP, ud.ERROR, "password_sync_s4_to_ucs: couldn't get user-object from UCS")
					return False

				pwhistoryPolicy = userobject.loadPolicyObject('policies/pwhistory')
				try:
					expiryInterval = int(pwhistoryPolicy['expiryInterval'])
				except (TypeError, ValueError):
					# expiryInterval is empty or no legal int-string
					pwhistoryPolicy['expiryInterval'] = ''
					expiryInterval = -1

				ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: password expiryInterval for %s is %s" % (ucs_object['dn'], expiryInterval))
				if expiryInterval in (-1, 0):
					new_shadowMax = ''
					new_krb5end = ''
				else:
					new_shadowMax = str(expiryInterval)
					new_krb5end = time.strftime("%Y%m%d000000Z", time.gmtime((pwdLastSet_unix + (int(expiryInterval) * 3600 * 24))))

			if new_shadowLastChange != old_shadowLastChange:
				ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: update shadowLastChange to %s for %s" % (new_shadowLastChange, ucs_object['dn']))
				modlist.append(('shadowLastChange', old_shadowLastChange, new_shadowLastChange))
			if new_shadowMax != old_shadowMax:
				ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: update shadowMax to %s for %s" % (new_shadowMax, ucs_object['dn']))
				modlist.append(('shadowMax', old_shadowMax, new_shadowMax))
			if new_krb5end != old_krb5end:
				ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: update krb5PasswordEnd to %s for %s" % (new_krb5end, ucs_object['dn']))
				modlist.append(('krb5PasswordEnd', old_krb5end, new_krb5end))

			if sambaPwdLastSet:
				if sambaPwdLastSet != newSambaPwdLastSet:
					modlist.append(('sambaPwdLastSet', sambaPwdLastSet, newSambaPwdLastSet))
					ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: sambaPwdLastSet in modlist (replace): %s" % newSambaPwdLastSet)
			else:
				modlist.append(('sambaPwdLastSet', '', newSambaPwdLastSet))
				ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: sambaPwdLastSet in modlist (set): %s" % newSambaPwdLastSet)

			if sambaPwdMustChange:
				modlist.append(('sambaPwdMustChange', sambaPwdMustChange, ''))
				ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: Removing sambaPwdMustChange")

		if len(modlist) > 0:
			ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: modlist: %s" % modlist)
			s4connector.lo.lo.modify(ucs_object['dn'], modlist)

	else:
		ud.debug(ud.LDAP, ud.WARN, "password_sync_ucs_s4_to_ucs: Failed to get Password-Hash from S4")


def password_sync_s4_to_ucs_no_userpassword(s4connector, key, ucs_object):
	# The userPassword should not synchronized for computer accounts
	password_sync_s4_to_ucs(s4connector, key, ucs_object, modifyUserPassword=False)


def lockout_sync_s4_to_ucs(s4connector, key, ucs_object):
	"""
	Sync account locking *state* from Samba/AD to OpenLDAP:
		sync Samba/AD (lockoutTime != 0)      ->  OpenLDAP sambaAcctFlags ("L")
		and  Samba/AD badPasswordTime         ->  OpenLDAP sambaBadPasswordTime
	"""
	function_name = 'lockout_sync_s4_to_ucs'
	_d = ud.function('ldap.s4.%s' % function_name)  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, "%s called" % function_name)

	if ucs_object['modtype'] not in ('modify', 'add'):
		return

	modlist = []

	try:
		ucs_object_attributes = s4connector.lo.get(ucs_object['dn'], ['sambaAcctFlags', 'sambaBadPasswordTime'], required=True)
	except ldap.NO_SUCH_OBJECT:
		ud.debug(ud.LDAP, ud.WARN, "%s: The UCS object (%s) was not found. The object was removed." % (function_name, ucs_object['dn']))
		return
	sambaAcctFlags = ucs_object_attributes.get('sambaAcctFlags', [''])[0]
	sambaBadPasswordTime = ucs_object_attributes.get('sambaBadPasswordTime', ["0"])[0]

	lockoutTime = ucs_object['attributes'].get('lockoutTime', ['0'])[0]
	if lockoutTime != "0":
		if "L" not in sambaAcctFlags:
			acctFlags = univention.admin.samba.acctFlags(sambaAcctFlags)
			new_sambaAcctFlags = acctFlags.set('L')
			ud.debug(ud.LDAP, ud.PROCESS, "%s: Marking Samba account as locked in OpenLDAP" % (function_name,))
			modlist.append(('sambaAcctFlags', sambaAcctFlags, new_sambaAcctFlags))

		badPasswordTime = ucs_object['attributes'].get('badPasswordTime', ["0"])[0]
		if badPasswordTime != sambaBadPasswordTime:
			ud.debug(ud.LDAP, ud.PROCESS, "%s: Copying badPasswordTime from S4: %s" % (function_name, badPasswordTime))
			if sambaBadPasswordTime:
				ud.debug(ud.LDAP, ud.INFO, "%s: Old sambaBadPasswordTime: %s" % (function_name, sambaBadPasswordTime))
			modlist.append(('sambaBadPasswordTime', sambaBadPasswordTime, badPasswordTime))
	else:
		if "L" in sambaAcctFlags:
			acctFlags = univention.admin.samba.acctFlags(sambaAcctFlags)
			new_sambaAcctFlags = acctFlags.unset('L')
			ud.debug(ud.LDAP, ud.PROCESS, "%s: Marking Samba account as unlocked in OpenLDAP" % (function_name,))
			modlist.append(('sambaAcctFlags', sambaAcctFlags, new_sambaAcctFlags))

		if sambaBadPasswordTime and sambaBadPasswordTime != "0":
			ud.debug(ud.LDAP, ud.PROCESS, "%s: Unsetting sambaBadPasswordTime: %s" % (function_name, sambaBadPasswordTime))
			modlist.append(('sambaBadPasswordTime', sambaBadPasswordTime, "0"))

	if modlist:
		ud.debug(ud.LDAP, ud.ALL, "%s: modlist: %s" % (function_name, modlist))
		s4connector.lo.lo.modify(ucs_object['dn'], modlist)


def lockout_sync_ucs_to_s4(s4connector, key, object):
	"""
	Sync unlock *modification* from OpenLDAP to Samba/AD:
		sync OpenLDAP ("L" not in sambaAcctFlags) ->  Samba/AD lockoutTime = 0

		sync OpenLDAP ("L" in sambaAcctFlags) ->  Samba/AD lockoutTime = sambaBadPasswordTime
		and  OpenLDAP sambaBadPasswordTime    ->  Samba/AD badPasswordTime
	"""
	function_name = 'lockout_sync_ucs_to_s4'
	_d = ud.function('ldap.s4.%s' % function_name)  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, "%s called" % function_name)

	if object['modtype'] not in ('modify', 'add'):
		return

	new_ucs_object = object.get('new_ucs_object', {})
	if not new_ucs_object:
		# only set by sync_from_ucs in MODIFY case
		return

	old_ucs_object = object.get('old_ucs_object', {})
	if not old_ucs_object:
		# only set by sync_from_ucs in MODIFY case
		return

	new_sambaAcctFlags = new_ucs_object.get('sambaAcctFlags', [''])[0]
	is_locked = "L" in new_sambaAcctFlags

	old_sambaAcctFlags = old_ucs_object.get('sambaAcctFlags', [''])[0]
	was_locked = "L" in old_sambaAcctFlags

	if is_locked == was_locked:
		# Require a change in the pickled state
		return

	modlist = []
	if not is_locked:
		s4_object_attributes = s4connector.lo_s4.get(compatible_modstring(object['dn']), ['lockoutTime', 'badPasswordTime'])
		if 'lockoutTime' not in s4_object_attributes:
			return

		lockoutTime = s4_object_attributes['lockoutTime'][0]
		if lockoutTime == "0":
			return

		# Now object.get('new_ucs_object') may be a stale pickled state, so let's lookup the current OpenLDAP object state
		# Unfortunately "object" doesn't hold the current OpenLDAP DN, so we need to map back first
		ucs_object = s4connector._object_mapping(key, object)
		try:
			ucs_object_attributes = s4connector.lo.get(ucs_object['dn'], ['sambaAcctFlags', 'sambaBadPasswordTime'], required=True)
		except ldap.NO_SUCH_OBJECT:
			ud.debug(ud.LDAP, ud.WARN, "%s: The UCS object (%s) was not found. The object was removed." % (function_name, ucs_object['dn']))
			return
		sambaAcctFlags = ucs_object_attributes.get('sambaAcctFlags', [''])[0]

		if "L" in sambaAcctFlags:
			# currently locked again
			return

		sambaBadPasswordTime = ucs_object_attributes.get('sambaBadPasswordTime', [''])[0]
		if sambaBadPasswordTime and sambaBadPasswordTime != "0":
			ud.debug(ud.LDAP, ud.ERROR, "%s: The UCS object (%s) is unlocked, but sambaBadPasswordTime is set." % (function_name, ucs_object['dn']))
			return

		# Ok here we have:
		# 1. Account currently not locked in OpenLDAP but in Samba/AD
		# 2. Lockout state has changed to unlocked at some pickled point in the past
		modlist.append((ldap.MOD_REPLACE, "lockoutTime", "0"))
		modlist.append((ldap.MOD_REPLACE, "badPasswordTime", "0"))
		ud.debug(ud.LDAP, ud.PROCESS, "%s: Marking account as unlocked in Samba/AD" % (function_name,))
	else:
		s4_object_attributes = s4connector.lo_s4.get(compatible_modstring(object['dn']), ['lockoutTime', 'badPasswordTime'])
		lockoutTime = s4_object_attributes.get('lockoutTime', ['0'])[0]

		# Now object.get('new_ucs_object') may be a stale pickled state, so let's lookup the current OpenLDAP object state
		# Unfortunately "object" doesn't hold the current OpenLDAP DN, so we need to map back first
		ucs_object = s4connector._object_mapping(key, object)
		try:
			ucs_object_attributes = s4connector.lo.get(ucs_object['dn'], ['sambaAcctFlags', 'sambaBadPasswordTime'], required=True)
		except ldap.NO_SUCH_OBJECT:
			ud.debug(ud.LDAP, ud.WARN, "%s: The UCS object (%s) was not found. The object was removed." % (function_name, ucs_object['dn']))
			return
		sambaAcctFlags = ucs_object_attributes.get('sambaAcctFlags', [''])[0]
		if "L" not in sambaAcctFlags:
			# currently not locked any longer
			return

		sambaBadPasswordTime = ucs_object_attributes.get('sambaBadPasswordTime', [''])[0]
		if not sambaBadPasswordTime:
			ud.debug(ud.LDAP, ud.ERROR, "%s: The UCS object (%s) is locked, but sambaBadPasswordTime is missing." % (function_name, ucs_object['dn']))
			return
		if sambaBadPasswordTime == "0":
			ud.debug(ud.LDAP, ud.ERROR, "%s: The UCS object (%s) is locked, but sambaBadPasswordTime is 0." % (function_name, ucs_object['dn']))
			return
		if sambaBadPasswordTime == lockoutTime:
			# already locked
			return

		# Ok here we have:
		# 1. Account currently locked in OpenLDAP but not in Samba/AD
		# 2. Lockout state has changed to locked at some pickled point in the past
		modlist.append((ldap.MOD_REPLACE, "lockoutTime", sambaBadPasswordTime))
		modlist.append((ldap.MOD_REPLACE, "badPasswordTime", sambaBadPasswordTime))
		ud.debug(ud.LDAP, ud.PROCESS, "%s: Marking account as locked in Samba/AD" % (function_name,))
		ud.debug(ud.LDAP, ud.INFO, "%s: Setting lockoutTime to the value of sambaBadPasswordTime: %s" % (function_name, sambaBadPasswordTime))

	if modlist:
		ud.debug(ud.LDAP, ud.ALL, "%s: modlist: %s" % (function_name, modlist))
		s4connector.lo_s4.lo.modify_ext_s(compatible_modstring(object['dn']), modlist)
