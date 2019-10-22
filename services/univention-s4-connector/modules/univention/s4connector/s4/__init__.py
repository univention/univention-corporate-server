#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Basic class for the AD connector part
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


from __future__ import print_function

import copy
import string
import re
import sys
import time
import types
import pprint
import warnings

import ldap
from ldap.controls import LDAPControl
from ldap.controls import SimplePagedResultsControl
from ldap.filter import escape_filter_chars
from samba.dcerpc import security
from samba.ndr import ndr_pack, ndr_unpack
from samba.dcerpc import misc

import univention.uldap
import univention.s4connector
import univention.debug2 as ud

DECODE_IGNORELIST = ['dNSProperty', 'securityIdentifier', 'jpegPhoto', 'mSMQDigests', 'msExchMailboxSecurityDescriptor', 'userCertificate', 'logonHours', 'mSMQSites', 'objectSid', 'ipsecData', 'dnsRecord', 'mSMQSignKey', 'dSASignature', 'may', 'objectGUID', 'linkTrackSecret', 'mSMQEncryptKey', 'currentLocation', 'repsFrom', 'mS-DS-CreatorSID', 'replUpToDateVector', 'mSMQSignCertificates', 'msExchMailboxGuid', 'sIDHistory']

LDAP_SERVER_SHOW_DELETED_OID = "1.2.840.113556.1.4.417"
LDB_CONTROL_DOMAIN_SCOPE_OID = "1.2.840.113556.1.4.1339"
LDB_CONTROL_RELAX_OID = "1.3.6.1.4.1.4203.666.5.12"
LDB_CONTROL_PROVISION_OID = '1.3.6.1.4.1.7165.4.3.16'
DSDB_CONTROL_REPLICATED_UPDATE_OID = '1.3.6.1.4.1.7165.4.3.3'

# page results
PAGE_SIZE = 1000


def normalise_userAccountControl(s4connector, key, object):
	"""deprecated unused function, should be removed in the future!"""
	warnings.warn('The function normalise_userAccountControl() is deprecated and should not be used in the mapping anymore. Use con_create_attributes instead.')
	# set userAccountControl to 512 -- accounts synced to samba4 alpha17 had userAccountControl == 544
	ud.debug(ud.LDAP, ud.ALL, "normalise_userAccountControl: dn: %s" % object['dn'])
	for i in range(0, 10):
		try:
			s4connector.lo_s4.lo.modify_s(compatible_modstring(object['dn']), [(ldap.MOD_REPLACE, 'userAccountControl', ['512'])])
		except ldap.NO_SUCH_OBJECT:
			time.sleep(1)
			continue
		return True
	return False


def group_members_sync_from_ucs(s4connector, key, object):
	return s4connector.group_members_sync_from_ucs(key, object)


def object_memberships_sync_from_ucs(s4connector, key, object):
	return s4connector.object_memberships_sync_from_ucs(key, object)


def group_members_sync_to_ucs(s4connector, key, object):
	return s4connector.group_members_sync_to_ucs(key, object)


def object_memberships_sync_to_ucs(s4connector, key, object):
	return s4connector.object_memberships_sync_to_ucs(key, object)


def primary_group_sync_from_ucs(s4connector, key, object):
	return s4connector.primary_group_sync_from_ucs(key, object)


def primary_group_sync_to_ucs(s4connector, key, object):
	return s4connector.primary_group_sync_to_ucs(key, object)


def disable_user_from_ucs(s4connector, key, object):
	return s4connector.disable_user_from_ucs(key, object)


def disable_user_to_ucs(s4connector, key, object):
	return s4connector.disable_user_to_ucs(key, object)


def add_primary_group_to_addlist(s4connector, property_type, object, addlist, serverctrls):
	gidNumber = object.get('attributes', {}).get('gidNumber')
	primary_group_sid = object.get('attributes', {}).get('sambaPrimaryGroupSID')
	if gidNumber:
		if isinstance(gidNumber, type([])):
			gidNumber = gidNumber[0]
		ud.debug(ud.LDAP, ud.INFO, 'add_primary_group_to_addlist: gidNumber: %s' % gidNumber)

		ucs_group_filter = format_escaped('(&(objectClass=univentionGroup)(gidNumber={0!e}))', gidNumber)
		ucs_group_ldap = s4connector.search_ucs(filter=ucs_group_filter)  # is empty !?
		if not ucs_group_ldap:
			ud.debug(ud.LDAP, ud.WARN, 'add_primary_group_to_addlist: Did not find UCS group with gidNumber %s' % gidNumber)
			return

		member_key = 'group'
		s4_group_object = s4connector._object_mapping(member_key, {'dn': ucs_group_ldap[0][0], 'attributes': ucs_group_ldap[0][1]}, 'ucs')
		ldap_object_s4_group = s4connector.get_object(s4_group_object['dn'])

		primary_group_sid = ldap_object_s4_group['objectSid'][0]
		primary_group_rid = primary_group_sid.split('-')[-1]

		# Is the primary group Domain Users (the default)?
		if primary_group_rid == '513':
			return

		ud.debug(ud.LDAP, ud.INFO, 'add_primary_group_to_addlist: Set primary group to %s (rid) for %s' % (primary_group_rid, object.get('dn')))
		addlist.append(('primaryGroupID', [primary_group_rid]))
		serverctrls.append(LDAPControl(LDB_CONTROL_RELAX_OID, criticality=0))


def __is_groupType_local(groupType):
	try:
		return int(groupType) & 0x1
	except ValueError:
		return False


def check_for_local_group_and_extend_serverctrls_and_sid(s4connector, property_type, object, add_or_modlist, serverctrls):
	groupType = object.get('attributes', {}).get('univentionGroupType', [None])[0]
	if not groupType:
		return

	ud.debug(ud.LDAP, ud.INFO, "groupType: %s" % groupType)
	if __is_groupType_local(groupType):
		serverctrls.append(LDAPControl(LDB_CONTROL_RELAX_OID, criticality=0))

		sambaSID = object.get('attributes', {}).get('sambaSID', [])[0]
		ud.debug(ud.LDAP, ud.INFO, "sambaSID: %s" % sambaSID)
		objectSid = ndr_pack(security.dom_sid('%s' % (sambaSID)))
		add_or_modlist.append(('objectSid', [objectSid]))


def unicode_to_utf8(attrib):
	'''The inverse of encode_attrib'''
	if not isinstance(attrib, types.UnicodeType):
		return attrib
	return attrib.encode('utf8')


def encode_attrib(attrib):
	if not attrib or isinstance(attrib, type(u'')):  # referral or already unicode
		return attrib
	return unicode(attrib, 'utf8')


def fix_dn_in_search(result):
	return [(fix_dn(dn), attrs) for dn, attrs in result]


def fix_dn(dn):
	# Samba LDAP returns broken DN, which cannot be parsed: ldap.dn.str2dn('cn=foo\\?,dc=base')
	return dn.replace('\\?', '?') if dn is not None else dn


def str2dn(dn):
	try:
		return ldap.dn.str2dn(dn)
	except ldap.DECODING_ERROR:
		return ldap.dn.str2dn(fix_dn(dn))


def encode_attriblist(attriblist):
	if not isinstance(attriblist, type([])):
		return encode_attrib(attriblist)
	else:
		for i in range(len(attriblist)):
			attriblist[i] = encode_attrib(attriblist[i])
		return attriblist


def encode_s4_object(s4_object):
	if isinstance(s4_object, type([])):
		return encode_attriblist(s4_object)
	else:
		for key in s4_object.keys():
			if key == 'objectSid':
				s4_object[key] = [decode_sid(s4_object[key][0])]
			elif key in DECODE_IGNORELIST:
				ud.debug(ud.LDAP, ud.INFO, "encode_s4_object: attrib %s ignored during encoding" % key)  # don't recode
			else:
				try:
					s4_object[key] = encode_attriblist(s4_object[key])
				except Exception:  # FIXME: which exception is to be caught?
					ud.debug(ud.LDAP, ud.WARN, "encode_s4_object: encode attrib %s failed, ignored!" % key)
		return s4_object


def encode_s4_result(s4_result):
	'''
	encode an result from an python-ldap search
	'''
	return (encode_attrib(s4_result[0]), encode_s4_object(s4_result[1]))


def encode_s4_resultlist(s4_resultlist):
	'''
	encode an result from an python-ldap search
	'''
	for i in range(len(s4_resultlist)):
		s4_resultlist[i] = encode_s4_result(s4_resultlist[i])
	return s4_resultlist


def unix2s4_time(l):
	d = 116444736000000000  # difference between 1601 and 1970
	return int(time.mktime(time.gmtime(time.mktime(time.strptime(l, "%Y-%m-%d")) + 90000))) * 10000000 + d  # 90000s are one day and one hour


def s42unix_time(l):
	d = 116444736000000000  # difference between 1601 and 1970
	return time.strftime("%d.%m.%y", time.gmtime((l - d) / 10000000))


def samba2s4_time(l):
	d = 116444736000000000  # difference between 1601 and 1970
	return int(time.mktime(time.localtime(l))) * 10000000 + d


def s42samba_time(l):
	if l == 0:
		return l
	d = 116444736000000000  # difference between 1601 and 1970
	return int(((l - d)) / 10000000)


# mapping funtions
def samaccountname_dn_mapping(s4connector, given_object, dn_mapping_stored, ucsobject, propertyname, propertyattrib, ocucs, ucsattrib, ocs4, dn_attr=None):
	'''
	map dn of given object (which must have an samaccountname in S4)
	ocucs and ocs4 are objectclasses in UCS and S4
	'''
	object = copy.deepcopy(given_object)

	samaccountname = u''
	dn_attr_val = u''

	if object['dn'] is not None:
		if 'sAMAccountName' in object['attributes']:
			samaccountname = object['attributes']['sAMAccountName'][0]
		if dn_attr:
			try:
				dn_attr_vals = [value for key, value in object['attributes'].iteritems() if dn_attr.lower() == key.lower()][0]
			except IndexError:
				pass
			else:
				dn_attr_val = dn_attr_vals[0]

	def dn_premapped(object, dn_key, dn_mapping_stored):
		if (dn_key not in dn_mapping_stored) or (not object[dn_key]):
			ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: not premapped (in first instance)")
			return False

		if object.get('modtype') == 'delete':
			# In case the object was deleted, the mapping premapped DN should be used.
			# But in case the sAMAccountName has been changed we should search for
			# the sAMAccountName. That's not the best solution but it works for now:
			# See the following test cases:
			#	125sync_recreate_user_at_different_position
			#	272read_ad_change_username
			t_dn = object.get('dn')
			if t_dn:
				(_rdn_attribute, rdn_value_utf8, _flags) = str2dn(unicode_to_utf8(t_dn))[0][0]
				rdn_value = unicode(rdn_value_utf8, 'utf8')
				t_samaccount = u''
				if object.get('attributes'):
					t_samaccount = object['attributes'].get('sAMAccountName', [u''])[0]
				if rdn_value.lower() == t_samaccount.lower():
					ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: modtype is delete, use the premapped DN: %s" % object[dn_key])
					return True

		if ucsobject:
			if s4connector.get_object(object[dn_key]) is not None:
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: premapped S4 object found")
				return True
			else:
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: premapped S4 object not found")
				return False
		else:
			if s4connector.get_ucs_ldap_object(object[dn_key]) is not None:
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: premapped UCS object found")
				return True
			else:
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: premapped UCS object not found")
				return False

	for dn_key in ['dn', 'olddn']:
		ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: check newdn for key %s: %s" % (dn_key, object.get(dn_key)))
		if dn_key in object and not dn_premapped(object, dn_key, dn_mapping_stored):

			dn = object[dn_key]

			# Skip Configuration objects with empty DNs
			if dn is None:
				break

			exploded_dn = str2dn(unicode_to_utf8(dn))
			(_fst_rdn_attribute_utf8, fst_rdn_value_utf8, _flags) = exploded_dn[0][0]

			if ucsobject and object.get('attributes') and object['attributes'].get(ucsattrib):
				value = object['attributes'][ucsattrib][0]
			else:
				value = unicode(fst_rdn_value_utf8, 'utf8')

			if ucsobject:
				# lookup the cn as sAMAccountName in S4 to get corresponding DN, if not found create new
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: got an UCS-Object")
				filter_parts_s4 = [format_escaped('(objectclass={0!e})', ocs4), ]

				alternative_samaccountnames = []
				if s4connector.property[propertyname].mapping_table and propertyattrib in s4connector.property[propertyname].mapping_table.keys():
					for ucsval, conval in s4connector.property[propertyname].mapping_table[propertyattrib]:
						try:
							if value.lower() == ucsval.lower():
								if ucsval == "Printer-Admins":	 # Also look for the original name (Bug #42675#c1)
									alternative_samaccountnames.append(ucsval)
								value = conval
								ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: map samaccountanme according to mapping-table")
								continue
						except UnicodeDecodeError:
							pass  # values are not the same codec

				if len(alternative_samaccountnames) == 0:
					filter_parts_s4.append(format_escaped('(samaccountname={0!e})', value))
				else:
					alternative_samaccountnames.append(value)
					samaccountname_filter_parts = map(lambda x: format_escaped('(samaccountname={0!e})', x), alternative_samaccountnames)
					filter_parts_s4.append(unicode_to_utf8(u'(|{})'.format(''.join(samaccountname_filter_parts))))

				if dn_attr and dn_attr_val:
					# also look for dn attr (needed to detect modrdn)
					filter_parts_s4.append(format_escaped('({0}={1!e})', dn_attr, dn_attr_val))
				filter_s4 = unicode_to_utf8(u'(&{})'.format(''.join(filter_parts_s4)))
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: search in s4 for %s" % filter_s4)
				result = s4connector.s4_search_ext_s(s4connector.lo_s4.base, ldap.SCOPE_SUBTREE, filter_s4, ['sAMAccountName'])

				if result and len(result) > 0 and result[0] and len(result[0]) > 0 and result[0][0]:  # no referral, so we've got a valid result
					if dn_key == 'olddn' or (dn_key == 'dn' and 'olddn' not in object):
						newdn = unicode(result[0][0], 'utf8')
					else:
						# move
						# return a kind of frankenstein DN here, sync_from_ucs replaces the UCS LDAP base
						# with the samba LDAP base at a later stage, see Bug #48440
						s4_rdn = str2dn(result[0][0])[0]
						newdn = unicode(ldap.dn.dn2str([s4_rdn] + exploded_dn[1:]), 'utf8')
				else:
					newdn_rdn = [('cn', fst_rdn_value_utf8, ldap.AVA_STRING)]
					newdn = unicode(ldap.dn.dn2str([newdn_rdn] + exploded_dn[1:]), 'utf8')  # new object, don't need to change
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: newdn: %s" % newdn)
			else:
				# get the object to read the sAMAccountName in S4 and use it as name
				# we have no fallback here, the given dn must be found in S4 or we've got an error
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: got an S4-Object")
				i = 0

				while (not samaccountname):  # in case of olddn this is already set
					i = i + 1
					search_dn = dn
					if 'deleted_dn' in object:
						search_dn = object['deleted_dn']
					try:
						samaccountname_filter = format_escaped('(objectClass={0!e})', ocs4)
						samaccountname_search_result = s4connector.s4_search_ext_s(compatible_modstring(search_dn), ldap.SCOPE_BASE, samaccountname_filter, ['sAMAccountName'])
						samaccountname_attribute = samaccountname_search_result[0][1]['sAMAccountName'][0]
						samaccountname = encode_attrib(samaccountname_attribute)
						ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: got samaccountname from S4")
					except ldap.NO_SUCH_OBJECT:  # S4 may need time
						if i > 5:
							raise
						time.sleep(1)  # S4 may need some time...

				if s4connector.property[propertyname].mapping_table and propertyattrib in s4connector.property[propertyname].mapping_table.keys():
					for ucsval, conval in s4connector.property[propertyname].mapping_table[propertyattrib]:
						if samaccountname.lower() == conval.lower():
							samaccountname = ucsval
							ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: map samaccountanme according to mapping-table")
							continue
						else:
							ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: samaccountname not in mapping-table")

				# search for object with this dn in ucs, needed if it lies in a different container
				ucsdn = ''
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: samaccountname is:%s" % samaccountname)
				ucsdn_filter = format_escaped(u'(&(objectclass={0!e})({1}={2!e}))', ocucs, ucsattrib, samaccountname)
				ucsdn_result = s4connector.search_ucs(filter=ucsdn_filter, base=s4connector.lo.base, scope='sub', attr=['objectClass'])
				if ucsdn_result and len(ucsdn_result) > 0 and ucsdn_result[0] and len(ucsdn_result[0]) > 0:
					ucsdn = unicode(ucsdn_result[0][0], 'utf8')

				if ucsdn and (dn_key == 'olddn' or (dn_key == 'dn' and 'olddn' not in object)):
					newdn = ucsdn
					ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: newdn is ucsdn")
				else:
					if dn_attr:
						newdn_rdn = [(dn_attr, unicode_to_utf8(dn_attr_val), ldap.AVA_STRING)]
					else:
						newdn_rdn = [(ucsattrib, unicode_to_utf8(samaccountname), ldap.AVA_STRING)]

					newdn = unicode(ldap.dn.dn2str([newdn_rdn] + exploded_dn[1:]), 'utf8')  # guess the old dn

			ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: newdn for key %r:" % (dn_key,))
			ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: olddn: %r" % (dn,))
			ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: newdn: %r" % (newdn,))

			object[dn_key] = newdn
	return object


def user_dn_mapping(s4connector, given_object, dn_mapping_stored, isUCSobject):
	'''
	map dn of given user using the samaccountname/uid
	s4connector is an instance of univention.s4connector.s4, given_object an object-dict,
	dn_mapping_stored a list of dn-types which are already mapped because they were stored in the config-file
	'''
	return samaccountname_dn_mapping(s4connector, given_object, dn_mapping_stored, isUCSobject, 'user', u'samAccountName', u'posixAccount', 'uid', u'user')


def group_dn_mapping(s4connector, given_object, dn_mapping_stored, isUCSobject):
	'''
	map dn of given group using the samaccountname/cn
	s4connector is an instance of univention.s4connector.s4, given_object an object-dict,
	dn_mapping_stored a list of dn-types which are already mapped because they were stored in the config-file
	'''
	return samaccountname_dn_mapping(s4connector, given_object, dn_mapping_stored, isUCSobject, 'group', u'cn', u'posixGroup', 'cn', u'group')


def windowscomputer_dn_mapping(s4connector, given_object, dn_mapping_stored, isUCSobject):
	'''
	map dn of given windows computer using the samaccountname/uid
	s4connector is an instance of univention.s4connector.s4, given_object an object-dict,
	dn_mapping_stored a list of dn-types which are already mapped because they were stored in the config-file
	'''
	return samaccountname_dn_mapping(s4connector, given_object, dn_mapping_stored, isUCSobject, 'windowscomputer', u'samAccountName', u'posixAccount', 'uid', u'computer', 'cn')


def dc_dn_mapping(s4connector, given_object, dn_mapping_stored, isUCSobject):
	'''
	map dn of given dc computer using the samaccountname/uid
	s4connector is an instance of univention.s4connector.s4, given_object an object-dict,
	dn_mapping_stored a list of dn-types which are already mapped because they were stored in the config-file
	'''
	return samaccountname_dn_mapping(s4connector, given_object, dn_mapping_stored, isUCSobject, 'dc', u'samAccountName', u'posixAccount', 'uid', u'computer', 'cn')


def decode_sid(value):
	# SID in S4
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
	sid = 'S-'
	sid += "%d" % ord(value[0])

	sid_len = ord(value[1])

	sid += "-%d" % ord(value[7])

	for i in range(0, sid_len):
		res = ord(value[8 + (i * 4)]) + (ord(value[9 + (i * 4)]) << 8) + (ord(value[10 + (i * 4)]) << 16) + (ord(value[11 + (i * 4)]) << 24)
		sid += "-%u" % res

	return sid


def encode_list(list, encoding):
	newlist = []
	if not list:
		return list
	for val in list:
		if hasattr(val, 'encode'):
			newlist.append(val.encode(encoding))
		else:
			newlist.append(val)
	return newlist


def decode_list(list, encoding):
	newlist = []
	if not list:
		return list
	for val in list:
		if hasattr(val, 'decode') and not isinstance(val, types.UnicodeType):
			newlist.append(val.decode(encoding))
		else:
			newlist.append(val)
	return newlist


def encode_modlist(list, encoding):
	newlist = []
	for (modtype, attr, values) in list:
		if hasattr(attr, 'encode'):
			newattr = attr.encode(encoding)
		else:
			newattr = attr

		if attr in DECODE_IGNORELIST:
			newlist.append((modtype, newattr, values))
			continue

		if isinstance(values, type([])):
			newlist.append((modtype, newattr, encode_list(values, encoding)))
		else:
			newlist.append((modtype, newattr, encode_list(values, encoding)))
	return newlist


def decode_modlist(list, encoding):
	newlist = []
	for (modtype, attr, values) in list:
		if hasattr(attr, 'decode') and not isinstance(attr, types.UnicodeType):
			newattr = attr.decode(encoding)
		else:
			newattr = attr

		if attr in DECODE_IGNORELIST:
			newlist.append((modtype, newattr, values))
			continue

		if isinstance(values, type([])):
			newlist.append((modtype, newattr, decode_list(values, encoding)))
		else:
			newlist.append((modtype, newattr, decode_list(values, encoding)))
	return newlist


def encode_addlist(list, encoding):
	newlist = []
	for (attr, values) in list:
		if hasattr(attr, 'encode'):
			newattr = attr.encode(encoding)
		else:
			newattr = attr

		if attr in DECODE_IGNORELIST:
			newlist.append((newattr, values))
			continue

		if isinstance(values, type([])):
			newlist.append((newattr, encode_list(values, encoding)))
		else:
			newlist.append((newattr, encode_list(values, encoding)))
	return newlist


def decode_addlist(list, encoding):
	newlist = []
	for (attr, values) in list:
		if hasattr(attr, 'decode') and not isinstance(attr, types.UnicodeType):
			newattr = attr.decode(encoding)
		else:
			newattr = attr

		if attr in DECODE_IGNORELIST:
			newlist.append((newattr, values))
			continue

		if isinstance(values, type([])):
			newlist.append((newattr, decode_list(values, encoding)))
		else:
			newlist.append((newattr, decode_list(values, encoding)))
	return newlist


def compatible_list(list):
	return encode_list(decode_list(list, 'latin1'), 'utf8')


def compatible_modlist(list):
	return encode_modlist(decode_modlist(list, 'latin1'), 'utf8')


def compatible_addlist(list):
	return encode_addlist(decode_addlist(list, 'latin1'), 'utf8')


def compatible_modstring(string):
	if hasattr(string, 'decode') and not isinstance(string, types.UnicodeType):
		string = string.decode('latin1')
	if hasattr(string, 'encode'):
		string = string.encode('utf8')
	return string


def __is_sid_string(sid):
	if sid.startswith('S-'):
		return True
	else:
		return False


def __is_int(value):
	try:
		int(value)
		return True
	except (ValueError, TypeError):
		return False


def compare_sid_lists(sid_list1, sid_list2):
	"""
			Compare the SID / RID attributes. Depending on the sync direction and
			SID sync configuration the function gets two SID lists or two RID values.
	"""

	# RID comparison
	if __is_int(sid_list1) or __is_int(sid_list2):
		if sid_list1 == sid_list2:
			return True
		else:
			return False

	# SID comparison
	len_sid_list1 = len(sid_list1)
	if len_sid_list1 != len(sid_list2):
		return False

	for i in range(0, len_sid_list1):
		sid1 = sid_list1[i]
		if not __is_sid_string(sid1):
			sid1 = decode_sid(sid1)

		sid2 = sid_list2[i]
		if not __is_sid_string(sid2):
			sid2 = decode_sid(sid2)

		if sid1 != sid2:
			return False

	return True


class LDAPEscapeFormatter(string.Formatter):
	"""
	A custom string formatter that supports a special `e` conversion, to employ
	the function `ldap.filter.escape_filter_chars()` on the given value.

	>>> LDAPEscapeFormatter().format("{0}", "*")
	'*'
	>>> LDAPEscapeFormatter().format("{0!e}", "*")
	'\\2a'

	Unfortunately this does not support the key/index-less variant
	(see http://bugs.python.org/issue13598).

	>>> LDAPEscapeFormatter().format("{!e}", "*")
	Traceback (most recent call last):
	KeyError: ''
	"""
	def convert_field(self, value, conversion):
		if conversion == 'e':
			if isinstance(value, basestring):
				return escape_filter_chars(value)
			return escape_filter_chars(str(value))
		return super(LDAPEscapeFormatter, self).convert_field(value, conversion)


def format_escaped(format_string, *args, **kwargs):
	"""
	Convenience-wrapper around `LDAPEscapeFormatter`.

	Use `!e` do denote format-field that should be escaped using
	`ldap.filter.escape_filter_chars()`'

	>>> format_escaped("{0!e}", "*")
	'\\2a'
	"""
	return LDAPEscapeFormatter().format(format_string, *args, **kwargs)


class s4(univention.s4connector.ucs):
	RANGE_RETRIEVAL_PATTERN = re.compile("^([^;]+);range=(\d+)-(\d+|\*)$")

	def __init__(self, CONFIGBASENAME, property, baseConfig, s4_ldap_host, s4_ldap_port, s4_ldap_base, s4_ldap_binddn, s4_ldap_bindpw, s4_ldap_certificate, listener_dir, init_group_cache=True):
		univention.s4connector.ucs.__init__(self, CONFIGBASENAME, property, baseConfig, listener_dir)

		self.CONFIGBASENAME = CONFIGBASENAME

		self.s4_ldap_host = s4_ldap_host
		self.s4_ldap_port = s4_ldap_port
		self.s4_ldap_base = s4_ldap_base
		self.s4_ldap_binddn = s4_ldap_binddn
		self.s4_ldap_bindpw = s4_ldap_bindpw
		self.s4_ldap_certificate = s4_ldap_certificate
		self.baseConfig = self.configRegistry = baseConfig

		self.open_s4()
		ud.debug(ud.LDAP, ud.ALL, 'Mapping is: %s' % (pprint.pformat(property, indent=4, width=250)))

		for key in self.property.keys():
			if hasattr(self.property[key], 'con_default_dn'):
				con_default_dn = self.property[key].con_default_dn
				if con_default_dn.lower().endswith(self.lo_s4.base.lower()):
					if con_default_dn[-len(self.lo_s4.base):] != self.lo_s4.base:
						self.property[key].con_default_dn = con_default_dn[:-len(self.lo_s4.base)] + self.lo_s4.base
						ud.debug(ud.LDAP, ud.INFO, "__init__: Fixing con ldap base case in %s con_default_dn %s" % (key, self.property[key].con_default_dn,))

		if not self.config.has_section('S4'):
			ud.debug(ud.LDAP, ud.INFO, "__init__: init add config section 'S4'")
			self.config.add_section('S4')

		if not self.config.has_section('S4 rejected'):
			ud.debug(ud.LDAP, ud.INFO, "__init__: init add config section 'S4 rejected'")
			self.config.add_section('S4 rejected')

		if not self.config.has_option('S4', 'lastUSN'):
			ud.debug(ud.LDAP, ud.INFO, "__init__: init lastUSN with 0")
			self._set_config_option('S4', 'lastUSN', '0')
			self.__lastUSN = 0
		else:
			self.__lastUSN = int(self._get_config_option('S4', 'lastUSN'))

		if not self.config.has_section('S4 GUID'):
			ud.debug(ud.LDAP, ud.INFO, "__init__: init add config section 'S4 GUID'")
			self.config.add_section('S4 GUID')
		try:
			self.ctrl_show_deleted = LDAPControl(LDAP_SERVER_SHOW_DELETED_OID, criticality=1)
			self.s4_search_ext_s('', ldap.SCOPE_BASE, 'objectclass=*', [], serverctrls=[self.ctrl_show_deleted])
		except ldap.UNAVAILABLE_CRITICAL_EXTENSION:
			# e.g. Samba4:
			#   ldapsearch -x -H ldap://localhost -b '' -s base '(objectClass=*)' supportedControl
			# shows that it's supported, but currently it is unhappy if you mark it critical
			self.ctrl_show_deleted = LDAPControl('1.2.840.113556.1.4.417', criticality=0)

		self.serverctrls_for_add_and_modify = []
		if 'univention_samaccountname_ldap_check' in self.configRegistry.get('samba4/ldb/sam/module/prepend', '').split():
			# The S4 connector must bypass this LDB module if it is activated via samba4/ldb/sam/module/prepend
			# The OID of the 'bypass_samaccountname_ldap_check' control is defined in ldb.h
			ldb_ctrl_bypass_samaccountname_ldap_check = LDAPControl('1.3.6.1.4.1.10176.1004.0.4.1', criticality=0)
			self.serverctrls_for_add_and_modify.append(ldb_ctrl_bypass_samaccountname_ldap_check)

		# objectSid modification for an Samba4 object is only possible with the "provision" control:
		if self.configRegistry.is_true('connector/s4/mapping/sid_to_s4', False):
			self.serverctrls_for_add_and_modify.append(LDAPControl(LDB_CONTROL_PROVISION_OID, criticality=0))
			self.serverctrls_for_add_and_modify.append(LDAPControl(DSDB_CONTROL_REPLICATED_UPDATE_OID, criticality=0))

		# Save a list of objects just created, this is needed to
		# prevent the back sync of a password if it was changed just
		# after the creation
		self.creation_list = []

		# Build an internal cache with S4 as key and the UCS object as cache

		# UCS group member DNs to S4 group member DN
		# * entry used and updated while reading in group_members_sync_from_ucs
		# * entry flushed during delete+move at in sync_to_ucs and sync_from_ucs
		self.group_member_mapping_cache_ucs = {}

		# S4 group member DNs to UCS group member DN
		# * entry used and updated while reading in group_members_sync_to_ucs
		# * entry flushed during delete+move at in sync_to_ucs and sync_from_ucs
		self.group_member_mapping_cache_con = {}

		# Save the old members of a group
		# The connector is object based, at least in the direction AD/S4 to LDAP, because we don't
		# have a local cache. group_members_cache_ucs and group_members_cache_con help to
		# determine if the group membership was already saved. For example, one group and
		# five users are created on UCS side. After two users have been synced to AD/S4,
		# the group is snyced. But in AD/S4 only existing members can be stored in the group.
		# Now the sync goes back from AD/S4 to LDAP and we should not remove the three users
		# from the group. For this we remove only members who are in the local cache.

		# UCS groups and UCS members
		# * initialized during start
		# * entry updated in group_members_sync_from_ucs and object_memberships_sync_from_ucs
		# * entry flushed for group object in sync_to_ucs / add_in_ucs
		# * entry used for decision in group_members_sync_to_ucs
		self.group_members_cache_ucs = {}

		# S4 groups and S4 members
		# * initialized during start
		# * entry updated in group_members_sync_to_ucs and object_memberships_sync_to_ucs
		# * entry flushed for group object in sync_from_ucs / ADD
		# * entry used for decision in group_members_sync_from_ucs
		self.group_members_cache_con = {}

		if init_group_cache:
			ud.debug(ud.LDAP, ud.PROCESS, 'Building internal group membership cache')
			s4_groups = self.__search_s4(filter='objectClass=group', attrlist=['member'])
			ud.debug(ud.LDAP, ud.ALL, "__init__: s4_groups: %s" % s4_groups)
			for s4_group in s4_groups:
				if not s4_group or not s4_group[0]:
					continue

				s4_group_dn, s4_group_attrs = s4_group
				self.group_members_cache_con[s4_group_dn.lower()] = []
				if s4_group_attrs:
					s4_members = self.get_s4_members(s4_group_dn, s4_group_attrs)
					group_cache = self.group_members_cache_con[s4_group_dn.lower()]
					group_cache.extend(m.lower() for m in s4_members)

			ud.debug(ud.LDAP, ud.ALL, "__init__: self.group_members_cache_con: %s" % self.group_members_cache_con)

			ucs_groups = self.search_ucs(filter='objectClass=univentionGroup', attr=['uniqueMember'])
			for ucs_group in ucs_groups:
				group = ucs_group[0].lower()
				self.group_members_cache_ucs[group] = []
				if ucs_group[1]:
					for member in ucs_group[1].get('uniqueMember'):
						self.group_members_cache_ucs[group].append(member.lower())
			ud.debug(ud.LDAP, ud.ALL, "__init__: self.group_members_cache_ucs: %s" % self.group_members_cache_ucs)

			ud.debug(ud.LDAP, ud.PROCESS, 'Internal group membership cache was created')

		try:
			self.s4_sid = univention.s4connector.s4.decode_sid(
				self.s4_search_ext_s(s4_ldap_base, ldap.SCOPE_BASE, 'objectclass=domain', ['objectSid'])[0][1]['objectSid'][0])
		except Exception as msg:
			print("Failed to get SID from S4: %s" % msg)
			sys.exit(1)

	def s4_search_ext_s(self, *args, **kwargs):
		return fix_dn_in_search(self.lo_s4.lo.search_ext_s(*args, **kwargs))

	def open_s4(self):
		tls_mode = 2
		if '%s/s4/ldap/ssl' % self.CONFIGBASENAME in self.baseConfig and self.baseConfig['%s/s4/ldap/ssl' % self.CONFIGBASENAME] == "no":
			ud.debug(ud.LDAP, ud.INFO, "__init__: The LDAP connection to S4 does not use SSL (switched off by UCR \"%s/s4/ldap/ssl\")." % self.CONFIGBASENAME)
			tls_mode = 0

		protocol = self.baseConfig.get('%s/s4/ldap/protocol' % self.CONFIGBASENAME, 'ldap').lower()
		if protocol == 'ldapi':
			import urllib
			socket = urllib.quote(self.baseConfig.get('%s/s4/ldap/socket' % self.CONFIGBASENAME, ''), '')
			ldapuri = "%s://%s" % (protocol, socket)
		else:
			ldapuri = "%s://%s:%d" % (protocol, self.baseConfig['%s/s4/ldap/host' % self.CONFIGBASENAME], int(self.baseConfig['%s/s4/ldap/port' % self.CONFIGBASENAME]))

		# Determine s4_ldap_base with exact case
		try:
			self.lo_s4 = univention.uldap.access(host=self.s4_ldap_host, port=int(self.s4_ldap_port), base='', binddn=None, bindpw=None, start_tls=tls_mode, ca_certfile=self.s4_ldap_certificate, uri=ldapuri, reconnect=False)
			self.s4_ldap_base = self.s4_search_ext_s('', ldap.SCOPE_BASE, 'objectclass=*', ['defaultNamingContext'])[0][1]['defaultNamingContext'][0]
		except Exception:  # FIXME: which exception is to be caught
			self._debug_traceback(ud.ERROR, 'Failed to lookup S4 LDAP base, using UCR value.')

		self.lo_s4 = univention.uldap.access(host=self.s4_ldap_host, port=int(self.s4_ldap_port), base=self.s4_ldap_base, binddn=self.s4_ldap_binddn, bindpw=self.s4_ldap_bindpw, start_tls=tls_mode, ca_certfile=self.s4_ldap_certificate, decode_ignorelist=DECODE_IGNORELIST, uri=ldapuri, reconnect=False)

		self.lo_s4.lo.set_option(ldap.OPT_REFERRALS, 0)

		if self.configRegistry.get('connector/s4/mapping/dns/position') == 'legacy':
			self.s4_ldap_partitions = (self.s4_ldap_base,)
		else:
			self.s4_ldap_partitions = (self.s4_ldap_base, "DC=DomainDnsZones,%s" % self.s4_ldap_base, "DC=ForestDnsZones,%s" % self.s4_ldap_base)

	# encode string to unicode
	def encode(self, string):
		try:
			return unicode(string)
		except Exception:  # FIXME: which exception is to be caught?
			return unicode(string, 'latin1')

	def _get_lastUSN(self):
		_d = ud.function('ldap._get_lastUSN')  # noqa: F841
		return max(self.__lastUSN, int(self._get_config_option('S4', 'lastUSN')))

	def get_lastUSN(self):
		return self._get_lastUSN()

	def _commit_lastUSN(self):
		_d = ud.function('ldap._commit_lastUSN')  # noqa: F841
		self._set_config_option('S4', 'lastUSN', str(self.__lastUSN))

	def _set_lastUSN(self, lastUSN):
		_d = ud.function('ldap._set_lastUSN')  # noqa: F841
		ud.debug(ud.LDAP, ud.INFO, "_set_lastUSN: new lastUSN is: %s" % lastUSN)
		self.__lastUSN = lastUSN

	def __encode_GUID(self, GUID):
		# GUID may be unicode
		if isinstance(GUID, type(u'')):
			return GUID.encode('latin1').encode('base64')
		else:
			return GUID.encode('base64')

	def _get_DN_for_GUID(self, GUID):
		_d = ud.function('ldap._get_DN_for_GUID')  # noqa: F841
		return self._decode_dn_from_config_option(self._get_config_option('S4 GUID', self.__encode_GUID(GUID)))

	def _set_DN_for_GUID(self, GUID, DN):
		_d = ud.function('ldap._set_DN_for_GUID')  # noqa: F841
		self._set_config_option('S4 GUID', self.__encode_GUID(GUID), self._encode_dn_as_config_option(DN))

	def _remove_GUID(self, GUID):
		_d = ud.function('ldap._remove_GUID')  # noqa: F841
		self._remove_config_option('S4 GUID', self.__encode_GUID(GUID))

	# handle rejected Objects
	def _save_rejected(self, id, dn):
		_d = ud.function('ldap._save_rejected')  # noqa: F841
		try:
			self._set_config_option('S4 rejected', str(id), encode_attrib(dn))
		except UnicodeEncodeError:
			self._set_config_option('S4 rejected', str(id), 'unknown')
			self._debug_traceback(ud.WARN, "failed to set dn in configfile (S4 rejected)")

	def _get_rejected(self, id):
		_d = ud.function('ldap._get_rejected')  # noqa: F841
		return self._get_config_option('S4 rejected', str(id))

	def _remove_rejected(self, id):
		_d = ud.function('ldap._remove_rejected')  # noqa: F841
		self._remove_config_option('S4 rejected', str(id))

	def _list_rejected(self):
		"""Returns rejected Samba4-objects"""
		_d = ud.function('ldap._list_rejected')  # noqa: F841
		result = []
		for i in self._get_config_items('S4 rejected'):
			result.append(i)
		return result

	def list_rejected(self):
		return self._list_rejected()

	def save_rejected(self, object):
		"""
		save object as rejected
		"""
		_d = ud.function('ldap.save_rejected')  # noqa: F841
		self._save_rejected(self.__get_change_usn(object), object['dn'])

	def remove_rejected(self, object):
		"""
		remove object from rejected
		"""
		_d = ud.function('ldap.remove_rejected')  # noqa: F841
		self._remove_rejected(self.__get_change_usn(object), object['dn'])

	def addToCreationList(self, dn):
		if not dn.lower() in self.creation_list:
			self.creation_list.append(dn.lower())

	def removeFromCreationList(self, dn):
		self.creation_list = [s for s in self.creation_list if s != dn.lower()]

	def isInCreationList(self, dn):
		return dn.lower() in self.creation_list

	def get_object_dn(self, dn):
		_d = ud.function('ldap.get_object_dn')  # noqa: F841
		for i in [0, 1]:  # do it twice if the LDAP connection was closed
			try:
				dn, s4_object = self.s4_search_ext_s(compatible_modstring(dn), ldap.SCOPE_BASE, '(objectClass=*)', ('dn',))[0]
				ud.debug(ud.LDAP, ud.INFO, "get_object: got object: %r" % (dn,))
				return dn
			except (IndexError, ldap.NO_SUCH_OBJECT):
				return
			except (ldap.SERVER_DOWN, SystemExit):
				if i == 0:
					self.open_s4()
					continue
				raise
			except Exception:  # FIXME: which exception is to be caught?
				self._debug_traceback(ud.ERROR, 'Could not get object DN')  # TODO: remove except block

	def parse_range_retrieval_attrs(self, s4_attrs, attr):
		for k in s4_attrs:
			m = self.RANGE_RETRIEVAL_PATTERN.match(k)
			if not m or m.group(1) != attr:
				continue

			key = k
			values = s4_attrs[key]
			lower = int(m.group(2))
			upper = m.group(3)
			if upper != "*":
				upper = int(upper)
			break
		else:
			key = None
			values = []
			lower = 0
			upper = "*"
		return (key, values, lower, upper)

	def value_range_retrieval(self, s4_dn, s4_attrs, attr):
		(key, values, lower, upper) = self.parse_range_retrieval_attrs(s4_attrs, attr)
		ud.debug(ud.LDAP, ud.INFO, "value_range_retrieval: response:  %s" % (key,))
		if lower != 0:
			ud.debug(ud.LDAP, ud.ERROR, "value_range_retrieval: invalid range retrieval response:  %s" % (key,))
			raise ldap.PROTOCOL_ERROR
		all_values = values

		while upper != "*":
			next_key = "%s;range=%d-*" % (attr, upper + 1)
			s4_attrs = self.get_object(s4_dn, [next_key])
			returned_before = upper
			(key, values, lower, upper) = self.parse_range_retrieval_attrs(s4_attrs, attr)
			if lower != returned_before + 1:
				ud.debug(ud.LDAP, ud.ERROR, "value_range_retrieval: invalid range retrieval response: asked for %s but got %s" % (next_key, key))
				raise ldap.PARTIAL_RESULTS
			ud.debug(ud.LDAP, ud.INFO, "value_range_retrieval: response:  %s" % (key,))
			all_values.extend(values)
		return all_values

	def get_s4_members(self, s4_dn, s4_attrs):
		s4_members = s4_attrs.get('member')
		if s4_members is None:
			s4_members = []
		elif s4_members == []:
			del s4_attrs['member']
			s4_members = self.value_range_retrieval(s4_dn, s4_attrs, 'member')
			s4_attrs['member'] = s4_members
		return s4_members

	def get_object(self, dn, attrlist=None):
		"""Get an object from S4-LDAP"""
		_d = ud.function('ldap.get_object')  # noqa: F841
		for i in [0, 1]:  # do it twice if the LDAP connection was closed
			try:
				dn, s4_object = self.s4_search_ext_s(compatible_modstring(dn), ldap.SCOPE_BASE, '(objectClass=*)', attrlist=attrlist)[0]
				ud.debug(ud.LDAP, ud.INFO, "get_object: got object: %r" % (dn,))
				return encode_s4_object(s4_object)
			except (IndexError, ldap.NO_SUCH_OBJECT):
				return
			except (ldap.SERVER_DOWN, SystemExit):
				if i == 0:
					self.open_s4()
					continue
				raise
			except Exception:  # FIXME: which exception is to be caught?
				self._debug_traceback(ud.ERROR, 'Could not get object')  # TODO: remove except block?

	def __get_change_usn(self, object):
		'''
		get change usn as max(uSNCreated,uSNChanged)
		'''
		_d = ud.function('ldap.__get_change_usn')  # noqa: F841
		if not object:
			return 0
		usnchanged = 0
		usncreated = 0
		if 'uSNCreated' in object['attributes']:
			usncreated = int(object['attributes']['uSNCreated'][0])
		if 'uSNChanged' in object['attributes']:
			usnchanged = int(object['attributes']['uSNChanged'][0])

		return max(usnchanged, usncreated)

	def __search_s4_partitions(self, scope=ldap.SCOPE_SUBTREE, filter='', attrlist=[], show_deleted=False):
		'''
		search s4 across all partitions listed in self.s4_ldap_partitions
		'''
		_d = ud.function('ldap.__search_s4_partitions')  # noqa: F841
		res = []
		for base in self.s4_ldap_partitions:
			res += self.__search_s4(base, scope, filter, attrlist, show_deleted)

		return res

	def __get_s4_deleted(self, dn):
		return self.__search_s4(dn, scope=ldap.SCOPE_BASE, filter='(objectClass=*)', show_deleted=True)[0]

	def __search_s4(self, base=None, scope=ldap.SCOPE_SUBTREE, filter='', attrlist=[], show_deleted=False):
		'''
		search s4
		'''
		_d = ud.function('ldap.__search_s4')  # noqa: F841

		if not base:
			base = self.lo_s4.base

		ctrls = [
			SimplePagedResultsControl(True, PAGE_SIZE, ''),  # Must be the first
			LDAPControl(LDB_CONTROL_DOMAIN_SCOPE_OID, criticality=0),  # Don't show referrals
		]

		if show_deleted:
			ctrls.append(LDAPControl(LDAP_SERVER_SHOW_DELETED_OID, criticality=1))

		ud.debug(ud.LDAP, ud.INFO, "Search S4 with filter: %s" % filter)
		msgid = self.lo_s4.lo.search_ext(base, scope, filter, attrlist, serverctrls=ctrls, timeout=-1, sizelimit=0)

		res = []
		pages = 0
		while True:
			pages += 1
			rtype, rdata, rmsgid, serverctrls = self.lo_s4.lo.result3(msgid)
			res += rdata

			pctrls = [
				c
				for c in serverctrls
				if c.controlType == SimplePagedResultsControl.controlType
			]
			if pctrls:
				cookie = pctrls[0].cookie
				if cookie:
					if pages > 1:
						ud.debug(ud.LDAP, ud.PROCESS, "S4 search continues, already found %s objects" % len(res))
					ctrls[0].cookie = cookie
					msgid = self.lo_s4.lo.search_ext(base, scope, filter, attrlist, serverctrls=ctrls, timeout=-1, sizelimit=0)
				else:
					break
			else:
				ud.debug(ud.LDAP, ud.WARN, "S4 ignores PAGE_RESULTS")
				break

		return encode_s4_resultlist(fix_dn_in_search(res))

	def __remove_duplicates_with_order_preserving(self, searchResult, idFunction):
		seen = {}
		result = []
		for item in searchResult:
			marker = idFunction(item)
			if marker in seen:
				continue
			seen[marker] = 1
			result.append(item)
		return result

	def __search_s4_changes(self, show_deleted=False, filter=''):
		'''
		search s4 for changes since last update (changes greater lastUSN)
		'''
		_d = ud.function('ldap.__search_s4_changes')  # noqa: F841
		lastUSN = self._get_lastUSN()
		# filter erweitern um "(|(uSNChanged>=lastUSN+1)(uSNCreated>=lastUSN+1))"
		# +1 da suche nur nach '>=', nicht nach '>' möglich

		def search_s4_changes_by_attribute(attribute, lowerUSN, higherUSN=''):
			if higherUSN:
				usn_filter_format = '(&({attribute}>={lower_usn!e})({attribute}<={higher_usn!e}))'
			else:
				usn_filter_format = '({attribute}>={lower_usn!e})'

			usnFilter = format_escaped(usn_filter_format, attribute=attribute, lower_usn=lowerUSN, higher_usn=higherUSN)

			if filter != '':
				usnFilter = '(&(%s)(%s))' % (filter, usnFilter)

			res = self.__search_s4_partitions(filter=usnFilter, show_deleted=show_deleted)
			return sorted(res, key=lambda element: element[1][attribute][0])

		# search for objects with uSNCreated and uSNChanged in the known range
		returnObjects = []
		try:
			if lastUSN > 0:
				# During the init phase we have to search for created and changed objects
				# but we need to sync the objects only once
				returnObjects = search_s4_changes_by_attribute('uSNCreated', lastUSN + 1)
				returnObjects += search_s4_changes_by_attribute('uSNChanged', lastUSN + 1)

				returnObjects = self.__remove_duplicates_with_order_preserving(returnObjects, lambda x: x[0])
			else:
				# Every object has got a uSNCreated
				returnObjects = search_s4_changes_by_attribute('uSNCreated', lastUSN + 1)
		except (ldap.SERVER_DOWN, SystemExit):
			raise
		except ldap.SIZELIMIT_EXCEEDED:
			# The LDAP control page results was not successful. Without this control
			# S4 does not return more than 1000 results. We are going to split the
			# search.
			highestCommittedUSN = self.__get_highestCommittedUSN()
			tmpUSN = lastUSN
			ud.debug(ud.LDAP, ud.PROCESS, "Need to split results. highest USN is %s, lastUSN is %s" % (highestCommittedUSN, lastUSN))
			while (tmpUSN != highestCommittedUSN):
				lastUSN = tmpUSN
				tmpUSN += 999
				if tmpUSN > highestCommittedUSN:
					tmpUSN = highestCommittedUSN

				ud.debug(ud.LDAP, ud.INFO, "__search_s4_changes: search between USNs %s and %s" % (lastUSN + 1, tmpUSN))

				if lastUSN > 0:
					returnObjects += search_s4_changes_by_attribute('uSNCreated', lastUSN + 1, tmpUSN)
					for changedObject in search_s4_changes_by_attribute('uSNChanged', lastUSN + 1, tmpUSN):
						if changedObject not in returnObjects:
							returnObjects.append(changedObject)
				else:
					# Every object has got a uSNCreated
					returnObjects += search_s4_changes_by_attribute('uSNCreated', lastUSN + 1, tmpUSN)

		return returnObjects

	def __search_s4_changeUSN(self, changeUSN, show_deleted=True, filter=''):
		'''
		search s4 for change with id
		'''
		_d = ud.function('ldap.__search_s4_changeUSN')  # noqa: F841

		usn_filter = format_escaped('(|(uSNChanged={0!e})(uSNCreated={0!e}))', changeUSN)
		if filter != '':
			usn_filter = '(&({}){})'.format(filter, usn_filter)

		return self.__search_s4_partitions(filter=usn_filter, show_deleted=show_deleted)

	def __dn_from_deleted_object(self, object, GUID):
		'''
		gets dn for deleted object (original dn before the object was moved into the deleted objects container)
		'''
		_d = ud.function('ldap.__dn_from_deleted_object')  # noqa: F841

		rdn = object['dn'].split('\\0ADEL:')[0]
		last_known_parent = object['attributes'].get('lastKnownParent', [None])[0]
		if last_known_parent and '\\0ADEL:' in last_known_parent:
			dn, attr = self.__get_s4_deleted(last_known_parent)
			last_known_parent = self.__dn_from_deleted_object({'dn': dn, 'attributes': attr}, GUID)

		if last_known_parent:
			ud.debug(ud.LDAP, ud.INFO, "__dn_from_deleted_object: get DN from lastKnownParent (%r) and rdn (%r)" % (last_known_parent, rdn))

			rdn_exploded = str2dn(unicode_to_utf8(rdn))
			parent_exploded = str2dn(unicode_to_utf8(last_known_parent))
			return unicode(ldap.dn.dn2str(rdn_exploded + parent_exploded), 'utf8')
		else:
			ud.debug(ud.LDAP, ud.WARN, 'lastKnownParent attribute for deleted object rdn="%s" was not set, so we must ignore the object' % rdn)
			return None

	def __object_from_element(self, element):
		"""
		gets an object from an S4 LDAP-element, implements necessary mapping

		:param element:
			(dn, attributes) tuple from a search in S4-LDAP
		:ptype element: tuple
		"""
		_d = ud.function('ldap.__object_from_element')  # noqa: F841
		if element[0] == 'None' or element[0] is None:
			return None  # referrals

		object = {}
		object['dn'] = self.encode(element[0])
		deleted_object = False
		GUID = element[1]['objectGUID'][0]  # don't send this GUID to univention-debug

		# modtype
		if 'isDeleted' in element[1] and element[1]['isDeleted'][0] == 'TRUE':
			object['modtype'] = 'delete'
			deleted_object = True
		else:
			# check if is moved
			olddn = self.encode(self._get_DN_for_GUID(GUID))
			ud.debug(ud.LDAP, ud.INFO, "object_from_element: olddn: %s" % olddn)
			if olddn and not compatible_modstring(olddn).lower() == compatible_modstring(self.encode(element[0])).lower() and ldap.explode_rdn(compatible_modstring(olddn).lower()) == ldap.explode_rdn(compatible_modstring(self.encode(element[0])).lower()):
				object['modtype'] = 'move'
				object['olddn'] = olddn
				ud.debug(ud.LDAP, ud.INFO, "object_from_element: detected move of S4-Object")
			else:
				object['modtype'] = 'modify'
				if olddn and not compatible_modstring(olddn).lower() == compatible_modstring(self.encode(element[0])).lower():  # modrdn
					object['olddn'] = olddn

		object['attributes'] = element[1]
		for key in object['attributes'].keys():
			vals = object['attributes'][key][:]
			if key not in DECODE_IGNORELIST:
				vals = [self.encode(value) for value in vals]
			object['attributes'][key] = vals

		if deleted_object:  # dn is in deleted-objects-container, need to parse to original dn
			object['deleted_dn'] = object['dn']
			object['dn'] = self.__dn_from_deleted_object(object, GUID)
			ud.debug(ud.LDAP, ud.PROCESS, "object_from_element: DN of removed object: %r" % (object['dn'],))
			# self._remove_GUID(GUID) # cache is not needed anymore?

			if not object['dn']:
				return None
		return object

	def __identify_s4_type(self, object):
		"""Identify the type of the specified S4 object"""
		_d = ud.function('ldap.__identify_s4_type')  # noqa: F841
		if not object or 'attributes' not in object:
			return None
		for key in self.property.keys():
			if self._filter_match(self.property[key].con_search_filter, object['attributes']):
				return key

	def __update_lastUSN(self, object):
		"""
		Update der lastUSN
		"""
		_d = ud.function('ldap.__update_lastUSN')  # noqa: F841
		if self.__get_change_usn(object) > self._get_lastUSN():
			self._set_lastUSN(self.__get_change_usn(object))

	def __get_highestCommittedUSN(self):
		'''
		get highestCommittedUSN stored in S4
		'''
		_d = ud.function('ldap.__get_highestCommittedUSN')  # noqa: F841
		try:
			res = self.s4_search_ext_s(
				'',  # base
				ldap.SCOPE_BASE,
				'objectclass=*',  # filter
				['highestCommittedUSN'],
			)[0][1]['highestCommittedUSN'][0]

			return int(res)
		except Exception:
			self._debug_traceback(ud.ERROR, "search for highestCommittedUSN failed")
			print("ERROR: initial search in S4 failed, check network and configuration")
			return 0

	def set_primary_group_to_ucs_user(self, object_key, object_ucs):
		'''
		check if correct primary group is set to a fresh UCS-User
		'''
		_d = ud.function('ldap.set_primary_group_to_ucs_user')  # noqa: F841

		rid_filter = format_escaped("(samaccountname={0!e})", compatible_modstring(object_ucs['username']))
		s4_group_rid_resultlist = self.__search_s4(base=self.lo_s4.base, scope=ldap.SCOPE_SUBTREE, filter=rid_filter, attrlist=['dn', 'primaryGroupID'])

		if not s4_group_rid_resultlist[0][0] in ['None', '', None]:

			s4_group_rid = s4_group_rid_resultlist[0][1]['primaryGroupID'][0]

			ud.debug(ud.LDAP, ud.INFO, "set_primary_group_to_ucs_user: S4 rid: %s" % s4_group_rid)
			object_sid_string = str(self.s4_sid) + "-" + str(s4_group_rid)

			ldap_group_filter = format_escaped("(objectSid={0!e})", object_sid_string)
			ldap_group_s4 = self.__search_s4(base=self.lo_s4.base, scope=ldap.SCOPE_SUBTREE, filter=ldap_group_filter)

			if not ldap_group_s4[0][0]:
				ud.debug(ud.LDAP, ud.ERROR, "s4.set_primary_group_to_ucs_user: Primary Group in S4 not found (not enough rights?), sync of this object will fail!")
			ucs_group = self._object_mapping('group', {'dn': ldap_group_s4[0][0], 'attributes': ldap_group_s4[0][1]}, object_type='con')

			object_ucs['primaryGroup'] = ucs_group['dn']

	def primary_group_sync_from_ucs(self, key, object):  # object mit s4-dn
		'''
		sync primary group of an ucs-object to s4
		'''
		_d = ud.function('ldap.primary_group_sync_from_ucs')  # noqa: F841

		object_key = key
		object_ucs = self._object_mapping(object_key, object)

		ldap_object_ucs = self.get_ucs_ldap_object(object_ucs['dn'])
		if not ldap_object_ucs:
			ud.debug(ud.LDAP, ud.PROCESS, 'primary_group_sync_from_ucs: The UCS object (%s) was not found. The object was removed.' % object_ucs['dn'])
			return

		ldap_object_s4 = self.get_object(object['dn'])
		if not ldap_object_s4:
			ud.debug(ud.LDAP, ud.PROCESS, 'primary_group_sync_from_ucs: The S4 object (%s) was not found. The object was removed.' % object['dn'])
			return

		ucs_group_id = ldap_object_ucs['gidNumber'][0]  # FIXME: fails if group does not exists
		ucs_group_filter = format_escaped('(&(objectClass=univentionGroup)(gidNumber={0!e}))', ucs_group_id)
		ucs_group_ldap = self.search_ucs(filter=ucs_group_filter)  # is empty !?

		if ucs_group_ldap == []:
			ud.debug(ud.LDAP, ud.WARN, "primary_group_sync_from_ucs: failed to get UCS-Group with gid %s, can't sync to S4" % ucs_group_id)
			return

		member_key = 'group'  # FIXME: generate by identify-function ?
		s4_group_object = self._object_mapping(member_key, {'dn': ucs_group_ldap[0][0], 'attributes': ucs_group_ldap[0][1]}, 'ucs')
		ldap_object_s4_group = self.get_object(s4_group_object['dn'])
		rid = "513"  # FIXME: Fallback: should be configurable
		if ldap_object_s4_group and 'objectSid' in ldap_object_s4_group:
			sid = ldap_object_s4_group['objectSid'][0]
			rid = sid[string.rfind(sid, "-") + 1:]
		else:
			print("no SID !!!")

		# to set a valid primary group we need to:
		# - check if either the primaryGroupID is already set to rid or
		# - prove that the user is member of this group, so: at first we need the s4_object for this element
		# this means we need to map the user to get it's S4-DN which would call this function recursively

		if "primaryGroupID" in ldap_object_s4 and ldap_object_s4["primaryGroupID"][0] == rid:
			ud.debug(ud.LDAP, ud.INFO, "primary_group_sync_from_ucs: primary Group is correct, no changes needed")
			return True  # nothing left to do
		else:
			s4_members = self.get_s4_members(s4_group_object['dn'], ldap_object_s4_group)
			s4_members = map(compatible_modstring, s4_members)
			object_dn_modstring = compatible_modstring(object['dn'])

			s4_members_lower = map(str.lower, s4_members)
			if object_dn_modstring.lower() not in s4_members_lower:  # add as member
				s4_members.append(object_dn_modstring)
				ud.debug(ud.LDAP, ud.INFO, "primary_group_sync_from_ucs: primary Group needs change of membership in S4")
				self.lo_s4.lo.modify_s(compatible_modstring(s4_group_object['dn']), [(ldap.MOD_REPLACE, 'member', s4_members)])

			# set new primary group
			ud.debug(ud.LDAP, ud.INFO, "primary_group_sync_from_ucs: changing primary Group in S4")
			self.lo_s4.lo.modify_s(object_dn_modstring, [(ldap.MOD_REPLACE, 'primaryGroupID', rid)])

			# If the user is not member in UCS of the previous primary group, the user must
			# be removed from this group in AD: https://forge.univention.org/bugzilla/show_bug.cgi?id=26514
			prev_samba_primary_group_id = ldap_object_s4.get('primaryGroupID', [])[0]
			object_sid_string = str(self.s4_sid) + "-" + str(prev_samba_primary_group_id)
			s4_group_filter = format_escaped('(objectSid={0!e})', object_sid_string)
			s4_group = self.__search_s4(base=self.lo_s4.base, scope=ldap.SCOPE_SUBTREE, filter=s4_group_filter)
			ucs_group_object = self._object_mapping('group', {'dn': s4_group[0][0], 'attributes': s4_group[0][1]}, 'con')
			ucs_group = self.get_ucs_ldap_object(ucs_group_object['dn'])
			is_member = False
			for member in ucs_group.get('uniqueMember', []):
				if member.lower() == object_ucs['dn'].lower():
					is_member = True
					break
			if not is_member:
				# remove S4 member from previous group
				ud.debug(ud.LDAP, ud.INFO, "primary_group_sync_from_ucs: remove S4 member from previous group")
				self.lo_s4.lo.modify_s(s4_group[0][0], [(ldap.MOD_DELETE, 'member', [object_dn_modstring])])

			return True

	def primary_group_sync_to_ucs(self, key, object):  # object mit ucs-dn
		'''
		sync primary group of an s4-object to ucs
		'''
		_d = ud.function('ldap.primary_group_sync_to_ucs')  # noqa: F841

		object_key = key

		s4_object = self._object_mapping(object_key, object, 'ucs')
		ldap_object_s4 = self.get_object(s4_object['dn'])
		s4_group_rid = ldap_object_s4['primaryGroupID'][0]
		ud.debug(ud.LDAP, ud.INFO, "primary_group_sync_to_ucs: S4 rid: %s" % s4_group_rid)

		object_sid_string = str(self.s4_sid) + "-" + str(s4_group_rid)

		ldap_group_filter = format_escaped('(objectSid={0!e})', object_sid_string)
		ldap_group_s4 = self.__search_s4(base=self.lo_s4.base, scope=ldap.SCOPE_SUBTREE, filter=ldap_group_filter)

		ucs_group = self._object_mapping('group', {'dn': ldap_group_s4[0][0], 'attributes': ldap_group_s4[0][1]})

		ud.debug(ud.LDAP, ud.INFO, "primary_group_sync_to_ucs: ucs-group: %s" % ucs_group['dn'])

		ucs_admin_object = univention.admin.objects.get(self.modules[object_key], co='', lo=self.lo, position='', dn=object['dn'])
		ucs_admin_object.open()

		if not ucs_admin_object['primaryGroup'].lower() == ucs_group['dn'].lower():
			# need to set to dn with correct case or the ucs-module will fail
			new_group = ucs_group['dn'].lower()
			ucs_admin_object['primaryGroup'] = new_group
			ucs_admin_object.modify()

			ud.debug(ud.LDAP, ud.INFO, "primary_group_sync_to_ucs: changed primary Group in ucs")
		else:
			ud.debug(ud.LDAP, ud.INFO, "primary_group_sync_to_ucs: change of primary Group in ucs not needed")

	def object_memberships_sync_from_ucs(self, key, object):
		"""
		sync group membership in S4 if object was changend in UCS
		"""
		_d = ud.function('ldap.object_memberships_sync_from_ucs')  # noqa: F841
		ud.debug(ud.LDAP, ud.INFO, "object_memberships_sync_from_ucs: object: %s" % object)

		if 'group' in self.property:
			if getattr(self.property['group'], 'sync_mode', '') in ['read', 'none']:
				ud.debug(ud.LDAP, ud.INFO, "group memberships sync to s4 ignored, group sync_mode is read")
				return

		# search groups in UCS which have this object as member

		object_ucs = self._object_mapping(key, object)

		# Exclude primary group
		ucs_object_gid = object_ucs['attributes'].get('gidNumber', [])[0]
		ucs_group_filter = format_escaped('(&(objectClass=univentionGroup)(uniqueMember={0!e})(!(gidNumber={1!e})))', object_ucs['dn'], ucs_object_gid)
		ucs_groups_ldap = self.search_ucs(filter=ucs_group_filter)

		if ucs_groups_ldap == []:
			ud.debug(ud.LDAP, ud.INFO, "object_memberships_sync_from_ucs: No group-memberships in UCS for %s" % object['dn'])
			return

		ud.debug(ud.LDAP, ud.INFO, "object_memberships_sync_from_ucs: is member in %s groups " % len(ucs_groups_ldap))

		for groupDN, attributes in ucs_groups_ldap:
			if groupDN not in ['None', '', None]:
				s4_object = {'dn': groupDN, 'attributes': attributes, 'modtype': 'modify'}
				if not self._ignore_object('group', s4_object):
					sync_object = self._object_mapping('group', s4_object, 'ucs')
					sync_object_s4 = self.get_object(sync_object['dn'])
					s4_group_object = {'dn': sync_object['dn'], 'attributes': sync_object_s4}
					if sync_object_s4:
						# self.group_members_sync_from_ucs( 'group', sync_object )
						self.one_group_member_sync_from_ucs(s4_group_object, object)

			self.__group_cache_ucs_append_member(groupDN, object_ucs['dn'])

	def __group_cache_ucs_append_member(self, group, member):
		group_lower = group.lower()
		member_lower = member.lower()
		ud.debug(ud.LDAP, ud.INFO, "__group_cache_ucs_append_member: Append user %s to UCS group member cache of %s" % (member_lower, group_lower))
		members = self.group_members_cache_ucs.get(group_lower)
		if not members:
			self.group_members_cache_ucs[group_lower] = [member_lower]
		else:
			members.append(member_lower)

	def group_members_sync_from_ucs(self, key, object):  # object mit s4-dn
		"""
		sync groupmembers in S4 if changend in UCS
		"""
		_d = ud.function('ldap.group_members_sync_from_ucs')  # noqa: F841

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: %s" % object)

		object_key = key
		object_ucs = self._object_mapping(object_key, object)
		object_ucs_dn = object_ucs['dn']

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: type of object_ucs['dn']: %s" % type(object_ucs_dn))
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: dn is: %s" % object_ucs_dn)
		ldap_object_ucs = self.get_ucs_ldap_object(object_ucs_dn)

		if not ldap_object_ucs:
			ud.debug(ud.LDAP, ud.PROCESS, 'group_members_sync_from_ucs:: The UCS object (%s) was not found. The object was removed.' % object_ucs_dn)
			return

		ldap_object_ucs_gidNumber = ldap_object_ucs['gidNumber'][0]
		ucs_members = set(ldap_object_ucs.get('uniqueMember', []))
		ud.debug(ud.LDAP, ud.INFO, "ucs_members: %s" % ucs_members)
		if ucs_members:
			# skip members which have this group as primary group (set same gidNumber)
			prim_members_ucs_filter = format_escaped('(gidNumber={0!e})', ldap_object_ucs_gidNumber)
			prim_members_ucs = self.lo.lo.search(filter=prim_members_ucs_filter, attr=['gidNumber'])
			for prim_object in prim_members_ucs:
				if prim_object[0].lower() in ucs_members:
					ucs_members.remove(prim_object[0].lower())
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: clean ucs_members: %s" % ucs_members)

		# all dn's need to be lower-case so we can compare them later and put them in the UCS group member cache:
		self.group_members_cache_ucs[object_ucs_dn.lower()] = []
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: UCS group member cache reset")

		# lookup all current members of S4 group
		ldap_object_s4 = self.get_object(object['dn'])
		if not ldap_object_s4:
			ud.debug(ud.LDAP, ud.PROCESS, 'group_members_sync_from_ucs:: The S4 object (%s) was not found. The object was removed.' % object['dn'])
			return
		s4_members = set(self.get_s4_members(object['dn'], ldap_object_s4))
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: s4_members %s" % s4_members)

		# map members from UCS to S4 and check if they exist
		s4_members_from_ucs = set()  # Code review comment: For some reason this is a list of lowercase DNs
		for member_dn in ucs_members:
			s4_dn = self.group_member_mapping_cache_ucs.get(member_dn.lower())
			if s4_dn:
				ud.debug(ud.LDAP, ud.INFO, "Found %s in UCS group member cache: %s" % (member_dn, s4_dn))
				s4_members_from_ucs.add(s4_dn.lower())
				self.__group_cache_ucs_append_member(object_ucs_dn, member_dn)
			else:
				ud.debug(ud.LDAP, ud.INFO, "Did not find %s in UCS group member cache" % member_dn)
				member_object = {'dn': member_dn, 'modtype': 'modify', 'attributes': self.lo.get(member_dn)}

				try:
					# check if this is members primary group, if true it shouldn't be added to s4
					if member_object['attributes']['gidNumber'][0] == ldap_object_ucs_gidNumber:
						# is primary group
						continue
				except (KeyError, IndexError):
					# can't sync them if users have no posix-account
					continue

				mo_key = self.identify_udm_object(member_dn, member_object['attributes'])
				if mo_key is None:
					ud.debug(ud.LDAP, ud.WARN, "group_members_sync_from_ucs: failed to identify object type of ucs member, ignore membership: %s" % member_dn)
					continue  # member is an object which will not be synced

				s4_dn = self._object_mapping(mo_key, member_object, 'ucs')['dn']
				# check if dn exists in s4
				try:
					if self.lo_s4.get(s4_dn, attr=['cn']):  # search only for cn to suppress coding errors
						s4_members_from_ucs.add(s4_dn.lower())
						ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: Adding %s to UCS group member cache, value: %s" % (member_dn.lower(), s4_dn))
						self.group_member_mapping_cache_ucs[member_dn.lower()] = s4_dn
						self.__group_cache_ucs_append_member(object_ucs_dn, member_dn)
				except ldap.SERVER_DOWN:
					raise
				except Exception:  # FIXME: which exception is to be caught?
					self._debug_traceback(ud.PROCESS, "group_members_sync_from_ucs: failed to get S4 dn for UCS group member %s, assume object doesn't exist" % member_dn)

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: UCS-members in s4_members_from_ucs %s" % s4_members_from_ucs)

		# check if members in S4 don't exist in UCS, if true they need to be added in S4
		for member_dn in s4_members_from_ucs:
			if not member_dn.lower() in s4_members_from_ucs:
				try:
					s4_object = self.get_object(member_dn)

					mo_key = self.__identify_s4_type({'dn': member_dn, 'attributes': s4_object})
					ucs_dn = self._object_mapping(mo_key, {'dn': member_dn, 'attributes': s4_object})['dn']
					if not self.lo.get(ucs_dn, attr=['cn']):
						# Leave the following line commented out, as we don't want to keep the member in Samba/AD if it's not present in OpenLDAP
						# Note: in this case the membership gets removed even if the object itself is ignored for synchronization
						# s4_members_from_ucs.append(member_dn.lower())
						ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: Object exists only in S4 [%s]" % ucs_dn)
					elif self._ignore_object(mo_key, {'dn': member_dn, 'attributes': s4_object}):
						# Keep the member in Samba/AD if it's also present in OpenLDAP but ignored in synchronization?
						s4_members_from_ucs.add(member_dn.lower())
						ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: Object ignored in S4 [%s], key = [%s]" % (ucs_dn, mo_key))
				except ldap.SERVER_DOWN:
					raise
				except Exception:  # FIXME: which exception is to be caught?
					self._debug_traceback(ud.PROCESS, "group_members_sync_from_ucs: failed to get UCS dn for S4 group member %s" % member_dn)

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: UCS-and S4-members in s4_members_from_ucs %s" % s4_members_from_ucs)

		# compare lists and generate modlist
		# direct compare is not possible, because s4_members_from_ucs are all lowercase, s4_members are not, so we need to iterate...
		# FIXME: should be done in the last iteration (above)

		# need to remove users from s4_members_from_ucs which have this group as primary group. may failed earlier if groupnames are mapped
		try:
			group_rid = decode_sid(fix_dn_in_search(self.lo_s4.lo.search_s(compatible_modstring(object['dn']), ldap.SCOPE_BASE, '(objectClass=*)', ['objectSid']))[0][1]['objectSid'][0]).split('-')[-1]
		except ldap.NO_SUCH_OBJECT:
			group_rid = None

		if group_rid:
			# search for members who have this as their primaryGroup
			prim_members_s4_filter = format_escaped('(primaryGroupID={0!e})', group_rid)
			prim_members_s4 = self.__search_s4(self.lo_s4.base, ldap.SCOPE_SUBTREE, prim_members_s4_filter, ['cn'])

			for prim_dn, prim_object in prim_members_s4:
				if prim_dn not in ['None', '', None]:  # filter referrals
					if prim_dn.lower() in s4_members_from_ucs:
						s4_members_from_ucs.remove(prim_dn.lower())
					elif prim_dn in s4_members_from_ucs:
						# Code review comment: Obsolete? s4_members_from_ucs should be all lowercase at this point
						s4_members_from_ucs.remove(prim_dn)

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: s4_members_from_ucs without members with this as their primary group: %s" % s4_members_from_ucs)

		add_members = s4_members_from_ucs
		del_members = set()

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: members to add initialized: %s" % add_members)

		for member_dn in s4_members:
			ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: %s in s4_members_from_ucs?" % member_dn)
			member_dn_lower = member_dn.lower()
			if member_dn_lower in s4_members_from_ucs:
				ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: Yes")
				add_members.remove(member_dn_lower)
			else:
				if object['modtype'] == 'add':
					ud.debug(ud.LDAP, ud.PROCESS, "group_members_sync_from_ucs: %s is newly added. For this case don't remove current S4 members." % (object['dn'].lower()))
				elif (member_dn_lower in self.group_members_cache_con.get(object['dn'].lower(), [])) or (self.property.get('group') and self.property['group'].sync_mode in ['write', 'none']):
					# FIXME: Should this really also be done if sync_mode for group is 'none'?
					# remove member only if he was in the cache on S4 side
					# otherwise it is possible that the user was just created on S4 and we are on the way back
					ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: No")
					del_members.add(member_dn)
				else:
					ud.debug(ud.LDAP, ud.PROCESS, "group_members_sync_from_ucs: %s was not found in S4 group member cache of %s, don't delete" % (member_dn_lower, object['dn'].lower()))

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: members to add: %s" % add_members)
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: members to del: %s" % del_members)

		if add_members or del_members:
			s4_members |= add_members  # Note: add_members are only lowercase
			s4_members -= del_members  # Note: del_members are case sensitive
			ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: members result: %s" % s4_members)

			modlist_members = [compatible_modstring(member) for member in s4_members]
			ud.debug(ud.LDAP, ud.ALL, "group_members_sync_from_ucs: modlist: %s" % modlist_members)
			try:
				self.lo_s4.lo.modify_s(compatible_modstring(object['dn']), [(ldap.MOD_REPLACE, 'member', modlist_members)])
			except ldap.SERVER_DOWN:
				raise
			except Exception:  # FIXME: which exception is to be caught?
				ud.debug(ud.LDAP, ud.WARN, "group_members_sync_from_ucs: failed to sync members: (%s,%s)" % (object['dn'], [(ldap.MOD_REPLACE, 'member', modlist_members)]))
				raise

		return True

	def object_memberships_sync_to_ucs(self, key, object):
		"""
		sync group membership in UCS if object was changend in S4
		"""
		_d = ud.function('ldap.object_memberships_sync_to_ucs')  # noqa: F841
		# disable this debug line, see Bug #12031
		# ud.debug(ud.LDAP, ud.INFO, "object_memberships_sync_to_ucs: object: %s" % object)

		if 'group' in self.property:
			if getattr(self.property['group'], 'sync_mode', '') in ['write', 'none']:
				ud.debug(ud.LDAP, ud.INFO, "group memberships sync to ucs ignored, group sync_mode is write")
				return

		if 'memberOf' in object['attributes']:
			for groupDN in object['attributes']['memberOf']:
				s4_object = {'dn': groupDN, 'attributes': self.get_object(groupDN), 'modtype': 'modify'}
				if not self._ignore_object('group', s4_object):
					sync_object = self._object_mapping('group', s4_object)
					ldap_object_ucs = self.get_ucs_ldap_object(sync_object['dn'])
					ucs_group_object = {'dn': sync_object['dn'], 'attributes': ldap_object_ucs}
					ud.debug(ud.LDAP, ud.INFO, "object_memberships_sync_to_ucs: sync_object: %s" % ldap_object_ucs)
					# check if group exists in UCS, may fail
					# if the group will be synced later
					if ldap_object_ucs:
						self.one_group_member_sync_to_ucs(ucs_group_object, object)

				if not self.group_members_cache_con.get(groupDN.lower()):
					self.group_members_cache_con[groupDN.lower()] = []
				dn = object['attributes'].get('distinguishedName', [None])[0]
				if dn:
					ud.debug(ud.LDAP, ud.INFO, "object_memberships_sync_to_ucs: Append user %s to S4 group member cache of %s" % (dn.lower(), groupDN.lower()))
					self.group_members_cache_con[groupDN.lower()].append(dn.lower())
				else:
					ud.debug(ud.LDAP, ud.INFO, "object_memberships_sync_to_ucs: Failed to append user %s to S4 group member cache of %s" % (object['dn'].lower(), groupDN.lower()))

	def __compare_lowercase(self, dn, dn_list):
		"""
		Checks if dn is in dn_list
		"""
		for d in dn_list:
			if dn.lower() == d.lower():
				return True
		return False

	def one_group_member_sync_to_ucs(self, ucs_group_object, object):
		"""
		sync groupmembers in UCS if changend one member in S4
		"""
		# In S4 the object['dn'] is member of the group sync_object

		ml = []
		if not self.__compare_lowercase(object['dn'], ucs_group_object['attributes'].get('uniqueMember', [])):
			ml.append((ldap.MOD_ADD, 'uniqueMember', [object['dn']]))

		if object['attributes'].get('uid'):
			uid = object['attributes'].get('uid', [])[0]
			if not self.__compare_lowercase(uid, ucs_group_object['attributes'].get('memberUid', [])):
				ml.append((ldap.MOD_ADD, 'memberUid', [uid]))

		if ml:
			ud.debug(ud.LDAP, ud.ALL, "one_group_member_sync_to_ucs: modlist: %s" % ml)
			try:
				self.lo.lo.modify_s(ucs_group_object['dn'], compatible_modlist(ml))
			except ldap.ALREADY_EXISTS:
				# The user is already member in this group or it is his primary group
				# This might happen, if we synchronize a rejected file with old information
				# See Bug #25709 Comment #17: https://forge.univention.org/bugzilla/show_bug.cgi?id=25709#c17
				ud.debug(ud.LDAP, ud.INFO, "one_group_member_sync_to_ucs: User is already member of the group: %s modlist: %s" % (ucs_group_object['dn'], ml))

	def one_group_member_sync_from_ucs(self, s4_group_object, object):
		"""
		sync groupmembers in S4 if changend one member in AD
		"""
		ml = []
		if not self.__compare_lowercase(object['dn'], s4_group_object['attributes'].get('member', [])):
			ml.append((ldap.MOD_ADD, 'member', [object['dn']]))

		if ml:
			ud.debug(ud.LDAP, ud.ALL, "one_group_member_sync_from_ucs: modlist: %s" % ml)
			try:
				self.lo_s4.lo.modify_s(s4_group_object['dn'], compatible_modlist(ml))
			except ldap.ALREADY_EXISTS:
				# The user is already member in this group or it is his primary group
				# This might happen, if we synchronize a rejected file with old information
				# See Bug #25709 Comment #17: https://forge.univention.org/bugzilla/show_bug.cgi?id=25709#c17
				ud.debug(ud.LDAP, ud.INFO, "one_group_member_sync_from_ucs: User is already member of the group: %s modlist: %s" % (s4_group_object['dn'], ml))

		# The user has been removed from the cache. He must be added in any case
		ud.debug(ud.LDAP, ud.INFO, "one_group_member_sync_from_ucs: Append user %s to S4 group member cache of %s" % (object['dn'].lower(), s4_group_object['dn'].lower()))
		if not self.group_members_cache_con.get(s4_group_object['dn'].lower()):
			self.group_members_cache_con[s4_group_object['dn'].lower()] = []
		self.group_members_cache_con[s4_group_object['dn'].lower()].append(object['dn'].lower())

	def __group_cache_con_append_member(self, group, member):
		group_lower = group.lower()
		member_lower = member.lower()
		ud.debug(ud.LDAP, ud.INFO, "__group_cache_con_append_member: Append user %s to S4 group member cache of %s" % (member_lower, group_lower))
		members = self.group_members_cache_con.get(group_lower)
		if not members:
			self.group_members_cache_con[group_lower] = [member_lower]
		else:
			members.append(member_lower)

	def group_members_sync_to_ucs(self, key, object):
		"""
		sync groupmembers in UCS if changend in S4
		"""
		_d = ud.function('ldap.group_members_sync_to_ucs')  # noqa: F841
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: object: %s" % object)

		object_key = key
		s4_object = self._object_mapping(object_key, object, 'ucs')
		s4_object_dn = s4_object['dn']
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: s4_object (mapped): %s" % s4_object)

		# FIXME: does not use dn-mapping-function
		ldap_object_s4 = self.get_object(s4_object_dn)
		if not ldap_object_s4:
			ud.debug(ud.LDAP, ud.PROCESS, 'group_members_sync_to_ucs:: The S4 object (%s) was not found. The object was removed.' % s4_object_dn)
			return

		s4_members = self.get_s4_members(object['dn'], ldap_object_s4)
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: s4_members %s" % s4_members)

		# search and add members which have this as their primaryGroup
		group_sid = ldap_object_s4['objectSid'][0]
		group_rid = group_sid[string.rfind(group_sid, "-") + 1:]
		prim_members_s4_filter = format_escaped('(primaryGroupID={0!e})', group_rid)
		prim_members_s4 = self.__search_s4(self.lo_s4.base, ldap.SCOPE_SUBTREE, prim_members_s4_filter)
		for prim_dn, prim_object in prim_members_s4:
			if prim_dn not in ['None', '', None]:  # filter referrals
				s4_members.append(prim_dn)
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: clean s4_members %s" % s4_members)

		self.group_members_cache_con[s4_object_dn.lower()] = []
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: S4 group member cache reset")

		# lookup all current members of UCS group
		ldap_object_ucs = self.get_ucs_ldap_object(object['dn'])
		ucs_members = set(ldap_object_ucs.get('uniqueMember', []))
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: ucs_members: %s" % ucs_members)

		# map members from S4 to UCS and check if they exist
		ucs_members_from_s4 = {'user': [], 'group': [], 'unknown': []}
		dn_mapping_ucs_member_to_s4 = {}
		for member_dn in s4_members:
			ucs_dn = self.group_member_mapping_cache_con.get(member_dn.lower())
			if ucs_dn:
				ud.debug(ud.LDAP, ud.INFO, "Found %s in S4 group member cache: DN: %s" % (member_dn, ucs_dn))
				ucs_members_from_s4['unknown'].append(ucs_dn.lower())
				dn_mapping_ucs_member_to_s4[ucs_dn.lower()] = member_dn
				self.__group_cache_con_append_member(s4_object_dn, member_dn)
			else:
				ud.debug(ud.LDAP, ud.INFO, "Did not find %s in S4 group member cache" % member_dn)
				member_object = self.get_object(member_dn)
				if member_object:
					mo_key = self.__identify_s4_type({'dn': member_dn, 'attributes': member_object})
					if not mo_key:
						ud.debug(ud.LDAP, ud.WARN, "group_members_sync_to_ucs: failed to identify object type of S4 group member, ignore membership: %s" % member_dn)
						continue  # member is an object which will not be synced
					if self._ignore_object(mo_key, {'dn': member_dn, 'attributes': member_object}):
						ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: Object dn %s should be ignored, ignore membership" % member_dn)
						continue

					ucs_dn = self._object_mapping(mo_key, {'dn': member_dn, 'attributes': member_object})['dn']
					ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: mapped S4 group member to ucs DN %s" % ucs_dn)

					dn_mapping_ucs_member_to_s4[ucs_dn.lower()] = member_dn

					try:
						if self.lo.get(ucs_dn):
							ucs_members_from_s4['unknown'].append(ucs_dn.lower())
							self.group_member_mapping_cache_con[member_dn.lower()] = ucs_dn
							self.__group_cache_con_append_member(s4_object_dn, member_dn)
						else:
							ud.debug(ud.LDAP, ud.INFO, "Failed to find %s via self.lo.get" % ucs_dn)
					except ldap.SERVER_DOWN:
						raise
					except Exception:  # FIXME: which exception is to be caught?
						self._debug_traceback(ud.PROCESS, "group_members_sync_to_ucs: failed to get UCS dn for S4 group member %s, assume object doesn't exist" % member_dn)

		# build an internal cache
		cache = {}

		# check if members in UCS don't exist in S4, if true they need to be added in UCS
		for member_dn in ucs_members:
			member_dn_lower = member_dn.lower()
			if not (member_dn_lower in ucs_members_from_s4['user'] or member_dn_lower in ucs_members_from_s4['group'] or member_dn_lower in ucs_members_from_s4['unknown']):
				try:
					cache[member_dn] = self.lo.get(member_dn)
					ucs_object = {'dn': member_dn, 'modtype': 'modify', 'attributes': cache[member_dn]}

					if self._ignore_object(key, object):
						continue

					for k in self.property.keys():
						if self.modules[k].identify(member_dn, ucs_object['attributes']):
							s4_dn = self._object_mapping(k, ucs_object, 'ucs')['dn']

							if not dn_mapping_ucs_member_to_s4.get(member_dn_lower):
								dn_mapping_ucs_member_to_s4[member_dn_lower] = s4_dn

							ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: search for: %s" % s4_dn)
							# search only for cn to suppress coding errors
							if not self.lo_s4.get(s4_dn, attr=['cn']):
								# member does not exist in S4 but should
								# stay a member in UCS
								ucs_members_from_s4[k].append(member_dn_lower)
							break
				except ldap.SERVER_DOWN:
					raise
				except Exception:  # FIXME: which exception is to be caught?
					self._debug_traceback(ud.PROCESS, "group_members_sync_to_ucs: failed to get S4 dn for UCS group member %s" % member_dn)

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: dn_mapping_ucs_member_to_s4=%s" % (dn_mapping_ucs_member_to_s4))
		add_members = copy.deepcopy(ucs_members_from_s4)
		del_members = {'user': [], 'group': []}

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: members to add initialized: %s" % add_members)

		for member_dn in ucs_members:
			member_dn_lower = member_dn.lower()
			if member_dn_lower in ucs_members_from_s4['user']:
				add_members['user'].remove(member_dn_lower)
			elif member_dn_lower in ucs_members_from_s4['group']:
				add_members['group'].remove(member_dn_lower)
			elif member_dn_lower in ucs_members_from_s4['unknown']:
				add_members['unknown'].remove(member_dn_lower)
			else:
				# remove member only if he was in the cache
				# otherwise it is possible that the user was just created on UCS

				if (member_dn_lower in self.group_members_cache_ucs.get(object['dn'].lower(), [])) or (self.property.get('group') and self.property['group'].sync_mode in ['read', 'none']):
					# FIXME: Should this really also be done if sync_mode for group is 'none'?
					ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: %s was found in UCS group member cache of %s" % (member_dn_lower, object['dn'].lower()))
					ucs_object_attr = cache.get(member_dn)
					if not ucs_object_attr:
						ucs_object_attr = self.lo.get(member_dn)
						cache[member_dn] = ucs_object_attr
					ucs_object = {'dn': member_dn, 'modtype': 'modify', 'attributes': ucs_object_attr}

					if not self._ignore_object('user', ucs_object) and not self._ignore_object('group', ucs_object):
						for k in self.property.keys():
							# identify if DN is a user or a group (will be ignored it is a host)
							if self.modules[k].identify(member_dn, ucs_object['attributes']):
								del_members[k].append(member_dn)
								break
				else:
					ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: %s was not found in UCS group member cache of %s, don't delete" % (member_dn_lower, object['dn'].lower()))

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: members to add: %s" % add_members)
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: members to del: %s" % del_members)

		if add_members['user'] or add_members['group'] or del_members['user'] or del_members['group'] or add_members['unknown']:
			ucs_admin_object = univention.admin.objects.get(self.modules[object_key], co='', lo=self.lo, position='', dn=object['dn'])
			ucs_admin_object.open()

			uniqueMember_add = add_members['user'] + add_members['group'] + add_members['unknown']
			uniqueMember_del = del_members['user'] + del_members['group']
			memberUid_add = []
			memberUid_del = []
			for member in add_members['user']:
				(_rdn_attribute, uid, _flags) = str2dn(unicode_to_utf8(member))[0][0]
				memberUid_add.append(unicode(uid, 'utf8'))
			for member in add_members['unknown']:  # user or group?
				ucs_object_attr = self.lo.get(member)
				uid = ucs_object_attr.get('uid')
				if uid:
					memberUid_add.append(uid[0])
			for member in del_members['user']:
				(_rdn_attribute, uid, _flags) = str2dn(unicode_to_utf8(member))[0][0]
				memberUid_del.append(unicode(uid, 'utf8'))
			if uniqueMember_del or memberUid_del:
				ucs_admin_object.fast_member_remove(uniqueMember_del, memberUid_del, ignore_license=1)
			if uniqueMember_add or memberUid_del:
				ucs_admin_object.fast_member_add(uniqueMember_add, memberUid_add)

	def disable_user_from_ucs(self, key, object):
		object_key = key

		object_ucs = self._object_mapping(object_key, object)
		ldap_object_s4 = self.get_object(object['dn'])

		try:
			ucs_admin_object = univention.admin.objects.get(self.modules[object_key], co='', lo=self.lo, position='', dn=object_ucs['dn'])
		except univention.admin.uexceptions.noObject as exc:
			ud.debug(ud.LDAP, ud.WARN, "Ignore already removed object %s." % (exc,))
			return
		ucs_admin_object.open()

		modlist = []

		ud.debug(ud.LDAP, ud.INFO, "Disabled state: %s" % ucs_admin_object['disabled'].lower())
		if not (ucs_admin_object['disabled'].lower() in ['none', '0']):
			# user disabled in UCS
			if 'userAccountControl' in ldap_object_s4 and (int(ldap_object_s4['userAccountControl'][0]) & 2) == 0:
				# user enabled in S4 -> change
				res = str(int(ldap_object_s4['userAccountControl'][0]) | 2)
				modlist.append((ldap.MOD_REPLACE, 'userAccountControl', [res]))
		else:
			# user enabled in UCS
			if 'userAccountControl' in ldap_object_s4 and (int(ldap_object_s4['userAccountControl'][0]) & 2) > 0:
				# user disabled in S4 -> change
				res = str(int(ldap_object_s4['userAccountControl'][0]) - 2)
				modlist.append((ldap.MOD_REPLACE, 'userAccountControl', [res]))

		# account expires
		# This value represents the number of 100 nanosecond intervals since January 1, 1601 (UTC). A value of 0 or 0x7FFFFFFFFFFFFFFF (9223372036854775807) indicates that the account never expires.
		if not ucs_admin_object['userexpiry']:
			# ucs account not expired
			if 'accountExpires' in ldap_object_s4 and (int(ldap_object_s4['accountExpires'][0]) != int(9223372036854775807) or ldap_object_s4['accountExpires'][0] == '0'):
				# s4 account expired -> change
				modlist.append((ldap.MOD_REPLACE, 'accountExpires', ['9223372036854775807']))
		else:
			# ucs account expired
			if 'accountExpires' in ldap_object_s4 and ldap_object_s4['accountExpires'][0] != unix2s4_time(ucs_admin_object['userexpiry']):
				# s4 account not expired -> change
				modlist.append((ldap.MOD_REPLACE, 'accountExpires', [str(unix2s4_time(ucs_admin_object['userexpiry']))]))

		if modlist:
			ud.debug(ud.LDAP, ud.ALL, "disable_user_from_ucs: modlist: %s" % modlist)
			self.lo_s4.lo.modify_s(compatible_modstring(object['dn']), compatible_modlist(modlist))

	def disable_user_to_ucs(self, key, object):
		object_key = key

		s4_object = self._object_mapping(object_key, object, 'ucs')

		ldap_object_s4 = self.get_object(s4_object['dn'])

		modified = 0
		ucs_admin_object = univention.admin.objects.get(self.modules[object_key], co='', lo=self.lo, position='', dn=object['dn'])
		ucs_admin_object.open()

		if 'userAccountControl' in ldap_object_s4 and (int(ldap_object_s4['userAccountControl'][0]) & 2) == 0:
			# user enabled in S4
			if not ucs_admin_object['disabled'].lower() in ['none', '0']:
				# user disabled in UCS -> change
				ucs_admin_object['disabled'] = '0'
				modified = 1
		else:
			# user disabled in S4
			if ucs_admin_object['disabled'].lower() in ['none', '0']:
				# user enabled in UCS -> change
				ucs_admin_object['disabled'] = '1'
				modified = 1
		if 'accountExpires' in ldap_object_s4 and (int(ldap_object_s4['accountExpires'][0]) == int(9223372036854775807) or ldap_object_s4['accountExpires'][0] == '0'):
			# s4 account not expired
			if ucs_admin_object['userexpiry']:
				# ucs account expired -> change
				ucs_admin_object['userexpiry'] = None
				modified = 1
		else:
			# s4 account expired
			ud.debug(ud.LDAP, ud.INFO, "sync account_expire:      s4time: %s    unixtime: %s" % (int(ldap_object_s4['accountExpires'][0]), ucs_admin_object['userexpiry']))

			if s42unix_time(int(ldap_object_s4['accountExpires'][0])) != ucs_admin_object['userexpiry']:
				# ucs account not expired -> change
				ucs_admin_object['userexpiry'] = s42unix_time(int(ldap_object_s4['accountExpires'][0]))
				modified = 1

		if modified:
			ucs_admin_object.modify()

	def initialize(self):
		_d = ud.function('ldap.initialize')  # noqa: F841
		print("--------------------------------------")
		print("Initialize sync from S4")
		if self._get_lastUSN() == 0:  # we startup new
			ud.debug(ud.LDAP, ud.PROCESS, "initialize S4: last USN is 0, sync all")
			# query highest USN in LDAP
			highestCommittedUSN = self.__get_highestCommittedUSN()

			# poll for all objects without deleted objects
			polled = self.poll(show_deleted=False)

			# compare highest USN from poll with highest before poll, if the last changes deletes
			# the highest USN from poll is to low
			self._set_lastUSN(max(highestCommittedUSN, self._get_lastUSN()))

			self._commit_lastUSN()
			ud.debug(ud.LDAP, ud.INFO, "initialize S4: sync of all objects finished, lastUSN is %d", self.__get_highestCommittedUSN())
		else:
			self.resync_rejected()
			polled = self.poll()
			self._commit_lastUSN()
		print("--------------------------------------")

	def resync_rejected(self):
		'''
		tries to resync rejected dn
		'''
		print("--------------------------------------")

		_d = ud.function('ldap.resync_rejected')  # noqa: F841
		change_count = 0
		rejected = self._list_rejected()
		print("Sync %s rejected changes from S4 to UCS" % len(rejected))
		sys.stdout.flush()
		for change_usn, dn in rejected:
			ud.debug(ud.LDAP, ud.PROCESS, 'sync to ucs: Resync rejected dn: %s' % (dn))
			try:
				sync_successfull = False
				elements = self.__search_s4_changeUSN(change_usn, show_deleted=True)
				if not elements or len(elements) < 1 or not elements[0][0]:
					ud.debug(ud.LDAP, ud.INFO, "rejected change with id %s not found, don't need to sync" % change_usn)
					self._remove_rejected(change_usn)
				elif len(elements) > 1 and not (elements[1][0] == 'None' or elements[1][0] is None):  # all except the first should be referrals
					ud.debug(ud.LDAP, ud.WARN, "more than one rejected object with id %s found, can't proceed" % change_usn)
				else:
					samba_object = self.__object_from_element(elements[0])
					property_key = self.__identify_s4_type(samba_object)
					mapped_object = self._object_mapping(property_key, samba_object)
					try:
						if not self._ignore_object(property_key, mapped_object) and not self._ignore_object(property_key, samba_object):
							sync_successfull = self.sync_to_ucs(property_key, mapped_object, dn, samba_object)
						else:
							sync_successfull = True
					except ldap.SERVER_DOWN:
						raise
					except Exception:  # FIXME: which exception is to be caught?
						self._debug_traceback(ud.ERROR, "sync of rejected object failed \n\t%s" % (samba_object['dn']))
						sync_successfull = False
					if sync_successfull:
						change_count += 1
						self._remove_rejected(change_usn)
						self.__update_lastUSN(samba_object)
						self._set_DN_for_GUID(elements[0][1]['objectGUID'][0], elements[0][0])
			except ldap.SERVER_DOWN:
				raise
			except Exception:
				self._debug_traceback(ud.ERROR, "unexpected Error during s4.resync_rejected")
		print("restored %s rejected changes" % change_count)
		print("--------------------------------------")
		sys.stdout.flush()

	def poll(self, show_deleted=True):
		'''
		poll for changes in S4
		'''
		_d = ud.function('s4.poll')  # noqa: F841
		# search from last_usn for changes
		change_count = 0
		changes = []
		try:
			changes = self.__search_s4_changes(show_deleted=show_deleted)
		except ldap.SERVER_DOWN:
			raise
		except Exception:  # FIXME: which exception is to be caught?
			self._debug_traceback(ud.WARN, "Exception during search_s4_changes")

		print("--------------------------------------")
		print("try to sync %s changes from S4" % len(changes))
		print("done:", end=' ')
		sys.stdout.flush()
		done_counter = 0
		samba_object = None
		lastUSN = self._get_lastUSN()
		newUSN = lastUSN

		# Check if the connection to UCS ldap exists. Otherwise re-create the session.
		try:
			self.search_ucs(scope=ldap.SCOPE_BASE)
		except ldap.SERVER_DOWN:
			ud.debug(ud.LDAP, ud.INFO, "UCS LDAP connection was closed, re-open the connection.")
			self.open_ucs()

		for element in changes:
			try:
				if element[0] == 'None':  # referrals
					continue
				old_element = copy.deepcopy(element)
				samba_object = self.__object_from_element(element)
			except Exception:  # FIXME: which exception is to be caught?
				# ud.debug(ud.LDAP, ud.ERROR, "Exception during poll/object-mapping, tried to map element: %s" % old_element[0])
				# ud.debug(ud.LDAP, ud.ERROR, "This object will not be synced again!")
				# debug-trace may lead to a segfault here :(
				self._debug_traceback(ud.ERROR, "Exception during poll/object-mapping, object will not be synced again!")

			if samba_object:
				property_key = self.__identify_s4_type(samba_object)
				if property_key:

					if self._ignore_object(property_key, samba_object):
						if samba_object['modtype'] == 'move':
							ud.debug(ud.LDAP, ud.INFO, "object_from_element: Detected a move of an S4 object into a ignored tree: dn: %s" % samba_object['dn'])
							samba_object['deleted_dn'] = samba_object['olddn']
							samba_object['dn'] = samba_object['olddn']
							samba_object['modtype'] = 'delete'
							# check the move target
						else:
							self.__update_lastUSN(samba_object)
							done_counter += 1
							print("%s" % done_counter, end=' ')
							continue

					if samba_object['dn'].find('\\0ACNF:') > 0:
						ud.debug(ud.LDAP, ud.PROCESS, 'Ignore conflicted object: %s' % samba_object['dn'])
						self.__update_lastUSN(samba_object)
						done_counter += 1
						print("%s" % done_counter, end=' ')
						continue

					sync_successfull = False
					try:
						mapped_object = self._object_mapping(property_key, samba_object)
						if not self._ignore_object(property_key, mapped_object):
							sync_successfull = self.sync_to_ucs(property_key, mapped_object, samba_object['dn'], samba_object)
						else:
							sync_successfull = True
					except ldap.SERVER_DOWN:
						ud.debug(ud.LDAP, ud.ERROR, "Got server down during sync, re-open the connection to UCS and S4")
						time.sleep(1)
						self.open_ucs()
						self.open_s4()
					except univention.admin.uexceptions.ldapError as msg:
						ud.debug(ud.LDAP, ud.INFO, "Exception during poll with message (1) %s" % msg)
						if msg == "Can't contact LDAP server":
							raise ldap.SERVER_DOWN
						else:
							self._debug_traceback(ud.WARN, "Exception during poll/sync_to_ucs")
					except Exception:  # FIXME: which exception is to be caught?
						self._debug_traceback(ud.WARN, "Exception during poll/sync_to_ucs")

					if not sync_successfull:
						ud.debug(ud.LDAP, ud.WARN, "sync to ucs was not successful, save rejected")
						ud.debug(ud.LDAP, ud.WARN, "object was: %s" % samba_object['dn'])

					if sync_successfull:
						change_count += 1
						newUSN = max(self.__get_change_usn(samba_object), newUSN)
						try:
							GUID = old_element[1]['objectGUID'][0]
							self._set_DN_for_GUID(GUID, old_element[0])
						except ldap.SERVER_DOWN:
							raise
						except Exception:  # FIXME: which exception is to be caught?
							self._debug_traceback(ud.WARN, "Exception during set_DN_for_GUID")

					else:
						self.save_rejected(samba_object)
						self.__update_lastUSN(samba_object)
				else:
					newUSN = max(self.__get_change_usn(samba_object), newUSN)

				done_counter += 1
				print("%s" % done_counter, end=' ')
			else:
				done_counter += 1
				print("(%s)" % done_counter, end=' ')
			sys.stdout.flush()

		print("")

		if newUSN != lastUSN:
			self._set_lastUSN(newUSN)
			self._commit_lastUSN()

		# return number of synced objects
		rejected = self._list_rejected()
		if rejected:
			print("Changes from S4:  %s (%s saved rejected)" % (change_count, len(rejected)))
		else:
			print("Changes from S4:  %s (%s saved rejected)" % (change_count, '0'))
		print("--------------------------------------")
		sys.stdout.flush()
		return change_count

	def __has_attribute_value_changed(self, attribute, old_ucs_object, new_ucs_object):
		return not old_ucs_object.get(attribute) == new_ucs_object.get(attribute)

	def _remove_dn_from_group_cache(self, con_dn=None, ucs_dn=None):
		if con_dn:
			try:
				ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: Removing %s from S4 group member mapping cache" % con_dn)
				del self.group_member_mapping_cache_con[con_dn.lower()]
			except KeyError:
				ud.debug(ud.LDAP, ud.ALL, "sync_from_ucs: %s was not present in S4 group member mapping cache" % con_dn)
				pass
		if ucs_dn:
			try:
				ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: Removing %s from UCS group member mapping cache" % ucs_dn)
				del self.group_member_mapping_cache_ucs[ucs_dn.lower()]
			except KeyError:
				ud.debug(ud.LDAP, ud.ALL, "sync_from_ucs: %s was not present in UCS group member mapping cache" % ucs_dn)
				pass

	def sync_from_ucs(self, property_type, object, pre_mapped_ucs_dn, old_dn=None, old_ucs_object=None, new_ucs_object=None):
		# NOTE: pre_mapped_ucs_dn means: original ucs_dn (i.e. before _object_mapping)
		_d = ud.function('ldap.__sync_from_ucs')  # noqa: F841
		# Diese Methode erhaelt von der UCS Klasse ein Objekt,
		# welches hier bearbeitet wird und in das S4 geschrieben wird.
		# object ist brereits vom eingelesenen UCS-Objekt nach S4 gemappt, old_dn ist die alte UCS-DN
		ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: sync object: %s" % object['dn'])

		# if sync is read (sync from S4) or none, there is nothing to do
		if self.property[property_type].sync_mode in ['read', 'none']:
			ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs ignored, sync_mode is %s" % self.property[property_type].sync_mode)
			return True

		# check for move, if old_object exists, set modtype move
		pre_mapped_ucs_old_dn = old_dn
		if old_dn:
			old_dn = object['olddn']
			# the old object was moved in UCS, but does this object exist in S4?
			try:
				old_object = self.s4_search_ext_s(compatible_modstring(old_dn), ldap.SCOPE_BASE, 'objectClass=*')
			except ldap.SERVER_DOWN:
				raise
			except Exception:
				old_object = None

			if old_object:
				ud.debug(ud.LDAP, ud.INFO, "move %s from [%s] to [%s]" % (property_type, old_dn, object['dn']))
				try:
					self.lo_s4.rename(unicode(old_dn), object['dn'])
				except ldap.NO_SUCH_OBJECT:  # check if object is already moved (we may resync now)
					new = encode_s4_resultlist(self.s4_search_ext_s(compatible_modstring(object['dn']), ldap.SCOPE_BASE, 'objectClass=*'))
					if not new:
						raise
				# need to actualise the GUID, group cache and DN-Mapping
				object['modtype'] = 'move'
				self._remove_dn_from_group_cache(con_dn=old_dn, ucs_dn=pre_mapped_ucs_old_dn)
				ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: Updating UCS and S4 group member mapping cache for %s to %s" % (pre_mapped_ucs_dn, object['dn']))
				self.group_member_mapping_cache_ucs[pre_mapped_ucs_dn.lower()] = object['dn']
				self.group_member_mapping_cache_con[object['dn'].lower()] = pre_mapped_ucs_dn

				self._set_DN_for_GUID(self.s4_search_ext_s(compatible_modstring(object['dn']), ldap.SCOPE_BASE, 'objectClass=*')[0][1]['objectGUID'][0], object['dn'])
				self._remove_dn_mapping(pre_mapped_ucs_old_dn, unicode(old_dn))
				self._check_dn_mapping(pre_mapped_ucs_dn, object['dn'])

		ud.debug(ud.LDAP, ud.PROCESS, 'sync from ucs: [%14s] [%10s] %s' % (property_type, object['modtype'], object['dn']))

		if 'olddn' in object:
			object.pop('olddn')  # not needed anymore, will fail object_mapping in later functions
		old_dn = None

		addlist = []
		modlist = []

		# get current object
		s4_object = self.get_object(object['dn'])
		if s4_object:
			guid_blob = s4_object.get('objectGUID')[0]
			objectGUID = str(ndr_unpack(misc.GUID, guid_blob))
			if self.lockingdb.is_s4_locked(objectGUID):
				ud.debug(ud.LDAP, ud.PROCESS, "Unable to sync %s (GUID: %s). The object is currently locked." % (object['dn'], objectGUID))
				return False

		entryUUID = object['attributes'].get('entryUUID', [None])[0]  # may be empty for back_mapped_subobject for leaf object delete_in_s4

		#
		# ADD
		#
		if not s4_object and object['modtype'] in ('add', 'modify', 'move'):
			ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: add object: %s" % object['dn'])

			ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: lock UCS entryUUID: %s" % entryUUID)
			if entryUUID and not self.lockingdb.is_ucs_locked(entryUUID):
				self.lockingdb.lock_ucs(entryUUID)

			self.addToCreationList(object['dn'])

			if hasattr(self.property[property_type], "con_sync_function"):
				self.property[property_type].con_sync_function(self, property_type, object)
			else:
				# objectClass
				if self.property[property_type].con_create_objectclass:
					addlist.append(('objectClass', self.property[property_type].con_create_objectclass))

				# fixed Attributes
				if self.property[property_type].con_create_attributes:
					addlist += self.property[property_type].con_create_attributes

				# Copy the LDAP controls, because they may be modified
				# in an ucs_create_extenstions
				ctrls = copy.deepcopy(self.serverctrls_for_add_and_modify)
				if hasattr(self.property[property_type], 'attributes') and self.property[property_type].attributes is not None:
					for attr, value in object['attributes'].items():
						for attribute in self.property[property_type].attributes.keys():
							if self.property[property_type].attributes[attribute].con_attribute == attr:
								addlist.append((attr, value))
							if self.property[property_type].attributes[attribute].con_other_attribute == attr:
								addlist.append((attr, value))
				if hasattr(self.property[property_type], 'con_create_extenstions') and self.property[property_type].con_create_extenstions is not None:
					for f in self.property[property_type].con_create_extenstions:
						f(self, property_type, object, addlist, ctrls)
				if hasattr(self.property[property_type], 'post_attributes') and self.property[property_type].post_attributes is not None:
					for attr, value in object['attributes'].items():
						for attribute in self.property[property_type].post_attributes.keys():
							if self.property[property_type].post_attributes[attribute].reverse_attribute_check:
								if not object['attributes'].get(self.property[property_type].post_attributes[attribute].ldap_attribute):
									continue
							if self.property[property_type].post_attributes[attribute].con_attribute == attr:
								if value:
									modlist.append((ldap.MOD_REPLACE, attr, value))
							if self.property[property_type].post_attributes[attribute].con_other_attribute == attr:
								if value:
									modlist.append((ldap.MOD_REPLACE, attr, value))

				ud.debug(ud.LDAP, ud.INFO, "to add: %s" % object['dn'])
				ud.debug(ud.LDAP, ud.ALL, "sync_from_ucs: addlist: %s" % addlist)
				try:
					self.lo_s4.lo.add_ext_s(compatible_modstring(object['dn']), compatible_addlist(addlist), serverctrls=ctrls)  # FIXME encoding
				except ldap.ALREADY_EXISTS:
					sAMAccountName = object['attributes'].get('sAMAccountName', [None])[0]
					sambaSID = object['attributes'].get('sambaSID', [None])[0]
					if not (sAMAccountName and sambaSID):
						raise  # unknown situation, raise original traceback
					filter_s4 = format_escaped(u'(&(sAMAccountName={0!e})(objectSid={1!e})(isDeleted=TRUE))', sAMAccountName, sambaSID)
					ud.debug(ud.LDAP, ud.PROCESS, "sync_from_ucs: error during add, searching for conflicting deleted object in S4")
					ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: search filter: %s" % filter_s4)
					result = self.s4_search_ext_s(self.lo_s4.base, ldap.SCOPE_SUBTREE, filter_s4, ['dn'], serverctrls=[LDAPControl(
						LDAP_SERVER_SHOW_DELETED_OID, criticality=1), LDAPControl(LDB_CONTROL_DOMAIN_SCOPE_OID, criticality=0)])
					if not result or len(result) > 1:  # the latter would indicate corruption
						ud.debug(ud.LDAP, ud.PROCESS, "sync_from_ucs: no conflicting deleted object found")
						raise  # unknown situation, raise original traceback
					ud.debug(ud.LDAP, ud.PROCESS, "sync_from_ucs: reanimating conflicting object: %s" % result[0][0])
					reanimate_modlist = [
						(ldap.MOD_DELETE, 'isDeleted', None),
						(ldap.MOD_REPLACE, 'distinguishedName', compatible_modstring(object['dn']))
					]
					self.lo_s4.lo.modify_ext_s(compatible_modstring(result[0][0]), reanimate_modlist, serverctrls=[LDAPControl(LDAP_SERVER_SHOW_DELETED_OID, criticality=1), ])
					# and try the sync again
					return self.sync_from_ucs(property_type, object, pre_mapped_ucs_dn, old_dn, old_ucs_object, new_ucs_object)
				except:
					ud.debug(ud.LDAP, ud.ERROR, "sync_from_ucs: traceback during add object: %s" % object['dn'])
					ud.debug(ud.LDAP, ud.ERROR, "sync_from_ucs: traceback due to addlist: %s" % addlist)
					raise

				if property_type == 'group':
					self.group_members_cache_con[object['dn'].lower()] = []
					ud.debug(ud.LDAP, ud.INFO, "group_members_cache_con[%s]: []" % (object['dn'].lower()))

				if hasattr(self.property[property_type], "post_con_create_functions"):
					for f in self.property[property_type].post_con_create_functions:
						f(self, property_type, object)

				ud.debug(ud.LDAP, ud.INFO, "and modify: %s" % object['dn'])
				if modlist:
					ud.debug(ud.LDAP, ud.ALL, "sync_from_ucs: modlist: %s" % modlist)
					try:
						self.lo_s4.lo.modify_ext_s(compatible_modstring(object['dn']), compatible_modlist(modlist), serverctrls=ctrls)
					except:
						ud.debug(ud.LDAP, ud.ERROR, "sync_from_ucs: traceback during modify object: %s" % object['dn'])
						ud.debug(ud.LDAP, ud.ERROR, "sync_from_ucs: traceback due to modlist: %s" % modlist)
						raise

				if hasattr(self.property[property_type], "post_con_modify_functions"):
					for f in self.property[property_type].post_con_modify_functions:
						ud.debug(ud.LDAP, ud.INFO, "Call post_con_modify_functions: %s" % f)
						f(self, property_type, object)
						ud.debug(ud.LDAP, ud.INFO, "Call post_con_modify_functions: %s (done)" % f)

		#
		# MODIFY
		#
		elif s4_object and object['modtype'] in ('add', 'modify', 'move'):
			ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: modify object: %s" % object['dn'])
			ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: old_object: %s" % old_ucs_object)
			ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: new_object: %s" % new_ucs_object)
			object['old_ucs_object'] = old_ucs_object
			object['new_ucs_object'] = new_ucs_object
			attribute_list = set(old_ucs_object.keys()).union(set(new_ucs_object.keys()))
			if hasattr(self.property[property_type], "con_sync_function"):
				self.property[property_type].con_sync_function(self, property_type, object)
			else:
				# Iterate over attributes and post_attributes
				for attribute_type_name, attribute_type in [('attributes', self.property[property_type].attributes), ('post_attributes', self.property[property_type].post_attributes)]:
					if hasattr(self.property[property_type], attribute_type_name) and attribute_type is not None:
						for attr in attribute_list:
							value = new_ucs_object.get(attr)
							if not self.__has_attribute_value_changed(attr, old_ucs_object, new_ucs_object):
								continue

							ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: The following attribute has been changed: %s" % attr)

							for attribute in attribute_type.keys():
								if attribute_type[attribute].ldap_attribute != attr:
									continue

								ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: Found a corresponding mapping definition: %s" % attribute)
								s4_attribute = attribute_type[attribute].con_attribute
								s4_other_attribute = attribute_type[attribute].con_other_attribute

								if not attribute_type[attribute].sync_mode in ['write', 'sync']:
									ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: %s is in not in write or sync mode. Skipping" % attribute)
									continue

								# Get the UCS attributes
								old_values = set(old_ucs_object.get(attr, []))
								new_values = set(new_ucs_object.get(attr, []))

								ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: old_values: %s" % old_values)
								ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: new_values: %s" % new_values)

								if attribute_type[attribute].compare_function(list(old_values), list(new_values)):
									ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: no modification necessary for %s" % attribute)
									continue

								# So, at this point we have the old and the new UCS object.
								# Thus we can create the diff, but we have to check the current S4 object

								if not old_values:
									to_add = new_values
									to_remove = set([])
								elif not new_values:
									to_remove = old_values
									to_add = set([])
								else:
									to_add = new_values - old_values
									to_remove = old_values - new_values

								if s4_other_attribute:
									# This is the case, where we map from a multi-valued UCS attribute to two S4 attributes.
									# telephoneNumber/otherTelephone (S4) to telephoneNumber (UCS) would be an example.
									#
									# The direct mapping assumes preserved ordering of the multi-valued UCS
									# attributes and places the first value in the primary S4 attribute,
									# the rest in the secondary S4 attributes.
									# Assuming preserved ordering is wrong, as LDAP does not guarantee is and the
									# deduplication of LDAP attribute values in `__set_values()` destroys it.
									#
									# The following code handles the correct distribution of the UCS attribute,
									# to two S4 attributes. It also ensures, that the primary S4 attribute keeps
									# its value as long as that value is not removed. If removed the primary
									# attribute is assigned a random value from the UCS attribute.
									try:
										current_s4_values = set([v for k, v in s4_object.iteritems() if s4_attribute.lower() == k.lower()][0])
									except IndexError:
										current_s4_values = set([])
									ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: The current S4 values: %s" % current_s4_values)

									try:
										current_s4_other_values = set([v for k, v in s4_object.iteritems() if s4_other_attribute.lower() == k.lower()][0])
									except IndexError:
										current_s4_other_values = set([])
									ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: The current S4 other values: %s" % current_s4_other_values)

									new_s4_values = current_s4_values - to_remove
									if not new_s4_values and to_add:
										for n_value in new_ucs_object.get(attr, []):
											if n_value in to_add:
												to_add = to_add - set([n_value])
												new_s4_values = [n_value]
												break

									new_s4_other_values = (current_s4_other_values | to_add) - to_remove - current_s4_values
									if current_s4_values != new_s4_values:
										if new_s4_values:
											modlist.append((ldap.MOD_REPLACE, s4_attribute, new_s4_values))
										else:
											modlist.append((ldap.MOD_REPLACE, s4_attribute, []))

									if current_s4_other_values != new_s4_other_values:
										modlist.append((ldap.MOD_REPLACE, s4_other_attribute, new_s4_other_values))
								else:
									try:
										current_s4_values = set([v for k, v in s4_object.iteritems() if s4_attribute.lower() == k.lower()][0])
									except IndexError:
										current_s4_values = set([])

									ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: The current S4 values: %s" % current_s4_values)

									has_mapping_function = hasattr(attribute_type[attribute], 'mapping') and len(attribute_type[attribute].mapping) > 0 and attribute_type[attribute].mapping[0]

									if (to_add or to_remove) and (attribute_type[attribute].single_value or has_mapping_function):
										modified = (not current_s4_values or not value) or \
											not attribute_type[attribute].compare_function(list(current_s4_values), list(value))
										if modified:
											if has_mapping_function:
												ud.debug(ud.LDAP, ud.PROCESS, "Calling value mapping function for attribute %s" % attribute)
												value = attribute_type[attribute].mapping[0](self, None, object)
											modlist.append((ldap.MOD_REPLACE, s4_attribute, value))
									else:
										if to_remove:
											r = current_s4_values & to_remove
											if r:
												modlist.append((ldap.MOD_DELETE, s4_attribute, r))
										if to_add:
											a = to_add - current_s4_values
											if a:
												modlist.append((ldap.MOD_ADD, s4_attribute, a))

				if not modlist:
					ud.debug(ud.LDAP, ud.ALL, "nothing to modify: %s" % object['dn'])
				else:
					ud.debug(ud.LDAP, ud.INFO, "to modify: %s" % object['dn'])
					ud.debug(ud.LDAP, ud.ALL, "sync_from_ucs: modlist: %s" % modlist)
					try:
						self.lo_s4.lo.modify_ext_s(compatible_modstring(object['dn']), compatible_modlist(modlist), serverctrls=self.serverctrls_for_add_and_modify)
					except:
						ud.debug(ud.LDAP, ud.ERROR, "sync_from_ucs: traceback during modify object: %s" % object['dn'])
						ud.debug(ud.LDAP, ud.ERROR, "sync_from_ucs: traceback due to modlist: %s" % modlist)
						raise

				if hasattr(self.property[property_type], "post_con_modify_functions"):
					for f in self.property[property_type].post_con_modify_functions:
						ud.debug(ud.LDAP, ud.INFO, "Call post_con_modify_functions: %s" % f)
						f(self, property_type, object)
						ud.debug(ud.LDAP, ud.INFO, "Call post_con_modify_functions: %s (done)" % f)
		#
		# DELETE
		#
		elif object['modtype'] == 'delete':
			if hasattr(self.property[property_type], "con_sync_function"):
				self.property[property_type].con_sync_function(self, property_type, object)
			else:
				self.delete_in_s4(object, property_type)
			# update group cache
			self._remove_dn_from_group_cache(con_dn=object['dn'], ucs_dn=pre_mapped_ucs_dn)
		else:
			ud.debug(ud.LDAP, ud.WARN, "unknown modtype (%s : %s)" % (object['dn'], object['modtype']))
			return False

		ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: unlock UCS entryUUID: %s" % entryUUID)
		if entryUUID:
			self.lockingdb.unlock_ucs(entryUUID)

		self._check_dn_mapping(pre_mapped_ucs_dn, object['dn'])

		ud.debug(ud.LDAP, ud.ALL, "sync from ucs return True")
		return True  # FIXME: return correct False if sync fails

	def _get_objectGUID(self, dn):
		objectGUID = ''
		try:
			s4_object = self.get_object(dn)
			objectGUID = s4_object.get('objectGUID')[0]
		except Exception:
			ud.debug(ud.LDAP, ud.WARN, "Failed to search objectGUID for %s" % dn)
		return objectGUID

	def delete_in_s4(self, object, property_type):
		_d = ud.function('ldap.delete_in_s4')  # noqa: F841
		ud.debug(ud.LDAP, ud.ALL, "delete: %s" % object['dn'])
		ud.debug(ud.LDAP, ud.ALL, "delete_in_s4: %s" % object)
		try:
			objectGUID = self._get_objectGUID(object['dn'])
			self.lo_s4.lo.delete_s(compatible_modstring(object['dn']))
		except ldap.NO_SUCH_OBJECT:
			pass  # object already deleted
		except ldap.NOT_ALLOWED_ON_NONLEAF:
			ud.debug(ud.LDAP, ud.INFO, "remove object from S4 failed, need to delete subtree")
			if self._remove_subtree_in_s4(object, property_type):
				# FIXME: endless recursion if there is one subtree-object which is ignored, not identifyable or can't be removed.
				return self.delete_in_s4(object, property_type)
			return False

		entryUUID = object.get('attributes').get('entryUUID', [None])[0]
		if entryUUID:
			self.update_deleted_cache_after_removal(entryUUID, objectGUID)
		else:
			ud.debug(ud.LDAP, ud.INFO, "delete_in_s4: Object without entryUUID: %s" % (object['dn'],))

	def _remove_subtree_in_s4(self, parent_s4_object, property_type):
		if self.property[property_type].con_subtree_delete_objects:
			_l = ["(%s)" % x for x in self.property[property_type].con_subtree_delete_objects]
			allow_delete_filter = "(|%s)" % ''.join(_l)
			for sub_dn, _ in self.s4_search_ext_s(compatible_modstring(parent_s4_object['dn']), ldap.SCOPE_SUBTREE, allow_delete_filter):
				if self.lo.compare_dn(unicode(sub_dn).lower(), unicode(parent_s4_object['dn']).lower()):  # FIXME: remove and search with scope=children instead
					continue
				ud.debug(ud.LDAP, ud.INFO, "delete: %r" % (sub_dn,))
				self.lo_s4.lo.delete_s(compatible_modstring(sub_dn))

		for subdn, subattr in self.s4_search_ext_s(compatible_modstring(parent_s4_object['dn']), ldap.SCOPE_SUBTREE, 'objectClass=*'):
			if self.lo.compare_dn(unicode(subdn).lower(), unicode(parent_s4_object['dn']).lower()):  # FIXME: remove and search with scope=children instead
				continue
			ud.debug(ud.LDAP, ud.INFO, "delete: %r" % (subdn,))

			subobject_s4 = {'dn': subdn, 'modtype': 'delete', 'attributes': subattr}
			key = self.__identify_s4_type(subobject_s4)
			back_mapped_subobject = self._object_mapping(key, subobject_s4)
			ud.debug(ud.LDAP, ud.WARN, "delete subobject: %r" % (back_mapped_subobject['dn'],))

			if not self._ignore_object(key, back_mapped_subobject):
				# FIXME: this call is wrong!: sync_from_ucs() must be called with a ucs_object not with a samba_object!
				if not self.sync_from_ucs(key, subobject_s4, back_mapped_subobject['dn']):
					ud.debug(ud.LDAP, ud.WARN, "delete of subobject failed: %r" % (subdn,))
					return False

		return True
