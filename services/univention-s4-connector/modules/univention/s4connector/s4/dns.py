#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  dns helper functions
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

from __future__ import absolute_import
import ldap
import univention.debug2 as ud
import univention.s4connector.s4
import univention.admin.uldap
from univention.s4connector.s4.dc import _unixTimeInverval2seconds
from univention.s4connector.s4 import compatible_modstring, unicode_to_utf8
from univention.s4connector.s4 import format_escaped, str2dn
from univention.admin.mapping import unmapUNIX_TimeInterval

from samba.dcerpc import dnsp
from samba.ndr import ndr_pack, ndr_unpack
import copy
import time
import sys

from dns.rdtypes.ANY.TXT import TXT
from dns import rdatatype
from dns import rdataclass
from dns.tokenizer import Tokenizer

from samba.provision.sambadns import ARecord
# def __init__(self, ip_addr, serial=1, ttl=900, rank=dnsp.DNS_RANK_ZONE):

from samba.provision.sambadns import AAAARecord
# def __init__(self, ip6_addr, serial=1, ttl=900, rank=dnsp.DNS_RANK_ZONE):

from samba.provision.sambadns import NSRecord
# def __init__(self, dns_server, serial=1, ttl=900, rank=dnsp.DNS_RANK_ZONE):

from samba.provision.sambadns import SOARecord
# def __init__(self, mname, rname, serial=1, refresh=900, retry=600, expire=86400, minimum=3600, ttl=3600, rank=dnsp.DNS_RANK_ZONE):

from samba.provision.sambadns import SRVRecord
# def __init__(self, target, port, priority=0, weight=100, serial=1, ttl=900, rank=dnsp.DNS_RANK_ZONE):

from samba.provision.sambadns import CNameRecord
# def __init__(self, cname, serial=1, ttl=900, rank=dnsp.DNS_RANK_ZONE):

from samba.provision.sambadns import TXTRecord
# def __init__(self, slist, serial=1, ttl=900, rank=dnsp.DNS_RANK_ZONE):

import univention.admin.handlers
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.alias
import univention.admin.handlers.dns.host_record
import univention.admin.handlers.dns.srv_record
import univention.admin.handlers.dns.reverse_zone
import univention.admin.handlers.dns.ptr_record


class PTRRecord(dnsp.DnssrvRpcRecord):

	def __init__(self, ptr, serial=1, ttl=900, rank=dnsp.DNS_RANK_ZONE):
		super(PTRRecord, self).__init__()
		self.wType = dnsp.DNS_TYPE_PTR
		self.rank = rank
		self.dwSerial = serial
		self.dwTtlSeconds = ttl
		self.data = ptr


class MXRecord(dnsp.DnssrvRpcRecord):

	def __init__(self, name, priority, serial=1, ttl=900, rank=dnsp.DNS_RANK_ZONE):
		super(MXRecord, self).__init__()
		self.wType = dnsp.DNS_TYPE_MX
		self.rank = rank
		self.dwSerial = serial
		self.dwTtlSeconds = ttl
		self.data.wPriority = priority
		self.data.nameTarget = name

# mapping functions


def dns_dn_mapping(s4connector, given_object, dn_mapping_stored, isUCSobject):
	'''
	map dn of given object (which must have an s4_RR_attr in S4)
	ol_oc_filter and s4_RR_filter are objectclass filters in UCS and S4

	Code is based on univention.s4connector.s4.samaccountname_dn_mapping
	'''
	obj = copy.deepcopy(given_object)

	propertyname = 'dns'
	propertyattrib = u'relativeDomainName'  # using LDAP name here, for simplicity
	ol_oc_filter = '(objectClass=dNSZone)'  # all OpenLDAP DNS records match
	ol_RR_attr = 'relativeDomainName'
	s4_RR_filter = u'(objectClass=dnsNode)'  # This also matches the DC=@ SOA object
	s4_RR_attr = 'dc'  # Note: the S4 attribute itself is lowercase

	if obj['dn'] is not None:
		try:
			s4_RR_val = [_value for _key, _value in obj['attributes'].iteritems() if s4_RR_attr.lower() == _key.lower()][0][0]
		except (KeyError, IndexError):
			s4_RR_val = ''

	def dn_premapped(given_object, dn_key, dn_mapping_stored):
		if (dn_key not in dn_mapping_stored) or (not given_object[dn_key]):
			ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: not premapped (in first instance)")
			return False
		else:  # check if DN exists
			if isUCSobject:
				premapped_dn = s4connector.get_object_dn(given_object[dn_key])
				if premapped_dn is not None:
					# ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: premapped S4 object found")
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: premapped S4 object: %s" % premapped_dn)
					return True
				else:
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: premapped S4 object not found")
					return False
			else:
				premapped_dn = s4connector.get_ucs_ldap_object_dn(given_object[dn_key])
				if premapped_dn is not None:
					# ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: premapped UCS object found")
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: premapped UCS object: %s" % premapped_dn)
					return True
				else:
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: premapped UCS object not found")
					return False

	for dn_key in ['dn', 'olddn']:
		ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: check newdn for key '%s'" % dn_key)
		if dn_key in obj and not dn_premapped(obj, dn_key, dn_mapping_stored):

			dn = obj[dn_key]
			ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: dn: %s" % dn)

			# Skip Configuration objects with empty DNs
			if dn is None:
				break

			exploded_dn = str2dn(unicode_to_utf8(dn))
			(fst_rdn_attribute_utf8, fst_rdn_value_utf8, _flags) = exploded_dn[0][0]

			if isUCSobject:
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: got an UCS-Object")
				# lookup the relativeDomainName as DC/dnsNode in S4 to get corresponding DN, if not found create new

				# Case move with rename
				if dn_key == 'olddn' and fst_rdn_attribute_utf8 == 'relativeDomainName':
					relativeDomainName = fst_rdn_value_utf8
				else:
					try:
						relativeDomainName = obj['attributes'][ol_RR_attr][0]
					except (KeyError, IndexError):
						# Safety fallback for the unexpected case, where relativeDomainName would not be set
						if 'zoneName' == fst_rdn_attribute_utf8:
							relativeDomainName = '@'
						else:
							raise  # can't determine relativeDomainName

				if s4connector.property[propertyname].mapping_table and propertyattrib in s4connector.property[propertyname].mapping_table.keys():
					for ucsval, conval in s4connector.property[propertyname].mapping_table[propertyattrib]:
						try:
							if relativeDomainName.lower() == ucsval.lower():
								relativeDomainName = conval
								ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: map relativeDomainName according to mapping-table")
								continue
						except UnicodeDecodeError:
							pass  # values are not the same codec

				try:
					ol_zone_name = obj['attributes']['zoneName'][0]
				except (KeyError, IndexError):
					# Safety fallback for the unexpected case, where zoneName would not be set
					if ol_RR_attr == fst_rdn_attribute_utf8:
						(snd_rdn_attribute_utf8, snd_rdn_value_utf8, _flags) = exploded_dn[1][0]
						if 'zoneName' == snd_rdn_attribute_utf8:
							ol_zone_name = snd_rdn_value_utf8
						else:
							raise  # can't determine zoneName for this relativeDomainName

				target_RR_val = relativeDomainName
				target_zone_name = ol_zone_name
				s4dn_utf16_le = None
				s4_zone_dn = None
				if '@' == relativeDomainName:  # or dn starts with 'zoneName='
					s4_filter = format_escaped('(&(objectClass=dnsZone)({0}={1!e}))', s4_RR_attr, compatible_modstring(ol_zone_name))
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: search in S4")
					for base in s4connector.s4_ldap_partitions:
						result = s4connector._s4__search_s4(
							base,
							ldap.SCOPE_SUBTREE,
							s4_filter,
							attrlist=(s4_RR_attr,),
							show_deleted=False)

						if result:
							# We only need the SOA dn here
							s4dn_utf16_le_rdn = [('DC', '@', ldap.AVA_STRING)]
							s4dn_utf16_le = unicode(ldap.dn.dn2str([s4dn_utf16_le_rdn] + str2dn(unicode_to_utf8(result[0][0]))), 'utf8')
							break
				else:
					# identify position by parent zone name
					target_zone_dn = s4connector.lo.parentDn(dn)
					if s4connector.configRegistry.get('connector/s4/mapping/dns/position') != 'legacy':
						if relativeDomainName.endswith('._msdcs'):
							target_zone_name = '_msdcs.' + ol_zone_name
							target_RR_val = relativeDomainName[:-7]
							target_zone_rdn = [(s4_RR_attr.upper(), unicode_to_utf8(target_zone_name), ldap.AVA_STRING)]
							target_zone_dn = unicode(ldap.dn.dn2str([target_zone_rdn] + exploded_dn[2:]), 'utf8')

					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: get dns_dn_mapping for target zone %s" % target_zone_dn)
					fake_ol_zone_object = {
						'dn': target_zone_dn,
						'attributes': {
							'objectClass': ['top', 'dNSZone'],
							'relativeDomainName': ['@'],
							'zoneName': [target_zone_name],
						},
					}
					s4_soa_object = dns_dn_mapping(s4connector, fake_ol_zone_object, dn_mapping_stored, isUCSobject)
					# and use its parent as the search base
					if s4_soa_object['dn'].startswith('DC=@,'):
						s4_zone_dn = s4connector.lo_s4.parentDn(s4_soa_object['dn'])
					else:
						# There is the corner case, where con2ucsc
						# syncs the objectClass=dnsZone container and
						# stores it's DN in the premapping.
						# After that, we don't get the DC=@ dnsNode
						# object DN here, but directly the parent.
						# So, actually it's not the SOA object DN:
						s4_zone_dn = s4_soa_object['dn']

					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: search in S4 base %s" % (s4_zone_dn,))
					s4_filter = format_escaped('(&{0}({1}={2!e}))', s4_RR_filter, s4_RR_attr, compatible_modstring(target_RR_val))
					result = s4connector._s4__search_s4(
						s4_zone_dn,
						ldap.SCOPE_SUBTREE,
						s4_filter,
						attrlist=('dn',),
						show_deleted=False)
					if result:
						s4dn_utf16_le = result[0][0]

				if s4dn_utf16_le:  # no referral, so we've got a valid result
					s4dn = univention.s4connector.s4.encode_attrib(s4dn_utf16_le)
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: got s4dn %s" % (s4dn,))
					if dn_key == 'olddn' or (dn_key == 'dn' and 'olddn' not in obj):
						# Cases: ("delete") or ("add" but exists already)
						newdn = s4dn
					else:
						# Case: "moved" (?)
						exploded_s4_dn = str2dn(unicode_to_utf8(s4dn))
						raw_new_dn = unicode(ldap.dn.dn2str([exploded_s4_dn[0]] + exploded_dn[1:]), 'utf8')
						# The next line looks wrong to me: the source DN is a UCS dn here..
						# But this is just like samaccountname_dn_mapping does it:
						newdn = raw_new_dn.lower().replace(s4connector.lo_s4.base.lower(), s4connector.lo.base.lower())
						ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: move case newdn=%s" % newdn)
				else:
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: target object not found")
					if s4_zone_dn:
						# At least we found the zone
						zone_dn = s4_zone_dn
						relativeDomainName = target_RR_val
					else:
						# Ok, it's a new object without existing parent zone in S4 (probably this object itself is a soa/zone), so propose an S4 DN for it:
						default_dn = s4connector.property['dns'].con_default_dn
						zone_rdn = [('DC', unicode_to_utf8(ol_zone_name), ldap.AVA_STRING)]
						zone_dn = unicode(ldap.dn.dn2str([zone_rdn] + str2dn(default_dn)), 'utf8')

					new_rdn = [('DC', unicode_to_utf8(relativeDomainName), ldap.AVA_STRING)]
					newdn = unicode(ldap.dn.dn2str([new_rdn] + str2dn(unicode_to_utf8(zone_dn))), 'utf8')

			else:
				# get the object to read the s4_RR_attr in S4 and use it as name
				# we have no fallback here, the given dn must be found in S4 or we've got an error
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: got an S4-Object")
				i = 0

				while (not s4_RR_val):  # in case of olddn this is already set
					i = i + 1
					search_base_dn = compatible_modstring(obj.get('deleted_dn', dn))
					try:
						search_result = s4connector.lo_s4.search(filter=s4_RR_filter, base=search_base_dn, scope='base', attr=[s4_RR_attr], required=True)
					except ldap.NO_SUCH_OBJECT:  # S4 may need time
						if i > 5:
							raise
						time.sleep(1)  # S4 may need some time...
					else:
						(_search_result_dn, search_result_attributes) = search_result[0]
						search_result_attributes = dict((k.lower(), v) for k, v in search_result_attributes)
						raw_s4_rr_val = search_result_attributes[s4_RR_attr.lower()][0]
						s4_RR_val = univention.s4connector.s4.encode_attrib(raw_s4_rr_val)
						ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: got %s from S4" % s4_RR_attr)

				if s4connector.property[propertyname].mapping_table and propertyattrib in s4connector.property[propertyname].mapping_table.keys():
					for ucsval, conval in s4connector.property[propertyname].mapping_table[propertyattrib]:
						if s4_RR_val.lower() == conval.lower():
							s4_RR_val = ucsval
							ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: map %s according to mapping-table" % s4_RR_attr)
							continue
						else:
							ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: %s not in mapping-table" % s4_RR_attr)

				# search for object with this dn in ucs, needed if it is located in a different container
				try:
					s4_ocs = obj['attributes']['objectClass']
				except (KeyError, TypeError):
					s4_ocs = []

				target_RR_val = s4_RR_val
				ol_zone_dn = None
				if 'dnsZone' in s4_ocs:
					if s4connector.configRegistry.get('connector/s4/mapping/dns/position') != 'legacy':
						if s4_RR_val.startswith('_msdcs.'):
							target_RR_val = s4_RR_val[7:]
					target_zone_name = target_RR_val
					base = s4connector.lo.base
					ol_search_attr = 'zoneName'
					# could use a specific LDAP filter here, but not necessary:
					# ol_oc_filter = '(&(objectClass=dNSZone)(|(univentionObjectType=dns/forward_zone)(univentionObjectType=dns/reverse_zone)))'
				elif 'dnsNode' in s4_ocs:
					# identify position of the parent zone
					(snd_rdn_attribute_utf8, snd_rdn_value_utf8, _flags) = exploded_dn[1][0]

					target_zone_name = snd_rdn_value_utf8
					target_zone_dn = s4connector.lo_s4.parentDn(dn)
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: get dns_dn_mapping for %s" % target_zone_dn)
					if s4connector.configRegistry.get('connector/s4/mapping/dns/position') != 'legacy':
						if target_zone_name.startswith('_msdcs.'):
							target_zone_name = target_zone_name[7:]
							target_RR_val += '._msdcs'
							target_zone_rdn = [(snd_rdn_attribute_utf8, target_zone_name, ldap.AVA_STRING)]
							target_zone_dn = unicode(ldap.dn.dn2str([target_zone_rdn] + exploded_dn[2:]), 'utf8')

					fake_s4_zone_object = {
						'dn': target_zone_dn,
						'attributes': {
							'objectClass': ['top', 'dnsZone'],
							'dc': [target_zone_name],
						},
					}
					ol_zone_object = dns_dn_mapping(s4connector, fake_s4_zone_object, dn_mapping_stored, isUCSobject)
					# and use that as the search base
					ol_zone_dn = ol_zone_object['dn']
					base = ol_zone_dn
					ol_search_attr = ol_RR_attr
					# could use a specific LDAP filter here, but not necessary:
					# ol_oc_filter = '(&(objectClass=dNSZone)(!(|(univentionObjectType=dns/forward_zone)(univentionObjectType=dns/reverse_zone))))'

				s4_filter = format_escaped('(&{0}({1}={2!e}))', ol_oc_filter, ol_search_attr, target_RR_val)
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: UCS filter: %s" % s4_filter)
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: UCS base: %s" % (base,))
				try:
					ucsdn_result = s4connector.search_ucs(filter=s4_filter, base=base, scope='sub', attr=('dn',))
				except univention.admin.uexceptions.noObject:
					ucsdn_result = None

				try:
					ucsdn = ucsdn_result[0][0]
				except (IndexError, TypeError):
					ucsdn = None

				ud.debug(ud.LDAP, ud.ALL, "dns_dn_mapping: Found ucsdn: %s" % ucsdn)
				if ucsdn and (dn_key == 'olddn' or (dn_key == 'dn' and 'olddn' not in obj)):
					# Cases: ("delete") or ("add" but exists already)
					newdn = ucsdn
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: newdn is ucsdn")
				else:
					# Cases: (Target not found) or/and ("moved" (?))
					# Ok, it's a new object, so propose a S4 DN for it:
					if ol_zone_dn:
						# At least we found the zone
						zone_dn = ol_zone_dn
						s4_RR_val = target_RR_val
					else:
						# Fallback, e.g. for new zones
						zone_dn = __get_zone_dn(s4connector, target_zone_name)
					if '@' == s4_RR_val:
						newdn = zone_dn
					elif 'dnsZone' in s4_ocs:
						# Hmm, is it ok to map it to the same as '@'?
						newdn = zone_dn
					else:
						new_rdn = [('relativeDomainName', unicode_to_utf8(s4_RR_val), ldap.AVA_STRING)]
						newdn = unicode(ldap.dn.dn2str([new_rdn] + str2dn(unicode_to_utf8(zone_dn))), 'utf8')

					if not (dn_key == 'olddn' or (dn_key == 'dn' and 'olddn' not in obj)):
						# Case: "moved" (?)
						ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: move case newdn=%s" % newdn)

			try:
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: mapping for key '%s':" % dn_key)
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: source DN: %s" % dn)
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: mapped DN: %s" % newdn)
			except:  # FIXME: which exception is to be caught?
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: dn-print failed")

			obj[dn_key] = newdn

	return obj


''' HELPER functions '''


def __get_zone_dn(s4connector, zone_name):
	default_dn = s4connector.property['dns'].ucs_default_dn
	zone_rdn = [('zoneName', unicode_to_utf8(zone_name), ldap.AVA_STRING)]
	return unicode(ldap.dn.dn2str([zone_rdn] + str2dn(unicode_to_utf8(default_dn))), 'utf8')


def __append_dot(str):
	if str[-1] != '.':
		str += '.'
	return str


def __remove_dot(str):
	if str[-1] == '.':
		return str[:-1]
	else:
		return str


def __split_s4_dnsNode_dn(dn):
	exploded_dn = str2dn(dn)  # TODO: fix encoding

	# split the DC= from the zoneName
	(_, zoneName, _) = exploded_dn[1][0]
	(_, relativeDomainName, _) = exploded_dn[0][0]
	return (zoneName, relativeDomainName)


def __split_ol_dNSZone_dn(dn, objectclasses):
	exploded_dn = str2dn(dn)  # TODO: fix encoding
	(fst_rdn_attribute_utf8, fst_rdn_value_utf8, _flags) = exploded_dn[0][0]
	(snd_rdn_attribute_utf8, snd_rdn_value_utf8, _flags) = exploded_dn[1][0]

	if fst_rdn_attribute_utf8.lower() == 'zonename':
		zoneName = fst_rdn_value_utf8
		if 'dnsNode' in objectclasses:
			relativeDomainName = '@'
		elif 'dnsZone' in objectclasses:
			# make S4 dnsZone containers distinguishable from SOA records
			relativeDomainName = zoneName
		else:
			relativeDomainName = None
	elif snd_rdn_attribute_utf8.lower() == 'zonename':
		zoneName = snd_rdn_value_utf8
		relativeDomainName = fst_rdn_value_utf8
	else:
		zoneName = None
		relativeDomainName = None
		ud.debug(ud.LDAP, ud.WARN, 'Failed to get zone name for object %s' % (object['dn']))
	return (zoneName, relativeDomainName)


def __create_s4_forward_zone(s4connector, zone_dn):
	al = []
	al.append(('objectClass', ['top', 'dnsZone']))

	ud.debug(ud.LDAP, ud.INFO, '_dns_zone_forward_con_create: dn: %s' % zone_dn)
	ud.debug(ud.LDAP, ud.INFO, '_dns_zone_forward_con_create: al: %s' % al)
	s4connector.lo_s4.lo.add_s(zone_dn, al)


def __create_s4_forward_zone_soa(s4connector, soa_dn):
	al = []
	al.append(('objectClass', ['top', 'dnsNode']))
	al.append(('dc', ['@']))

	s4connector.lo_s4.lo.add_s(soa_dn, al)


def __create_s4_dns_node(s4connector, dnsNodeDn, relativeDomainNames, dnsRecords):
	al = []

	al.append(('objectClass', ['top', 'dnsNode']))
	al.append(('dc', relativeDomainNames))
	if dnsRecords:
		al.append(('dnsRecord', dnsRecords))

	ud.debug(ud.LDAP, ud.INFO, '__create_s4_dns_node: dn: %s' % dnsNodeDn)
	ud.debug(ud.LDAP, ud.INFO, '__create_s4_dns_node: al: %s' % al)
	s4connector.lo_s4.lo.add_s(dnsNodeDn, al)


''' Pack and unpack DNS records by using the
	Samba NDR functions
'''


def __pack_aRecord(object, dnsRecords):
	# add aRecords

	# IPv4
	for a in object['attributes'].get('aRecord', []):
		a = compatible_modstring(a)
		a_record = ARecord(a)
		dnsRecords.append(ndr_pack(a_record))

	# IPv6
	for a in object['attributes'].get('aAAARecord', []):
		a = compatible_modstring(a)
		a_record = AAAARecord(a)
		dnsRecords.append(ndr_pack(a_record))


def __unpack_aRecord(object):
	a = []
	dnsRecords = object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		ndrRecord = ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_A or ndrRecord.wType == dnsp.DNS_TYPE_AAAA:
			a.append(ndrRecord.data)
	return a


def __pack_soaRecord(object, dnsRecords):
	soaRecord = object['attributes'].get('sOARecord', [None])[0]
	if soaRecord:
		soaRecord = compatible_modstring(soaRecord)
		soa = soaRecord.split(' ')
		mname = soa[0]
		rname = soa[1]
		serial = int(soa[2])
		refresh = int(soa[3])
		retry = int(soa[4])
		expire = int(soa[5])
		ttl = int(soa[6])
		soa_record = SOARecord(mname=mname, rname=rname, serial=serial, refresh=refresh, retry=retry, expire=expire, minimum=3600, ttl=ttl)

		dnsRecords.append(ndr_pack(soa_record))


def __unpack_soaRecord(object):
	soa = {}
	dnsRecords = object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		ndrRecord = ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_SOA:
			soa['mname'] = ndrRecord.data.mname
			soa['rname'] = ndrRecord.data.rname
			soa['serial'] = str(ndrRecord.data.serial)
			soa['refresh'] = str(ndrRecord.data.refresh)
			soa['retry'] = str(ndrRecord.data.retry)
			soa['expire'] = str(ndrRecord.data.expire)
			soa['minimum'] = str(ndrRecord.data.minimum)
			soa['ttl'] = str(ndrRecord.dwTtlSeconds)
	return soa


def __pack_nsRecord(object, dnsRecords):
	for nSRecord in object['attributes'].get('nSRecord', []):
		nSRecord = compatible_modstring(nSRecord)
		a_record = NSRecord(nSRecord)
		dnsRecords.append(ndr_pack(a_record))


def __unpack_nsRecord(object):
	ns = []
	dnsRecords = object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		ndrRecord = ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_NS:
			ns.append(__append_dot(ndrRecord.data))
	return ns


def __pack_mxRecord(object, dnsRecords):
	for mXRecord in object['attributes'].get('mXRecord', []):
		if mXRecord:
			ud.debug(ud.LDAP, ud.INFO, '__pack_mxRecord: %s' % mXRecord)
			mXRecord = compatible_modstring(mXRecord)
			mx = mXRecord.split(' ')
			priority = mx[0]
			name = mx[1]
			mx_record = MXRecord(name, int(priority))
			dnsRecords.append(ndr_pack(mx_record))
			ud.debug(ud.LDAP, ud.INFO, '__pack_mxRecord: %s' % ndr_pack(mx_record))


def __unpack_mxRecord(object):
	mx = []
	dnsRecords = object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		ndrRecord = ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_MX:
			mx.append([str(ndrRecord.data.wPriority), __append_dot(ndrRecord.data.nameTarget)])
	return mx


def __pack_txtRecord(object, dnsRecords):
	slist = []
	for txtRecord in object['attributes'].get('tXTRecord', []):
		if txtRecord:
			ud.debug(ud.LDAP, ud.INFO, '__pack_txtRecord: %s' % txtRecord)
			txtRecord = compatible_modstring(txtRecord)
			token_list = TXT.from_text(rdataclass.IN, rdatatype.TXT, Tokenizer(txtRecord)).strings
			ndr_txt_record = ndr_pack(TXTRecord(token_list))
			dnsRecords.append(ndr_txt_record)
			ud.debug(ud.LDAP, ud.INFO, '__pack_txtRecord: %s' % ndr_txt_record)


def __unpack_txtRecord(object):
	txt = []
	dnsRecords = object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		ndrRecord = ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_TXT:
			txt.append(str(TXT(rdataclass.IN, rdatatype.TXT, ndrRecord.data.str)))
			# or: txt.append(' '.join(['"%s"' % token for token in ndrRecord.data.str]))
	return txt


def __pack_cName(object, dnsRecords):
	for c in object['attributes'].get('cNAMERecord', []):
		c = compatible_modstring(__remove_dot(c))
		c_record = CNameRecord(c)
		dnsRecords.append(ndr_pack(c_record))


def __unpack_cName(object):
	c = []
	dnsRecords = object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		ndrRecord = ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_CNAME:
			if "." in ndrRecord.data:
				c.append(__append_dot(ndrRecord.data))
			else:
				c.append(ndrRecord.data)
	return c


def __pack_sRVrecord(object, dnsRecords):
	for srvRecord in object['attributes'].get('sRVRecord', []):
		srvRecord = compatible_modstring(srvRecord)
		srv = srvRecord.split(' ')
		priority = int(srv[0])
		weight = int(srv[1])
		port = int(srv[2])
		target = __remove_dot(srv[3])
		s = SRVRecord(target, port, priority, weight)
		dnsRecords.append(ndr_pack(s))


def __unpack_sRVrecord(object):
	srv = []
	dnsRecords = object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		ndrRecord = ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_SRV:
			srv.append([str(ndrRecord.data.wPriority), str(ndrRecord.data.wWeight), str(ndrRecord.data.wPort), __append_dot(ndrRecord.data.nameTarget)])
	return srv


def __pack_ptrRecord(object, dnsRecords):
	for ptr in object['attributes'].get('pTRRecord', []):
		ptr = compatible_modstring(__remove_dot(ptr))
		ptr_record = PTRRecord(ptr)
		dnsRecords.append(ndr_pack(ptr_record))


def __unpack_ptrRecord(object):
	ptr = []
	dnsRecords = object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		ndrRecord = ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_PTR:
			ptr.append(__append_dot(ndrRecord.data))
	return ptr


def __get_s4_msdcs_soa(s4connector, zoneName):
	''' Required to keep the SOA serial numbers in sync
	'''
	func_name = sys._getframe().f_code.co_name
	_d = ud.function(func_name)  # noqa: F841

	msdcs_obj = {}
	msdcs_zonename = compatible_modstring('_msdcs.%s' % zoneName)
	s4_filter = format_escaped('(&(objectClass=dnsZone)(DC={0!e}))', msdcs_zonename)
	ud.debug(ud.LDAP, ud.INFO, "%s: search _msdcs in S4" % func_name)
	msdcs_obj = {}
	for base in s4connector.s4_ldap_partitions:
		resultlist = s4connector._s4__search_s4(
			base,
			ldap.SCOPE_SUBTREE,
			s4_filter,
			show_deleted=False)

		if resultlist:
			break
	else:
		ud.debug(ud.LDAP, ud.WARN, "%s: _msdcs sub-zone for %s not found in S4" % (func_name, zoneName))
		return

	# We need the SOA here
	msdcs_soa_rdn = [('DC', '@', ldap.AVA_STRING)]
	msdcs_soa_dn = unicode(ldap.dn.dn2str([msdcs_soa_rdn] + str2dn(resultlist[0][0])), 'utf8')
	ud.debug(ud.LDAP, ud.INFO, "%s: search DC=@ for _msdcs in S4" % (func_name,))
	resultlist = s4connector._s4__search_s4(
		msdcs_soa_dn,
		ldap.SCOPE_BASE,
		'(objectClass=dnsNode)',
		show_deleted=False)
	if resultlist:
		# __object_from_element not required here
		msdcs_obj = s4connector._s4__object_from_element(resultlist[0])
		return msdcs_obj


''' Create/modify a DNS zone in Samba 4 '''


def s4_zone_create(s4connector, object):
	_d = ud.function('s4_zone_create')  # noqa: F841

	soa_dn = object['dn']
	zone_dn = s4connector.lo.parentDn(soa_dn)

	zoneName = object['attributes']['zoneName'][0]

	# Create the forward zone in S4 if it does not exist
	try:
		s4connector.lo_s4.get(zone_dn, attr=[''], required=True)
	except ldap.NO_SUCH_OBJECT:
		__create_s4_forward_zone(s4connector, zone_dn)

	# Create SOA DC=@ object
	old_dnsRecords = []

	try:
		old_dnsRecords = s4connector.lo_s4.get(soa_dn, attr=['dnsRecord'], required=True).get('dnsRecord')
	except ldap.NO_SUCH_OBJECT:
		__create_s4_forward_zone_soa(s4connector, soa_dn)

	dnsRecords = []

	__pack_nsRecord(object, dnsRecords)

	__pack_soaRecord(object, dnsRecords)

	# The IP address of the DNS forward zone will be used to determine the
	# sysvol share. On a selective replicated DC only a short list of DCs
	# should be returned
	aRecords = s4connector.configRegistry.get('connector/s4/mapping/dns/forward_zone/%s/static/ipv4' % zoneName.lower())
	aAAARecords = s4connector.configRegistry.get('connector/s4/mapping/dns/forward_zone/%s/static/ipv6' % zoneName.lower())
	if aRecords or aAAARecords:
		# IPv4
		if aRecords:
			for a in aRecords.split(' '):
				a = compatible_modstring(a)
				a_record = ARecord(a)
				dnsRecords.append(ndr_pack(a_record))

		# IPv6
		if aAAARecords:
			for a in aAAARecords.split(' '):
				a = compatible_modstring(a)
				a_record = AAAARecord(a)
				dnsRecords.append(ndr_pack(a_record))
	else:
		__pack_aRecord(object, dnsRecords)

	__pack_mxRecord(object, dnsRecords)

	__pack_txtRecord(object, dnsRecords)

	s4connector.lo_s4.modify(soa_dn, [('dnsRecord', old_dnsRecords, dnsRecords)])

	return True


def s4_zone_msdcs_sync(s4connector, object):
	_d = ud.function('s4_zone_msdcs_sync')  # noqa: F841

	# Get the current serial number of the OpenLDAP domainname zone
	domainZoneName = object['attributes']['zoneName'][0]
	soaRecord = object['attributes'].get('sOARecord', [None])[0]
	if not soaRecord:
		ud.debug(ud.LDAP, ud.WARN, 's4_zone_msdcs_sync: OL zone %s has no SOA info' % domainZoneName)
		return

	soaRecord = compatible_modstring(soaRecord)
	soa = soaRecord.split(' ')
	serial = int(soa[2])

	# lookup the the SOA record of the _msdcs sub-zone for the domainname zone
	msdcs_soa_obj = __get_s4_msdcs_soa(s4connector, domainZoneName)
	if not msdcs_soa_obj:
		return
	msdcs_soa_dn = msdcs_soa_obj['dn']

	dnsRecords = []
	msdcs_soa = {}
	old_dnsRecords = msdcs_soa_obj['attributes'].get('dnsRecord', [])
	found = False
	for dnsRecord in old_dnsRecords:
		ndrRecord = ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_SOA:
			if ndrRecord.data.serial >= serial:
				ud.debug(ud.LDAP, ud.WARN, 's4_zone_msdcs_sync: SOA serial OpenLDAP zone %s is higher than corresponding value of %s' % (domainZoneName, msdcs_soa_dn))
				return
			ndrRecord.data.serial = serial
			dnsRecords.append(ndr_pack(ndrRecord))
			found = True
		else:
			dnsRecords.append(dnsRecord)

	if not found:
		ud.debug(ud.LDAP, ud.WARN, 's4_zone_msdcs_sync: object %s has no SOA info' % msdcs_soa_dn)
		return

	s4connector.lo_s4.modify(msdcs_soa_dn, [('dnsRecord', old_dnsRecords, dnsRecords)])

	return True


''' Create/modify a DNS zone and possibly _msdcs in Samba 4 '''


def s4_zone_create_wrapper(s4connector, object):
	''' Handle s4_zone_create to additionally sync to _msdcs.$domainname
		Required to keep the SOA serial numbers in sync
	'''
	result = s4_zone_create(s4connector, object)

	zoneName = object['attributes']['zoneName'][0]
	if zoneName == s4connector.configRegistry.get('domainname') and s4connector.configRegistry.get('connector/s4/mapping/dns/position') != 'legacy' and object['modtype'] == 'modify':
		# Additionally sync serialNumber to _msdcs zone
		result = result and s4_zone_msdcs_sync(s4connector, object)

	return result


''' Delete a forward zone in Samaba 4 '''


def s4_zone_delete(s4connector, object):
	_d = ud.function('s4_zone_delete')  # noqa: F841

	soa_dn = object['dn']
	zone_dn = s4connector.lo.parentDn(soa_dn)

	try:
		res = s4connector.lo_s4.lo.delete_s(soa_dn)
	except ldap.NO_SUCH_OBJECT:
		pass  # the object was already removed

	try:
		res = s4connector.lo_s4.lo.delete_s(zone_dn)
	except ldap.NO_SUCH_OBJECT:
		pass  # the object was already removed

	return True


def s4_dns_node_base_create(s4connector, object, dnsRecords):
	_d = ud.function('s4_dns_node_base_create')  # noqa: F841

	relativeDomainNames = object['attributes'].get('relativeDomainName')
	relativeDomainNames = univention.s4connector.s4.compatible_list(relativeDomainNames)

	old_dnsRecords = []

	# Create dnsNode object
	dnsNodeDn = object['dn']
	try:
		old_dnsRecords = s4connector.lo_s4.get(dnsNodeDn, attr=['dnsRecord'], required=True).get('dnsRecord')
	except ldap.NO_SUCH_OBJECT:
		__create_s4_dns_node(s4connector, dnsNodeDn, relativeDomainNames, dnsRecords)
	else:
		_res = s4connector.lo_s4.modify(dnsNodeDn, [('dnsRecord', old_dnsRecords, dnsRecords)])

	return dnsNodeDn


def s4_dns_node_base_delete(s4connector, object):
	_d = ud.function('s4_dns_node_base_delete')  # noqa: F841

	relativeDomainNames = object['attributes'].get('relativeDomainName')
	relativeDomainNames = univention.s4connector.s4.compatible_list(relativeDomainNames)

	dnsNodeDn = object['dn']
	try:
		res = s4connector.lo_s4.lo.delete_s(dnsNodeDn)
	except ldap.NO_SUCH_OBJECT:
		pass  # the object was already removed

	return True


''' Create a host record in Samaba 4 '''


def s4_host_record_create(s4connector, object):
	_d = ud.function('s4_host_record_create')  # noqa: F841

	dnsRecords = []

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	aRecords = s4connector.configRegistry.get('connector/s4/mapping/dns/host_record/%s.%s/static/ipv4' % (relativeDomainName.lower(), zoneName.lower()))
	aAAARecords = s4connector.configRegistry.get('connector/s4/mapping/dns/host_record/%s.%s/static/ipv6' % (relativeDomainName.lower(), zoneName.lower()))
	if aRecords or aAAARecords:
		# IPv4
		if aRecords:
			for a in aRecords.split(' '):
				a = compatible_modstring(a)
				a_record = ARecord(a)
				dnsRecords.append(ndr_pack(a_record))

		# IPv6
		if aAAARecords:
			for a in aAAARecords.split(' '):
				a = compatible_modstring(a)
				a_record = AAAARecord(a)
				dnsRecords.append(ndr_pack(a_record))
	else:
		__pack_aRecord(object, dnsRecords)

	__pack_mxRecord(object, dnsRecords)
	__pack_txtRecord(object, dnsRecords)

	dnsNodeDn = s4_dns_node_base_create(s4connector, object, dnsRecords)

	return True


def ucs_host_record_create(s4connector, object):
	_d = ud.function('ucs_host_record_create')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_create: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	aRecords = s4connector.configRegistry.get('connector/s4/mapping/dns/host_record/%s.%s/static/ipv4' % (relativeDomainName.lower(), zoneName.lower()))
	if aRecords:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_create: do not write host record back from S4 to UCS because location of A record has been overwritten by UCR')
		return
	aAAARecords = s4connector.configRegistry.get('connector/s4/mapping/dns/host_record/%s.%s/static/ipv6' % (relativeDomainName.lower(), zoneName.lower()))
	if aAAARecords:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_create: do not write host record back from S4 to UCS because location of AAAA record has been overwritten by UCR')
		return

	# unpack the host record
	a = __unpack_aRecord(object)

	# Does a host record for this zone already exist?
	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		newRecord = univention.admin.handlers.dns.host_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		newRecord.open()
		if set(newRecord['a']) != set(a):
			newRecord['a'] = a
			newRecord.modify()
		else:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_create: do not modify host record')
	else:
		zoneDN = __get_zone_dn(s4connector, zoneName)

		ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_create: zoneDN: %s' % zoneDN)

		position = univention.admin.uldap.position(zoneDN)

		newRecord = univention.admin.handlers.dns.host_record.object(None, s4connector.lo, position, dn=None, attributes=[], update_zone=False)
		newRecord.open()
		newRecord['name'] = relativeDomainName
		newRecord['a'] = a
		newRecord.create()


def ucs_host_record_delete(s4connector, object):
	_d = ud.function('ucs_host_record_delete')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_delete: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		newRecord = univention.admin.handlers.dns.host_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		newRecord.open()
		newRecord.delete()
	else:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_delete: Object was not found, filter was: %s' % ol_filter)

	return True


def s4_ptr_record_create(s4connector, object):
	_d = ud.function('s4_ptr_record_create')  # noqa: F841

	dnsRecords = []

	__pack_ptrRecord(object, dnsRecords)

	dnsNodeDn = s4_dns_node_base_create(s4connector, object, dnsRecords)

	return True


def ucs_ptr_record_create(s4connector, object):
	_d = ud.function('ucs_ptr_record_create')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, 'ucs_ptr_record_create: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	# unpack the host record
	ptr = __unpack_ptrRecord(object)

	# Does a host record for this zone already exist?
	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		newRecord = univention.admin.handlers.dns.ptr_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		newRecord.open()
		if set(newRecord['ptr_record']) != set(ptr):
			newRecord['ptr_record'] = ptr[0]
			newRecord.modify()
		else:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_ptr_record_create: do not modify ptr record')
	else:
		zoneDN = __get_zone_dn(s4connector, zoneName)

		position = univention.admin.uldap.position(zoneDN)

		newRecord = univention.admin.handlers.dns.ptr_record.object(None, s4connector.lo, position, dn=None, attributes=[], update_zone=False)
		newRecord.open()
		newRecord['address'] = relativeDomainName
		newRecord['ptr_record'] = ptr[0]
		newRecord.create()


def ucs_ptr_record_delete(s4connector, object):
	_d = ud.function('ucs_ptr_record_delete')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, 'ucs_ptr_record_delete: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		newRecord = univention.admin.handlers.dns.ptr_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		newRecord.open()
		newRecord.delete()
	else:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_ptr_record_delete: Object was not found, filter was: %s' % ol_filter)

	return True


def ucs_cname_create(s4connector, object):
	_d = ud.function('ucs_cname_create')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, 'ucs_cname_create: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	# unpack the host record
	c = __unpack_cName(object)

	# Does a host record for this zone already exist?
	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		newRecord = univention.admin.handlers.dns.alias.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		newRecord.open()
		if set(newRecord['cname']) != set(c):
			newRecord['cname'] = c[0]
			newRecord.modify()
		else:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_cname_create: do not modify cname record')
	else:
		zoneDN = __get_zone_dn(s4connector, zoneName)

		position = univention.admin.uldap.position(zoneDN)

		newRecord = univention.admin.handlers.dns.alias.object(None, s4connector.lo, position, dn=None, attributes=[], update_zone=False)
		newRecord.open()
		newRecord['name'] = relativeDomainName
		newRecord['cname'] = c[0]
		newRecord.create()


def ucs_cname_delete(s4connector, object):
	_d = ud.function('ucs_cname_delete')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, 'ucs_cname_delete: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		newRecord = univention.admin.handlers.dns.alias.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		newRecord.open()
		newRecord.delete()
	else:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_cname_delete: Object was not found, filter was: %s' % ol_filter)

	return True


def s4_cname_create(s4connector, object):
	_d = ud.function('s4_cname_create')  # noqa: F841

	dnsRecords = []

	__pack_cName(object, dnsRecords)

	dnsNodeDn = s4_dns_node_base_create(s4connector, object, dnsRecords)


def ucs_srv_record_create(s4connector, object):
	_d = ud.function('ucs_srv_record_create')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	# unpack the host record
	srv = __unpack_sRVrecord(object)

	# ucr set connector/s4/mapping/dns/srv_record/_ldap._tcp.test.local/location='100 0 389 foobar.test.local. 100 0 389 foobar2.test.local.'
	ucr_locations = s4connector.configRegistry.get('connector/s4/mapping/dns/srv_record/%s.%s/location' % (relativeDomainName.lower(), zoneName.lower()))
	ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: ucr_locations for connector/s4/mapping/dns/srv_record/%s.%s/location: %s' % (relativeDomainName.lower(), zoneName.lower(), ucr_locations))

	if ucr_locations and ucr_locations.lower() == 'ignore':
		return

	# Does a host record for this zone already exist?
	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		newRecord = univention.admin.handlers.dns.srv_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		newRecord.open()
		if ucr_locations:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: do not write SRV record back from S4 to UCS because location of SRV record have been overwritten by UCR')
		else:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: location: %s' % newRecord['location'])
			ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: srv     : %s' % srv)
			srv.sort()
			newRecord['location'].sort()
			if srv != newRecord['location']:
				newRecord['location'] = srv
				newRecord.modify()
			else:
				ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: do not modify srv record')
	else:
		zoneDN = __get_zone_dn(s4connector, zoneName)

		position = univention.admin.uldap.position(zoneDN)

		newRecord = univention.admin.handlers.dns.srv_record.object(None, s4connector.lo, position, dn=None, attributes=[], update_zone=False)
		newRecord.open()
		# Make syntax UDM compatible
		parts = univention.admin.handlers.dns.srv_record.unmapName([relativeDomainName])
		if len(parts) == 3 and parts[2]:
			msg = 'SRV create: service="%s" protocol="%s" extension="%s"' % (parts[0], parts[1], parts[2])
		if len(parts) == 2:
			msg = 'SRV create: service="%s" protocol="%s"' % (parts[0], parts[1])
		else:
			msg = 'SRV create: unexpected format, parts: %s' % (parts,)

		ud.debug(ud.LDAP, ud.INFO, msg)
		newRecord['name'] = parts
		newRecord['location'] = srv
		newRecord.create()


def ucs_srv_record_delete(s4connector, object):
	_d = ud.function('ucs_srv_record_delete')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_delete: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		newRecord = univention.admin.handlers.dns.srv_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		newRecord.open()
		newRecord.delete()
	else:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_delete: Object was not found, filter was: %s' % ol_filter)

	return True


def s4_srv_record_create(s4connector, object):
	_d = ud.function('s4_srv_record_create')  # noqa: F841

	dnsRecords = []

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	# ucr set connector/s4/mapping/dns/srv_record/_ldap._tcp.test.local/location='100 0 389 foobar.test.local.'
	# ucr set connector/s4/mapping/dns/srv_record/_ldap._tcp.test.local/location='100 0 389 foobar.test.local. 100 0 389 foobar2.test.local.'
	ucr_locations = s4connector.configRegistry.get('connector/s4/mapping/dns/srv_record/%s.%s/location' % (relativeDomainName.lower(), zoneName.lower()))
	ud.debug(ud.LDAP, ud.INFO, 's4_srv_record_create: ucr_locations for connector/s4/mapping/dns/srv_record/%s.%s/location: %s' % (relativeDomainName.lower(), zoneName.lower(), ucr_locations))
	if ucr_locations:
		if ucr_locations.lower() == 'ignore':
			return
		# Convert ucr variable
		priority = None
		weight = None
		port = None
		target = None
		for v in ucr_locations.split(' '):
			# Check explicit for None, because the int values may be 0
			if priority is None:
				priority = int(v)
			elif weight is None:
				weight = int(v)
			elif port is None:
				port = int(v)
			elif not target:
				target = __remove_dot(v)
			if priority is not None and weight is not None and port is not None and target:
				ud.debug(ud.LDAP, ud.INFO, 'priority=%d weight=%d port=%d target=%s' % (priority, weight, port, target))
				s = SRVRecord(target, port, priority, weight)
				dnsRecords.append(ndr_pack(s))
				priority = None
				weight = None
				port = None
				target = None

	else:
		__pack_sRVrecord(object, dnsRecords)

	dnsNodeDn = s4_dns_node_base_create(s4connector, object, dnsRecords)


def ucs_txt_record_create(s4connector, object):
	_d = ud.function('ucs_txt_record_create')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, 'ucs_txt_record_create: object: %s' % object)
	udm_property = 'txt'

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	# unpack the record
	c = __unpack_txtRecord(object)

	# Does a host record for this zone already exist?
	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		foundRecord = univention.admin.handlers.dns.txt_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		foundRecord.open()

		# use normalized TXT records for comparison
		normalized_txtRecord_list = []
		for txtRecord in foundRecord['txt']:
			normalized_txtRecord = str(TXT.from_text(rdataclass.IN, rdatatype.TXT, Tokenizer(txtRecord)))
			normalized_txtRecord_list.append(normalized_txtRecord)

		if set(normalized_txtRecord_list) != set(c):
			foundRecord[udm_property] = c
			foundRecord.modify()
		else:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_txt_record_create: do not modify txt record')
	else:
		zoneDN = __get_zone_dn(s4connector, zoneName)

		position = univention.admin.uldap.position(zoneDN)

		newRecord = univention.admin.handlers.dns.txt_record.object(None, s4connector.lo, position, dn=None, attributes=[], update_zone=False)
		newRecord.open()
		newRecord['name'] = relativeDomainName
		newRecord[udm_property] = c
		newRecord.create()


def ucs_txt_record_delete(s4connector, object):
	_d = ud.function('ucs_txt_record_delete')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, 'ucs_txt_record_delete: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		newRecord = univention.admin.handlers.dns.txt_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		newRecord.open()
		newRecord.delete()
	else:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_txt_record_delete: Object was not found, filter was: %s' % ol_filter)

	return True


def s4_txt_record_create(s4connector, object):
	_d = ud.function('s4_txt_record_create')  # noqa: F841

	dnsRecords = []

	__pack_txtRecord(object, dnsRecords)

	dnsNodeDn = s4_dns_node_base_create(s4connector, object, dnsRecords)


def ucs_ns_record_create(s4connector, object):
	_d = ud.function('ucs_ns_record_create')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, 'ucs_ns_record_create: object: %s' % object)
	udm_property = 'nameserver'

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	# unpack the record
	c = __unpack_nsRecord(object)

	# Does a host record for this zone already exist?
	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		foundRecord = univention.admin.handlers.dns.ns_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		foundRecord.open()

		if set(foundRecord[udm_property]) != set(c):
			foundRecord[udm_property] = c
			foundRecord.modify()
		else:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_ns_record_create: do not modify ns record')
	else:
		zoneDN = __get_zone_dn(s4connector, zoneName)
		position = univention.admin.uldap.position(zoneDN)

		newRecord = univention.admin.handlers.dns.ns_record.object(None, s4connector.lo, position, dn=None, attributes=[], update_zone=False)
		newRecord.open()
		newRecord['zone'] = relativeDomainName
		newRecord[udm_property] = c
		newRecord.create()


def ucs_ns_record_delete(s4connector, object):
	_d = ud.function('ucs_ns_record_delete')  # noqa: F841
	ud.debug(ud.LDAP, ud.INFO, 'ucs_ns_record_delete: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		newRecord = univention.admin.handlers.dns.ns_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		newRecord.open()
		newRecord.delete()
	else:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_ns_record_delete: Object was not found, filter was: %s' % ol_filter)

	return True


def s4_ns_record_create(s4connector, object):
	_d = ud.function('s4_ns_record_create')  # noqa: F841

	dnsRecords = []

	__pack_nsRecord(object, dnsRecords)

	dnsNodeDn = s4_dns_node_base_create(s4connector, object, dnsRecords)


def ucs_zone_create(s4connector, object, dns_type):
	_d = ud.function('ucs_zone_create')  # noqa: F841

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	# create the zone when the dc=@ object has been created
	if relativeDomainName != '@':
		ud.debug(ud.LDAP, ud.INFO, "ucs_zone_create: ignoring DC=%s object" % (relativeDomainName,))
		return

	ns = __unpack_nsRecord(object)

	soa = __unpack_soaRecord(object)

	a = __unpack_aRecord(object)

	mx = __unpack_mxRecord(object)

	if zoneName == s4connector.configRegistry.get('domainname') and s4connector.configRegistry.get('connector/s4/mapping/dns/position') != 'legacy' and object['modtype'] == 'modify':
		# Determine max of serialNumber from _msdcs zone
		msdcs_soa_obj = __get_s4_msdcs_soa(s4connector, zoneName)
		if msdcs_soa_obj:
			msdcs_soa = __unpack_soaRecord(msdcs_soa_obj)
			soa['serial'] = str(max(int(soa['serial']), int(msdcs_soa['serial'])))

	mname = soa['mname']
	if mname and not mname.endswith("."):
		mname = "%s." % mname

	ns_lower = [x.lower() for x in ns]
	mname_lower = mname.lower()
	if mname_lower not in ns_lower:
		ns.insert(0, mname)
		ns_lower.insert(0, mname_lower)

	# Does a zone already exist?
	modify = False
	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		if dns_type == 'forward_zone':
			zone = univention.admin.handlers.dns.forward_zone.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[])
		elif dns_type == 'reverse_zone':
			zone = univention.admin.handlers.dns.reverse_zone.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[])
		zone.open()
		udm_zone_nameservers_lower = [x.lower() for x in zone['nameserver']]
		if set(ns_lower) != set(udm_zone_nameservers_lower):
			zone['nameserver'] = ns
			modify = True
		if soa['rname'].replace('.', '@', 1) != zone['contact'].rstrip('.'):
			zone['contact'] = soa['rname'].replace('.', '@', 1)
			modify = True
		if int(soa['serial']) != int(zone['serial']):
			zone['serial'] = soa['serial']
			modify = True
		for k in ['refresh', 'retry', 'expire', 'ttl']:
			if int(soa[k]) != _unixTimeInverval2seconds(zone[k]):
				zone[k] = unmapUNIX_TimeInterval(soa[k])
				modify = True
		if dns_type == 'forward_zone':
			# The IP address of the DNS forward zone will be used to determine the
			# sysvol share. On a selective replicated DC only a short list of DCs
			# should be returned
			aRecords = s4connector.configRegistry.get('connector/s4/mapping/dns/forward_zone/%s/static/ipv4' % zoneName.lower())
			aAAARecords = s4connector.configRegistry.get('connector/s4/mapping/dns/forward_zone/%s/static/ipv6' % zoneName.lower())
			if not aRecords and not aAAARecords:
				if set(a) != set(zone['a']):
					zone['a'] = a
					modify = True
			if mx:
				def mapMX(m):
					return '%s %s' % (m[0], m[1])
				if set(map(mapMX, mx)) != set(map(mapMX, zone['mx'])):
					zone['mx'] = mx
					modify = True
		if modify:
			zone.modify()
	else:
		position = univention.admin.uldap.position(s4connector.property['dns'].ucs_default_dn)

		if dns_type == 'forward_zone':
			zone = univention.admin.handlers.dns.forward_zone.object(None, s4connector.lo, position, dn=None, attributes=[])
			name_key = 'zone'
		elif dns_type == 'reverse_zone':
			zone = univention.admin.handlers.dns.reverse_zone.object(None, s4connector.lo, position, dn=None, attributes=[])
			name_key = 'subnet'
			zoneName = univention.admin.handlers.dns.reverse_zone.unmapSubnet(zoneName)
		zone.open()
		zone[name_key] = zoneName
		zone['nameserver'] = ns
		zone['contact'] = soa['rname'].replace('.', '@', 1)
		zone['serial'] = soa['serial']
		zone['refresh'] = [soa['refresh']]  # complex UDM syntax
		zone['retry'] = [soa['retry']]  # complex UDM syntax
		zone['expire'] = [soa['expire']]  # complex UDM syntax
		zone['ttl'] = [soa['ttl']]  # complex UDM syntax
		if dns_type == 'forward_zone':
			zone['a'] = a
			zone['mx'] = mx
		zone.create()


def ucs_zone_delete(s4connector, object, dns_type):
	_d = ud.function('ucs_zone_delete')  # noqa: F841

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	if relativeDomainName != '@':
		ud.debug(ud.LDAP, ud.INFO, "ucs_zone_delete: ignoring DC=%s object" % (relativeDomainName,))
		return

	ol_filter = format_escaped('(&(relativeDomainName={0!e})(zoneName={1!e}))', relativeDomainName, zoneName)
	searchResult = s4connector.lo.search(filter=ol_filter, unique=True)
	if len(searchResult) > 0:
		if dns_type == 'forward_zone':
			zone = univention.admin.handlers.dns.forward_zone.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		elif dns_type == 'reverse_zone':
			zone = univention.admin.handlers.dns.reverse_zone.object(None, s4connector.lo, position=None, dn=searchResult[0][0], attributes=[], update_zone=False)
		zone.open()
		zone.delete()


def _identify_dns_ucs_object(s4connector, object):
	# At this point dn_mapping_function already has converted object['dn'] from ucs to con
	# But since there is no attribute mapping defined for DNS, the object attributes still
	# are the ones from UCS. Passing the Samba4 object['dn'] is irrelevant here:
	if object.get('attributes'):
		if univention.admin.handlers.dns.forward_zone.identify(object['dn'], object['attributes']):
			return 'forward_zone'
		if univention.admin.handlers.dns.reverse_zone.identify(object['dn'], object['attributes']):
			return 'reverse_zone'
		if univention.admin.handlers.dns.alias.identify(object['dn'], object['attributes']):
			return 'alias'
		if univention.admin.handlers.dns.host_record.identify(object['dn'], object['attributes']):
			return 'host_record'
		if univention.admin.handlers.dns.srv_record.identify(object['dn'], object['attributes']):
			return 'srv_record'
		if univention.admin.handlers.dns.ptr_record.identify(object['dn'], object['attributes']):
			return 'ptr_record'
		if univention.admin.handlers.dns.txt_record.identify(object['dn'], object['attributes']):
			return 'txt_record'
		if univention.admin.handlers.dns.ns_record.identify(object['dn'], object['attributes']):
			return 'ns_record'
	return None


def _identify_dns_con_object(s4connector, object):
	_d = ud.function('_identify_dns_con_object')  # noqa: F841
	# At this point dn_mapping_function already has converted object['dn'] from con to ucs
	# But since there is no attribute mapping defined for DNS, the object attributes still
	# are the ones from Samba.

	if object.get('attributes'):
		oc = object['attributes'].get('objectClass')
		dc = object['attributes'].get('dc') or object['attributes'].get('DC')
		if oc and 'dnsZone' in oc:
			# forward or reverse zone
			if dc and dc[0].endswith('in-addr.arpa'):
				return 'reverse_zone'
			else:
				return 'forward_zone'
		if oc and 'dnsNode' in oc:
			if dc and dc[0] == '@':
				zone_type = 'forward_zone'
				exploded_dn = str2dn(unicode_to_utf8(object['dn']))
				for multi_rdn in exploded_dn:
					(attribute, value, _flags) = multi_rdn[0]
					if attribute.lower() == 'zonename' and value.lower().endswith('in-addr.arpa'):
						zone_type = 'reverse_zone'
						break
				return zone_type

			else:
				dnsRecords = object['attributes'].get('dnsRecord')
				if not dnsRecords:
					return None

				dns_types = set()
				for dnsRecord in dnsRecords:
					dnsRecord_DnssrvRpcRecord = ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
					dns_types.add(dnsRecord_DnssrvRpcRecord.wType)

				if dnsp.DNS_TYPE_PTR in dns_types:
					return 'ptr_record'
				elif dnsp.DNS_TYPE_CNAME in dns_types:
					return 'alias'
				elif dnsp.DNS_TYPE_SRV in dns_types:
					return 'srv_record'
				elif set((dnsp.DNS_TYPE_A, dnsp.DNS_TYPE_AAAA)) & dns_types:
					return 'host_record'
				elif dnsp.DNS_TYPE_TXT in dns_types:
					return 'txt_record'
				elif dnsp.DNS_TYPE_NS in dns_types:
					return 'ns_record'

	return None


def ucs2con(s4connector, key, object):
	_d = ud.function('dns: ucs2con')  # noqa: F841

	# At this point dn_mapping_function already has converted object['dn'] from ucs to con
	# But since there is no attribute mapping defined for DNS, the object attributes still
	# are the ones from UCS.
	dns_type = _identify_dns_ucs_object(s4connector, object)

	if not dns_type:
		# unknown object -> ignore
		ud.debug(ud.LDAP, ud.INFO, 'dns ucs2con: Ignore unknown dns object: %s' % object['dn'])
		return True

	ud.debug(ud.LDAP, ud.INFO, 'dns ucs2con: Object (%s) is of type %s' % (object['dn'], dns_type))

	# We can only get the mapped zone_name from the DN here (see comment above):
	# (In the case of _msdcs the zoneName would be wrong here otherwise)

	(zoneName, relativeDomainName) = __split_s4_dnsNode_dn(object['dn'])
	object['attributes']['zoneName'] = [zoneName]
	relativeDomainName = univention.s4connector.s4.compatible_list([relativeDomainName])[0]
	object['attributes']['relativeDomainName'] = [relativeDomainName]

	if dns_type == 'forward_zone' or dns_type == 'reverse_zone':
		if object['modtype'] in ['add', 'modify']:
			s4_zone_create_wrapper(s4connector, object)
		elif object['modtype'] in ['delete']:
			s4_zone_delete(s4connector, object)
		# ignore move

	elif dns_type == 'host_record':
		if object['modtype'] in ['add', 'modify']:
			s4_host_record_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			s4_dns_node_base_delete(s4connector, object)
		# ignore move

	elif dns_type == 'alias':
		if object['modtype'] in ['add', 'modify']:
			s4_cname_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			s4_dns_node_base_delete(s4connector, object)
		# ignore move

	elif dns_type == 'srv_record':
		if object['modtype'] in ['add', 'modify']:
			s4_srv_record_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			s4_dns_node_base_delete(s4connector, object)
		# ignore move

	elif dns_type == 'ptr_record':
		if object['modtype'] in ['add', 'modify']:
			s4_ptr_record_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			s4_dns_node_base_delete(s4connector, object)
		# ignore move

	elif dns_type == 'txt_record':
		if object['modtype'] in ['add', 'modify']:
			s4_txt_record_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			s4_dns_node_base_delete(s4connector, object)
		# ignore move

	elif dns_type == 'ns_record':
		if object['modtype'] in ['add', 'modify']:
			s4_ns_record_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			s4_dns_node_base_delete(s4connector, object)
		# ignore move

	return True


def con2ucs(s4connector, key, object):
	_d = ud.function('dns: con2ucs')  # noqa: F841

	ud.debug(ud.LDAP, ud.INFO, 'dns con2ucs: Object (%s): %s' % (object['dn'], object))

	# At this point dn_mapping_function already has converted object['dn'] from con to ucs
	# But since there is no attribute mapping defined for DNS, the object attributes still
	# are the ones from Samba.
	dns_type = _identify_dns_con_object(s4connector, object)

	if not dns_type:
		# unknown object -> ignore
		ud.debug(ud.LDAP, ud.INFO, 'dns con2ucs: Ignore unknown dns object: %s' % object['dn'])
		return True

	ud.debug(ud.LDAP, ud.INFO, 'dns con2ucs: Object (%s) is of type %s' % (object['dn'], dns_type))

	# We can only get the mapped zone_name from the DN here (see comment above):

	(zoneName, relativeDomainName) = __split_ol_dNSZone_dn(object['dn'], object['attributes']['objectClass'])
	# Inject the zoneName and relativeDomainName to simplify things below
	object['attributes']['zoneName'] = [zoneName]
	object['attributes']['relativeDomainName'] = [relativeDomainName]

	if dns_type == 'host_record':
		if object['modtype'] in ['add', 'modify']:
			ucs_host_record_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			ucs_host_record_delete(s4connector, object)
		# ignore move
	elif dns_type == 'ptr_record':
		if object['modtype'] in ['add', 'modify']:
			ucs_ptr_record_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			ucs_ptr_record_delete(s4connector, object)
		# ignore move
	elif dns_type == 'alias':
		if object['modtype'] in ['add', 'modify']:
			ucs_cname_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			ucs_cname_delete(s4connector, object)
		# ignore move
	elif dns_type == 'srv_record':
		if object['modtype'] in ['add', 'modify']:
			ucs_srv_record_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			ucs_srv_record_delete(s4connector, object)
		# ignore move
	elif dns_type == 'txt_record':
		if object['modtype'] in ['add', 'modify']:
			ucs_txt_record_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			ucs_txt_record_delete(s4connector, object)
		# ignore move
	elif dns_type == 'ns_record':
		if object['modtype'] in ['add', 'modify']:
			ucs_ns_record_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			ucs_ns_record_delete(s4connector, object)
		# ignore move
	if dns_type in ['forward_zone', 'reverse_zone']:
		if object['modtype'] in ['add', 'modify']:
			ucs_zone_create(s4connector, object, dns_type)
		elif object['modtype'] in ['delete']:
			ucs_zone_delete(s4connector, object, dns_type)
		# ignore move

	return True
