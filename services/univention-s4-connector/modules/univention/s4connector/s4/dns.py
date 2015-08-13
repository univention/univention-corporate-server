#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  dns helper functions
#
# Copyright 2004-2015 Univention GmbH
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

import ldap, string
import univention.debug2 as ud
import univention.s4connector.s4
import univention.admin.uldap
from univention.s4connector.s4.dc import _unixTimeInverval2seconds
from univention.admin.mapping import unmapUNIX_TimeInterval

from samba.dcerpc import dnsp
from samba.ndr import ndr_pack, ndr_unpack, ndr_print
import copy
import time
import sys

from samba.provision.sambadns import ARecord
# def __init__(self, ip_addr, serial=1, ttl=3600):

from samba.provision.sambadns import AAAARecord
# def __init__(self, ip6_addr, serial=1, ttl=3600):

from samba.provision.sambadns import NSRecord
# def __init__(self, dns_server, serial=1, ttl=3600):

from samba.provision.sambadns import SOARecord
# def __init__(self, mname, rname, serial=1, refresh=900, retry=600, expire=86400, minimum=3600, ttl=3600):

from samba.provision.sambadns import SRVRecord
# def __init__(self, target, port, priority=0, weight=0, serial=1, ttl=3600):

class CName(dnsp.DnssrvRpcRecord):
	def __init__(self, cname, serial=1, ttl=3600):
		super(CName, self).__init__()
		self.wType=dnsp.DNS_TYPE_CNAME
		self.dwSerial=serial
		self.dwTtlSeconds=ttl
		self.data=cname

class PTRRecord(dnsp.DnssrvRpcRecord):
	def __init__(self, ptr, serial=1, ttl=3600):
		super(PTRRecord, self).__init__()
		self.wType=dnsp.DNS_TYPE_PTR
		self.dwSerial=serial
		self.dwTtlSeconds=ttl
		self.data=ptr

class MXRecord(dnsp.DnssrvRpcRecord):
	def __init__(self, name, priority, serial=1, ttl=3600):
		super(MXRecord, self).__init__()
		self.wType=dnsp.DNS_TYPE_MX
		self.dwSerial=serial
		self.dwTtlSeconds=ttl
		self.data.wPriority=priority
		self.data.nameTarget=name

import univention.admin.handlers
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.alias
import univention.admin.handlers.dns.host_record
import univention.admin.handlers.dns.srv_record
import univention.admin.handlers.dns.reverse_zone
import univention.admin.handlers.dns.ptr_record

# mapping funtions
def dns_dn_mapping(s4connector, given_object, dn_mapping_stored, isUCSobject):
	'''
	map dn of given object (which must have an s4_RR_attr in S4)
	ol_oc_filter and s4_RR_filter are objectclass filters in UCS and S4

	Code is based on univention.s4connector.s4.samaccountname_dn_mapping
	'''
	obj = copy.deepcopy(given_object)

	propertyname = 'dns'
	propertyattrib = u'relativeDomainName'	## using LDAP name here, for simplicity
	ol_oc_filter = '(objectClass=dNSZone)'	## all OpenLDAP DNS records match
	ol_RR_attr = 'relativeDomainName'
	s4_RR_filter = u'(objectClass=dnsNode)'	## This also matches the DC=@ SOA object
	s4_RR_attr = 'dc'						## Note: the S4 attribute itself is lowercase

	if obj['dn'] != None:
		try:
			s4_RR_val = obj['attributes'][s4_RR_attr][0]
		except (KeyError, IndexError):
			s4_RR_val = ''
	
	def dn_premapped(given_object, dn_key, dn_mapping_stored):
		if (not dn_key in dn_mapping_stored) or (not given_object[dn_key]):
			ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: not premapped (in first instance)")
			return False
		else: # check if DN exists
			if isUCSobject:
				premapped_dn = s4connector.get_object_dn(given_object[dn_key])
				if premapped_dn != None:
					# ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: premapped S4 object found")
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: premapped S4 object: %s" % premapped_dn)
					return True
				else:
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: premapped S4 object not found")
					return False
			else:
				premapped_dn = s4connector.get_ucs_ldap_object_dn(given_object[dn_key])
				if premapped_dn != None:
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
			if dn == None:
				break

			pos = string.find(dn,'=')
			rdn = univention.s4connector.s4.explode_unicode_dn(dn)
			pos2 = len(rdn[0])

			if isUCSobject:
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: got an UCS-Object")
				# lookup the relativeDomainName as DC/dnsNode in S4 to get corresponding DN, if not found create new

				try:
					relativeDomainName = obj['attributes'][ol_RR_attr][0]
				except (KeyError, IndexError):
					### Safety fallback for the unexpected case, where relativeDomainName would not be set
					rdn0_attrib = dn[:pos]
					if 'zoneName' == rdn0_attrib:
						relativeDomainName = '@'
					else:
						raise ## can't determine relativeDomainName

				if s4connector.property[propertyname].mapping_table and propertyattrib in s4connector.property[propertyname].mapping_table.keys():
					for ucsval, conval in s4connector.property[propertyname].mapping_table[propertyattrib]:
						try:
							if relativeDomainName.lower() == ucsval.lower():
								relativeDomainName = conval
								ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: map relativeDomainName according to mapping-table")
								continue
						except UnicodeDecodeError:
							pass # values are not the same codec
				
				try:
					ol_zone_name = obj['attributes']['zoneName'][0]
				except (KeyError, IndexError):
					### Safety fallback for the unexpected case, where zoneName would not be set
					rdn0_attrib = dn[:pos]
					if ol_RR_attr == rdn0_attrib:
						## get parent following the recipe from __split_s4_dns_dn:
						rdn1_tmp = rdn[1].split('=')
						rdn1_key, rdn1_val = (rdn1_tmp[0], string.join(rdn1_tmp[1:], '='))
						if 'zoneName' == rdn1_key:
							ol_zone_name = rdn1_val
						else:
							raise ## can't determine zoneName for this relativeDomainName

				target_RR_val = relativeDomainName
				target_zone_name = ol_zone_name
				s4dn_utf16_le = None
				s4_zone_dn = None
				if '@' == relativeDomainName:	## or dn starts with 'zoneName='
					s4_filter = '(&(objectClass=dnsZone)(%s=%s))' % (s4_RR_attr, ol_zone_name)
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: search in S4")
					for base in s4connector.s4_ldap_partitions:
						result = s4connector._s4__search_s4(
								base,
								ldap.SCOPE_SUBTREE,
								univention.s4connector.s4.compatible_modstring(s4_filter),
								attrlist=(s4_RR_attr,),
								show_deleted=False)

						if result:
							## We only need the SOA dn here
							s4dn_utf16_le = 'DC=@,' + result[0][0]
							break
				else:
					## identify position by parent zone name
					target_zone_dn = s4connector.lo.parentDn(dn)
					if s4connector.configRegistry.get('connector/s4/mapping/dns/position') != 'legacy':
						if relativeDomainName.endswith('._msdcs'):
							target_zone_name = '_msdcs.' + ol_zone_name
							target_RR_val = relativeDomainName[:-7]
							_rdn = [s4_RR_attr.upper() + '=' + target_zone_dn] + rdn[2:]
							target_zone_dn = ','.join(_rdn)

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
					## and use its parent as the search base
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
					result = s4connector._s4__search_s4(
							s4_zone_dn,
							ldap.SCOPE_SUBTREE,
							univention.s4connector.s4.compatible_modstring('(&%s(%s=%s))' % (s4_RR_filter, s4_RR_attr, target_RR_val)),
							attrlist=('dn',),
							show_deleted=False)
					if result:
						s4dn_utf16_le = result[0][0]

				if s4dn_utf16_le: # no referral, so we've got a valid result
					s4dn = univention.s4connector.s4.encode_attrib(s4dn_utf16_le)
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: got s4dn %s" % (s4dn,))
					s4pos2 = len(univention.s4connector.s4.explode_unicode_dn(s4dn)[0])
					if dn_key == 'olddn' or (dn_key == 'dn' and not 'olddn' in obj):
						## Cases: ("delete") or ("add" but exists already)
						newdn = s4dn
					else:
						## Case: "moved" (?)
						s4dn = s4dn[:s4pos2] + dn[pos2:]
						## The next line looks wrong to me: the source DN is a UCS dn here..
						## But this is just like samaccountname_dn_mapping does it:
						newdn = s4dn.lower().replace(s4connector.lo_s4.base.lower(), s4connector.lo.base.lower())					
						ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: move case newdn=%s" % newdn)
				else:
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: target object not found")
					if s4_zone_dn:
						## At least we found the zone
						zone_dn = s4_zone_dn
						relativeDomainName = target_RR_val
					else:
						## Ok, it's a new object without existing parent zone in S4 (probably this object itself is a soa/zone), so propose an S4 DN for it:
						zone_dn = 'DC=%s,%s' % (ol_zone_name, s4connector.property['dns'].con_default_dn)
					newdn = 'DC=%s,%s' % (relativeDomainName, zone_dn)

			else:
				# get the object to read the s4_RR_attr in S4 and use it as name
				# we have no fallback here, the given dn must be found in S4 or we've got an error
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: got an S4-Object")
				i = 0
				
				while ( not s4_RR_val ): # in case of olddn this is already set
					i = i + 1
					search_dn = obj.get('deleted_dn', dn)
					try:
						s4_RR_val = univention.s4connector.s4.encode_attrib(
							s4connector.lo_s4.lo.search_ext_s(univention.s4connector.s4.compatible_modstring(search_dn), ldap.SCOPE_BASE,
											s4_RR_filter, [s4_RR_attr]) [0][1][s4_RR_attr][0])
						ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: got %s from S4" % s4_RR_attr)
					except ldap.NO_SUCH_OBJECT: # S4 may need time
						if i > 5:
							raise
						time.sleep(1) # S4 may need some time...

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
					## could use a specific LDAP filter here, but not necessary:
					# ol_oc_filter = '(&(objectClass=dNSZone)(|(univentionObjectType=dns/forward_zone)(univentionObjectType=dns/reverse_zone)))'
				elif 'dnsNode' in s4_ocs:
					## identify position of the parent zone
					s4pos = string.find(rdn[1], '=')
					target_zone_name = rdn[1][s4pos+1:]
					target_zone_dn = s4connector.lo_s4.parentDn(dn)
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: get dns_dn_mapping for %s" % target_zone_dn)
					if s4connector.configRegistry.get('connector/s4/mapping/dns/position') != 'legacy':
						if target_zone_name.startswith('_msdcs.'):
							target_zone_name = target_zone_name[7:]
							target_RR_val += '._msdcs'
							_rdn = [rdn[1][:s4pos+1] + target_zone_name] + rdn[2:]
							target_zone_dn = ','.join(_rdn)

					fake_s4_zone_object = {
						'dn': target_zone_dn,
						'attributes': {
							'objectClass': ['top', 'dnsZone'],
							'dc': [target_zone_name],
						},
						}
					ol_zone_object = dns_dn_mapping(s4connector, fake_s4_zone_object, dn_mapping_stored, isUCSobject)
					## and use that as the search base
					ol_zone_dn = ol_zone_object['dn']
					base = ol_zone_dn
					ol_search_attr = ol_RR_attr
					## could use a specific LDAP filter here, but not necessary:
					# ol_oc_filter = '(&(objectClass=dNSZone)(!(|(univentionObjectType=dns/forward_zone)(univentionObjectType=dns/reverse_zone))))'

				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: UCS filter: (&%s(%s=%s))" % (ol_oc_filter, ol_search_attr, target_RR_val))
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: UCS base: %s" % (base,))
				try:
					ucsdn_result = s4connector.search_ucs(filter=u'(&%s(%s=%s))' % (ol_oc_filter, ol_search_attr, target_RR_val),
								   base=base, scope='sub', attr=('dn',))
				except univention.admin.uexceptions.noObject:
					ucsdn_result = None

				try:
					ucsdn = ucsdn_result[0][0]
				except (IndexError, TypeError):
					ucsdn = None
					
				ud.debug(ud.LDAP, ud.ALL, "dns_dn_mapping: Found ucsdn: %s" % ucsdn)
				if ucsdn and (dn_key == 'olddn' or (dn_key == 'dn' and not 'olddn' in obj)):
					## Cases: ("delete") or ("add" but exists already)
					newdn = ucsdn
					ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: newdn is ucsdn")
				else:
					## Cases: (Target not found) or/and ("moved" (?))
					## Ok, it's a new object, so propose a S4 DN for it:
					if ol_zone_dn:
						## At least we found the zone
						zone_dn = ol_zone_dn
						s4_RR_val = target_RR_val
					else:
						## Fallback, e.g. for new zones
						zone_dn = 'zoneName=%s,%s' % (target_zone_name, s4connector.property['dns'].ucs_default_dn)
					if '@' == s4_RR_val:
						newdn = zone_dn
					elif 'dnsZone' in s4_ocs:
						## Hmm, is it ok to map it to the same as '@'?
						newdn = zone_dn
					else:
						newdn = 'relativeDomainName=%s,%s' % (s4_RR_val, zone_dn)

					if not (dn_key == 'olddn' or (dn_key == 'dn' and not 'olddn' in obj)):
						## Case: "moved" (?)
						ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: move case newdn=%s" % newdn)

			try:
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: mapping for key '%s':" % dn_key)
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: source DN: %s" % dn)
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: mapped DN: %s" % newdn)
			except: # FIXME: which exception is to be caught?
				ud.debug(ud.LDAP, ud.INFO, "dns_dn_mapping: dn-print failed")

			obj[dn_key]=newdn

	return obj

''' HELPER functions '''
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
	# split zone
	dn=ldap.explode_dn(dn)

	# split the DC= from the zoneName
	zoneName=string.join(dn[1].split('=')[1:], '=')
	relativeDomainName=string.join(dn[0].split('=')[1:], '=')

	return (zoneName, relativeDomainName)

def __split_ol_dNSZone_dn(dn, objectclasses):
	dn=ldap.explode_dn(dn)
	relativeDomainName = None
	if dn[0].lower().startswith('zonename'):
		zoneName = string.join(dn[0].split('=')[1:], '=')
		if 'dnsNode' in objectclasses:
			relativeDomainName = '@'
		elif 'dnsZone' in objectclasses:
			## make S4 dnsZone containers distinguishable from SOA records
			relativeDomainName = zoneName
	elif dn[1].lower().startswith('zonename'):
		zoneName = string.join(dn[1].split('=')[1:], '=')
		relativeDomainName = string.join(dn[0].split('=')[1:], '=')
	else:
		ud.debug(ud.LDAP, ud.WARN, 'Failed to get zone name for object %s' % (object['dn']))
		zoneName = None
	return (zoneName, relativeDomainName)

def __create_s4_forward_zone(s4connector, zone_dn):
	al=[]
	al.append(('objectClass', ['top', 'dnsZone']))

	ud.debug(ud.LDAP, ud.INFO, '_dns_zone_forward_con_create: dn: %s' % zone_dn)
	ud.debug(ud.LDAP, ud.INFO, '_dns_zone_forward_con_create: al: %s' % al)
	s4connector.lo_s4.lo.add_s(zone_dn, al)

def __create_s4_forward_zone_soa(s4connector, soa_dn):
	al=[]
	al.append(('objectClass', ['top', 'dnsNode']))
	al.append(('dc', ['@']))

	s4connector.lo_s4.lo.add_s(soa_dn, al)

def __create_s4_dns_node(s4connector, dnsNodeDn, relativeDomainNames, dnsRecords):
	al=[]

	al.append(('objectClass', ['top', 'dnsNode']))
	al.append(('dc', relativeDomainNames))
	al.append(('dnsRecord', dnsRecords))

	ud.debug(ud.LDAP, ud.INFO, '__create_s4_dns_node: dn: %s' % dnsNodeDn)
	ud.debug(ud.LDAP, ud.INFO, '__create_s4_dns_node: al: %s' % al)
	s4connector.lo_s4.lo.add_s(dnsNodeDn, al)

''' Pack and unpack DNS records by using the
	Samba NDR functions
'''
def __pack_aRecord(object, dnsRecords):
	# add aRecords

	#IPv4
	for a in object['attributes'].get('aRecord', []):
		a=univention.s4connector.s4.compatible_modstring(a)
		a_record=ARecord(a)
		dnsRecords.append(ndr_pack(a_record))

	#IPv6
	for a in object['attributes'].get('aAAARecord', []):
		a=univention.s4connector.s4.compatible_modstring(a)
		a_record=AAAARecord(a)
		dnsRecords.append(ndr_pack(a_record))

def __unpack_aRecord(object):
	a=[]
	dnsRecords=object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_A or ndrRecord.wType == dnsp.DNS_TYPE_AAAA:
			a.append(ndrRecord.data)
	return a

def __pack_soaRecord(object, dnsRecords):
	soaRecord=object['attributes'].get('sOARecord', [None])[0]
	if soaRecord:
		soaRecord=univention.s4connector.s4.compatible_modstring(soaRecord)
		soa=soaRecord.split(' ')
		mname=soa[0]
		rname=soa[1]
		serial=int(soa[2])
		refresh=int(soa[3])
		retry=int(soa[4])
		expire=int(soa[5])
		ttl=int(soa[6])
		soa_record=SOARecord(mname=mname, rname=rname, serial=serial, refresh=refresh, retry=retry, expire=expire, minimum=3600, ttl=ttl)

		dnsRecords.append(ndr_pack(soa_record))

def __unpack_soaRecord(object):
	soa={}
	dnsRecords=object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_SOA:
			soa['mname']=ndrRecord.data.mname
			soa['rname']=ndrRecord.data.rname
			soa['serial']=str(ndrRecord.data.serial)
			soa['refresh']=str(ndrRecord.data.refresh)
			soa['retry']=str(ndrRecord.data.retry)
			soa['expire']=str(ndrRecord.data.expire)
			soa['minimum']=str(ndrRecord.data.minimum)
			soa['ttl']=str(ndrRecord.dwTtlSeconds)
	return soa

def __pack_nsRecord(object, dnsRecords):
	for nSRecord in object['attributes'].get('nSRecord', []):
		nSRecord=univention.s4connector.s4.compatible_modstring(nSRecord)
		a_record=NSRecord(nSRecord)
		dnsRecords.append(ndr_pack(a_record))

def __unpack_nsRecord(object):
	ns=[]
	dnsRecords=object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_NS:
			ns.append(__append_dot(ndrRecord.data))
	return ns

def __pack_mxRecord(object, dnsRecords):
	for mXRecord in object['attributes'].get('mXRecord', []):
		if mXRecord:
			ud.debug(ud.LDAP, ud.INFO, '__pack_mxRecord: %s' % mXRecord)
			mXRecord=univention.s4connector.s4.compatible_modstring(mXRecord)
			mx=mXRecord.split(' ')
			priority=mx[0]
			name=mx[1]
			mx_record=MXRecord(name, int(priority))
			dnsRecords.append(ndr_pack(mx_record))
			ud.debug(ud.LDAP, ud.INFO, '__pack_mxRecord: %s' % ndr_pack(mx_record))

def __unpack_mxRecord(object):
	mx=[]
	dnsRecords=object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_MX:
			mx.append( [str(ndrRecord.data.wPriority), __append_dot(ndrRecord.data.nameTarget)] )
	return mx

def __pack_cName(object, dnsRecords):
	for c in object['attributes'].get('cNAMERecord', []):
		c=univention.s4connector.s4.compatible_modstring(__remove_dot(c))
		c_record=CName(c)
		dnsRecords.append(ndr_pack(c_record))

def __unpack_cName(object):
	c=[]
	dnsRecords=object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_CNAME:
			c.append(__append_dot(ndrRecord.data))
	return c

def __pack_sRVrecord(object, dnsRecords):
	for srvRecord in object['attributes'].get('sRVRecord', []):
		srvRecord=univention.s4connector.s4.compatible_modstring(srvRecord)
		srv=srvRecord.split(' ')
		priority=int(srv[0])
		weight=int(srv[1])
		port=int(srv[2])
		target=__remove_dot(srv[3])
		s=SRVRecord(target, port, priority, weight)
		dnsRecords.append(ndr_pack(s))

def __unpack_sRVrecord(object):
	srv=[]
	dnsRecords=object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_SRV:
			srv.append([str(ndrRecord.data.wPriority), str(ndrRecord.data.wWeight), str(ndrRecord.data.wPort), __append_dot(ndrRecord.data.nameTarget)])
	return srv

def __pack_ptrRecord(object, dnsRecords):
	for ptr in object['attributes'].get('pTRRecord', []):
		ptr=univention.s4connector.s4.compatible_modstring(__remove_dot(ptr))
		ptr_record=PTRRecord(ptr)
		dnsRecords.append(ndr_pack(ptr_record))

def __unpack_ptrRecord(object):
	ptr=[]
	dnsRecords=object['attributes'].get('dnsRecord', [])
	for dnsRecord in dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_PTR:
			ptr.append(__append_dot(ndrRecord.data))
	return ptr

def __get_s4_msdcs_soa(s4connector, zoneName):
	''' Required to keep the SOA serial numbers in sync
	'''
	func_name = sys._getframe().f_code.co_name
	_d=ud.function(func_name)

	msdcs_obj = {}
	s4_filter = '(&(objectClass=dnsZone)(DC=%s))' % ('_msdcs.%s' % zoneName,)
	ud.debug(ud.LDAP, ud.INFO, "%s: search _msdcs in S4" % func_name)
	msdcs_obj = {}
	for base in s4connector.s4_ldap_partitions:
		resultlist = s4connector._s4__search_s4(
				base,
				ldap.SCOPE_SUBTREE,
				univention.s4connector.s4.compatible_modstring(s4_filter),
				show_deleted=False)

		if resultlist:
			break
	else:
		ud.debug(ud.LDAP, ud.WARN, "%s: _msdcs sub-zone for %s not found in S4" % (func_name, zoneName))
		return

	## We need the SOA here
	msdcs_soa_dn = 'DC=@,' + resultlist[0][0]
	ud.debug(ud.LDAP, ud.INFO, "%s: search DC=@ for _msdcs in S4", func_name)
	resultlist = s4connector._s4__search_s4(
			msdcs_soa_dn,
			ldap.SCOPE_BASE,
			'(objectClass=dnsNode)',
			show_deleted=False)
	if resultlist:
		## __object_from_element not required here
		msdcs_obj = s4connector._s4__object_from_element(resultlist[0])
		return msdcs_obj


''' Create/modify a DNS zone in Samba 4 '''
def s4_zone_create(s4connector, object):
	_d=ud.function('s4_zone_create')

	soa_dn = object['dn']
	zone_dn = s4connector.lo.parentDn(soa_dn)

	zoneName = object['attributes']['zoneName'][0]

	# Create the forward zone in S4 if it does not exist
	try:
		searchResult=s4connector.lo_s4.lo.search_s(zone_dn, ldap.SCOPE_BASE, '(objectClass=*)',['dn'])
	except ldap.NO_SUCH_OBJECT:
		__create_s4_forward_zone(s4connector, zone_dn)
	
	# Create SOA DC=@ object
	old_dnsRecords=[]

	try:
		searchResult=s4connector.lo_s4.lo.search_s(soa_dn, ldap.SCOPE_BASE, '(objectClass=*)')
		if searchResult and searchResult[0][1]:
			old_dnsRecords=searchResult[0][1].get('dnsRecord')
	except ldap.NO_SUCH_OBJECT:
		__create_s4_forward_zone_soa(s4connector, soa_dn)

	dnsRecords=[]

	__pack_nsRecord(object, dnsRecords)

	__pack_soaRecord(object, dnsRecords)

	# The IP address of the DNS forward zone will be used to determine the
	# sysvol share. On a selective replicated DC only a short list of DCs
	# should be returned
	aRecords = s4connector.configRegistry.get('connector/s4/mapping/dns/forward_zone/%s/static/ipv4' % zoneName.lower())
	aAAARecords = s4connector.configRegistry.get('connector/s4/mapping/dns/forward_zone/%s/static/ipv6' % zoneName.lower())
	if aRecords or aAAARecords:
		#IPv4
		if aRecords:
			for a in aRecords.split(' '):
				a=univention.s4connector.s4.compatible_modstring(a)
				a_record=ARecord(a)
				dnsRecords.append(ndr_pack(a_record))

		#IPv6
		if aAAARecords:
			for a in aAAARecords.split(' '):
				a=univention.s4connector.s4.compatible_modstring(a)
				a_record=AAAARecord(a)
				dnsRecords.append(ndr_pack(a_record))
	else:
		__pack_aRecord(object, dnsRecords)

	__pack_mxRecord(object, dnsRecords)

	s4connector.lo_s4.modify(soa_dn, [('dnsRecord', old_dnsRecords, dnsRecords)])

	return True


def s4_zone_msdcs_sync(s4connector, object):
	_d=ud.function('s4_zone_msdcs_sync')

	## Get the current serial number of the OpenLDAP domainname zone
	domainZoneName = object['attributes']['zoneName'][0]
	soaRecord = object['attributes'].get('sOARecord', [None])[0]
	if not soaRecord:
		ud.debug(ud.LDAP, ud.WARN, 's4_zone_msdcs_sync: OL zone %s has no SOA info' % domainZoneName)
		return

	soaRecord=univention.s4connector.s4.compatible_modstring(soaRecord)
	soa=soaRecord.split(' ')
	serial=int(soa[2])

	## lookup the the SOA record of the _msdcs sub-zone for the domainname zone
	msdcs_soa_obj = __get_s4_msdcs_soa(s4connector, domainZoneName)
	if not msdcs_soa_obj:
		return
	msdcs_soa_dn = msdcs_soa_obj['dn']

	dnsRecords=[]
	msdcs_soa={}
	old_dnsRecords=msdcs_soa_obj['attributes'].get('dnsRecord', [])
	found = False
	for dnsRecord in old_dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
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
	if	(
		zoneName == s4connector.configRegistry.get('domainname')
		and s4connector.configRegistry.get('connector/s4/mapping/dns/position') != 'legacy'
		and object['modtype'] == 'modify'
		):
		# Additionally sync serialNumber to _msdcs zone
		result = result and s4_zone_msdcs_sync(s4connector, object)

	return result


''' Delete a forward zone in Samaba 4 '''
def s4_zone_delete(s4connector, object):
	_d=ud.function('s4_zone_delete')

	soa_dn = object['dn']
	zone_dn = s4connector.lo.parentDn(soa_dn)

	try:
		res=s4connector.lo_s4.lo.delete_s(soa_dn)
	except ldap.NO_SUCH_OBJECT:
		pass #the object was already removed
	
	try:
		res=s4connector.lo_s4.lo.delete_s(zone_dn)
	except ldap.NO_SUCH_OBJECT:
		pass #the object was already removed

	return True

def s4_dns_node_base_create(s4connector, object, dnsRecords):
	_d=ud.function('s4_dns_node_base_create')

	relativeDomainNames=object['attributes'].get('relativeDomainName')
	relativeDomainNames=univention.s4connector.s4.compatible_list(relativeDomainNames)
	
	old_dnsRecords=[]

	# Create dnsNode object
	dnsNodeDn=object['dn']
	try:
		searchResult=s4connector.lo_s4.lo.search_s(dnsNodeDn, ldap.SCOPE_BASE, '(objectClass=*)')
		if searchResult and searchResult[0][1]:
			old_dnsRecords=searchResult[0][1].get('dnsRecord')
	except ldap.NO_SUCH_OBJECT:
		__create_s4_dns_node(s4connector, dnsNodeDn, relativeDomainNames, dnsRecords)
	else:
		res=s4connector.lo_s4.modify(dnsNodeDn, [('dnsRecord', old_dnsRecords, dnsRecords)])

	return dnsNodeDn

def s4_dns_node_base_delete(s4connector, object):
	_d=ud.function('s4_dns_node_base_delete')

	relativeDomainNames=object['attributes'].get('relativeDomainName')
	relativeDomainNames=univention.s4connector.s4.compatible_list(relativeDomainNames)

	dnsNodeDn=object['dn']
	try:
		res=s4connector.lo_s4.lo.delete_s(dnsNodeDn)
	except ldap.NO_SUCH_OBJECT:
		pass #the object was already removed
	
	return True


''' Create a host record in Samaba 4 '''
def s4_host_record_create(s4connector, object):
	_d=ud.function('s4_host_record_create')

	dnsRecords=[]

	__pack_aRecord(object, dnsRecords)

	dnsNodeDn=s4_dns_node_base_create(s4connector, object, dnsRecords)

	return True

def ucs_host_record_create(s4connector, object):
	_d=ud.function('ucs_host_record_create')
	ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_create: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	# unpack the host record
	a=__unpack_aRecord(object)

	# Does a host record for this zone already exist?
	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=s4connector_get_superordinate('dns/host_record', s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.host_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		if set(newRecord['a']) != set(a):
			newRecord['a']=a
			newRecord.modify()
		else:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_create: do not modify host record')
	else:
		zoneDN='zoneName=%s,%s' % (zoneName, s4connector.property['dns'].ucs_default_dn)

		ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_create: zoneDN: %s' % zoneDN)
		superordinate=s4connector_get_superordinate('dns/host_record', s4connector.lo, zoneDN)
		ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_create: superordinate: %s' % superordinate)

		position=univention.admin.uldap.position(zoneDN)

		newRecord= univention.admin.handlers.dns.host_record.object(None, s4connector.lo, position, dn=None, superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		newRecord['name']=relativeDomainName
		newRecord['a']=a
		newRecord.create()
	

def ucs_host_record_delete(s4connector, object):
	_d=ud.function('ucs_host_record_delete')
	ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_delete: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=s4connector_get_superordinate('dns/host_record', s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.host_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		newRecord.delete()
	else:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_delete: Object was not found, filter was: ((&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName))

	return True
	

def s4_ptr_record_create(s4connector, object):
	_d=ud.function('s4_ptr_record_create')

	dnsRecords=[]

	__pack_ptrRecord(object, dnsRecords)

	dnsNodeDn=s4_dns_node_base_create(s4connector, object, dnsRecords)

	return True

def ucs_ptr_record_create(s4connector, object):
	_d=ud.function('ucs_ptr_record_create')
	ud.debug(ud.LDAP, ud.INFO, 'ucs_ptr_record_create: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	# unpack the host record
	ptr=__unpack_ptrRecord(object)

	# Does a host record for this zone already exist?
	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=s4connector_get_superordinate('dns/ptr_record', s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.ptr_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		if set(newRecord['ptr_record']) != set(ptr):
			newRecord['ptr_record']=ptr[0]
			newRecord.modify()
		else:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_ptr_record_create: do not modify host record')
	else:
		zoneDN='zoneName=%s,%s' % (zoneName, s4connector.property['dns'].ucs_default_dn)

		superordinate=s4connector_get_superordinate('dns/ptr_record', s4connector.lo, zoneDN)
		ud.debug(ud.LDAP, ud.INFO, 'ucs_ptr_record_create: superordinate: %s' % superordinate)

		position=univention.admin.uldap.position(zoneDN)

		newRecord= univention.admin.handlers.dns.ptr_record.object(None, s4connector.lo, position, dn=None, superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		newRecord['address']=relativeDomainName
		newRecord['ptr_record']=ptr[0]
		newRecord.create()
	

def ucs_ptr_record_delete(s4connector, object):
	_d=ud.function('ucs_ptr_record_delete')
	ud.debug(ud.LDAP, ud.INFO, 'ucs_ptr_record_delete: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=s4connector_get_superordinate('dns/ptr_record', s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.ptr_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		newRecord.delete()
	else:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_ptr_record_delete: Object was not found, filter was: ((&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName))

	return True

def ucs_cname_create(s4connector, object):
	_d=ud.function('ucs_cname_create')
	ud.debug(ud.LDAP, ud.INFO, 'ucs_cname_create: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	# unpack the host record
	c=__unpack_cName(object)

	# Does a host record for this zone already exist?
	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=s4connector_get_superordinate('dns/alias', s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.alias.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		if set(newRecord['cname']) != set(c):
			newRecord['cname']=c[0]
			newRecord.modify()
		else:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_cname_create: do not modify host record')
	else:
		zoneDN='zoneName=%s,%s' % (zoneName, s4connector.property['dns'].ucs_default_dn)

		superordinate=s4connector_get_superordinate('dns/alias', s4connector.lo, zoneDN)
		ud.debug(ud.LDAP, ud.INFO, 'ucs_cname_create: superordinate: %s' % superordinate)

		position=univention.admin.uldap.position(zoneDN)

		newRecord= univention.admin.handlers.dns.alias.object(None, s4connector.lo, position, dn=None, superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		newRecord['name']=relativeDomainName
		newRecord['cname']=c[0]
		newRecord.create()
	

def ucs_cname_delete(s4connector, object):
	_d=ud.function('ucs_cname_delete')
	ud.debug(ud.LDAP, ud.INFO, 'ucs_cname_delete: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=s4connector_get_superordinate('dns/alias', s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.alias.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		newRecord.delete()
	else:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_cname_delete: Object was not found, filter was: ((&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName))

	return True
	
def s4_cname_create(s4connector, object):
	_d=ud.function('s4_cname_create')

	dnsRecords=[]

	__pack_cName(object, dnsRecords)

	dnsNodeDn=s4_dns_node_base_create(s4connector, object, dnsRecords)

def ucs_srv_record_create(s4connector, object):
	_d=ud.function('ucs_srv_record_create')
	ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	# unpack the host record
	srv=__unpack_sRVrecord(object)

	# ucr set connector/s4/mapping/dns/srv_record/_ldap._tcp.test.local/location='100 0 389 foobar.test.local. 100 0 389 foobar2.test.local.'
	ucr_locations = s4connector.configRegistry.get('connector/s4/mapping/dns/srv_record/%s.%s/location' % (relativeDomainName.lower(),zoneName.lower()))
	ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: ucr_locations for connector/s4/mapping/dns/srv_record/%s.%s/location: %s' % (relativeDomainName.lower(),zoneName.lower(),ucr_locations))

	if ucr_locations and ucr_locations.lower() == 'ignore':
		return

	# Does a host record for this zone already exist?
	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=s4connector_get_superordinate('dns/srv_record', s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.srv_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		if ucr_locations:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: do not write SRV record back from S4 to UCS because location of SRV record have been overwritten by UCR')
		else:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: location: %s' % newRecord['location'])
			ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: srv     : %s' % srv)
			srv.sort()
			newRecord['location'].sort()
			if srv != newRecord['location']:
				newRecord['location']=srv
				newRecord.modify()
			else:
				ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: do not modify host record')
	else:
		zoneDN='zoneName=%s,%s' % (zoneName, s4connector.property['dns'].ucs_default_dn)

		superordinate=s4connector_get_superordinate('dns/srv_record', s4connector.lo, zoneDN)
		ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: superordinate: %s' % superordinate)

		position=univention.admin.uldap.position(zoneDN)

		newRecord= univention.admin.handlers.dns.srv_record.object(None, s4connector.lo, position, dn=None, superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		# Make syntax UDM compatible
		parts = univention.admin.handlers.dns.srv_record.unmapName([relativeDomainName])
		if len( parts ) == 3 and parts[ 2 ]:
			msg='SRV create: service="%s" protocol="%s" extension="%s"' % (parts[0], parts[1], parts[2])
		if len( parts ) == 2:
			msg='SRV create: service="%s" protocol="%s"' % (parts[0], parts[1])
		else:
			msg='SRV create: unexpected format, parts: %s' % (parts,)

		ud.debug(ud.LDAP, ud.INFO, msg)
		newRecord['name']=parts
		newRecord['location']=srv
		newRecord.create()
	

def ucs_srv_record_delete(s4connector, object):
	_d=ud.function('ucs_srv_record_delete')
	ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_delete: object: %s' % object)

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=s4connector_get_superordinate('dns/srv_record', s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.srv_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		newRecord.delete()
	else:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_delete: Object was not found, filter was: ((&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName))

	return True


def s4_srv_record_create(s4connector, object):
	_d=ud.function('s4_srv_record_create')

	dnsRecords=[]

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	# ucr set connector/s4/mapping/dns/srv_record/_ldap._tcp.test.local/location='100 0 389 foobar.test.local.'
	# ucr set connector/s4/mapping/dns/srv_record/_ldap._tcp.test.local/location='100 0 389 foobar.test.local. 100 0 389 foobar2.test.local.'
	ucr_locations = s4connector.configRegistry.get('connector/s4/mapping/dns/srv_record/%s.%s/location' % (relativeDomainName.lower(),zoneName.lower()))
	ud.debug(ud.LDAP, ud.INFO, 's4_srv_record_create: ucr_locations for connector/s4/mapping/dns/srv_record/%s.%s/location: %s' % (relativeDomainName.lower(),zoneName.lower(),ucr_locations))
	if ucr_locations:
		if ucr_locations.lower() == 'ignore':
			return
		# Convert ucr variable
		priority=None; weight=None; port=None; target=None
		for v in ucr_locations.split(' '):
			# Check explicit for None, because the int values may be 0
			if priority == None: priority=int(v)
			elif weight == None: weight=int(v)
			elif port == None: port=int(v)
			elif not target: target=__remove_dot(v)
			if priority != None and weight != None and port != None and target:
				ud.debug(ud.LDAP, ud.INFO, 'priority=%d weight=%d port=%d target=%s' % (priority,weight,port,target))
				s=SRVRecord(target, port, priority, weight)
				dnsRecords.append(ndr_pack(s))
				priority=None; weight=None; port=None; target=None

	else:
		__pack_sRVrecord(object, dnsRecords)

	dnsNodeDn=s4_dns_node_base_create(s4connector, object, dnsRecords)

	
def ucs_zone_create(s4connector, object, dns_type):
	_d=ud.function('ucs_zone_create')

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	# create the zone when the dc=@ object has been created
	if relativeDomainName != '@':
		ud.debug(ud.LDAP, ud.INFO, "ucs_zone_create: ignoring DC=%s object" % (relativeDomainName,))
		return

	ns=__unpack_nsRecord(object)

	soa=__unpack_soaRecord(object)

	a=__unpack_aRecord(object)

	mx=__unpack_mxRecord(object)

	if	(
		zoneName == s4connector.configRegistry.get('domainname')
		and s4connector.configRegistry.get('connector/s4/mapping/dns/position') != 'legacy'
		and object['modtype'] == 'modify'
		):
		# Determine max of serialNumber from _msdcs zone
		msdcs_soa_obj = __get_s4_msdcs_soa(s4connector, zoneName)
		if msdcs_soa_obj:
			msdcs_soa = __unpack_soaRecord(msdcs_soa_obj)
			soa['serial'] = str(max(int(soa['serial']), int(msdcs_soa['serial'])))
	
	# Does a zone already exist?
	modify = False
	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		if dns_type == 'forward_zone':
			zone= univention.admin.handlers.dns.forward_zone.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=None, attributes=[])
		elif dns_type == 'reverse_zone':
			zone= univention.admin.handlers.dns.reverse_zone.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=None, attributes=[])
		zone.open()
		if set(ns) != set(zone['nameserver']):
			if soa['mname'] not in ns:
				ns.insert(0, soa['mname'])
			zone['nameserver'] = ns
			modify = True
		if soa['rname'].replace('.', '@', 1) != zone['contact'].rstrip('.'):
			zone['contact'] = soa['rname'].replace('.', '@', 1)
			modify = True
		if long(soa['serial']) != long(zone['serial']):
			zone['serial'] = soa['serial']
			modify = True
		for k in ['refresh', 'retry', 'expire', 'ttl']:
			if long(soa[k]) != _unixTimeInverval2seconds(zone[k]):
				zone[k] = unmapUNIX_TimeInterval(soa[k])
				modify = True
		if dns_type == 'forward_zone':
			# The IP address of the DNS forward zone will be used to determine the
			# sysvol share. On a selective replicated DC only a short list of DCs
			# should be returned
			aRecords = s4connector.configRegistry.get('connector/s4/mapping/dns/forward_zone/%s/static/ipv4' % zoneName.lower())
			aAAARecords = s4connector.configRegistry.get('connector/s4/mapping/dns/forward_zone/%s/static/ipv6' % zoneName.lower())
			if not aRecords and not  aAAARecords:
				if set(a) != set(zone['a']):
					zone['a'] = a
					modify = True
			if mx:
				mapMX=lambda m: '%s %s' % (m[0], m[1])
				if set(map(mapMX,mx)) != set(map(mapMX,zone['mx'])):
					zone['mx'] = mx
					modify = True
		if modify:
			zone.modify()
	else:
		position=univention.admin.uldap.position( s4connector.property['dns'].ucs_default_dn )

		if dns_type == 'forward_zone':
			zone= univention.admin.handlers.dns.forward_zone.object(None, s4connector.lo, position, dn=None, superordinate=None, attributes=[])
			name_key = 'zone'
		elif dns_type == 'reverse_zone':
			zone= univention.admin.handlers.dns.reverse_zone.object(None, s4connector.lo, position, dn=None, superordinate=None, attributes=[])
			name_key = 'subnet'
			zoneName = univention.admin.handlers.dns.reverse_zone.unmapSubnet(zoneName)
		zone.open()
		zone[name_key]=zoneName
		if soa['mname'] not in ns:
			ns.insert(0, soa['mname'])
		zone['nameserver']=ns
		zone['contact']=soa['rname'].replace('.', '@', 1)
		zone['serial']=soa['serial']
		zone['refresh']=[ soa['refresh'] ]	## complex UDM syntax
		zone['retry']=[ soa['retry'] ]		## complex UDM syntax
		zone['expire']=[ soa['expire'] ]	## complex UDM syntax
		zone['ttl']=[ soa['ttl'] ]			## complex UDM syntax
		if dns_type == 'forward_zone':
			zone['a']=a
			zone['mx']=mx
		zone.create()

		

def ucs_zone_delete(s4connector, object, dns_type):
	_d=ud.function('ucs_zone_delete')

	zoneName = object['attributes']['zoneName'][0]
	relativeDomainName = object['attributes']['relativeDomainName'][0]

	if relativeDomainName != '@':
		ud.debug(ud.LDAP, ud.INFO, "ucs_zone_delete: ignoring DC=%s object" % (relativeDomainName,))
		return

	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		if dns_type == 'forward_zone':
			zone= univention.admin.handlers.dns.forward_zone.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=None, attributes=[], update_zone=False)
		elif dns_type == 'reverse_zone':
			zone= univention.admin.handlers.dns.reverse_zone.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=None, attributes=[], update_zone=False)
		zone.open()
		zone.delete()

	

def _identify_dns_ucs_object(s4connector, object):
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
	return None

def _identify_dns_con_object(s4connector, object):
	_d=ud.function('_identify_dns_con_object')

	if object.get('attributes'):
		oc=object['attributes'].get('objectClass')
		dc=object['attributes'].get('dc')
		if oc and 'dnsZone' in oc:
			# forward or reverse zone
			if dc and dc[0].endswith('in-addr.arpa'):
				return 'reverse_zone'
			else:
				return 'forward_zone'
		if oc and 'dnsNode' in oc:
			if dc and dc[0] == '@':
				zone_type='forward_zone'
				split_dn=object['dn'].split(',')[1:]
				for rdn in split_dn:
					rdn=rdn.lower()
					if rdn.startswith('dc=') and rdn.endswith('in-addr.arpa'):
						zone_type='reverse_zone'
						break
				return zone_type
				
			else:
				dnsRecords=object['attributes'].get('dnsRecord')
				if not dnsRecords:
					return None

				dns_types=set()
				for dnsRecord in dnsRecords:
					dnsRecord=dnsRecord.encode('latin1')
					dnsRecord_DnssrvRpcRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
					dns_types.add(dnsRecord_DnssrvRpcRecord.wType)

				if dnsp.DNS_TYPE_PTR in dns_types:
					return 'ptr_record'
				elif dnsp.DNS_TYPE_CNAME in dns_types:
					return 'alias'
				elif dnsp.DNS_TYPE_SRV in dns_types:
					return 'srv_record'
				elif set((dnsp.DNS_TYPE_A, dnsp.DNS_TYPE_AAAA)) & dns_types:
					return 'host_record'
				
	return None
	

def ucs2con (s4connector, key, object):
	_d=ud.function('dns: ucs2con')

	dns_type=_identify_dns_ucs_object(s4connector, object)
	
	if not dns_type:
		# unknown object -> ignore
		ud.debug(ud.LDAP, ud.INFO, 'dns ucs2con: Ignore unkown dns object: %s' % object['dn'])
		return True

	ud.debug(ud.LDAP, ud.INFO, 'dns ucs2con: Object (%s) is of type %s' % (object['dn'], dns_type))

	## At this point dn_mapping_function already has converted object['dn'] from ucs to con
	## But since there is no attribute mapping defined for DNS, the object attributes still
	## are the ones from UCS.
	## We can only get the mapped zone_name from the DN here:

	(zoneName, relativeDomainName) = __split_s4_dnsNode_dn(object['dn'])
	object['attributes']['zoneName'] = [zoneName]
	relativeDomainName=univention.s4connector.s4.compatible_list([relativeDomainName])[0]
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

	return True

def con2ucs (s4connector, key, object):
	_d=ud.function('dns: con2ucs')

	ud.debug(ud.LDAP, ud.INFO, 'dns con2ucs: Object (%s): %s' % (object['dn'], object))
	
	dns_type=_identify_dns_con_object(s4connector, object)

	if not dns_type:
		# unknown object -> ignore
		ud.debug(ud.LDAP, ud.INFO, 'dns con2ucs: Ignore unkown dns object: %s' % object['dn'])
		return True

	ud.debug(ud.LDAP, ud.INFO, 'dns con2ucs: Object (%s) is from type %s' % (object['dn'], dns_type))

	## At this point dn_mapping_function already has converted object['dn'] from con to ucs
	## But since there is no attribute mapping defined for DNS, the object attributes still
	## are the ones from Samba.
	## We can only get the mapped zone_name from the DN here:

	(zoneName, relativeDomainName) = __split_ol_dNSZone_dn(object['dn'], object['attributes']['objectClass'])
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
			ucs_ptr_record_create(s4connector, object)
		# ignore move
	elif dns_type == 'alias':
		if object['modtype'] in ['add', 'modify']:
			ucs_cname_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			ucs_cname_create(s4connector, object)
		# ignore move
	elif dns_type == 'srv_record':
		if object['modtype'] in ['add', 'modify']:
			ucs_srv_record_create(s4connector, object)
		elif object['modtype'] in ['delete']:
			ucs_srv_record_delete(s4connector, object)
		# ignore move
	if dns_type in ['forward_zone', 'reverse_zone']:
		if object['modtype'] in ['add', 'modify']:
			ucs_zone_create(s4connector, object, dns_type)
		elif object['modtype'] in ['delete']:
			ucs_zone_delete(s4connector, object, dns_type)
		# ignore move

	return True

'''
	Override the identify function for dns/dns.py otherwise we 
	don't get one mapping for all dns childmodules.
	Be careful, this function will be called for nearly every 
	object.
'''
def identify(dn, attr, canonical=0):
	_d=ud.function('dns: identify')
	
	return  univention.admin.handlers.dns.forward_zone.identify(dn, attr) or\
			univention.admin.handlers.dns.reverse_zone.identify(dn, attr) or\
			univention.admin.handlers.dns.alias.identify(dn, attr) or\
			univention.admin.handlers.dns.host_record.identify(dn, attr) or\
			univention.admin.handlers.dns.srv_record.identify(dn, attr) or\
			univention.admin.handlers.dns.ptr_record.identify(dn, attr) 
 
'''
	Because the dns/dns.py identify function has been overwritten
	we have to use our own get_superordinate function. Otherwise
	identifyOne in udm will return two results
'''
def s4connector_get_superordinate(module, lo, dn):
	super_module = univention.admin.modules.superordinate( module )
	if super_module:
		while dn:
			attr = lo.get( dn )
			for mod in  univention.admin.modules.identify( dn, attr ):
				if mod == super_module:
					return univention.admin.objects.get( super_module, None, lo, None, dn )
			dn = lo.parentDn( dn )
	return None
