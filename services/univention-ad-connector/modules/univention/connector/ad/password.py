#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  control the password sync communication with the ad password service
#
# Copyright 2004-2014 Univention GmbH
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
import array, socket, ldap
import univention.debug2 as ud
import univention.connector.ad

import M2Crypto

def nt_password_to_arcfour_hmac_md5(nt_password):
	# all arcfour-hmac-md5 keys begin this way
	key='0\x1d\xa1\x1b0\x19\xa0\x03\x02\x01\x17\xa1\x12\x04\x10'
	
	for i in range(0, 16):
		o=nt_password[2*i:2*i+2]
		key+=chr(int(o, 16))
	return key
	
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

def ssl_init(sd):
	meth = M2Crypto.__m2crypto.sslv3_method();
	ctx = M2Crypto.__m2crypto.ssl_ctx_new (meth);
	ssl = M2Crypto.__m2crypto.ssl_new (ctx);
	M2Crypto.__m2crypto.ssl_set_fd (ssl, sd);
	err = M2Crypto.__m2crypto.ssl_connect (ssl);
	return ssl

def set_password_in_ad(connector, samaccountname, pwd):
	_d=ud.function('ldap.ad.set_password_in_ad')
	compatible_modstring = univention.connector.ad.compatible_modstring

	a = array.array('c')
	
	if connector.lo_ad.binddn:
		bind_username = univention.connector.ad.explode_unicode_dn(connector.lo_ad.binddn,1)[0]
	else:
		bind_username = connector.baseConfig['%s/ad/ldap/binddn' % connector.CONFIGBASENAME]
	
	_append ( a, bind_username )
	_append ( a, connector.lo_ad.bindpw )
	a.append ( 'S' )

	# The copypwd utility on the windows side needs the
	# username as iso8859 string. See Bug #8516
	# _append ( a, compatible_modstring(samaccountname) )
	_append ( a, samaccountname.encode(connector.baseConfig.get('connector/password/service/encoding', 'iso8859-15')))

	_append ( a, str(pwd) )
	package = array.array('c')
	_append_array( package, a)

	# Create Socket and send package
	s = socket.socket( socket.AF_INET, socket.SOCK_STREAM );
	s.connect ( (connector.lo_ad.host, 6670) )
	ssl=ssl_init(s.fileno())
	M2Crypto.__m2crypto.ssl_write(ssl, package)

	return M2Crypto.__m2crypto.ssl_read(ssl, 8192)


def get_password_from_ad(connector, rid):
	_d=ud.function('ldap.ad.get_password_from_ad')
	a = array.array('c')

	if connector.lo_ad.binddn:
		bind_username = univention.connector.ad.explode_unicode_dn(connector.lo_ad.binddn,1)[0]
	else:
		bind_username = connector.baseConfig['%s/ad/ldap/binddn' % connector.CONFIGBASENAME]
	
	_append ( a, bind_username )
	_append ( a, connector.lo_ad.bindpw )
	a.append ( 'G' )

	_append(a, rid)
		
	package = array.array('c')
	_append_array( package, a)

	# Create Socket and send package
	s = socket.socket( socket.AF_INET, socket.SOCK_STREAM );

	s.connect ( (connector.lo_ad.host, 6670) )
	ssl=ssl_init(s.fileno())
	M2Crypto.__m2crypto.ssl_write(ssl, package)

	return M2Crypto.__m2crypto.ssl_read(ssl, 8192)


def password_sync_ucs(connector, key, object):
	_d=ud.function('ldap.ad.password_sync_ucs')
	# externes Programm zum Überptragen des Hash aufrufen
	# per ldapmodify pwdlastset auf -1 setzen

	compatible_modstring = univention.connector.ad.compatible_modstring
	try:
		ud.debug(ud.LDAP, ud.INFO, "Object DN=%s" % object['dn'])
	except: # FIXME: which exception is to be caught?
		ud.debug(ud.LDAP, ud.INFO, "Object DN not printable")
		
	ucs_object = connector._object_mapping(key, object, 'con')

	try:
		ud.debug(ud.LDAP, ud.INFO, "   UCS DN = %s" % ucs_object['dn'])
	except: # FIXME: which exception is to be caught?
		ud.debug(ud.LDAP, ud.INFO, "   UCS DN not printable")

	try:
		res = connector.lo.lo.search(base=ucs_object['dn'], scope='base', attr=['sambaLMPassword', 'sambaNTPassword','sambaPwdLastSet'])
	except ldap.NO_SUCH_OBJECT:
		ud.debug(ud.LDAP, ud.PROCESS, "password_sync_ucs: The UCS object (%s) was not found. The object was removed." % ucs_object['dn'])
		return
	
	sambaPwdLastSet = None
	if res[0][1].has_key('sambaPwdLastSet'):
		sambaPwdLastSet = long(res[0][1]['sambaPwdLastSet'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: sambaPwdLastSet: %s" % sambaPwdLastSet)
	
	pwd = None
	if res[0][1].has_key('sambaNTPassword'):
		pwd=res[0][1]['sambaNTPassword'][0]
	else:
		pwd='NO PASSWORDXXXXXX'
		ud.debug(ud.LDAP, ud.WARN, "password_sync_ucs: Failed to get NT Hash from UCS")

	if pwd in ['NO PASSWORDXXXXXX', 'NO PASSWORD*********************']:
		ud.debug(ud.LDAP, ud.PROCESS, "The sambaNTPassword hash is set to %s. Skip the synchronisation of this hash to AD." % pwd)
		

	if res[0][1].has_key('sambaLMPassword'):
		pwd+=res[0][1]['sambaLMPassword'][0]
	else:
		pwd+='NO PASSWORDXXXXX'
		if connector.baseConfig.is_true('password/samba/lmhash'):
			ud.debug(ud.LDAP, ud.WARN, "password_sync_ucs: Failed to get LM Hash from UCS")

	res=connector.lo_ad.lo.search_s(univention.connector.ad.compatible_modstring(object['dn']), ldap.SCOPE_BASE, '(objectClass=*)',['pwdLastSet','objectSid'])
	pwdLastSet = None
	if res[0][1].has_key('pwdLastSet'):
		pwdLastSet = long(res[0][1]['pwdLastSet'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: pwdLastSet from AD : %s" % pwdLastSet)
	rid = None
	if res[0][1].has_key('objectSid'):
		rid = str(univention.connector.ad.decode_sid(res[0][1]['objectSid'][0]).split('-')[-1])

	# Only sync passwords from UCS to AD when the password timestamp in UCS is newer
	if connector.baseConfig.is_true('%s/ad/password/timestamp/check' % connector.CONFIGBASENAME, False):
		ad_password_last_set = 0
		# If sambaPwdLast was set to 1 the password must be changed on next login. In this
		# case the timestamp is ignored and the password will be synced. This behaviour can
		# be disbled by setting connector/ad/password/timestamp/syncreset/ucs to false. This
		# might be necessary if the connector is configured in read mode and the password will be
		# synced in two ways: Bug #22653
		if sambaPwdLastSet > 1 or ( sambaPwdLastSet <= 2 and connector.baseConfig.is_false('%s/ad/password/timestamp/syncreset/ucs' % connector.CONFIGBASENAME, False)):
			ad_password_last_set = univention.connector.ad.ad2samba_time(pwdLastSet)
			if sambaPwdLastSet:
				if long(ad_password_last_set) >= long(sambaPwdLastSet):
					# skip
					ud.debug(ud.LDAP, ud.PROCESS, "password_sync: Don't sync the password from UCS to AD because the AD password equal or is newer.")
					ud.debug(ud.LDAP, ud.INFO, "password_sync:  AD pwdlastset: %s (original (%s))" % (ad_password_last_set, pwdLastSet))
					ud.debug(ud.LDAP, ud.INFO, "password_sync: UCS pwdlastset: %s" % (sambaPwdLastSet))
					return

		ud.debug(ud.LDAP, ud.INFO, "password_sync: Sync the passwords from UCS to AD.")
		ud.debug(ud.LDAP, ud.INFO, "password_sync:  AD pwdlastset: %s (original (%s))" % (ad_password_last_set, pwdLastSet))
		ud.debug(ud.LDAP, ud.INFO, "password_sync: UCS pwdlastset: %s" % (sambaPwdLastSet))
	
	pwd_set = False
	pwd_ad_res = get_password_from_ad(connector, rid)
	pwd_ad = ''
	if len(pwd_ad_res) >3 and _get_integer(pwd_ad_res[4:]) == 0:
		pwd_ad = pwd_ad_res[12:].split(':')[1].strip().upper()
	else:
		ud.debug(ud.LDAP, ud.WARN, "password_sync_ucs: Failed to get Password-Hash from AD")
	res = ''

	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: Hash AD: %s Hash UCS: %s"%(pwd_ad,pwd))
	if not pwd == pwd_ad:
		pwd_set = True
		res = set_password_in_ad(connector, object['attributes']['sAMAccountName'][0], pwd)

	if not pwd_set or len(res) >3 and _get_integer(res[4:]) == 0 :
		newpwdlastset = "-1" # if pwd was set in ad we need to set pwdlastset to -1 or it will be 0		
		#if sambaPwdMustChange >= 0 and sambaPwdMustChange < time.time():
		#	# password expired, must be changed on next login
		#	ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: samba pwd expired, set newpwdLastSet to 0")
		#	newpwdlastset = "0"
		if sambaPwdLastSet <= 1:
			newpwdlastset = "0" # User must change his password
		elif pwdLastSet and int(pwdLastSet) > 0 and not pwd_set:
			newpwdlastset = "1"
		if long(newpwdlastset) != 1:
			ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: pwdlastset in modlist: %s" % newpwdlastset)
			connector.lo_ad.lo.modify_s(compatible_modstring(object['dn']), [(ldap.MOD_REPLACE, 'pwdlastset', newpwdlastset)])
		else:
			ud.debug(ud.LDAP, ud.INFO, "password_sync_ucs: don't modify pwdlastset")
	else:
		ud.debug(ud.LDAP, ud.ERROR, "password_sync_ucs: Failed to sync Password from AD ")

		#if res and len(res) >3 and _get_integer(res[4:]) == 0:
		#	connector.lo_ad.lo.modify_s(compatible_modstring(object['dn']), [(ldap.MOD_REPLACE, 'pwdlastset', "-1")])
		#else:
		#	ud.debug(ud.LDAP, ud.ERROR, "password_sync_ucs: Failed to sync Password from AD ")

def password_sync_kinit(connector, key, ucs_object):
	_d=ud.function('ldap.ad.password_sync_kinit')

	object=connector._object_mapping(key, ucs_object, 'ucs')

	attr = {'userPassword': '{KINIT}', 'sambaNTPassword': 'NO PASSWORD*********************', 'sambaLMPassword': 'NO PASSWORD*********************'}

	ucs_result=connector.lo.search(base=ucs_object['dn'], attr=attr.keys())
	
	modlist = []
	for attribute in attr.keys():
		expected_value = attr[attribute]
		if ucs_result[0][1].has_key(attribute):
			userPassword = ucs_result[0][1][attribute][0]
			if userPassword != expected_value:
				modlist.append((ldap.MOD_REPLACE, attribute, expected_value))

	if modlist:
		connector.lo.lo.lo.modify_s(univention.connector.ad.compatible_modstring(ucs_object['dn']), modlist)

def password_sync(connector, key, ucs_object):
	_d=ud.function('ldap.ad.password_sync')
	# externes Programm zum holen des Hash aufrufen
	# "kerberos_now"

	object=connector._object_mapping(key, ucs_object, 'ucs')
	res=connector.lo_ad.lo.search_s(univention.connector.ad.compatible_modstring(object['dn']), ldap.SCOPE_BASE, '(objectClass=*)',['objectSid','pwdLastSet'])

	if connector.isInCreationList(object['dn']):
		connector.removeFromCreationList(object['dn'])
		ud.debug(ud.LDAP, ud.INFO, "password_sync: Synchronisation of password has been canceled. Object was just created.")
		return

	pwdLastSet = None
	if res[0][1].has_key('pwdLastSet'):
		pwdLastSet = long(res[0][1]['pwdLastSet'][0])
	ud.debug(ud.LDAP, ud.INFO, "password_sync: pwdLastSet from AD: %s (%s)" % (pwdLastSet,res))

	rid = None
	if res[0][1].has_key('objectSid'):
		rid = str(univention.connector.ad.decode_sid(res[0][1]['objectSid'][0]).split('-')[-1])

	ucs_result=connector.lo.search(base=ucs_object['dn'], attr=['sambaPwdLastSet','sambaNTPassword', 'sambaLMPassword', 'krb5PrincipalName', 'shadowLastChange', 'shadowMax', 'krb5PasswordEnd'])

	sambaPwdLastSet = None
	if ucs_result[0][1].has_key('sambaPwdLastSet'):
		sambaPwdLastSet=ucs_result[0][1]['sambaPwdLastSet'][0]
	ud.debug(ud.LDAP, ud.INFO, "password_sync: sambaPwdLastSet: %s" % sambaPwdLastSet)

	if connector.baseConfig.is_true('%s/ad/password/timestamp/check' % connector.CONFIGBASENAME, False):
		# Only sync the passwords from AD to UCS when the pwdLastSet timestamps in AD are newer
		ad_password_last_set = 0

		# If pwdLastSet was set to 0 the password must be changed on next login. In this
		# case the timestamp is ignored and the password will be synced. This behaviour can
		# be disabled by setting connector/ad/password/timestamp/syncreset/ad to false. This
		# might be necessary if the connector is configured in read mode and the password will be
		# synced in two ways: Bug #22653
		if (pwdLastSet > 1) or (pwdLastSet in [0,1] and connector.baseConfig.is_false('%s/ad/password/timestamp/syncreset/ad' % connector.CONFIGBASENAME, False)):
			ad_password_last_set = univention.connector.ad.ad2samba_time(pwdLastSet)
			if sambaPwdLastSet:
				if long(sambaPwdLastSet) >= long(ad_password_last_set) and long(sambaPwdLastSet) != 1:
					# skip
					ud.debug(ud.LDAP, ud.PROCESS, "password_sync: Don't sync the passwords from AD to UCS because the UCS password is equal or newer.")
					ud.debug(ud.LDAP, ud.INFO, "password_sync:  AD pwdlastset: %s (original (%s))" % (ad_password_last_set, pwdLastSet))
					ud.debug(ud.LDAP, ud.INFO, "password_sync: UCS pwdlastset: %s" % (sambaPwdLastSet))
					return

		ud.debug(ud.LDAP, ud.INFO, "password_sync: Sync the passwords from AD to UCS.")
		ud.debug(ud.LDAP, ud.INFO, "password_sync:  AD pwdlastset: %s (original (%s))" % (ad_password_last_set, pwdLastSet))
		ud.debug(ud.LDAP, ud.INFO, "password_sync: UCS pwdlastset: %s" % (sambaPwdLastSet))

	res = get_password_from_ad(connector, rid)

	if len(res) >3 and _get_integer(res[4:]) == 0:
		ntPwd_ucs = ''
		lmPwd_ucs = ''
		krb5Principal = ''
		userPassword = ''

		data = res[12:].split(':')[1].strip()
		ntPwd = data[:32]
		lmPwd = data[32:]
		modlist=[]

		if ucs_result[0][1].has_key('sambaLMPassword'):
			lmPwd_ucs = ucs_result[0][1]['sambaLMPassword'][0]
		if ucs_result[0][1].has_key('sambaNTPassword'):
			ntPwd_ucs = ucs_result[0][1]['sambaNTPassword'][0]
		if ucs_result[0][1].has_key('krb5PrincipalName'):
			krb5Principal=ucs_result[0][1]['krb5PrincipalName'][0]
		if ucs_result[0][1].has_key('userPassword'):
			userPassword=ucs_result[0][1]['userPassword'][0]

		pwd_changed = False

 		if lmPwd.upper() != lmPwd_ucs.upper():
			if not lmPwd in ['00000000000000000000000000000000', 'NO PASSWORD*********************']:
				pwd_changed = True
				modlist.append(('sambaLMPassword', lmPwd_ucs, str(lmPwd.upper())))
		if ntPwd.upper() != ntPwd_ucs.upper():
			if ntPwd in ['00000000000000000000000000000000', 'NO PASSWORD*********************']:
				ud.debug(ud.LDAP, ud.WARN, "password_sync: AD connector password daemon retured 0 for the nt hash. Please check the AD settings.")
			else:
				pwd_changed = True
				modlist.append(('sambaNTPassword', ntPwd_ucs, str(ntPwd.upper())))
				if krb5Principal:
					connector.lo.lo.lo.modify_s(univention.connector.ad.compatible_modstring(ucs_object['dn']),
									[(ldap.MOD_REPLACE, 'krb5Key', nt_password_to_arcfour_hmac_md5(ntPwd.upper()))])
		if pwd_changed:
			connector.lo.lo.lo.modify_s(univention.connector.ad.compatible_modstring(ucs_object['dn']), [(ldap.MOD_REPLACE, 'userPassword', '{K5KEY}')])
			# Remove the POSIX and Kerberos password expiry interval
			if ucs_result[0][1].has_key('shadowLastChange'):
				modlist.append(('shadowLastChange', ucs_result[0][1]['shadowLastChange'][0], None))
			if ucs_result[0][1].has_key('shadowMax'):
				modlist.append(('shadowMax', ucs_result[0][1]['shadowMax'][0], None))
			if ucs_result[0][1].has_key('krb5PasswordEnd'):
				modlist.append(('krb5PasswordEnd', ucs_result[0][1]['krb5PasswordEnd'][0], None))

			if pwdLastSet or pwdLastSet == 0:
				newSambaPwdLastSet = str(univention.connector.ad.ad2samba_time(pwdLastSet))

				if sambaPwdLastSet:
					if sambaPwdLastSet != newSambaPwdLastSet:
						modlist.append(('sambaPwdLastSet', sambaPwdLastSet, newSambaPwdLastSet))
						ud.debug(ud.LDAP, ud.INFO, "password_sync: sambaPwdLastSet in modlist (replace): %s" %
											newSambaPwdLastSet)
				else:
					modlist.append(('sambaPwdLastSet', '', newSambaPwdLastSet ))
					ud.debug(ud.LDAP, ud.INFO, "password_sync: sambaPwdLastSet in modlist (set): %s" %
										newSambaPwdLastSet)

		if len(modlist)>0:	
			connector.lo.lo.modify(ucs_object['dn'], modlist)


	else:
		ud.debug(ud.LDAP, ud.ERROR, "password_sync: sync failed, no result from AD" )


