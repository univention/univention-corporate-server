#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  Basic class for the AD connector part
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


import string, ldap, sys, traceback, base64, time, pdb, os, copy, types
import array
import univention.uldap
import univention.connector

def activate_user (connector, key, object):
        # set userAccountControl to 544
        for i in range(0,10):
                try:
                        connector.lo_ad.lo.modify_s(compatible_modstring(object['dn']), [(ldap.MOD_REPLACE, 'userAccountControl', ['544'])])
                except ldap.NO_SUCH_OBJECT:
                        time.sleep(1)
                        continue
                return True
        return False

def group_members_sync_from_ucs(connector, key, object):
	return connector.group_members_sync_from_ucs(key, object)
	
def group_members_sync_to_ucs(connector, key, object):
	return connector.group_members_sync_to_ucs(key, object)

def primary_group_sync_from_ucs(connector, key, object):
	return connector.primary_group_sync_from_ucs(key, object)
	
def primary_group_sync_to_ucs(connector, key, object):
	return connector.primary_group_sync_to_ucs(key, object)

def disable_user_from_ucs(connector, key, object):
	return connector.disable_user_from_ucs(key, object)

def disable_user_to_ucs(connector, key, object):
	return connector.disable_user_to_ucs(key, object)

def encode_attrib(attrib):
	if not attrib or type(attrib) == type(u''): # referral or already unicode
		return attrib
	return unicode(attrib, 'utf8')

def encode_attriblist(attriblist):
	if not type(attriblist) == type([]):
		return encode_attrib(attriblist)
	else:
		for i in range(len(attriblist)):
			attriblist[i] = encode_attrib(attriblist[i])
		return attriblist

def encode_ad_object(ad_object):
	if type(ad_object) == type([]):
		return encode_attriblist(ad_object)
	else:
		for key in ad_object.keys():
			if key == 'objectSid':
				ad_object[key]=[decode_sid(ad_object[key][0])]
			elif key in ['objectGUID','ipsecData','repsFrom','replUpToDateVector','userCertificate','dNSProperty','dnsRecord','securityIdentifier','mS-DS-CreatorSID','logonHours','mSMQSites','mSMQSignKey','currentLocation','dSASignature','linkTrackSecret','mSMQDigests','mSMQEncryptKey','mSMQSignCertificates','may','sIDHistory', 'msExchMailboxSecurityDescriptor', 'msExchMailboxGuid']:
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
						       "encode_ad_object: attrib %s ignored during encoding" % key) # don't recode
			else:
				try:
					ad_object[key]=encode_attriblist(ad_object[key])
				except:
					univention.debug.debug(univention.debug.LDAP, univention.debug.WARN,
							       "encode_ad_object: encode attrib %s failed, ignored!" % key)
		return ad_object

def encode_ad_result(ad_result):
	'''
	encode an result from an python-ldap search
	'''
	return (encode_attrib(ad_result[0]),encode_ad_object(ad_result[1]))

def encode_ad_resultlist(ad_resultlist):
	'''
	encode an result from an python-ldap search
	'''
	for i in range(len(ad_resultlist)):
		ad_resultlist[i] = encode_ad_result(ad_resultlist[i])
	return ad_resultlist

def unix2ad_time(l):
	d=116444736000000000L #difference between 1601 and 1970
	return long(time.mktime(time.gmtime(time.mktime(time.strptime(l,"%d.%m.%y"))+90000)))*10000000+d # 90000s are one day and one hour

def ad2unix_time(l):
	d=116444736000000000L #difference between 1601 and 1970
	return time.strftime("%d.%m.%y",time.gmtime((l-d)/10000000))

def samba2ad_time(l):
	d=116444736000000000L #difference between 1601 and 1970
	return long(time.mktime(time.gmtime(l+3600)))*10000000+d

def ad2samba_time(l):
	d=116444736000000000L #difference between 1601 and 1970
	return long(((l-d))/10000000)

# mapping funtions
def samaccountname_dn_mapping(connector, given_object, dn_mapping_stored, ucsobject, propertyname, propertyattrib, ocucs, ucsattrib, ocad):
	'''
	map dn of given object (which must have an samaccountname in AD)
	ocucs and ocad are objectclasses in UCS and AD
	'''
	object = copy.deepcopy(given_object)

	samaccountname = ''
	
	if object['dn'] != None:
		if object['attributes'].has_key('sAMAccountName'):
			samaccountname=object['attributes']['sAMAccountName'][0]
		
	def dn_premapped(object, dn_key, dn_mapping_stored):
		if (not dn_key in dn_mapping_stored) or (not object[dn_key]):
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: not premapped (in first instance)")
			return False
		else: # check if DN exists
			if ucsobject:
				if connector.get_object(object[dn_key]) != None:
					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: premapped AD object found")
					return True
				else:
					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: premapped AD object not found")
					return False
			else:
				if connector.get_ucs_ldap_object(object[dn_key]) != None:
					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: premapped UCS object found")
					return True
				else:
					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: premapped UCS object not found")
					return False
					
								

	for dn_key in ['dn','olddn']:
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: check newdn for key %s:"%dn_key)
		if object.has_key(dn_key) and not dn_premapped(object, dn_key, dn_mapping_stored):

			dn = object[dn_key]

			# Skip Configuration objects with empty DNs
			if dn == None:
				break

			pos = string.find(dn,'=')
			pos2 =  len(univention.connector.ad.explode_unicode_dn(dn)[0])
			attrib = dn[:pos]
			value = dn[pos+1:pos2]

			if ucsobject:
				# lookup the cn as sAMAccountName in AD to get corresponding DN, if not found create new
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: got an UCS-Object")

				if connector.property[propertyname].mapping_table and propertyattrib in connector.property[propertyname].mapping_table.keys():
					for ucsval, conval in connector.property[propertyname].mapping_table[propertyattrib]:
						try:
							if value.lower() == ucsval.lower():
								value = conval
								univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: map samaccountanme regarding to mapping-table")
								continue
						except UnicodeDecodeError:
							pass # values are not the same codec
								
				
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: search in ad samaccountname=%s"%value)
				result = connector.lo_ad.lo.search_ext_s(connector.lo_ad.base,ldap.SCOPE_SUBTREE,
								     compatible_modstring('(&(objectclass=%s)(samaccountname=%s))'%(ocad,value)))
				if result and len(result)>0 and result[0] and len(result[0])>0 and result[0][0]: # no referral, so we've got a valid result
					addn = encode_attrib(result[0][0])
					adpos2 = len(univention.connector.ad.explode_unicode_dn(addn)[0])
					if dn_key == 'olddn' or (dn_key == 'dn' and not object.has_key('olddn')):
						newdn = addn
					else:
						addn = addn[:adpos2] + dn[pos2:]
						newdn = addn.lower().replace(connector.lo_ad.base.lower(), connector.lo.base.lower())					
					
				else:
					newdn = 'cn' + dn[pos:] #new object, don't need to change

			else:
				# get the object to read the sAMAccountName in AD and use it as name
				# we have no fallback here, the given dn must be found in AD or we've got an error
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: got an AD-Object")
				i = 0
				
				while ( not samaccountname ): # in case of olddn this is already set
					i = i + 1
					search_dn = dn
					if object.has_key('deleted_dn'):
						search_dn = object['deleted_dn']
					try:
						samaccountname = encode_attrib(
							connector.lo_ad.lo.search_ext_s(compatible_modstring(search_dn), ldap.SCOPE_BASE,
											'(objectClass=%s)' % ocad, ['sAMAccountName']) [0][1]['sAMAccountName'][0])
						univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: got samaccountname from AD")
					except ldap.NO_SUCH_OBJECT: # AD may need time
						if i > 5:
							raise
						time.sleep(1) # AD may need some time...

				pos = string.find(dn,'=')
				pos2 = len(univention.connector.ad.explode_unicode_dn(dn)[0])

				if connector.property[propertyname].mapping_table and propertyattrib in connector.property[propertyname].mapping_table.keys():
					for ucsval, conval in connector.property[propertyname].mapping_table[propertyattrib]:
						if samaccountname.lower() == conval.lower():
							samaccountname = ucsval
							univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: map samaccountanme regarding to mapping-table")
							continue
						else:
							univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: samaccountname not in mapping-table")

				# search for object with this dn in ucs, needed if it lies in a different container
				ucsdn = ''
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: samaccountname is:%s"%samaccountname)
				ucsdn_result = connector.lo.search(filter=unicode(u'(&(objectclass=%s)(%s=%s))' % (ocucs, ucsattrib, samaccountname)),
								   base=connector.lo.base, scope='sub', attr=['objectClass'])
				if ucsdn_result and len(ucsdn_result) > 0 and ucsdn_result[0] and len(ucsdn_result[0]) > 0:
					ucsdn = ucsdn_result[0][0]
					
				if ucsdn and (dn_key == 'olddn' or (dn_key == 'dn' and not object.has_key('olddn'))):
					newdn = ucsdn
					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: newdn is ucsdn")
				else:
					newdn = ucsattrib + '=' + samaccountname + dn[pos2:] # guess the old dn
			try:
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: newdn for key %s:" % dn_key)
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: olddn: %s" % dn)
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: newdn: %s" % newdn)
			except:
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "samaccount_dn_mapping: dn-print failed")


			object[dn_key]=newdn
	return object


def user_dn_mapping(connector, given_object, dn_mapping_stored, isUCSobject):
	'''
	map dn of given user using the samaccountname/uid
	connector is an instance of univention.connector.ad, given_object an object-dict,
	dn_mapping_stored a list of dn-types which are already mapped because they were stored in the config-file
	'''
	return samaccountname_dn_mapping(connector, given_object, dn_mapping_stored, isUCSobject, 'user', u'samAccountName', u'posixAccount', 'uid', u'user')

def group_dn_mapping(connector, given_object, dn_mapping_stored, isUCSobject):
	'''
	map dn of given group using the samaccountname/cn
	connector is an instance of univention.connector.ad, given_object an object-dict,
	dn_mapping_stored a list of dn-types which are already mapped because they were stored in the config-file
	'''
	return samaccountname_dn_mapping(connector, given_object, dn_mapping_stored, isUCSobject, 'group', u'cn', u'posixGroup', 'cn', u'group')

def old_user_dn_mapping(connector, given_object):
	object = copy.deepcopy(given_object)

	# LDAP_SERVER_SHOW_DELETED_OID -> 1.2.840.113556.1.4.417
	ctrls = [LDAPControl('1.2.840.113556.1.4.417',criticality=1)]
	samaccountname = ''

	if object.has_key('sAMAccountName'):
		samaccountname=object['sAMAccountName']
		
	for dn_key in ['dn','olddn']:
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "check newdn for key %s:"%dn_key)
		if object.has_key(dn_key):

			dn = object[dn_key]

			pos = string.find(dn,'=')
			pos2 = len(univention.connector.ad.explode_unicode_dn(dn)[0])-1
			attrib = dn[:pos]
			value = dn[pos+1:pos2]

			if attrib == 'uid':
				# lookup the uid as sAMAccountName in AD to get corresponding DN, if not found create new User
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "search in ad samaccountname=%s"%value)
				result = connector.lo_ad.lo.search_ext_s(connector.lo_ad.base,ldap.SCOPE_SUBTREE,
								     '(&(objectclass=user)(samaccountname=%s))'%compatible_modstring(value))
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "search in result %s"%result)
				if result and len(result)>0 and result[0] and len(result[0])>0 and result[0][0]: # no referral, so we've got a valid result
					addn = encode_attrib(result[0][0])
					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "search in ad gave dn %s"%addn)
					adpos2 = len(univention.connector.ad.explode_unicode_dn(addn)[0])-1					
					#newdn = addn[:adpos2] + dn[pos2:]
					newdn = addn
				else:
 					newdn = 'cn' + dn[pos:]

			else:
				# get the object to read the sAMAccountName in AD and use it as uid
				# we have no fallback here, the given dn must be found in AD or we've got an error
				i = 0
				while ( not samaccountname ): # in case of olddn this is already set
					i = i + 1
					search_dn = dn
					if object.has_key('deleted_dn'):
						search_dn = object['deleted_dn']
					try:
						samaccountname = encode_attrib(
							connector.lo_ad.lo.search_ext_s(compatible_modstring(search_dn), ldap.SCOPE_BASE,
											'(objectClass=user)', ['sAMAccountName'],
											serverctrls=ctrls) [0][1]['sAMAccountName'][0])
					except ldap.NO_SUCH_OBJECT: # AD may need time
						if i > 5:
							raise
						time.sleep(1) # AD may need some time...

				pos = string.find(dn,'=')
				pos2 = len(univention.connector.ad.explode_unicode_dn(dn)[0])-1

				newdn = 'uid=' + samaccountname + dn[pos2:]
			try:
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "newdn for key %s:"%dn_key)
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "olddn: %s"%dn)
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "newdn: %s"%newdn)
			except:
				pass

			object[dn_key]=newdn
	return object

def decode_sid(value):
	# SID in AD
	#
	#   | Byte 1         | Byte 2-7           | Byte 9-12                | Byte 13-16 |
	#   ----------------------------------------------------------------------------------------------------------------
	#   | Der erste Wert | Gibt die Laenge    | Hier sind jetzt          | siehe 9-12 |
	#   | der SID, also  | des restlichen     | die eiegntlichen         |            |
	#   | der Teil nach  | Strings an, da die | SID Daten.               |            |
	#   | S-             | SID immer relativ  | In einem int Wert        |            |
	#   |                | kurz ist, meistens | sind die Werte           |            |
	#   |                | nur das 2. Byte    | Hexadezimal gespeichert. |            |
	#
	sid='S-'
	sid+="%d" % ord(value[0])
	
	sid_len=ord(value[1])
	
	sid+="-%d" % ord(value[7])
	
	for i in range(0,sid_len):
		res=ord(value[8+(i*4)]) + (ord(value[9+(i*4)]) << 8) + (ord(value[10+(i*4)]) << 16) + (ord(value[11+(i*4)]) << 24)
		sid+="-%u" % res
			
	return sid

def encode_sid(value):
	a=array.array('c')

	vlist=value.replace('S-','').split('-')
	a.append(chr(int(vlist[0])))
	a.append(chr(len(vlist)-2))
	a.append(chr(0))
	a.append(chr(0))
	a.append(chr(0))
	a.append(chr(0))
	a.append(chr(0))
	a.append(chr(int(vlist[1])))
	for i in range(2,len(vlist)):
		a.append(chr((long(vlist[i]) & 0xff)))
		a.append(chr((long(vlist[i]) & 0xff00) >> 8))
		a.append(chr((long(vlist[i]) & 0xff0000) >> 16))
		a.append(chr((long(vlist[i]) & 0xff000000) >> 24))

	return a


def encode_object_sid(sid_string, encode_in_base64=True):
    binary_encoding = ""

    for i in sid.split("-")[1:]:
        j = int(i)

        oc1 = (j >> 24)
        oc2 = (j - (oc1 * (2 << 23))) >> 16
        oc3 = (j - (oc1 * (2 << 23)) - (oc2 * (2 << 15))) >> 8
        oc4 = j - (oc1 * (2 << 23)) - (oc2 * (2 << 15)) - (oc3 * (2 << 7))

        binary_encoding_chunk = chr(oc4) + chr(oc3) + chr(oc2) + chr(oc1)
        binary_encoding += binary_encoding_chunk

    if encode_in_base64:
        return base64.encodestring(binary_encoding)

    return binary_encoding

def encode_object_sid_to_binary_ldapfilter(sid_string):
    binary_encoding = ""

    # The first two bytes do not seem to follow the expected binary LDAP filter
    # conversion scheme. Thus, we skip them and prepend the encoding of "1-5"
    # statically

    univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"encode_object_sid_to_binary %s:" % str(sid_string))

    
    for i in sid_string.split("-")[3:]:
        j = hex(int(i))
        hex_repr = (((8-len(j[2:]))*"0") + j[2:])

        binary_encoding_chunk  = '\\' + hex_repr[6:8] + "\\" + hex_repr[4:6] + "\\" + hex_repr[2:4] + "\\" + hex_repr[0:2]
        binary_encoding += binary_encoding_chunk

    return "\\01\\05\\00\\00\\00\\00\\00\\05" + binary_encoding



def encode_list(list, encoding):
	newlist=[]
	for val in list:
		if hasattr(val,'encode'):
			newlist.append(val.encode(encoding))
		else:
			newlist.append(val)
	return newlist

def decode_list(list, encoding):
	newlist=[]
	for val in list:
		if hasattr(val,'decode') and not type(val) == types.UnicodeType:
			newlist.append(val.decode(encoding))
		else:
			newlist.append(val)
	return newlist

def unicode_list(list, encoding):
	newlist=[]
	if encoding:
		for val in list:
			newlist.append(unicode(val,encoding))
	else:
		for val in list:
			newlist.append(unicode(val))
	return newlist

def encode_modlist(list, encoding):
	newlist=[]
	for (modtype, attr, values) in list:
		if hasattr(attr,'encode'):
			newattr=attr.encode(encoding)
		else:
			newattr=attr
		if type(values) == type([]):
			newlist.append((modtype,newattr,encode_list(values, encoding)))
		else:
			newlist.append((modtype,newattr,encode_list(values, encoding)))
	return newlist

def decode_modlist(list, encoding):
	newlist=[]
	for (modtype, attr, values) in list:
		if hasattr(attr,'decode') and not type(attr)==types.UnicodeType:
			newattr=attr.decode(encoding)
		else:
			newattr=attr
		if type(values) == type([]):
			newlist.append((modtype,newattr,decode_list(values, encoding)))
		else:
			newlist.append((modtype,newattr,decode_list(values, encoding)))
	return newlist

def encode_addlist(list, encoding):
	newlist=[]
	for (attr, values) in list:
		if hasattr(attr,'encode'):
			newattr=attr.encode(encoding)
		else:
			newattr=attr
		if type(values) == type([]):
			newlist.append((newattr,encode_list(values, encoding)))
		else:
			newlist.append((newattr,encode_list(values, encoding)))
	return newlist

def decode_addlist(list, encoding):
	newlist=[]
	for (attr, values) in list:
		if hasattr(attr,'decode') and not type(attr)==types.UnicodeType:
			newattr=attr.decode(encoding)
		else:
			newattr=attr
		if type(values) == type([]):
			newlist.append((newattr,decode_list(values, encoding)))
		else:
			newlist.append((newattr,decode_list(values, encoding)))
	return newlist

def compatible_list(list):
	return encode_list(decode_list(list,'latin'),'utf8')

def compatible_modlist(list):
	return encode_modlist(decode_modlist(list,'latin'),'utf8')

def compatible_addlist(list):
	return encode_addlist(decode_addlist(list,'latin'),'utf8')

def compatible_modstring(string):
	if hasattr(string,'decode') and not type(string) == types.UnicodeType:
		string = string.decode('latin')
	if hasattr(string,'encode'):
		string = string.encode('utf8')
	return string

def explode_unicode_dn(dn, notypes=0):
	ret = []
	last = -1
	last_found = 0
	while dn.find(',',last+1) > 0:
		last = dn.find(',',last+1)
		if dn[last-1] != '\\':
			if notypes == 1:
				last_found = dn.find('=',last_found)+1
			if dn[last_found] == ',':
				last_found += 1
			ret.append(dn[last_found:last])
			last_found = last			
	
	return ret

class ad(univention.connector.ucs):
	def __init__(self, property, baseConfig, ad_ldap_host, ad_ldap_port, ad_ldap_base, ad_ldap_binddn, ad_ldap_bindpw, ad_ldap_certificate, listener_dir):

		univention.connector.ucs.__init__(self, property, baseConfig, listener_dir)

		self.lo_ad=univention.uldap.access(host=ad_ldap_host, port=int(ad_ldap_port), base=ad_ldap_base, binddn=ad_ldap_binddn, bindpw=ad_ldap_bindpw, start_tls=2, ca_certfile=ad_ldap_certificate, decode_ignorelist=['objectSid', 'objectGUID', 'repsFrom', 'replUpToDateVector', 'ipsecData', 'logonHours', 'userCertificate', 'dNSProperty', 'dnsRecord', 'member'])
		self.lo_ad.lo.set_option(ldap.OPT_REFERRALS,0)
		self.baseConfig = baseConfig

		if not self.config.has_section('AD'):
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"__init__: init add config section 'AD'")
			self.config.add_section('AD')

		if not self.config.has_section('AD rejected'):
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"__init__: init add config section 'AD rejected'")
			self.config.add_section('AD rejected')
			
		if not self.config.has_option('AD','lastUSN'):
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"__init__: init lastUSN with 0")
			self._set_config_option('AD','lastUSN','0')

		if not self.config.has_section('AD GUID'):
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"__init__: init add config section 'AD GUID'")
			self.config.add_section('AD GUID')
		try:
			self.ad_sid = univention.connector.ad.decode_sid(
				self.lo_ad.lo.search_ext_s(ad_ldap_base,ldap.SCOPE_BASE,
										   'objectclass=domain',['objectSid'],
										   timeout=-1, sizelimit=0)[0][1]['objectSid'][0])
			
		except Exception, msg:
			print "Failed to get SID from AD: %s" % msg
			sys.exit(1)


	# encode string to unicode
	def encode(self, string):
		try:
			return unicode(string)
		except:
			return unicode(string, 'Latin-1')
			
	def _get_lastUSN(self):
		_d=univention.debug.function('ldap._get_lastUSN')
		return int(self._get_config_option('AD','lastUSN'))
	
	def get_lastUSN(self):
		return self._get_lastUSN()

	def _set_lastUSN(self, lastUSN):
		_d=univention.debug.function('ldap._set_lastUSN')
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"_set_lastUSN: new lastUSN is: %s" % lastUSN)
		self._set_config_option('AD','lastUSN',str(lastUSN))

	# save ID's
	def __check_base64(self,string):
		# check if base64 encoded string string has correct length
		if not len(string) & 3 == 0:
			string = string + "="*(4 - len(string) & 3)
		return string

	def __encode_GUID(self, GUID):
		# GUID may be unicode
		if type(GUID) == type(u''):
			return GUID.encode('ISO-8859-1').encode('base64')
		else:
			return unicode(GUID,'latin').encode('ISO-8859-1').encode('base64')

	def _get_DN_for_GUID(self,GUID):
		_d=univention.debug.function('ldap._get_DN_for_GUID')
		return self._decode_dn_from_config_option(self._get_config_option('AD GUID', self.__encode_GUID(GUID)))
		
		
	def _set_DN_for_GUID(self,GUID,DN):
		_d=univention.debug.function('ldap._set_DN_for_GUID')
		self._set_config_option('AD GUID', self.__encode_GUID(GUID), self._encode_dn_as_config_option(DN))

	def _remove_GUID(self,GUID):
		_d=univention.debug.function('ldap._remove_GUID')
		self._remove_config_option('AD GUID', self.__encode_GUID(GUID))

## handle rejected Objects

	def _save_rejected(self, id, dn):
		_d=univention.debug.function('ldap._save_rejected')
		try:
			self._set_config_option('AD rejected',str(id),compatible_modstring(dn))
		except UnicodeEncodeError, msg:
			self._set_config_option('AD rejected',str(id),'unknown')
			self._debug_traceback(univention.debug.WARN,
					      "failed to set dn in configfile (AD rejected)")

	def _get_rejected(self, id):
		_d=univention.debug.function('ldap._get_rejected')
		return self._get_config_option('AD rejected',str(id))

	def _remove_rejected(self,id):
		_d=univention.debug.function('ldap._remove_rejected')
		self._remove_config_option('AD rejected',str(id))

	def _list_rejected(self):
		_d=univention.debug.function('ldap._list_rejected')
		result = []
		for i in self._get_config_items('AD rejected'):
			result.append(i)
		return result

	def list_rejected(self):
		return self._list_rejected()

	def save_rejected(self, object):
		"""
		save object as rejected
		"""
		_d=univention.debug.function('ldap.save_rejected')
		self._save_rejected(self.__get_change_usn(object),object['dn'])

	def remove_rejected(self, object):
		"""
		remove object from rejected
		"""
		_d=univention.debug.function('ldap.remove_rejected')
		self._remove_rejected(self.__get_change_usn(object),object['dn'])


	def get_object(self, dn):
		_d=univention.debug.function('ldap.get_object')
		try:
			dn, ad_object=self.lo_ad.lo.search_ext_s(compatible_modstring(dn),ldap.SCOPE_BASE,'(objectClass=*)')[0]
			try:
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"get_object: got object: %s" % dn)
			except:
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"get_object: got object: <print failed>")
			return encode_ad_object(ad_object)
		except ldap.SERVER_DOWN:
			raise
		except:			
			pass
		

	def __get_change_usn(self, object):
		'''
		get change usn as max(uSNCreated,uSNChanged)
		'''
		_d=univention.debug.function('ldap.__get_change_usn')
		if not object:
			return 0
		usnchanged=0
		usncreated=0		
		if object['attributes'].has_key('uSNCreated'):
			usncreated = int(object['attributes']['uSNCreated'][0])
		if object['attributes'].has_key('uSNChanged'):
			usnchanged = int(object['attributes']['uSNChanged'][0])

		return max(usnchanged,usncreated)

	def __search_ad(self, show_deleted=False, filter=''):
		'''
		search ad
		'''
		_d=univention.debug.function('ldap.__search_ad')
		ctrls=[]
		if show_deleted:
			# LDAP_SERVER_SHOW_DELETED_OID -> 1.2.840.113556.1.4.417
			ctrls.append(LDAPControl('1.2.840.113556.1.4.417',criticality=1))
		return encode_ad_resultlist(self.lo_ad.lo.search_ext_s(self.lo_ad.base,ldap.SCOPE_SUBTREE,filter,serverctrls=ctrls))
		

	def __search_ad_changes(self, show_deleted=False, filter=''):
		'''
		search ad for changes since last update (changes greater lastUSN)
		'''
		_d=univention.debug.function('ldap.__search_ad_changes')
		lastUSN = self._get_lastUSN()
		# filter erweitern um "(|(uSNChanged>=lastUSN+1)(uSNCreated>=lastUSN+1))"
		# +1 da suche nur nach '>=', nicht nach '>' möglich
		if filter != '':
			newfilter = '(&(%s)(|(uSNChanged>=%s)(uSNCreated>=%s)))' % (filter,lastUSN+1,lastUSN+1)
		else:
			newfilter = '(|(uSNChanged>=%s)(uSNCreated>=%s))' % (lastUSN+1,lastUSN+1)
		try:
			return self.__search_ad(filter=newfilter, show_deleted=show_deleted)
		except ldap.SERVER_DOWN:
			raise
		except: #AD can`t return > 1000 results, we are going to split the search
			returnd=[]
			highestCommittedUSN = self.__get_highestCommittedUSN()
			tmpUSN=lastUSN
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "__search_ad_changes: need to split results. highest USN is %s, lastUSN is %s"%(highestCommittedUSN,lastUSN))
			while (tmpUSN != highestCommittedUSN):
				lastUSN=tmpUSN
				tmpUSN+=999
				if tmpUSN > highestCommittedUSN:
					tmpUSN=highestCommittedUSN
				if filter != '':
					newfilter = '(&(%s)(&(|(uSNChanged>=%s)(uSNCreated>=%s))(uSNChanged<=%s)))' %(filter,lastUSN+1,lastUSN+1,tmpUSN)
				else:
					newfilter = '(&(|(uSNChanged>=%s)(uSNCreated>=%s))(uSNChanged<=%s))' %(lastUSN+1,lastUSN+1,tmpUSN)
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "__search_ad_changes: search between USNs %s and %s"%(lastUSN+1,tmpUSN))
				returnd=returnd+self.__search_ad(filter=newfilter, show_deleted=show_deleted)
			return returnd
				

	def __search_ad_changeUSN(self, changeUSN, show_deleted=True, filter=''):
		'''
		search ad for change with id
		'''
		_d=univention.debug.function('ldap.__search_ad_changeUSN')
		if filter != '':
			filter = '(&(%s)(|(uSNChanged=%s)(uSNCreated=%s)))' % (filter,changeUSN,changeUSN)
		else:
			filter = '(|(uSNChanged=%s)(uSNCreated=%s))' % (changeUSN,changeUSN)
		return self.__search_ad(filter=filter, show_deleted=show_deleted)


	def __dn_from_deleted_object(self, object):
		'''
		gets dn for deleted object (original dn before the object was moved into the deleted objects container)
		'''
		_d=univention.debug.function('ldap.__dn_from_deleted_object')

		# In Windows 2000 there's no lastKnownParent attribute. Thus, we have to map the
		# relevant object according to the objectGUID of the removed object
		if self.baseConfig.has_key('connector/ad/windows_version') and self.baseConfig['connector/ad/windows_version'] == "win2000":
			GUID = object['objectGUID'][0]
			return self._get_DN_for_GUID(GUID)

		# FIXME: should be called recursively, if containers are deleted subobjects have lastKnowParent in deletedObjects
 		rdn = object['dn'][:string.find(object['dn'],'DEL:')-3]
 		if object['attributes'].has_key('lastKnownParent'):
 			return rdn + "," + object['attributes']['lastKnownParent'][0]							
 		else:
 			univention.debug.debug(univention.debug.LDAP, univention.debug.WARN, 'lastKnownParent attribute for deleted object rdn="%s" was not set, so we must ignore the object' % rdn )
 			return None

	def __object_from_element(self, element):
		"""
		gets an object from an LDAP-element, implements necessary mapping

		"""
		_d=univention.debug.function('ldap.__object_from_element')
		if element[0] == 'None' or element[0] == None:
			return None # referrals
		object = {}
		object['dn'] = self.encode(element[0])
		deleted_object = False
		GUID = element[1]['objectGUID'][0]
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "GUID: %s " % str(GUID))

		# modtype
		if element[1].has_key('isDeleted') and element[1]['isDeleted'][0] == 'TRUE':
			object['modtype'] = 'delete'
			deleted_object = True

			# Windows 2000 doesn't provide a LastKnownParent attribute for deleted objects
			# Thus, we need to perform mapping according to the objectGUID, so do not delete
			# it if running against Windows 2000
			if self.baseConfig.has_key('connector/ad/windows_version') and self.baseConfig['connector/ad/windows_version'] == "win2000":
				pass
			else:
				self._remove_GUID(GUID)
		else:
			#check if is moved
			olddn = self.encode(self._get_DN_for_GUID(GUID))
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "object_from_element: olddn: %s"%olddn)
			if olddn and not compatible_modstring(olddn).lower() == compatible_modstring(self.encode(element[0])).lower(): #.encode('ISO-8859-1'): # FIXME: better encoding possible
				object['modtype'] = 'move'
				object['olddn'] = olddn
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "object_from_element: detected move of AD-Object")
			else:
				object['modtype'] = 'modify'

		object['attributes'] = element[1]
		for key in object['attributes'].keys():
			vals = []
			for value in object['attributes'][key]:
				vals.append(self.encode(value))
			object['attributes'][key] = vals	

		
			
		if deleted_object: # dn is in deleted-objects-container, need to parse to original dn
			object['deleted_dn'] = object['dn']
			object['dn'] = self._get_DN_for_GUID(GUID)
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "w2k: DN of removed object: %s" % object['dn'])
			
			if not object['dn']:
				return None
		return object

	def __identify(self, object):
		_d=univention.debug.function('ldap.__identify')
		if not object or not object.has_key('attributes'):
			return None
		for key in self.property.keys():
			if self._filter_match(self.property[key].con_search_filter,object['attributes']):
				return key

	def __update_lastUSN(self, object):
		"""
		Update der lastUSN
		"""
		_d=univention.debug.function('ldap.__update_lastUSN')
		if self.__get_change_usn(object) > self._get_lastUSN():
			self._set_lastUSN(self.__get_change_usn(object))

	def __get_highestCommittedUSN(self):
		'''
		get highestCommittedUSN stored in AD
		'''
		_d=univention.debug.function('ldap.__get_highestCommittedUSN')
		try:
			res=self.lo_ad.lo.search_ext_s('', # base
				 ldap.SCOPE_BASE,
				 'objectclass=*', # filter
				 ['highestCommittedUSN'],
				 timeout=-1, sizelimit=0)[0][1]['highestCommittedUSN'][0]

			return int(res)
		except Exception, msg:
			self._debug_traceback(univention.debug.ERROR,
								  "search for highestCommittedUSN failed")
			print "ERROR: initial search in AD failed, check network and configuration"
			return 0

	def set_primary_group_to_ucs_user(self, object_key, object_ucs):
		'''
		check if correct primary group is set to a fresh UCS-User
		'''
		_d=univention.debug.function('ldap.set_primary_group_to_ucs_user')

		ad_group_rid_resultlist = encode_ad_resultlist(self.lo_ad.lo.search_ext_s(self.lo_ad.base,ldap.SCOPE_SUBTREE,
							   'samaccountname=%s' % compatible_modstring(object_ucs['username']),
							   timeout=-1, sizelimit=0))

		if not ad_group_rid_resultlist[0][0] in ['None','',None]:

			ad_group_rid = ad_group_rid_resultlist[0][1]['primaryGroupID'][0]

			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
								   "set_primary_group_to_ucs_user: AD rid: %s"%ad_group_rid)
			object_sid_string = str(self.ad_sid) + "-" + str(ad_group_rid)
			if self.baseConfig.has_key('connector/ad/windows_version') and self.baseConfig['connector/ad/windows_version'] == "win2000":
				object_sid_string = encode_object_sid_to_binary_ldapfilter(object_sid_string)

			ldap_group_ad = encode_ad_resultlist(self.lo_ad.lo.search_ext_s(self.lo_ad.base,ldap.SCOPE_SUBTREE,
								   "objectSid=" + object_sid_string,
								   timeout=-1, sizelimit=0))

			if not ldap_group_ad[0][0]:
				univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR, "ad.set_primary_group_to_ucs_user: Primary Group in AD not found (not enough rights?), sync of this object will fail!")
			ucs_group = self._object_mapping('group',{'dn':ldap_group_ad[0][0],'attributes':ldap_group_ad[0][1]}, object_type='con')


			object_ucs['primaryGroup'] = ucs_group['dn']

	def primary_group_sync_from_ucs(self, key, object): # object mit ad-dn
		'''
		sync primary group of an ucs-object to ad
		'''
		_d=univention.debug.function('ldap.primary_group_sync_from_ucs')

		object_key = key
		object_ucs = self._object_mapping(object_key,object)

		ldap_object_ucs = self.get_ucs_ldap_object(object_ucs['dn'])

		ldap_object_ad = self.get_object(object['dn'])
		
		ucs_group_id = ldap_object_ucs['gidNumber'][0] # FIXME: fails if group does not exsist
		ucs_group_ldap = self.lo.search(filter='(&(objectClass=univentionGroup)(gidNumber=%s))' % ucs_group_id) # is empty !?

		if ucs_group_ldap == []:
			univention.debug.debug(univention.debug.LDAP, univention.debug.WARN,
								   "primary_group_sync_from_ucs: failed to get UCS-Group with gid %s, can't sync to AD"%ucs_group_id)
			return


		member_key = 'group' # FIXME: generate by identify-function ?
		ad_group_object = self._object_mapping(member_key, {'dn':ucs_group_ldap[0][0], 'attributes': ucs_group_ldap[0][1]}, 'ucs')
		ldap_object_ad_group = self.get_object(ad_group_object['dn'])
		rid = "513" # FIXME: Fallback: should be configurable
		if ldap_object_ad_group and ldap_object_ad_group.has_key('objectSid'):
			sid = ldap_object_ad_group['objectSid'][0]
			rid = sid[string.rfind(sid,"-")+1:]
		else:
			print "no SID !!!"

		# to set a valid primary group we need to:
		# - check if either the primaryGroupID is already set to rid or
		# - proove that the user is member of this group, so: at first we need the ad_object for this element
		# this means we need to map the user to get it's AD-DN which would call this function recursively

		if ldap_object_ad.has_key("primaryGroupID") and ldap_object_ad["primaryGroupID"][0] == rid:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
								   "primary_group_sync_from_ucs: primary Group is correct, no changes needed")
			return True # nothing left to do
		else:
			is_member = False
			if ldap_object_ad_group.has_key('member'):
				for member in ldap_object_ad_group['member']:
					if compatible_modstring(object['dn']).lower() == compatible_modstring(member).lower():
						is_member = True # FIXME: should left the for-loop here for better perfomance

			if not is_member: # add as member
				ad_members = []
				if ldap_object_ad_group.has_key('member'):
					for member in ldap_object_ad_group['member']:
						ad_members.append(compatible_modstring(member))
				ad_members.append(compatible_modstring(object['dn']))
				self.lo_ad.lo.modify_s(compatible_modstring(ad_group_object['dn']),[(ldap.MOD_REPLACE, 'member', ad_members)])
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
									   "primary_group_sync_from_ucs: primary Group needed change of membership in AD")
				
			# set new primary group
			self.lo_ad.lo.modify_s(compatible_modstring(object['dn']),[(ldap.MOD_REPLACE, 'primaryGroupID', rid)])
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
								   "primary_group_sync_from_ucs: changed primary Group in AD")
			return True


	def primary_group_sync_to_ucs(self, key, object): # object mit ucs-dn
		'''
		sync primary group of an ad-object to ucs
		'''
		_d=univention.debug.function('ldap.primary_group_sync_to_ucs')

		object_key = key

		ad_object = self._object_mapping(object_key,object,'ucs')
		ldap_object_ad = self.get_object(ad_object['dn'])
		ad_group_rid = ldap_object_ad['primaryGroupID'][0]
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   "primary_group_sync_to_ucs: AD rid: %s"%ad_group_rid)

		object_sid_string = str(self.ad_sid) + "-" + str(ad_group_rid)

		if self.baseConfig.has_key('connector/ad/windows_version') and self.baseConfig['connector/ad/windows_version'] == "win2000":
			object_sid_string = encode_object_sid_to_binary_ldapfilter(object_sid_string)

		ldap_group_ad = encode_ad_resultlist(self.lo_ad.lo.search_ext_s(self.lo_ad.base,ldap.SCOPE_SUBTREE,
							   ('objectSID=' + object_sid_string),
							   timeout=-1, sizelimit=0))

		ucs_group = self._object_mapping('group',{'dn':ldap_group_ad[0][0],'attributes':ldap_group_ad[0][1]})

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   "primary_group_sync_to_ucs: ucs-group: %s" % ucs_group['dn'])

		ucs_admin_object=univention.admin.objects.get(self.modules[object_key], co='', lo=self.lo, position='', dn=object['dn'])
		ucs_admin_object.open()

		if not ucs_admin_object['primaryGroup'].lower() == ucs_group['dn'].lower():
			# need to set to dn with correct case or the ucs-module will fail
			new_group = ucs_group['dn'].lower()
			ucs_admin_object['primaryGroup'] = new_group
			ucs_admin_object.modify()

			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
								   "primary_group_sync_to_ucs: changed primary Group in ucs")
		else:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
								   "primary_group_sync_to_ucs: change of primary Group in ucs not needed")
		

	def group_members_sync_from_ucs(self, key, object): # object mit ad-dn
		"""
		sync groupmembers in AD if changend in UCS
		"""
		_d=univention.debug.function('ldap.group_members_sync_from_ucs')

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"group_members_sync_from_ucs: %s"%object)

		object_key = key
		object_ucs = self._object_mapping(object_key,object)

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"group_members_sync_from_ucs: type of object_ucs['dn']: %s"%type(object_ucs['dn']))
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"group_members_sync_from_ucs: dn is: %s"%object_ucs['dn'])
		ldap_object_ucs = self.get_ucs_ldap_object(object_ucs['dn'])
		if ldap_object_ucs.has_key('uniqueMember'):
			ucs_members = ldap_object_ucs['uniqueMember']
		else:
			ucs_members = []

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   "ucs_members: %s" % ucs_members)

		# remove members which have this group as primary group (set same gidNumber)
		prim_members_ucs = self.lo.lo.search(filter='gidNumber=%s'%ldap_object_ucs['gidNumber'][0],attr=['gidNumber'])
		

		# all dn's need to be lower-case so we can compare them later:
		ucs_members_lower = []
		for dn in ucs_members:
			ucs_members_lower.append(dn.lower())

		ucs_members = ucs_members_lower
		
		for prim_object in prim_members_ucs:
			if  prim_object[0].lower() in ucs_members:
				ucs_members.remove(prim_object[0].lower())

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   "group_members_sync_from_ucs: clean ucs_members: %s" % ucs_members)

		ldap_object_ad = self.get_object(object['dn'])
		if ldap_object_ad and ldap_object_ad.has_key('member'):
			ad_members = ldap_object_ad['member']
		else:
			ad_members = []

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   "group_members_sync_from_ucs: ad_members %s" % ad_members)

		ad_members_from_ucs = []

		# map members from UCS to AD and check if they exist
		for member_dn in ucs_members:
			member_object = {'dn':member_dn,'modtype':'modify','attributes':self.lo.get(member_dn)}

			# can't sync them if users have no posix-account
			if not member_object['attributes'].has_key('gidNumber'):
				continue

			# check if this is members primary group, if true it shouldn't be added to ad
			if member_object['attributes'].has_key('gidNumber') and ldap_object_ucs.has_key('gidNumber') and \
			       member_object['attributes']['gidNumber'] == ldap_object_ucs['gidNumber']:
				# is primary group
				continue
			
			#print 'member_object: %s '%member_object
			for k in self.property.keys():
				if self.modules[k].identify(member_dn, member_object['attributes']):
					key=k
					break
			#print 'object key: %s' % key
			ad_dn = self._object_mapping(key, member_object, 'ucs')['dn']
			# check if dn exists in ad
			try:
				if self.lo_ad.get(ad_dn,attr=['cn']): # search only for cn to suppress coding errors
					ad_members_from_ucs.append(ad_dn.lower())
			except ldap.SERVER_DOWN:
				raise
			except:
				self._debug_traceback(univention.debug.INFO, "group_members_sync_from_ucs: failed to get dn from ad, assume object doesn't exist")

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   "group_members_sync_from_ucs: UCS-members in ad_members_from_ucs %s" % ad_members_from_ucs)

		# check if members in AD don't exist in UCS, if true they need to be added in AD
		for member_dn in ad_members:
			if not member_dn.lower() in ad_members_from_ucs:
				try:
					ad_object = self.get_object(member_dn)					
					
					key = self.__identify({'dn':member_dn,'attributes':ad_object})
					ucs_dn = self._object_mapping(key, {'dn':member_dn,'attributes':ad_object})['dn']
					if not self.lo.get(ucs_dn):
						ad_members_from_ucs.append(member_dn.lower())
						univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
								       "group_members_sync_from_ucs: Object exists only in AD [%s]" % ucs_dn)			
					elif self._ignore_object(key,{'dn':member_dn,'attributes':ad_object}):
						ad_members_from_ucs.append(member_dn.lower())
						univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
								       "group_members_sync_from_ucs: Object ignored in AD [%s], key = [%s]" % (ucs_dn,key))			
				except ldap.SERVER_DOWN:
					raise
				except:
					self._debug_traceback(univention.debug.INFO, "group_members_sync_from_ucs: failed to get dn from ad which is groupmember")

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   "group_members_sync_from_ucs: UCS-and AD-members in ad_members_from_ucs %s" % ad_members_from_ucs)

		# compare lists and generate modlist
		# direct compare is not possible, because ad_members_from_ucs are all lowercase, ad_members are not, so we need to iterate...
		# FIXME: should be done in the last iteration (above)

		# need to remove users from ad_members which have this group as primary group. may failed earlier if groupnames are mapped
		try:
			group_rid = decode_sid(self.lo_ad.lo.search_s(compatible_modstring(object['dn']), ldap.SCOPE_BASE,
								      '(objectClass=*)', ['objectSid'])[0][1]['objectSid'][0]).split('-')[-1]
		except ldap.NO_SUCH_OBJECT:
			group_rid = ''

		tmp_members = ad_members_from_ucs
		for member_dn in tmp_members:			
			member_object = self.get_object(member_dn)
			if member_object and member_object.has_key('primaryGroupID') and member_object['primaryGroupID'][0] == group_rid:
				ad_members_from_ucs.remove(member_dn)

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   "group_members_sync_from_ucs: ad_members_from_ucs without members with this as their primary group: %s" % ad_members_from_ucs)

		add_members = ad_members_from_ucs
		del_members = []

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   "group_members_sync_from_ucs: members to add initialized: %s" % add_members)
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   "group_members_sync_from_ucs: members to del initialized: %s" % del_members)

		for member_dn in ad_members:
			if member_dn.lower() in ad_members_from_ucs:
				add_members.remove(member_dn.lower())
			else:
				del_members.append(member_dn)

		
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   "group_members_sync_from_ucs: members to add: %s" % add_members)
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   "group_members_sync_from_ucs: members to del: %s" % del_members)

		if add_members or del_members:
			ad_members = ad_members + add_members
			for member in del_members:
				ad_members.remove(member)
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
								   "group_members_sync_from_ucs: members result: %s" % ad_members)

			modlist_members = []
			for member in ad_members:
				modlist_members.append(compatible_modstring(member))

			try:
				self.lo_ad.lo.modify_s(compatible_modstring(object['dn']),[(ldap.MOD_REPLACE, 'member', modlist_members)])
			except ldap.SERVER_DOWN:
				raise
			except:
				univention.debug.debug(univention.debug.LDAP, univention.debug.WARN,
						       "group_members_sync_from_ucs: failed to sync members: (%s,%s)" % (object['dn'],[(ldap.MOD_REPLACE, 'member', modlist_members)]))
				raise

			return True
		else:
			return True
			
		
	def group_members_sync_to_ucs(self, key, object):
		_d=univention.debug.function('ldap.group_members_sync_to_ucs')
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "group_members_sync_to_ucs: object: %s" % object)

		object_key = key

		ad_object = self._object_mapping(object_key,object,'ucs')
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "group_members_sync_to_ucs: ad_object (mapped): %s" % ad_object)

		
		ldap_object_ucs = self.get_ucs_ldap_object(object['dn'])
		if ldap_object_ucs.has_key('uniqueMember'):
			ucs_members = ldap_object_ucs['uniqueMember']
		else:
			ucs_members = []
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,"ucs_members: %s" % ucs_members)
		
		ldap_object_ad = self.get_object(ad_object['dn']) # FIXME: may fail if object doesn't exist
		if ldap_object_ad and ldap_object_ad.has_key('member'):
			ad_members = ldap_object_ad['member']
		else:
			ad_members = []

		group_sid = ldap_object_ad['objectSid'][0]
		group_rid = group_sid[string.rfind(group_sid,"-")+1:]

		# search for members who have this as their primaryGroup
		prim_members_ad = encode_ad_resultlist(self.lo_ad.lo.search_ext_s(self.lo_ad.base,ldap.SCOPE_SUBTREE,
							     'primaryGroupID=%s'%group_rid,
							     timeout=-1, sizelimit=0))


		for prim_dn, prim_object in prim_members_ad:
			if not prim_dn in ['None','',None]: # filter referrals
				ad_members.append(prim_dn)

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   "ad_members %s" % ad_members)

		ucs_members_from_ad = []
		
		# map members from AD to UCS and check if they exist
		for member_dn in ad_members:
			member_object = self.get_object(member_dn)
			if member_object:
				key = self.__identify({'dn':member_dn,'attributes':member_object})
				if not key:
					continue # member is an object which will not be synced
				ucs_dn = self._object_mapping(key, {'dn':member_dn,'attributes':member_object})['dn']
				try:
					if self.lo.get(ucs_dn):
						ucs_members_from_ad.append(ucs_dn.lower())
				except ldap.SERVER_DOWN:
					raise
				except:
					self._debug_traceback(univention.debug.INFO, "failed to get dn from ucs, assume object doesn't exist")
				
		# check if members in UCS don't exist in AD, if true they need to be added in UCS
		for member_dn in ucs_members:
			if not member_dn.lower() in ucs_members_from_ad:
				try:
					ucs_object = {'dn':member_dn,'modtype':'modify','attributes':self.lo.get(member_dn)}

					if self._ignore_object(key, object):
						continue

					for k in self.property.keys():
						if self.modules[k].identify(member_dn, ucs_object['attributes']):
							key=k
							break

					ad_dn = self._object_mapping(key, ucs_object, 'ucs')['dn']

					if not self.lo_ad.get(ad_dn,attr=['cn']): # search only for cn to suppress coding errors
						ucs_members_from_ad.append(member_dn.lower())
				except ldap.SERVER_DOWN:
					raise
				except:
					self._debug_traceback(univention.debug.INFO, "failed to get dn from ucs which is groupmember")

		# compare lists and generate modlist
		# direct compare is not possible, because ucs_members_from_ad are all lowercase, ad_members are not, so we need to iterate...
		# FIXME: should be done in the last iteration (above)
		add_members = ucs_members_from_ad
		del_members = []

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "ucs_members: %s" % ucs_members)
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "ucs_members_from_ad: %s" % ucs_members_from_ad)

		for member_dn in ucs_members:
			if member_dn.lower() in ucs_members_from_ad:
				add_members.remove(member_dn.lower())
			else:
				del_members.append(member_dn)

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "members to add: %s" % add_members)
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "members to del: %s" % del_members)

		if add_members or del_members:
			ucs_members = ucs_members + add_members
			for member in del_members:
				ucs_members.remove(member)
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
								   "members result: %s" % ucs_members)

			modlist_members = []
			for member in ucs_members:
				modlist_members.append(member)

			ucs_admin_object=univention.admin.objects.get(self.modules[object_key], co='', lo=self.lo, position='', dn=object['dn'])
			ucs_admin_object.open()
			ucs_admin_object['users'] = modlist_members
			ucs_admin_object.modify()

		else:
			pass
			
	def disable_user_from_ucs(self, key, object):		
		object_key = key

		object_ucs = self._object_mapping(object_key,object)
		ldap_object_ad = self.get_object(object['dn'])

		ucs_admin_object=univention.admin.objects.get(self.modules[object_key], co='', lo=self.lo, position='', dn=object_ucs['dn'])
		ucs_admin_object.open()

		modlist=[]

		if ucs_admin_object['disabled'] == '1':
			# user disabled in UCS
			if ldap_object_ad.has_key('userAccountControl') and (int(ldap_object_ad['userAccountControl'][0]) & 2 ) == 0:
				#user enabled in AD -> change
				res=str(int(ldap_object_ad['userAccountControl'][0]) | 2)
				modlist.append((ldap.MOD_REPLACE, 'userAccountControl', [res]))
		else:
			# user enabled in UCS
			if ldap_object_ad.has_key('userAccountControl') and (int(ldap_object_ad['userAccountControl'][0]) & 2 ) > 0:
				#user disabled in AD -> change
				res=str(int(ldap_object_ad['userAccountControl'][0]) + 2)
				modlist.append((ldap.MOD_REPLACE, 'userAccountControl', [res]))

		# account expires
		# This value represents the number of 100 nanosecond intervals since January 1, 1601 (UTC). A value of 0 or 0x7FFFFFFFFFFFFFFF (9223372036854775807) indicates that the account never expires.
		if not ucs_admin_object['userexpiry']:
			# ucs account not expired
			if ldap_object_ad.has_key('accountExpires') and (long(ldap_object_ad['accountExpires'][0]) != long(9223372036854775807) or ldap_object_ad['accountExpires'][0] == '0'):
				# ad account expired -> change
				modlist.append((ldap.MOD_REPLACE, 'accountExpires', ['9223372036854775807']))
		else:
			# ucs account expired
			if ldap_object_ad.has_key('accountExpires') and ldap_object_ad['accountExpires'][0] != unix2ad_time(ucs_admin_object['userexpiry']):
				# ad account not expired -> change
				modlist.append((ldap.MOD_REPLACE, 'accountExpires', [str(unix2ad_time(ucs_admin_object['userexpiry']))]))

		if modlist:
			self.lo_ad.lo.modify_s(compatible_modstring(object['dn']), compatible_modlist(modlist))
		pass

	def disable_user_to_ucs(self, key, object):
		object_key = key

		ad_object = self._object_mapping(object_key,object,'ucs')

		ldap_object_ucs = self.get_ucs_ldap_object(object['dn'])
		ldap_object_ad = self.get_object(ad_object['dn'])

		modified=0
		ucs_admin_object=univention.admin.objects.get(self.modules[object_key], co='', lo=self.lo, position='', dn=object['dn'])
		ucs_admin_object.open()

		if ldap_object_ad.has_key('userAccountControl') and (int(ldap_object_ad['userAccountControl'][0]) & 2) == 0:
			#user enabled in AD
			if ucs_admin_object['disabled'] == '1':
				#user disabled in UCS -> change
				ucs_admin_object['disabled']='0'
				modified=1
		else:
			#user disabled in AD
			if ucs_admin_object['disabled'] == '0':
				#user enabled in UCS -> change
				ucs_admin_object['disabled']='1'
				modified=1
		if ldap_object_ad.has_key('accountExpires') and ( long(ldap_object_ad['accountExpires'][0]) == long(9223372036854775807) or ldap_object_ad['accountExpires'][0] == '0'):
			# ad account not expired
			if ucs_admin_object['userexpiry']:
				# ucs account expired -> change
				ucs_admin_object['userexpiry']=None
				modified=1
		else:
			# ad account expired
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "sync account_expire:      adtime: %s    unixtime: %s" %
					       (long(ldap_object_ad['accountExpires'][0]),ucs_admin_object['userexpiry']))

			if ad2unix_time(long(ldap_object_ad['accountExpires'][0])) != ucs_admin_object['userexpiry']:
				# ucs account not expired -> change
				ucs_admin_object['userexpiry']=ad2unix_time(long(ldap_object_ad['accountExpires'][0]))
				modified=1

		if modified:
			ucs_admin_object.modify()
		pass



	def initialize(self):
		_d=univention.debug.function('ldap.initialize')
		print "--------------------------------------"
		print "Initialize sync from AD"
		self.resync_rejected()
		if self._get_lastUSN() == 0: # we startup new
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "initialize AD: last USN is 0, sync all")
			# query highest USN in LDAP
			highestCommittedUSN = self.__get_highestCommittedUSN()

			# poll for all objects without deleted objects
			polled=self.poll(show_deleted=False)

			# compare highest USN from poll with highest before poll, if the last changes deletes
			# the highest USN from poll is to low
			self._set_lastUSN(max(highestCommittedUSN,self._get_lastUSN()))
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "initialize AD: sync of all objects finished, lastUSN is %d", self.__get_highestCommittedUSN())
		else:
			polled=self.poll()		
		print "--------------------------------------"
		
	def resync_rejected(self):
		'''
		tries to resync rejected dn
		'''
		print "--------------------------------------"
		
		_d=univention.debug.function('ldap.resync_rejected')
		change_count = 0
		rejected = self._list_rejected()
		print "Sync %s rejected changes from AD to UCS" % len(rejected)
		sys.stdout.flush()
		if rejected:
			for id, dn in rejected:
				premapped_ad_dn = unicode(dn, 'utf8')
				try:
					sync_successfull = False
					elements = self.__search_ad_changeUSN(id, show_deleted=True)
					if not elements or len(elements) < 1 or not elements[0][0]:
						univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
											   "rejected change with id %s not found, don't need to sync" % id)
						self._remove_rejected(id)
					elif len(elements) > 1 and not (elements[1][0] == 'None' or elements[1][0] == None): # all except the first should be referrals
						univention.debug.debug(univention.debug.LDAP, univention.debug.WARN,
											   "more than one rejected object with id %s found, can't proceed" % id)
					else:						
						object = self.__object_from_element(elements[0])
						property_key = self.__identify(object)
						mapped_object = self._object_mapping(property_key,object)
						try:
							sync_successfull = self.sync_to_ucs(property_key, mapped_object, premapped_ad_dn)
						except ldap.SERVER_DOWN:
							raise
						except:
							self._debug_traceback(univention.debug.ERROR,
												  "sync of rejected object failed \n\t%s" % (object['dn']))
							sync_successfull = False
						if sync_successfull:
							change_count+=1
							self._remove_rejected(id)
							self.__update_lastUSN(object)
							self._set_DN_for_GUID(elements[0][1]['objectGUID'][0],elements[0][0])
				except Exception, msg:
					self._debug_traceback(univention.debug.ERROR,
										  "unexpected Error during ad.resync_rejected")
		print "restored %s rejected changes" % change_count
		print "--------------------------------------"
		sys.stdout.flush()

	def poll(self, show_deleted=True):
		'''
		poll for changes in AD
		'''
		_d=univention.debug.function('ldap.poll')
		# search from last_usn for changes
		change_count = 0
		changes = []
		try:
			changes = self.__search_ad_changes(show_deleted=show_deleted)
		except ldap.SERVER_DOWN:
			raise		
		except:
			self._debug_traceback(univention.debug.WARN,"Exception during search_ad_changes")

		print "--------------------------------------"
		print "try to sync %s changes from AD" % len(changes)
		print "done:",
		sys.stdout.flush()
		done_counter = 0

		for element in changes:
			if element[0] == 'None': # referrals
				continue
			old_element = copy.deepcopy(element)
			object = self.__object_from_element(element)
			if object:
				property_key = self.__identify(object)
				if property_key and not self._ignore_object(property_key,object):

					sync_successfull = False
					try:
						mapped_object = self._object_mapping(property_key,object)
						sync_successfull = self.sync_to_ucs(property_key, mapped_object, object['dn'])
					except ldap.SERVER_DOWN:
						raise ldap.SERVER_DOWN
					except univention.admin.uexceptions.ldapError, msg:
						univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "Exception during poll with message (1) %s"%msg)
						if msg == "Can't contact LDAP server":
							raise ldap.SERVER_DOWN
						else:
							self._debug_traceback(univention.debug.WARN,"Exception during poll")
					except univention.admin.uexceptions.ldapError, msg:
						univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "Exception during poll with message (2) %s"%msg)
						if msg == "Can't contact LDAP server":
							raise ldap.SERVER_DOWN
						else:
							self._debug_traceback(univention.debug.WARN,"Exception during poll")
					except:
						self._debug_traceback(univention.debug.WARN,
								"Exception during poll")



					if not sync_successfull:
						univention.debug.debug(univention.debug.LDAP, univention.debug.WARN,
											   "sync to ucs was not successfull, save rejected")
						univention.debug.debug(univention.debug.LDAP, univention.debug.WARN,
											   "object was: %s"%object['dn'])

					if sync_successfull:
						change_count+=1
						self.__update_lastUSN(object)
						try:
							GUID = old_element[1]['objectGUID'][0]
							self._set_DN_for_GUID(GUID,old_element[0])
						except:
							self._debug_traceback(univention.debug.WARN,
									      "Exception during set_DN_for_GUID")

					else:
						self.save_rejected(object)
				else:
					self.__update_lastUSN(object)

				done_counter += 1
				print "%s"%done_counter,
			else:
				done_counter += 1
				print "(%s)"%done_counter,
			sys.stdout.flush()
				
		print ""

		# return number of synced objects
		rejected = self._list_rejected()
		if rejected:
			print "Changes from AD:  %s (%s saved rejected)" % (change_count, len(rejected))
		else:
			print "Changes from AD:  %s (%s saved rejected)" % (change_count, '0')
		print "--------------------------------------"
		sys.stdout.flush()
		return change_count


	def sync_from_ucs(self, property_type, object, pre_mapped_ucs_dn, old_dn=None):
		_d=univention.debug.function('ldap.__sync_from_ucs')
		# Diese Methode erhaelt von der UCS Klasse ein Objekt,
		# welches hier bearbeitet wird und in das AD geschrieben wird.
		# object ist brereits vom eingelesenen UCS-Objekt nach AD gemappt, old_dn ist die alte UCS-DN
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "sync_from_ucs: sync object: %s"%object['dn'])

		# if sync is read (sync from AD) or none, there is nothing to do
		if self.property[property_type].sync_mode in ['read', 'none']:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "sync_from_ucs ignored, sync_mode is %s" % self.property[property_type].sync_mode)
			return True

		pre_mapped_ucs_old_dn = old_dn		
		
		if old_dn:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "move %s from [%s] to [%s]" % (property_type, old_dn, object['dn']))
			if hasattr ( self.property[property_type], 'dn_mapping_function' ):
				tmp_object = copy.deepcopy(object)
				tmp_object['dn'] = old_dn
				for function in self.property[property_type].dn_mapping_function:
					tmp_object=function(self, tmp_object, [], isUCSobject=True)
				old_dn = tmp_object['dn']
			if hasattr(self.property[property_type], 'position_mapping'):
				for mapping in self.property[property_type].position_mapping:
					old_dn=self._subtree_replace(old_dn,mapping[0],mapping[1])
				old_dn = self._subtree_replace(old_dn,self.lo.base,self.lo_ad.base)
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "move %s from [%s] to [%s]" % (property_type, old_dn, object['dn']))
			try:
				self.lo_ad.rename(unicode(old_dn), object['dn'])
			except ldap.NO_SUCH_OBJECT: # check if object is already moved (we may resync now)
				new = encode_ad_resultlist(self.lo_ad.lo.search_ext_s(compatible_modstring(object['dn']),ldap.SCOPE_BASE,'objectClass=*',timeout=-1,sizelimit=0))
				if not new:
					raise
			# need to actualise the GUID and DN-Mapping
			self._set_DN_for_GUID(self.lo_ad.lo.search_ext_s(compatible_modstring(object['dn']),ldap.SCOPE_BASE,'objectClass=*',timeout=-1,sizelimit=0)[0][1]['objectGUID'][0],
					      object['dn'])
			self._remove_dn_mapping(pre_mapped_ucs_old_dn, unicode(old_dn))
			self._check_dn_mapping(pre_mapped_ucs_dn, object['dn'])

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO,
							   'sync from ucs: [%10s] [%10s] %s' % (property_type,object['modtype'], object['dn']))

		if object.has_key('olddn'):
			object.pop('olddn') # not needed anymore, will fail object_mapping in later functions
		old_dn=None

		addlist=[]
		modlist=[]

		ad_object=self.get_object(object['dn'])

		if (object['modtype'] == 'add' and not ad_object) or (object['modtype'] == 'modify' and not ad_object):
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "sync_from_ucs: add object: %s"%object['dn'])

			# objectClass
			if self.property[property_type].con_create_objectclass:
				addlist.append(('objectClass', self.property[property_type].con_create_objectclass))

			if hasattr(self.property[property_type], 'attributes') and self.property[property_type].attributes != None:
				for attr,value in object['attributes'].items():
					for attribute in self.property[property_type].attributes.keys():
						if self.property[property_type].attributes[attribute].con_attribute == attr:
							addlist.append((attr, value))
			if hasattr(self.property[property_type], 'post_attributes') and self.property[property_type].post_attributes != None:
				for attr,value in object['attributes'].items():
					for attribute in self.property[property_type].post_attributes.keys():
						if self.property[property_type].post_attributes[attribute].con_attribute == attr:
							modlist.append((ldap.MOD_REPLACE, attr, value))

			self.lo_ad.lo.add_s(compatible_modstring(object['dn']), compatible_addlist(addlist)) #FIXME encoding

			if hasattr(self.property[property_type],"post_con_create_functions"):
				for f in self.property[property_type].post_con_create_functions:
					f(self, property_type, object)

			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "to modify: %s"%object['dn'])
			if modlist:
				self.lo_ad.lo.modify_s(compatible_modstring(object['dn']), compatible_modlist(modlist))

			if hasattr(self.property[property_type],"post_con_modify_functions"):
				for f in self.property[property_type].post_con_modify_functions:
					f(self, property_type, object)

		elif (object['modtype'] == 'modify' and ad_object) or (object['modtype'] == 'add' and ad_object):
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "sync_from_ucs: modify object: %s"%object['dn'])
			if hasattr(self.property[property_type], 'attributes') and self.property[property_type].attributes != None:
				for attr,value in object['attributes'].items():
					for attribute in self.property[property_type].attributes.keys():
						if self.property[property_type].attributes[attribute].con_attribute == attr:
							if not ad_object.has_key(attr):
								if value != None:
									modlist.append((ldap.MOD_ADD, attr, value))
 							elif not univention.connector.compare_lowercase(value,ad_object[attr]): # FIXME: use defined compare-function from mapping.py
								modlist.append((ldap.MOD_REPLACE, attr, value))
			if hasattr(self.property[property_type], 'post_attributes') and self.property[property_type].post_attributes != None:
				for attr,value in object['attributes'].items():
					for attribute in self.property[property_type].post_attributes.keys():
						if self.property[property_type].post_attributes[attribute].con_attribute == attr:
							if not ad_object.has_key(attr):
								if value != None:
									modlist.append((ldap.MOD_ADD, attr, value))
 							elif not univention.connector.compare_lowercase(value,ad_object[attr]): # FIXME: use defined compare-function from mapping.py
								modlist.append((ldap.MOD_REPLACE, attr, value))
			if modlist:
				self.lo_ad.lo.modify_s(compatible_modstring(object['dn']), compatible_modlist(modlist))
				
			attrs_in_current_ucs_object = object['attributes'].keys()
 			attrs_which_should_be_mapped = []
 			attrs_to_remove_from_ad_object = []
			attrs_which_should_be_mapped = []

 			if hasattr(self.property['container'], 'post_attributes') and self.property['ou'].post_attributes != None:
				for ac in self.property['container'].post_attributes.keys():
					attrs_which_should_be_mapped.append(self.property['container'].post_attributes[ac].con_attribute)

			if hasattr(self.property['ou'], 'post_attributes') and self.property['ou'].post_attributes != None:
				for ac in self.property['ou'].post_attributes.keys():
					attrs_which_should_be_mapped.append(self.property['ou'].post_attributes[ac].con_attribute)

 			if hasattr(self.property['group'], 'post_attributes') and self.property['group'].post_attributes != None:
				for ac in self.property['group'].post_attributes.keys():
					attrs_which_should_be_mapped.append(self.property['group'].post_attributes[ac].con_attribute)

 			if hasattr(self.property['user'], 'post_attributes') and self.property['user'].post_attributes != None:
				for ac in self.property['user'].post_attributes.keys():
					attrs_which_should_be_mapped.append(self.property['user'].post_attributes[ac].con_attribute)

			modlist_empty_attrs = []			
 			for expected_attribute in attrs_which_should_be_mapped:
				if not object['attributes'].has_key(expected_attribute):
					attrs_to_remove_from_ad_object.append(expected_attribute)

				if modlist:
					for modified_attrs in modlist:
						if modified_attrs[1] in attrs_to_remove_from_ad_object and len(modified_attrs[2]) > 0:
							attrs_to_remove_from_ad_object.remove(modified_attrs[1])

			for yank_empty_attr in attrs_to_remove_from_ad_object:
				if ad_object.has_key(yank_empty_attr):
					if value != None:
						# the description attribute is managed internally by AD and cannot
						# be removed directly. Thus we set it to " " instead
						# FIXME: Make this configurable by baseconfig
						if yank_empty_attr != "description":
							modlist_empty_attrs.append((ldap.MOD_REPLACE, yank_empty_attr, ""))
						else:
							univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "Value for description reset to a blank instead of removing attribute")
							modlist_empty_attrs.append((ldap.MOD_REPLACE, yank_empty_attr, "x"))

			if len(modlist_empty_attrs) > 0:
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "Attributes were removed in UCS LDAP, removing them in AD likewise: %s " % str(modlist_empty_attrs))
				
				self.lo_ad.lo.modify_s(compatible_modstring(object['dn']), compatible_modlist(modlist_empty_attrs))
				modlist_empty_attrs = []


			if hasattr(self.property[property_type],"post_con_modify_functions"):
				for f in self.property[property_type].post_con_modify_functions:
					f(self, property_type, object)
		elif object['modtype'] == 'delete':
			try:
				self.lo_ad.lo.delete_s(compatible_modstring(object['dn']))
			except ldap.NO_SUCH_OBJECT:
				pass # object already deleted
				
		else:
			univention.debug.debug(univention.debug.LDAP, univention.debug.WARN,
								   "unknown modtype (%s : %s)" %
								   (object['dn'],object['modtype']))
			return False


		self._check_dn_mapping(pre_mapped_ucs_dn, object['dn'])

		univention.debug.debug(univention.debug.LDAP, univention.debug.ALL,
							   "sync from ucs return True" )
		return True # FIXME: return correct False if sync fails


