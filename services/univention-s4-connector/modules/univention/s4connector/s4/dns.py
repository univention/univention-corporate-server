#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  dns helper functions
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

import ldap, string
import univention.debug2 as ud
import univention.s4connector.s4
import univention.admin.uldap
                                                                                                                                                                                                   
from samba.dcerpc import dnsp                                                                                                                                                                      
from samba.ndr import ndr_print                                                                                                                                                                    
from samba.ndr import ndr_pack
from samba.ndr import ndr_unpack                                                                                                                                                                   
import binascii                                                                                                                                                                                    

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

import univention.admin.handlers
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.alias
import univention.admin.handlers.dns.host_record
import univention.admin.handlers.dns.srv_record
import univention.admin.handlers.dns.reverse_zone
import univention.admin.handlers.dns.ptr_record

''' HELPER functions '''
def __get_zone_name(object):
	zoneName=object['attributes'].get('zoneName')
	if not zoneName:
		ud.debug(ud.LDAP, ud.WARN, 'Failed to get zone name for object %s' % (object['dn']))
		raise 
	return zoneName

def __create_default_s4_zone_dn(s4connector, object):
	zoneName=__get_zone_name(object)
	dn='DC=%s,%s' % (zoneName[0], s4connector.property['dns'].con_default_dn)
	return (dn, zoneName)

def __create_s4_forward_zone(s4connector, zoneDn, zoneName):
	al=[]
	al.append(('objectClass', ['top', 'dnsZone']))
	al.append(('DC', univention.s4connector.s4.compatible_list(zoneName)))

	ud.debug(ud.LDAP, ud.INFO, '_dns_zone_forward_con_create: dn: %s' % zoneDn)
	ud.debug(ud.LDAP, ud.INFO, '_dns_zone_forward_con_create: al: %s' % al)
	s4connector.lo_s4.lo.add_s(zoneDn, al)

def __create_s4_forward_zone_at(s4connector, zoneDnAt, zoneName):
	al=[]
	al.append(('objectClass', ['top', 'dnsNode']))
	al.append(('dc', ['@']))

	s4connector.lo_s4.lo.add_s(zoneDnAt, al)

def __create_s4_dns_node(s4connector, dnsNodeDn, relativeDomainNames, dnsRecords):
	al=[]

	al.append(('objectClass', ['top', 'dnsNode']))
	al.append(('dc', relativeDomainNames))
	al.append(('dnsRecord', dnsRecords))

	s4connector.lo_s4.lo.add_s(dnsNodeDn, al)

''' Pack and unpack DNS records by using the
	Samba NDR functions
'''
def __pack_aRecord(object, dnsRecords):
	# add aRecords
	for a in object['attributes'].get('aRecord', []):
		a=univention.s4connector.s4.compatible_modstring(a)
		a_record=ARecord(a)
		dnsRecords.append(ndr_pack(a_record))

def __unpack_aRecord(object):
	a=[]
	dnsRecords=object['attributes'].get('dnsRecord')
	for dnsRecord in dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_A or ndrRecord.wType == dnsp.DNS_TYPE_AAAA:
			a.append(ndrRecord.data)
	return a

def __pack_soaRecord(object, dnsRecords):
	soaRecord=object['attributes'].get('sOARecord', [])[0]
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
	dnsRecords=object['attributes'].get('dnsRecord')
	for dnsRecord in dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_SOA:
			soa['mname']=ndrRecord.data.mname
			soa['rname']=ndrRecord.data.mname
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
	dnsRecords=object['attributes'].get('dnsRecord')
	for dnsRecord in dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_NS:
			ns.append(ndrRecord.data)
	return ns

def __pack_cName(object, dnsRecords):
	for c in object['attributes'].get('cNAMERecord', []):
		c=univention.s4connector.s4.compatible_modstring(c)
		c_record=CName(c)
		dnsRecords.append(ndr_pack(c_record))

def __unpack_cName(object):
	c=[]
	dnsRecords=object['attributes'].get('dnsRecord')
	for dnsRecord in dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_CNAME:
			c.append(ndrRecord.data)
	return c

def __pack_sRVrecord(object, dnsRecords):
	for srvRecord in object['attributes'].get('sRVRecord', []):
		srvRecord=univention.s4connector.s4.compatible_modstring(srvRecord)
		srv=srvRecord.split(' ')
		priority=int(srv[0])
		weight=int(srv[1])
		port=int(srv[2])
		target=srv[3]
		s=SRVRecord(target, port, priority, weight)
		dnsRecords.append(ndr_pack(s))

def __unpack_sRVrecord(object):
	srv=[]
	dnsRecords=object['attributes'].get('dnsRecord')
	for dnsRecord in dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_SRV:
			srv.append([str(ndrRecord.data.wPriority), str(ndrRecord.data.wWeight), str(ndrRecord.data.wPort), ndrRecord.data.nameTarget])
	return srv

def __pack_ptrRecord(object, dnsRecords):
	for ptr in object['attributes'].get('pTRRecord', []):
		ptr=univention.s4connector.s4.compatible_modstring(ptr)
		ptr_record=PTRRecord(ptr)
		dnsRecords.append(ndr_pack(ptr_record))

def __unpack_ptrRecord(object):
	ptr=[]
	dnsRecords=object['attributes'].get('dnsRecord')
	for dnsRecord in dnsRecords:
		dnsRecord=dnsRecord.encode('latin1')
		ndrRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
		if ndrRecord.wType == dnsp.DNS_TYPE_PTR:
			ptr.append(ndrRecord.data)
	return ptr

''' Create a forward zone in Samaba 4 '''
def s4_zone_create(s4connector, object):
	_d=ud.function('s4_zone_create')

	zoneDn, zoneName=__create_default_s4_zone_dn(s4connector, object)
		
	# Create the forward zone in S4 if it does not exist
	try:
		searchResult=s4connector.lo_s4.lo.search_s(zoneDn, ldap.SCOPE_BASE, '(objectClass=*)',['dn'])
	except ldap.NO_SUCH_OBJECT:
		__create_s4_forward_zone(s4connector, zoneDn, zoneName)
	
	# Create @ object
	zoneDnAt='DC=@,%s' % zoneDn

	old_dnsRecords=[]

	try:
		searchResult=s4connector.lo_s4.lo.search_s(zoneDnAt, ldap.SCOPE_BASE, '(objectClass=*)')
		if searchResult and searchResult[0][1]:
			old_dnsRecords=searchResult[0][1].get('dnsRecord')
	except ldap.NO_SUCH_OBJECT:
		__create_s4_forward_zone_at(s4connector, zoneDnAt, zoneName)

	dnsRecords=[]

	__pack_nsRecord(object, dnsRecords)

	__pack_soaRecord(object, dnsRecords)

	__pack_aRecord(object, dnsRecords)

	s4connector.lo_s4.modify(zoneDnAt, [('dnsRecord', old_dnsRecords, dnsRecords)])

	return True


''' Delete a forward zone in Samaba 4 '''
def s4_zone_delete(s4connector, object):
	_d=ud.function('s4_zone_create')

	zoneDn, zoneName=__create_default_s4_zone_dn(s4connector, object)

	zoneDnAt='DC=@,%s' % zoneDn

	try:
		res=s4connector.lo_s4.lo.delete_s(zoneDnAt)
	except ldap.NO_SUCH_OBJECT:
		pass #the object was already removed
	
	try:
		res=s4connector.lo_s4.lo.delete_s(zoneDn)
	except ldap.NO_SUCH_OBJECT:
		pass #the object was already removed

	return True

def s4_dns_node_base_create(s4connector, object, dnsRecords):
	_d=ud.function('s4_dns_node_base_create')

	zoneDn, zoneName=__create_default_s4_zone_dn(s4connector, object)

	relativeDomainNames=object['attributes'].get('relativeDomainName')
	relativeDomainNames=univention.s4connector.s4.compatible_list(relativeDomainNames)
	
	old_dnsRecords=[]

	# Create dnsNode object
	dnsNodeDn='DC=%s,%s' % (relativeDomainNames[0],zoneDn)
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

	zoneDn, zoneName=__create_default_s4_zone_dn(s4connector, object)

	relativeDomainNames=object['attributes'].get('relativeDomainName')
	relativeDomainNames=univention.s4connector.s4.compatible_list(relativeDomainNames)

	dnsNodeDn='DC=%s,%s' % (relativeDomainNames[0],zoneDn)
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

def __split_s4_dn(dn):
	# split zone
	dn=ldap.explode_dn(dn)

	# split the DC= from the zoneName
	zoneName=string.join(dn[1].split('=')[1:], '=')
	relativeDomainName=string.join(dn[0].split('=')[1:], '=')

	return (zoneName, relativeDomainName)

def ucs_host_record_create(s4connector, object):
	_d=ud.function('ucs_host_record_create')
	ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_create: object: %s' % object)

	zoneName, relativeDomainName=__split_s4_dn(object['dn'])

	# unpack the host record
	a=__unpack_aRecord(object)

	# Does a host record for this zone already exist?
	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=univention.admin.objects.get_superordinate('dns/host_record', None, s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.host_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		if set(newRecord['a']) != set(a):
			newRecord['a']=a
			newRecord.modify()
		else:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_host_record_create: do not modify host record')
	else:
		zoneDN='zoneName=%s,%s' % (zoneName, s4connector.property['dns'].ucs_default_dn)

		superordinate=univention.admin.objects.get_superordinate('dns/host_record', None, s4connector.lo, zoneDN)
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

	zoneName, relativeDomainName=__split_s4_dn(object['dn'])

	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=univention.admin.objects.get_superordinate('dns/host_record', None, s4connector.lo, searchResult[0][0])
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

	zoneName, relativeDomainName=__split_s4_dn(object['dn'])

	# unpack the host record
	ptr=__unpack_ptrRecord(object)

	# Does a host record for this zone already exist?
	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=univention.admin.objects.get_superordinate('dns/ptr_record', None, s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.ptr_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		if set(newRecord['ptr']) != set(ptr):
			newRecord['ptr']=ptr
			newRecord.modify()
		else:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_ptr_record_create: do not modify host record')
	else:
		zoneDN='zoneName=%s,%s' % (zoneName, s4connector.property['dns'].ucs_default_dn)

		superordinate=univention.admin.objects.get_superordinate('dns/ptr_record', None, s4connector.lo, zoneDN)
		ud.debug(ud.LDAP, ud.INFO, 'ucs_ptr_record_create: superordinate: %s' % superordinate)

		position=univention.admin.uldap.position(zoneDN)

		newRecord= univention.admin.handlers.dns.ptr_record.object(None, s4connector.lo, position, dn=None, superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		newRecord['name']=relativeDomainName
		newRecord['ptr']=ptr
		newRecord.create()
	

def ucs_ptr_record_delete(s4connector, object):
	_d=ud.function('ucs_ptr_record_delete')
	ud.debug(ud.LDAP, ud.INFO, 'ucs_ptr_record_delete: object: %s' % object)

	zoneName, relativeDomainName=__split_s4_dn(object['dn'])

	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=univention.admin.objects.get_superordinate('dns/ptr_record', None, s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.ptr_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		newRecord.delete()
	else:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_ptr_record_delete: Object was not found, filter was: ((&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName))

	return True

def ucs_cname_create(s4connector, object):
	_d=ud.function('ucs_cname_create')
	ud.debug(ud.LDAP, ud.INFO, 'ucs_cname_create: object: %s' % object)

	zoneName, relativeDomainName=__split_s4_dn(object['dn'])

	# unpack the host record
	c=__unpack_cName(object)

	# Does a host record for this zone already exist?
	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=univention.admin.objects.get_superordinate('dns/alias', None, s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.alias.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		if set(newRecord['c']) != set(c):
			newRecord['cname']=c
			newRecord.modify()
		else:
			ud.debug(ud.LDAP, ud.INFO, 'ucs_cname_create: do not modify host record')
	else:
		zoneDN='zoneName=%s,%s' % (zoneName, s4connector.property['dns'].ucs_default_dn)

		superordinate=univention.admin.objects.get_superordinate('dns/alias', None, s4connector.lo, zoneDN)
		ud.debug(ud.LDAP, ud.INFO, 'ucs_cname_create: superordinate: %s' % superordinate)

		position=univention.admin.uldap.position(zoneDN)

		newRecord= univention.admin.handlers.dns.alias.object(None, s4connector.lo, position, dn=None, superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		newRecord['name']=relativeDomainName
		newRecord['cname']=c
		newRecord.create()
	

def ucs_cname_delete(s4connector, object):
	_d=ud.function('ucs_cname_delete')
	ud.debug(ud.LDAP, ud.INFO, 'ucs_cname_delete: object: %s' % object)

	zoneName, relativeDomainName=__split_s4_dn(object['dn'])

	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=univention.admin.objects.get_superordinate('dns/alias', None, s4connector.lo, searchResult[0][0])
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

	zoneName, relativeDomainName=__split_s4_dn(object['dn'])

	# unpack the host record
	srv=__unpack_sRVrecord(object)

	# Does a host record for this zone already exist?
	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=univention.admin.objects.get_superordinate('dns/srv_record', None, s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.srv_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
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

		superordinate=univention.admin.objects.get_superordinate('dns/srv_record', None, s4connector.lo, zoneDN)
		ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_create: superordinate: %s' % superordinate)

		position=univention.admin.uldap.position(zoneDN)

		newRecord= univention.admin.handlers.dns.srv_record.object(None, s4connector.lo, position, dn=None, superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		newRecord['name']=relativeDomainName
		newRecord['location']=srv
		newRecord.create()
	

def ucs_srv_record_delete(s4connector, object):
	_d=ud.function('ucs_srv_record_delete')
	ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_delete: object: %s' % object)

	zoneName, relativeDomainName=__split_s4_dn(object['dn'])

	searchResult=s4connector.lo.search(filter='(&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName), unique=1)
	if len(searchResult) > 0:
		superordinate=univention.admin.objects.get_superordinate('dns/srv_record', None, s4connector.lo, searchResult[0][0])
		newRecord= univention.admin.handlers.dns.srv_record.object(None, s4connector.lo, position=None, dn=searchResult[0][0], superordinate=superordinate, attributes=[], update_zone=False)
		newRecord.open()
		newRecord.delete()
	else:
		ud.debug(ud.LDAP, ud.INFO, 'ucs_srv_record_delete: Object was not found, filter was: ((&(relativeDomainName=%s)(zoneName=%s))' % (relativeDomainName, zoneName))

	return True


def s4_srv_record_create(s4connector, object):                                                                                                                                                     
	_d=ud.function('s4_srv_record_create')

	dnsRecords=[]

	__pack_sRVrecord(object, dnsRecords)

	dnsNodeDn=s4_dns_node_base_create(s4connector, object, dnsRecords)

def ucs_zone_create(s4connector, object, dns_type):
	_d=ud.function('ucs_zone_create')

	zoneName, relativeDomainName=__split_s4_dn(object['dn'])

	# create the zone if the dc=@ object was created
	if relativeDomainName != '@':
		return

	ns=__unpack_nsRecord(object)

	soa=__unpack_soaRecord(object)

	a=__unpack_aRecord(object)

	# Does a zone already exist?
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
		if soa['rname'] != zone['contact']:
			zone['contact'] = soa['rname'].replace('.', '@', 1)
		for k in ['serial', 'refresh', 'retry', 'expire', 'ttl']:
			if set(soa[k]) != set(zone[k]):
				zone[k] = soa[k]
		if set(a) != set(zone['a']):
			zone['a'] = a
	else:
		zoneDN='zoneName=%s,%s' % (zoneName, s4connector.property['dns'].ucs_default_dn)

		position=univention.admin.uldap.position(zoneDN)

		if dns_type == 'forward_zone':
			zone= univention.admin.handlers.dns.forward_zone.object(None, s4connector.lo, position, dn=None, superordinate=None, attributes=[])
		elif dns_type == 'reverse_zone':
			zone= univention.admin.handlers.dns.reverse_zone.object(None, s4connector.lo, position, dn=None, superordinate=None, attributes=[])
		zone.open()
		zone['zone']=zoneName
		if soa['mname'] not in ns:
			ns.insert(0, soa['mname'])
		zone['namesever']=ns
		zone['contact']=soa['rname'].replace('.', '@', 1)
		zone['serial']=soa['serial']
		zone['refresh']=soa['refresh']
		zone['retry']=soa['retry']
		zone['expire']=soa['expire']
		zone['ttl']=soa['ttl']
		zone['a']=a
		zone.create()

		

def ucs_zone_delete(s4connector, objecti, dns_type):
	_d=ud.function('ucs_zone_delete')

	zoneName, relativeDomainName=__split_s4_dn(object['dn'])

	if relativeDomainName == '@':
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
				dns_types=[]
				for dnsRecord in dnsRecords:
					dnsRecord=dnsRecord.encode('latin1')
					dnsRecord_DnssrvRpcRecord=ndr_unpack(dnsp.DnssrvRpcRecord, dnsRecord)
					dns_types.append(dnsRecord_DnssrvRpcRecord.wType)

				if dnsp.DNS_TYPE_PTR in dns_types:
					return 'ptr_record'
				elif dnsp.DNS_TYPE_CNAME in dns_types:
					return 'alias'
				elif dnsp.DNS_TYPE_SRV in dns_types:
					return 'srv_record'
				elif dnsp.DNS_TYPE_A in dns_types or dnsp.DNS_TYPE_AAAA:
					return 'host_record'
				
	return None
	

def ucs2con (s4connector, key, object):
	_d=ud.function('dns: ucs2con')

	dns_type=_identify_dns_ucs_object(s4connector, object)
	
	if not dns_type:
		# unknown object -> ignore
		ud.debug(ud.LDAP, ud.INFO, 'dns ucs2con: Ignore unkown dns object: %s' % object['dn'])
		return True

	ud.debug(ud.LDAP, ud.INFO, 'dns ucs2con: Object (%s) is from type %s' % (object['dn'], dns_type))
		
	if dns_type == 'forward_zone' or dns_type == 'reverse_zone':
		if object['modtype'] in ['add', 'modify']:
			s4_zone_create(s4connector, object)
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
 

