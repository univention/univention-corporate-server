#!/usr/bin/python2.4
#
# Univention AD Connector
#  control the password sync communication with the ad password service
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
# 
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


import os, time
import array, socket, ldap
import univention.debug
import univention.connector.ad

import M2Crypto

def nt_password_to_arcfour_hmac_md5(nt_password):
	# all arcfour-hmac-md5 keys begin this way
	key='0\x1d\xa1\x1b0\x19\xa0\x03\x02\x01\x17\xa1\x12\x04\x10'
	
	for i in range(0, 16):
		o=nt_password[2*i:2*i+2]
		key+=chr(int(o, 16))
	return key
	
def lm_password_to_user_password(lm_password):
	return '{LANMAN}%s' % lm_password
	
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
	meth = M2Crypto.__m2crypto.sslv2_method();
	ctx = M2Crypto.__m2crypto.ssl_ctx_new (meth);
	ssl = M2Crypto.__m2crypto.ssl_new (ctx);
	M2Crypto.__m2crypto.ssl_set_fd (ssl, sd);
	err = M2Crypto.__m2crypto.ssl_connect (ssl);
	return ssl

def set_password_in_ad(connector, samaccountname, pwd):
	compatible_modstring = univention.connector.ad.compatible_modstring

	a = array.array('c')
	
	_append ( a, univention.connector.ad.explode_unicode_dn(connector.lo_ad.binddn,1)[0] )
	_append ( a, connector.lo_ad.bindpw )
	a.append ( 'S' )
	_append ( a, compatible_modstring(samaccountname) )
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
	a = array.array('c')

	_append ( a, univention.connector.ad.explode_unicode_dn(connector.lo_ad.binddn,1)[0] )
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
	# externes Programm zum Überptragen des Hash aufrufen
	# per ldapmodify pwdlastset auf -1 setzen
	
	compatible_modstring = univention.connector.ad.compatible_modstring
	try:
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "Object DN=%s" % object['dn'])
	except:
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "Object DN not printable")
		
	ucs_object = connector._object_mapping(key, object, 'con')

	try:
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "   UCS DN = %s" % ucs_object['dn'])
	except:
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "   UCS DN not printable")

	res = connector.lo.lo.search(base=ucs_object['dn'], scope='base', attr=['sambaLMPassword', 'sambaNTPassword','sambaPwdLastSet','sambaPwdMustChange'])
	
	sambaPwdLastSet = None
	if res[0][1].has_key('sambaPwdLastSet'):
		sambaPwdLastSet = long(res[0][1]['sambaPwdLastSet'][0])
	univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync_ucs: sambaPwdLastSet: %s" % sambaPwdLastSet)
	
	sambaPwdMustChange = -1
	if res[0][1].has_key('sambaPwdMustChange'):
		sambaPwdMustChange = long(res[0][1]['sambaPwdMustChange'][0])
	univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync_ucs: sambaPwdMustChange: %s" % sambaPwdMustChange)

	pwd=None
	if res[0][1].has_key('sambaLMPassword') and res[0][1].has_key('sambaNTPassword'):
		pwd=res[0][1]['sambaNTPassword'][0]+res[0][1]['sambaLMPassword'][0]

	if not pwd:
		univention.debug.debug(univention.debug.LDAP, univention.debug.WARN, "password_sync_ucs: Failed to get Password-Hash from UCS")

	res=connector.lo_ad.lo.search_s(univention.connector.ad.compatible_modstring(object['dn']), ldap.SCOPE_BASE, '(objectClass=*)',['pwdLastSet','objectSid'])
	pwdLastSet = None
	if res[0][1].has_key('pwdLastSet'):
		pwdLastSet = long(res[0][1]['pwdLastSet'][0])
	univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync_ucs: pwdLastSet from AD : %s" % pwdLastSet)
	rid = None
	if res[0][1].has_key('objectSid'):
		rid = str(univention.connector.ad.decode_sid(res[0][1]['objectSid'][0]).split('-')[-1])

	pwd_set = False
	pwd_ad_res = get_password_from_ad(connector, rid)
	pwd_ad = ''
	if len(pwd_ad_res) >3 and _get_integer(pwd_ad_res[4:]) == 0:
		pwd_ad = pwd_ad_res[12:].split(':')[1].strip().upper()
	else:
		univention.debug.debug(univention.debug.LDAP, univention.debug.WARN, "password_sync_ucs: Failed to get Password-Hash from AD")
	res = ''

	univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync_ucs: Hash AD: %s Hash UCS: %s"%(pwd_ad,pwd))
	if not pwd == pwd_ad:
		pwd_set = True
		res = set_password_in_ad(connector, object['attributes']['sAMAccountName'][0], pwd)

	if not pwd_set or len(res) >3 and _get_integer(res[4:]) == 0 :
		newpwdlastset = "-1" # if pwd was set in ad we need to set pwdlastset to -1 or it will be 0		
		if sambaPwdMustChange >= 0 and sambaPwdMustChange < time.time():
			# password expired, must be changed on next login
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync_ucs: samba pwd expired, set newpwdLastSet to 0")
			newpwdlastset = "0"
		elif pwdLastSet and int(pwdLastSet) > 0 and not pwd_set:
			newpwdlastset = "1"
		if not long(newpwdlastset) > 0: # means: not == 1
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync_ucs: pwdlastset in modlist: %s" % newpwdlastset)
			connector.lo_ad.lo.modify_s(compatible_modstring(object['dn']), [(ldap.MOD_REPLACE, 'pwdlastset', newpwdlastset)])
		else:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync_ucs: don't modify pwdlastset")
	else:
		univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR, "password_sync_ucs: Failed to sync Password from AD ")

	res=connector.lo_ad.lo.search_s(univention.connector.ad.compatible_modstring(object['dn']), ldap.SCOPE_BASE, '(objectClass=*)',['pwdLastSet'])
	pwdLastSet = None
	if res[0][1].has_key('pwdLastSet'):
		pwdLastSet = long(res[0][1]['pwdLastSet'][0])
	univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync_ucs: pwdLastSet from AD : %s" % pwdLastSet)


def password_sync(connector, key, ucs_object):
	# externes Programm zum holen des Hash aufrufen
	# "kerberos_now"

	object=connector._object_mapping(key, ucs_object, 'ucs')
	res=connector.lo_ad.lo.search_s(univention.connector.ad.compatible_modstring(object['dn']), ldap.SCOPE_BASE, '(objectClass=*)',['objectSid','pwdLastSet'])

	pwdLastSet = None
	if res[0][1].has_key('pwdLastSet'):
		pwdLastSet = long(res[0][1]['pwdLastSet'][0])
	univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync: pwdLastSet from AD: %s (%s)" % (pwdLastSet,res))

	rid = None
	if res[0][1].has_key('objectSid'):
		rid = str(univention.connector.ad.decode_sid(res[0][1]['objectSid'][0]).split('-')[-1])

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
		res=connector.lo.search(base=ucs_object['dn'], attr=['sambaPwdMustChange', 'sambaPwdLastSet','sambaNTPassword', 'sambaLMPassword', 'krb5PrincipalName'])

		if res[0][1].has_key('sambaLMPassword') and res[0][1].has_key('sambaNTPassword'):
			ntPwd_ucs = res[0][1]['sambaNTPassword'][0]
			lmPwd_ucs = res[0][1]['sambaLMPassword'][0]
		if res[0][1].has_key('krb5PrincipalName'):
			krb5Principal=res[0][1]['krb5PrincipalName'][0]
		if res[0][1].has_key('userPassword'):
			userPassword=res[0][1]['userPassword'][0]
		sambaPwdLastSet = None
		if res[0][1].has_key('sambaPwdLastSet'):
			sambaPwdLastSet=res[0][1]['sambaPwdLastSet'][0]
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync: sambaPwdLastSet: %s" % sambaPwdLastSet)
		sambaPwdMustChange = ''
		if res[0][1].has_key('sambaPwdMustChange'):
			sambaPwdMustChange=res[0][1]['sambaPwdMustChange'][0]
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync: sambaPwdMustChange: %s" % sambaPwdMustChange)

		pwd_changed = False
		if ntPwd.upper() != ntPwd_ucs.upper() and lmPwd.upper() != lmPwd_ucs.upper():
			pwd_changed = True
			modlist.append(('sambaNTPassword', ntPwd_ucs, str(ntPwd.upper())))
			modlist.append(('sambaLMPassword', lmPwd_ucs, str(lmPwd.upper())))
			if krb5Principal:
				connector.lo.lo.lo.modify_s(univention.connector.ad.compatible_modstring(ucs_object['dn']),
								[(ldap.MOD_REPLACE, 'krb5Key', nt_password_to_arcfour_hmac_md5(ntPwd.upper()))])
			connector.lo.lo.lo.modify_s(univention.connector.ad.compatible_modstring(ucs_object['dn']),
							[(ldap.MOD_REPLACE, 'userPassword', lm_password_to_user_password(lmPwd.upper()))])
		if pwdLastSet or pwdLastSet == 0:
			newSambaPwdMustChange = sambaPwdMustChange
			if pwdLastSet == 0: # pwd change on next login
				newSambaPwdMustChange = str(pwdLastSet)
				newSambaPwdLastSet = str(pwdLastSet)
			else:
				newSambaPwdLastSet = str(univention.connector.ad.ad2samba_time(pwdLastSet))
				userobject = connector.get_ucs_object('user', ucs_object['dn'])
				if not userobject:
					univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR, "password_sync: couldn't get user-object from UCS")
					return False
				sambaPwdMustChange=sambaPwdMustChange.strip()
				if not sambaPwdMustChange.isdigit():
					pass
				elif pwd_changed or (long(sambaPwdMustChange) < time.time() and not pwdLastSet == 0):
					pwhistoryPolicy = userobject.loadPolicyObject('policies/pwhistory')
					try:
						expiryInterval=int(pwhistoryPolicy['expiryInterval'])
						newSambaPwdMustChange = str(long(newSambaPwdLastSet)+(expiryInterval*3600*24) )
					except:
						# expiryInterval is empty or no legal int-string
						pwhistoryPolicy['expiryInterval']=''
						expiryInterval=-1
						newSambaPwdMustChange = ''

					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync: pwhistoryPolicy: expiryInterval: %s" %
										   expiryInterval)


			if sambaPwdLastSet:
				if sambaPwdLastSet != newSambaPwdLastSet:
					modlist.append(('sambaPwdLastSet', sambaPwdLastSet, newSambaPwdLastSet))
					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync: sambaPwdLastSet in modlist (replace): %s" %
										newSambaPwdLastSet)
			else:
				modlist.append(('sambaPwdLastSet', '', newSambaPwdLastSet ))
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync: sambaPwdLastSet in modlist (set): %s" %
									newSambaPwdLastSet)

			if sambaPwdMustChange != newSambaPwdMustChange:
				# change if password has changed or "change pwd on next login" is not set
				# set sambaPwdMustChange regarding to the univention-policy
				if sambaPwdMustChange:
					modlist.append(('sambaPwdMustChange', sambaPwdMustChange, newSambaPwdMustChange))
					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync: sambaPwdMustChange in modlist (replace): %s" %
							       newSambaPwdMustChange)
				else:
					modlist.append(('sambaPwdMustChange', '', newSambaPwdMustChange))
					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "password_sync: sambaPwdMustChange in modlist (set): %s" %
							       newSambaPwdMustChange)

		if len(modlist)>0:	
			connector.lo.lo.modify(ucs_object['dn'], modlist)


	else:
		univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR, "password_sync: sync failed, no result from AD" )


