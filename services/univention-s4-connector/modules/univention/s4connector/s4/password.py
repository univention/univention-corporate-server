#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  control the password sync communication with the s4 password service
#
# Copyright 2004-2011 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.


import os, time
import ldap
import univention.debug2 as ud
import univention.s4connector.s4
import binascii
import types

from samba.ndr import ndr_unpack, ndr_pack
from samba.dcerpc import drsblobs
import heimdal
from ldap.controls import LDAPControl
import ctypes
import traceback
_PyCObject_FromVoidPtr = ctypes.pythonapi.PyCObject_FromVoidPtr 
_PyCObject_FromVoidPtr.argtypes = [ctypes.POINTER(ctypes.c_char_p), ctypes.c_void_p] 
_PyCObject_FromVoidPtr.restype = ctypes.py_object 


def calculate_krb5key(unicodePwd, supplementalCredentials, kvno=0):
	up_blob = unicodePwd
	sc_blob = supplementalCredentials

	keys = []
	keytypes = []
	context = heimdal.context()

	if up_blob:
		#ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: up_blob: %s" % binascii.b2a_base64(up_blob))
		assert len(up_blob) == 16
		key = heimdal.keyblock_raw(context, 23, up_blob)
		keys.append(heimdal.asn1_encode_key(key, None, kvno))

	if sc_blob:
		#ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: sc_blob: %s" % binascii.b2a_base64(sc_blob))
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
								if k.value == up_blob:
									ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: ignoring arc4 key key with invalid keytype %s in %s" % (k.keytype, p.name))
								else:
									traceback.print_exc()
									ud.debug(ud.LDAP, ud.ERROR, "calculate_krb5key: krb5Key with keytype %s could not be parsed. Continuing anyway." % k.keytype)

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
								if k.value == up_blob:
									ud.debug(ud.LDAP, ud.INFO, "calculate_krb5key: ignoring arc4 key key with invalid keytype %s in %s" % (k.keytype, p.name))
								else:
									traceback.print_exc()
									ud.debug(ud.LDAP, ud.ERROR, "calculate_krb5key: krb5Key with keytype %s could not be parsed. Continuing anyway." % k.keytype)

		except Exception:
			import sys
			exc = sys.exc_info()[1]
			if type(exc.args) == type(()) and len(exc.args) == 2 and exc.args[1] == 'Buffer Size Error':
				ud.debug(ud.LDAP, ud.WARN, "calculate_krb5key: '%s' while unpacking supplementalCredentials:: %s" % ( exc, binascii.b2a_base64(sc_blob) ) )
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
				krb = ndr_unpack(drsblobs.package_PrimaryKerberosBlob, krb_blob)
				assert krb.version == 3
				old_krb['ctr3'] = krb.ctr
				for k in krb.ctr.keys:	
					ud.debug(ud.LDAP, ud.INFO, "calculate_supplementalCredentials: ctr3.key.keytype: %s" % k.keytype)
			elif p.name == "Primary:Kerberos-Newer-Keys":
				krb_blob = binascii.unhexlify(p.data)
				krb = ndr_unpack(drsblobs.package_PrimaryKerberosBlob, krb_blob)
				assert krb.version == 4
				old_krb['ctr4'] = krb.ctr
				for k in krb.ctr.keys:	
					ud.debug(ud.LDAP, ud.INFO, "calculate_supplementalCredentials: ctr4.key.keytype: %s" % k.keytype)

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

	## build new drsblobs.supplementalCredentialsBlob

	sc_blob = None
	cred_List = []
	package_names = []
	
	## Primary:Kerberos-Newer-Keys : AES keys
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
			ctr4.older_keys = old_krb['ctr4'].old_keys
			ctr4.num_older_keys = old_krb['ctr4'].num_old_keys
			ctr4.old_keys = old_krb['ctr4'].keys
			ctr4.num_old_keys = old_krb['ctr4'].num_keys

		if ctr4.num_old_keys != ctr4.num_keys:
			pass	# TODO: Recommended policy is to fill up old_keys to match num_keys

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

	## Primary:Kerberos : MD5 and CRC keys
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
			ctr3.old_keys = old_krb['ctr3'].keys
			ctr3.num_old_keys = old_krb['ctr3'].num_keys

		if ctr3.num_old_keys != ctr3.num_keys:
			pass	# TODO: Recommended policy is to fill up old_keys to match num_keys

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
		package_names_carray = (ctypes.c_char_p * len(package_names))(*package_names)
		package_names_PyCObject = _PyCObject_FromVoidPtr(ctypes.cast(package_names_carray, ctypes.POINTER(ctypes.c_char_p)), None) 
		krb_Packages = drsblobs.package_PackagesBlob() 
		krb_Packages.names = package_names_PyCObject
		krb_blob_Packages = ndr_pack(krb_Packages)
		# krb_blob_Packages = '\0'.join(package_names).encode('utf-16le')       # this pretty much simulates it
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

def _append_string(a, strstr):
	for i in range(0,len(strstr)):
		a.append(strstr[i])

def _append(a, strstr):
	_append_length(a, str(strstr))
	_append_string(a, str(strstr))

def _append_array(a, strstr):
	_append_length(a, strstr)
	_append_string(a, strstr)


def _get_integer(str):
	res=ord(str[0]) + (ord(str[1]) << 8) + (ord(str[2]) << 16) + (ord(str[3]) << 24)
	return res

def password_sync_ucs_to_s4(s4connector, key, object):
	_d=ud.function('ldap.s4.password_sync_ucs_to_s4')
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4 called")
	
	compatible_modstring = univention.s4connector.s4.compatible_modstring
	try:
		ud.debug(ud.LDAP, ud.INFO, "Object DN=%s" % object['dn'])
	except: # FIXME: which exception is to be caught?
		ud.debug(ud.LDAP, ud.INFO, "Object DN not printable")
		
	ucs_object = s4connector._object_mapping(key, object, 'con')

	try:
		ud.debug(ud.LDAP, ud.INFO, "   UCS DN = %s" % ucs_object['dn'])
	except: # FIXME: which exception is to be caught?
		ud.debug(ud.LDAP, ud.INFO, "   UCS DN not printable")

	try:
		res = s4connector.lo.lo.search(base=ucs_object['dn'], scope='base', attr=['sambaLMPassword', 'sambaNTPassword','sambaPwdLastSet','sambaPwdMustChange', 'krb5PrincipalName', 'krb5Key', 'shadowLastChange', 'shadowMax', 'krb5PasswordEnd', 'univentionService'])
	except ldap.NO_SUCH_OBJECT:
		ud.debug(ud.LDAP, ud.PROCESS, "password_sync_ucs_to_s4: The UCS object (%s) was not found. The object was removed." % ucs_object['dn'])
		return
	
	services=res[0][1].get('univentionService', [])
	if 'Samba 4' in services:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: %s is a S4 server, skip password sync" % ucs_object['dn'])
		return
			
	sambaPwdLastSet = None
	if res[0][1].has_key('sambaPwdLastSet'):
		sambaPwdLastSet = long(res[0][1]['sambaPwdLastSet'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: sambaPwdLastSet: %s" % sambaPwdLastSet)
	
	sambaPwdMustChange = -1
	if res[0][1].has_key('sambaPwdMustChange'):
		sambaPwdMustChange = long(res[0][1]['sambaPwdMustChange'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: sambaPwdMustChange: %s" % sambaPwdMustChange)

	ucsLMhash = res[0][1].get('sambaLMPassword', [None])[0]
	ucsNThash = res[0][1].get('sambaNTPassword', [None])[0]
	krb5Principal = res[0][1].get('krb5PrincipalName', [None])[0]
	krb5Key = res[0][1].get('krb5Key', [])

	if not ucsNThash:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: sambaNTPassword missing in UCS LDAP, trying krb5Key")
		ucsNThash = extract_NThash_from_krb5key(krb5Key)

	if not ucsNThash:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: Failed to get NT Password-Hash from UCS LDAP")

	# ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: Password-Hash from UCS: %s" % ucsNThash)

	res=s4connector.lo_s4.lo.search_s(univention.s4connector.s4.compatible_modstring(object['dn']), ldap.SCOPE_BASE, '(objectClass=*)',['pwdLastSet','objectSid'])
	pwdLastSet = None
	if res[0][1].has_key('pwdLastSet'):
		pwdLastSet = long(res[0][1]['pwdLastSet'][0])
	objectSid = univention.s4connector.s4.decode_sid(res[0][1]['objectSid'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: pwdLastSet from S4 : %s" % pwdLastSet)
	# rid = None
	# if res[0][1].has_key('objectSid'):
	# 	rid = str(univention.s4connector.s4.decode_sid(res[0][1]['objectSid'][0]).split('-')[-1])

	pwd_set = False
	res=s4connector.lo_s4.lo.search_s(s4connector.lo_s4.base, ldap.SCOPE_SUBTREE, compatible_modstring('(objectSid=%s)' % objectSid), ['unicodePwd', 'userPrincipalName', 'supplementalCredentials', 'msDS-KeyVersionNumber', 'dBCSPwd'])
	unicodePwd_attr = res[0][1].get('unicodePwd', [None])[0]
	dBCSPwd_attr = res[0][1].get('dBCSPwd', [None])[0]
	userPrincipalName_attr = res[0][1].get('userPrincipalName', [None])[0]
	supplementalCredentials = res[0][1].get('supplementalCredentials', [None])[0]
	msDS_KeyVersionNumber = res[0][1].get('msDS-KeyVersionNumber', [0])[0]
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

	modlist=[]
	if krb5Principal != userPrincipalName_attr:
		if krb5Principal:
			if not userPrincipalName_attr:	## new and not old
				modlist.append((ldap.MOD_ADD, 'userPrincipalName', krb5Principal))
			else:				## new and old differ
				if krb5Principal.lower() != userPrincipalName_attr.lower():
					ud.debug(ud.LDAP, ud.WARN, "password_sync_ucs_to_s4: userPrincipalName != krb5Principal: '%s' != '%s'" % (userPrincipalName_attr, krb5Principal))
				modlist.append((ldap.MOD_REPLACE, 'userPrincipalName', krb5Principal))
		else:
			if userPrincipalName_attr:	## old and not new
				modlist.append((ldap.MOD_DELETE, 'userPrincipalName', userPrincipalName_attr))

	if not ucsNThash == s4NThash:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: NT Hash S4: %s NT Hash UCS: %s" % (s4NThash, ucsNThash))
		## Now if ucsNThash is empty there should at least some timestamp in UCS,
		## otherwise it's probably not a good idea to remove the unicodePwd.
		## Usecase: LDB module on ucs_3.0-0-ucsschool slaves creates XP computers/windows in UDM without password
		if ucsNThash or sambaPwdLastSet:
			pwd_set = True
			if unicodePwd_attr:
				modlist.append((ldap.MOD_DELETE, 'unicodePwd', unicodePwd_attr))
			if ucsNThash:
				unicodePwd_new = binascii.a2b_hex(ucsNThash)
				modlist.append((ldap.MOD_ADD, 'unicodePwd', unicodePwd_new))

	if not ucsLMhash == s4LMhash:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: LM Hash S4: %s LM Hash UCS: %s" % (s4LMhash, ucsLMhash))
		pwd_set = True
		if dBCSPwd_attr:
			modlist.append((ldap.MOD_DELETE, 'dBCSPwd', dBCSPwd_attr))
		if ucsLMhash:
			dBCSPwd_new = binascii.a2b_hex(ucsLMhash)
			modlist.append((ldap.MOD_ADD, 'dBCSPwd', dBCSPwd_new))

	if pwd_set or not supplementalCredentials:
		if krb5Principal:
			## encoding of Samba4 supplementalCredentials
			if supplementalCredentials:
				modlist.append((ldap.MOD_DELETE, 'supplementalCredentials', supplementalCredentials))
			if krb5Key:
				supplementalCredentials_new = calculate_supplementalCredentials(krb5Key, supplementalCredentials)
				if supplementalCredentials_new:
					modlist.append((ldap.MOD_ADD, 'supplementalCredentials', supplementalCredentials_new))
				else:
					ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: no supplementalCredentials_new")
				#if supplementalCredentials:
				#	modlist.append((ldap.MOD_REPLACE, 'msDS-KeyVersionNumber', krb5KeyVersionNumber))
				#else:
				#	modlist.append((ldap.MOD_ADD, 'msDS-KeyVersionNumber', krb5KeyVersionNumber))

		if sambaPwdMustChange >= 0 and sambaPwdMustChange < time.time():
			# password expired, must be changed on next login
			ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: samba pwd expired, set newpwdLastSet to 0")
			newpwdlastset = "0"
		else:
			if sambaPwdLastSet == None:
				sambaPwdLastSet = int(time.time())
				newpwdlastset = str(univention.s4connector.s4.samba2s4_time(sambaPwdLastSet))
			elif sambaPwdLastSet in [0, 1]:
				newpwdlastset = "0"
			else:
				newpwdlastset = str(univention.s4connector.s4.samba2s4_time(sambaPwdLastSet))
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: pwdlastset in modlist: %s" % newpwdlastset)
		modlist.append((ldap.MOD_REPLACE, 'pwdlastset', newpwdlastset))

	else:
		ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: No password change to sync to S4 ")

		# check pwdLastSet
		if sambaPwdLastSet != None:
			newpwdlastset = str(univention.s4connector.s4.samba2s4_time(sambaPwdLastSet))
			ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: sambaPwdLastSet: %d" % sambaPwdLastSet)
			ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: newpwdlastset  : %s" % newpwdlastset)
			ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: pwdLastSet (AD): %s" % pwdLastSet)
			if sambaPwdLastSet in [0, 1]:
				modlist.append((ldap.MOD_REPLACE, 'pwdlastset', "0"))
			elif pwdLastSet != newpwdlastset:
				modlist.append((ldap.MOD_REPLACE, 'pwdlastset', newpwdlastset))

	## TODO: Password History
	ctrl_bypass_password_hash = LDAPControl('1.3.6.1.4.1.7165.4.3.12',criticality=0)
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs_to_s4: modlist: %s" % modlist)
	if modlist:
		s4connector.lo_s4.lo.modify_ext_s(compatible_modstring(object['dn']), modlist, serverctrls=[ ctrl_bypass_password_hash ])


def password_sync_s4_to_ucs(s4connector, key, ucs_object, modifyUserPassword=True):
	_d=ud.function('ldap.s4.password_sync_s4_to_ucs')
	ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs called")

	object=s4connector._object_mapping(key, ucs_object, 'ucs')
	res=s4connector.lo_s4.lo.search_s(univention.s4connector.s4.compatible_modstring(object['dn']), ldap.SCOPE_BASE, '(objectClass=*)',['objectSid','pwdLastSet'])

	pwdLastSet = None
	if res[0][1].has_key('pwdLastSet'):
		pwdLastSet = long(res[0][1]['pwdLastSet'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: pwdLastSet from S4: %s (%s)" % (pwdLastSet,res))
	objectSid = univention.s4connector.s4.decode_sid(res[0][1]['objectSid'][0])

	# rid = None
	# if res[0][1].has_key('objectSid'):
	# 	rid = str(univention.s4connector.s4.decode_sid(res[0][1]['objectSid'][0]).split('-')[-1])

	res=s4connector.lo_s4.lo.search_s(s4connector.lo_s4.base, ldap.SCOPE_SUBTREE, univention.s4connector.s4.compatible_modstring('(objectSid=%s)' % objectSid), ['unicodePwd', 'supplementalCredentials', 'msDS-KeyVersionNumber', 'dBCSPwd'])
	unicodePwd_attr = res[0][1].get('unicodePwd', [None])[0]
	if unicodePwd_attr:
		ntPwd = binascii.b2a_hex(unicodePwd_attr).upper()

		lmPwd = ''
		dBCSPwd = res[0][1].get('dBCSPwd', [None])[0]
		if dBCSPwd:
			lmPwd = binascii.b2a_hex(dBCSPwd).upper()

		supplementalCredentials = res[0][1].get('supplementalCredentials', [None])[0]
		msDS_KeyVersionNumber = res[0][1].get('msDS-KeyVersionNumber', [0])[0]

		ntPwd_ucs = ''
		lmPwd_ucs = ''
		krb5Principal = ''
		userPassword = ''
		modlist=[]
		res=s4connector.lo.search(base=ucs_object['dn'], attr=['sambaPwdMustChange', 'sambaPwdLastSet','sambaNTPassword', 'sambaLMPassword', 'krb5PrincipalName', 'krb5Key', 'krb5KeyVersionNumber', 'userPassword', 'shadowLastChange', 'shadowMax', 'krb5PasswordEnd'])

		if res[0][1].has_key('sambaNTPassword'):
			ntPwd_ucs = res[0][1]['sambaNTPassword'][0]
		if res[0][1].has_key('sambaLMPassword'):
			lmPwd_ucs = res[0][1]['sambaLMPassword'][0]
		if res[0][1].has_key('krb5PrincipalName'):
			krb5Principal=res[0][1]['krb5PrincipalName'][0]
		if res[0][1].has_key('userPassword'):
			userPassword=res[0][1]['userPassword'][0]
		sambaPwdLastSet = None
		if res[0][1].has_key('sambaPwdLastSet'):
			sambaPwdLastSet=res[0][1]['sambaPwdLastSet'][0]
		ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: sambaPwdLastSet: %s" % sambaPwdLastSet)
		sambaPwdMustChange = ''
		if res[0][1].has_key('sambaPwdMustChange'):
			sambaPwdMustChange=res[0][1]['sambaPwdMustChange'][0]
		ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: sambaPwdMustChange: %s" % sambaPwdMustChange)
		krb5Key_ucs=res[0][1].get('krb5Key', [])
		userPassword_ucs=res[0][1].get('userPassword', [None])[0]
		krb5KeyVersionNumber=res[0][1].get('krb5KeyVersionNumber', [None])[0]

		pwd_changed = False
		if ntPwd != ntPwd_ucs:
			pwd_changed = True
			modlist.append(('sambaNTPassword', ntPwd_ucs, str(ntPwd)))

		if lmPwd != lmPwd_ucs:
			pwd_changed = True
			modlist.append(('sambaLMPassword', lmPwd_ucs, str(lmPwd)))

		if pwd_changed:
			if krb5Principal:
				## decoding of Samba4 supplementalCredentials
				krb5Key_new = calculate_krb5key(unicodePwd_attr, supplementalCredentials, int(msDS_KeyVersionNumber))
				
				modlist.append(('krb5Key', krb5Key_ucs, krb5Key_new))
				if int(msDS_KeyVersionNumber) != int(krb5KeyVersionNumber):
					modlist.append(('krb5KeyVersionNumber', krb5KeyVersionNumber, msDS_KeyVersionNumber))

			## Append modification as well to modlist, to apply in one transaction
			if modifyUserPassword:
				modlist.append(('userPassword', userPassword_ucs, '{K5KEY}'))

			# Remove the POSIX and Kerberos password expiry interval
			if res[0][1].has_key('shadowLastChange'):
				modlist.append(('shadowLastChange', res[0][1]['shadowLastChange'][0], None))
			if res[0][1].has_key('shadowMax'):
				modlist.append(('shadowMax', res[0][1]['shadowMax'][0], None))
			if res[0][1].has_key('krb5PasswordEnd'):
				modlist.append(('krb5PasswordEnd', res[0][1]['krb5PasswordEnd'][0], None))
		else:
			ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: No password change to sync to UCS")

		if pwd_changed and (pwdLastSet or pwdLastSet == 0):
			newSambaPwdMustChange = sambaPwdMustChange
			if pwdLastSet == 0: # pwd change on next login
				newSambaPwdMustChange = str(pwdLastSet)
				newSambaPwdLastSet = str(pwdLastSet)
			else:
				newSambaPwdLastSet = str(univention.s4connector.s4.s42samba_time(pwdLastSet))
				userobject = s4connector.get_ucs_object('user', ucs_object['dn'])
				if not userobject:
					ud.debug(ud.LDAP, ud.ERROR, "password_sync_s4_to_ucs: couldn't get user-object from UCS")
					return False
				sambaPwdMustChange=sambaPwdMustChange.strip()
				if not sambaPwdMustChange.isdigit():
					pass
				elif pwd_changed or (long(sambaPwdMustChange) < time.time() and not pwdLastSet == 0):
					pwhistoryPolicy = userobject.loadPolicyObject('policies/pwhistory')
					try:
						expiryInterval=int(pwhistoryPolicy['expiryInterval'])
						newSambaPwdMustChange = str(long(newSambaPwdLastSet)+(expiryInterval*3600*24) )
					except: # FIXME: which exception is to be caught?
						# expiryInterval is empty or no legal int-string
						pwhistoryPolicy['expiryInterval']=''
						expiryInterval=-1
						newSambaPwdMustChange = ''

					ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: pwhistoryPolicy: expiryInterval: %s" %
										   expiryInterval)


			if sambaPwdLastSet:
				if sambaPwdLastSet != newSambaPwdLastSet:
					modlist.append(('sambaPwdLastSet', sambaPwdLastSet, newSambaPwdLastSet))
					ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: sambaPwdLastSet in modlist (replace): %s" %
										newSambaPwdLastSet)
			else:
				modlist.append(('sambaPwdLastSet', '', newSambaPwdLastSet ))
				ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: sambaPwdLastSet in modlist (set): %s" %
									newSambaPwdLastSet)

			if sambaPwdMustChange != newSambaPwdMustChange:
				# change if password has changed or "change pwd on next login" is not set
				# set sambaPwdMustChange regarding to the univention-policy
				if sambaPwdMustChange:
					modlist.append(('sambaPwdMustChange', sambaPwdMustChange, newSambaPwdMustChange))
					ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: sambaPwdMustChange in modlist (replace): %s" %
							       newSambaPwdMustChange)
				else:
					modlist.append(('sambaPwdMustChange', '', newSambaPwdMustChange))
					ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: sambaPwdMustChange in modlist (set): %s" %
							       newSambaPwdMustChange)

		if len(modlist)>0:	
			ud.debug(ud.LDAP, ud.INFO, "password_sync_s4_to_ucs: modlist: %s" % modlist)
			s4connector.lo.lo.modify(ucs_object['dn'], modlist)


	else:
		ud.debug(ud.LDAP, ud.WARN, "password_sync_ucs_s4_to_ucs: Failed to get Password-Hash from S4")


def password_sync_s4_to_ucs_no_userpassword(s4connector, key, ucs_object):
	# The userPassword should not synchronized for computer accounts
	password_sync_s4_to_ucs(s4connector, key, ucs_object, modifyUserPassword=False)

