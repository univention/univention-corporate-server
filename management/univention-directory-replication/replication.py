# -*- coding: utf-8 -*-
#
# Univention Directory Replication
#  listener module for Directory replication
#
# Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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
# Univention Directory Listener replication module

# Possible initialization scenarios:
# 1. New slave
#    pull complete database from master
# 2. Master is degraded to slave
#    use existing database

import listener
import os, pwd, types, ldap, ldap.schema, re, time, copy, codecs, base64
import univention_baseconfig, univention.debug

name='replication'
description='LDAP slave replication'
filter='(objectClass=*)' # default filter - may be overwritten later
attributes=[]

slave=0
if listener.baseConfig['ldap/server/type'] == 'slave':
	slave=1

if listener.baseConfig['ldap/slave/filter']:
	filter=listener.baseConfig['ldap/slave/filter']

LDIF_FILE = '/var/lib/univention-directory-replication/failed.ldif'

EXCLUDE_ATTRIBUTES=['subschemaSubentry', 'hasSubordinates', 'entryDN']

# don't use built-in OIDs from slapd
BUILTIN_OIDS=[
	# attributeTypes
	'1.3.6.1.1.4',			# vendorName
	'1.3.6.1.1.5',			# vendorVersion
	'1.3.6.1.4.1.250.1.57',         # labeledURI
	'1.3.6.1.4.1.250.1.32',         # krbName
	'1.3.6.1.4.1.1466.101.119.2',   # dynamicObject
	'1.3.6.1.4.1.1466.101.119.3',   # entryTtl
	'1.3.6.1.4.1.1466.101.119.4',   # dynamicSubtrees
	'1.3.6.1.4.1.1466.101.120.5',	# namingContexts
	'1.3.6.1.4.1.1466.101.120.6',	# altServer
	'1.3.6.1.4.1.1466.101.120.7',	# supportedExtension
	'1.3.6.1.4.1.1466.101.120.13',	# supportedControla
	'1.3.6.1.4.1.1466.101.120.14',	# supportedSASLMechanisms
	'1.3.6.1.4.1.1466.101.120.15',	# supportedLDAPVersion
	'1.3.6.1.4.1.1466.101.120.16',	# ldapSyntaxes (operational)
	'1.3.6.1.4.1.1466.101.120.111',	# extensibleObject
	'1.3.6.1.4.1.4203.1.4.1',	# OpenLDAProotDSE
	'1.3.6.1.4.1.4203.1.3.1',       # entry
	'1.3.6.1.4.1.4203.1.3.2',       # children
	'1.3.6.1.4.1.4203.1.3.3',       # supportedAuthPasswordSchemes
	'1.3.6.1.4.1.4203.1.3.4',       # authPassword
	'1.3.6.1.4.1.4203.1.3.5',	# supportedFeatures
	'1.3.6.1.4.1.4203.666.1.5',     # OpenLDAPaci
	'1.3.6.1.4.1.4203.666.1.6',     # entryUUID
	'1.3.6.1.4.1.4203.666.1.7',     # entryCSN
	'1.3.6.1.4.1.4203.666.1.8',     # saslAuthzTo
	'1.3.6.1.4.1.4203.666.1.9',     # saslAuthzFrom
	'1.3.6.1.4.1.4203.666.1.10',    # monitorContext
	'1.3.6.1.4.1.4203.666.1.11',    # superiorUUID
	'1.3.6.1.4.1.4203.666.1.13',    # namingCSN
	'1.3.6.1.4.1.4203.666.1.23',    # syncreplCookie
	'1.3.6.1.4.1.4203.666.1.25',    # contextCSN
	'1.3.6.1.4.1.4203.666.1.33',    # entryDN
	'1.3.6.1.4.1.4203.666.3.4',     # glue
	'1.3.6.1.4.1.4203.666.3.5',     # syncConsumerSubentry
	'1.3.6.1.4.1.4203.666.3.6',     # syncProviderSubentry
	'2.5.4.0',			# objectClass
	'2.5.4.1',			# aliasedObjectName
	'2.5.4.3',			# cn
	'2.5.4.35',			# userPassword
	'2.5.4.41',			# name
	'2.5.4.49',			# dn
	'2.5.6.0',			# top
	'2.5.6.1',			# alias
	'2.5.17.0',			# subentry
	'2.5.17.2',                     # collectiveAttributeSubentry
	'2.5.18.1',			# createTimestamp
	'2.5.18.2',			# modifyTimestamp
	'2.5.18.3',			# creatorsName
	'2.5.18.4',			# modifiersName
	'2.5.18.5',                     # administrativeRole
	'2.5.18.6',                     # subtreeSpecification
	'2.5.18.7',                     # collectiveExclusions
	'2.5.18.9',			# hasSubordinates
	'2.5.18.10',			# subschemaSubentry
	'2.5.18.12',                    # collectiveAttributeSubentries
	'2.5.20.1',			# subschema
	'2.5.21.1',                     # ditStructureRules
	'2.5.21.2',                     # ditContentRules
	'2.5.21.4',			# matchingRules
	'2.5.21.5',			# attributeTypes
	'2.5.21.6',			# objectClasses
	'2.5.21.7',                     # nameForms
	'2.5.21.8',			# matchingRuleUse
	'2.5.21.9',			# structuralObjectClass
	'1.3.6.1.1.16.4',       	# entryUUID
	'1.3.6.1.4.1.4203.666.11.1.3.0.80',	# olcToolThreads
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.12',	# olcUpdateDN
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.13',	# olcUpdateRef
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.10',	# olcSuffix
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.11',	# olcSyncrepl
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.15',	# olcSubordinate
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.1',	# olcDbDirectory
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.2',	# olcDbIndex
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.3',	# olcDbMode
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.4',	# olcLastMod
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.5',	# olcLimits
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.6',	# olcMaxDerefDepth
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.7',	# olcReplica
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.8',	# olcRootDN
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.9',	# olcRootPW
	'1.3.6.1.4.1.4203.666.11.1.3.0.32',	# olcObjectClasses
	'1.3.6.1.4.1.4203.666.11.1.3.0.33',	# olcObjectIdentifier
	'1.3.6.1.4.1.4203.666.11.1.3.0.30',	# olcModuleLoad
	'1.3.6.1.4.1.4203.666.11.1.3.0.31',	# olcModulePath
	'1.3.6.1.4.1.4203.666.11.1.3.0.36',	# olcPasswordHash
	'1.3.6.1.4.1.4203.666.11.1.3.0.37',	# olcPidFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.9',	# olcBackend
	'1.3.6.1.4.1.4203.666.11.1.3.0.13',	# olcDatabase
	'1.3.6.1.4.1.4203.666.11.1.3.0.34',	# olcOverlay
	'1.3.6.1.4.1.4203.666.11.1.3.0.35',	# olcPasswordCryptSaltFormat
	'1.3.6.1.4.1.4203.666.11.1.3.0.38',	# olcPlugin
	'1.3.6.1.4.1.4203.666.11.1.3.0.39',	# olcPluginLogFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.69',	# olcTLSCACertificatePath
	'1.3.6.1.4.1.4203.666.11.1.3.0.68',	# olcTLSCACertificateFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.61',	# olcSockbufMaxIncoming
	'1.3.6.1.4.1.4203.666.11.1.3.0.60',	# olcSizeLimit
	'1.3.6.1.4.1.4203.666.11.1.3.0.63',	# olcSrvtab
	'1.3.6.1.4.1.4203.666.11.1.3.0.62',	# olcSockbufMaxIncomingAuth
	'1.3.6.1.4.1.4203.666.11.1.3.0.67',	# olcTimeLimit
	'1.3.6.1.4.1.4203.666.11.1.3.0.66',	# olcThreads
	'1.3.6.1.4.1.4203.666.11.1.3.0.27',	# olcLogFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.26',	# olcLocalSSF
	'1.3.6.1.4.1.4203.666.11.1.3.0.21',	# olcIndexSubstrIfMaxLen
	'1.3.6.1.4.1.4203.666.11.1.3.0.20',	# olcIndexSubstrIfMinLen
	'1.3.6.1.4.1.4203.666.11.1.3.0.23',	# olcIndexSubstrAnyStep
	'1.3.6.1.4.1.4203.666.11.1.3.0.22',	# olcIndexSubstrAnyLen
	'1.3.6.1.4.1.4203.666.11.1.3.0.28',	# olcLogLevel
	'1.3.6.1.4.1.4203.666.11.1.3.0.51',	# olcRootDSE
	'1.3.6.1.4.1.4203.666.11.1.3.0.53',	# olcSaslHost
	'1.3.6.1.4.1.4203.666.11.1.3.0.54',	# olcSaslRealm
	'1.3.6.1.4.1.4203.666.11.1.3.0.56',	# olcSaslSecProps
	'1.3.6.1.4.1.4203.666.11.1.3.0.58',	# olcSchemaDN
	'1.3.6.1.4.1.4203.666.11.1.3.0.59',	# olcSecurity
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.11',	# olcDbCacheFree
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.10',	# olcDbShmKey
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.4',	# olcDbNoSync
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.6',	# olcDbIDLcacheSize
	'1.3.6.1.4.1.4203.666.11.1.3.0.18',	# olcIdleTimeout
	'1.3.6.1.4.1.4203.666.11.1.3.0.19',	# olcInclude
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.3',	# olcDbConfig
	'1.3.6.1.4.1.4203.666.11.1.3.0.14',	# olcDefaultSearchBase
	'1.3.6.1.4.1.4203.666.11.1.3.0.15',	# olcDisallows
	'1.3.6.1.4.1.4203.666.11.1.3.0.16',	# olcDitContentRules
	'1.3.6.1.4.1.4203.666.11.1.3.0.17',	# olcGentleHUP
	'1.3.6.1.4.1.4203.666.11.1.3.0.10',	# olcConcurrency
	'1.3.6.1.4.1.4203.666.11.1.3.0.11',	# olcConnMaxPending
	'1.3.6.1.4.1.4203.666.11.1.3.0.12',	# olcConnMaxPendingAuth
	'1.3.6.1.4.1.4203.666.11.1.3.0.43',	# olcReplicaArgsFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.41',	# olcReferral
	'1.3.6.1.4.1.4203.666.11.1.3.0.40',	# olcReadOnly
	'1.3.6.1.4.1.4203.666.11.1.3.0.47',	# olcRequires
	'1.3.6.1.4.1.4203.666.11.1.3.0.46',	# olcReplogFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.45',	# olcReplicationInterval
	'1.3.6.1.4.1.4203.666.11.1.3.0.44',	# olcReplicaPidFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.49',	# olcReverseLookup
	'1.3.6.1.4.1.4203.666.11.1.3.0.48',	# olcRestrict
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.1',	# olcDbCacheSize
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.5',	# olcDbDirtyRead
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.7',	# olcDbLinearIndex
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.2',	# olcDbCheckpoint
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.9',	# olcDbSearchStack
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.8',	# olcDbLockDetect
	'1.3.6.1.4.1.4203.666.11.1.3.0.77',	# olcTLSDHParamFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.74',	# olcTLSRandFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.75',	# olcTLSVerifyClient
	'1.3.6.1.4.1.4203.666.11.1.3.0.72',	# olcTLSCipherSuite
	'1.3.6.1.4.1.4203.666.11.1.3.0.73',	# olcTLSCRLCheck
	'1.3.6.1.4.1.4203.666.11.1.3.0.70',	# olcTLSCertificateFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.71',	# olcTLSCertificateKeyFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.78',	# olcConfigFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.79',	# olcConfigDir
	'1.3.6.1.4.1.4203.666.11.1.3.0.8',	# olcAuthzRegexp
	'1.3.6.1.4.1.4203.666.11.1.3.0.2',	# olcAllows
	'1.3.6.1.4.1.4203.666.11.1.3.0.3',	# olcArgsFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.1',	# olcAccess
	'1.3.6.1.4.1.4203.666.11.1.3.0.6',	# olcAuthIDRewrite
	'1.3.6.1.4.1.4203.666.11.1.3.0.7',	# olcAuthzPolicy
	'1.3.6.1.4.1.4203.666.11.1.3.0.4',	# olcAttributeTypes
	'1.3.6.1.4.1.4203.666.11.1.3.0.5',	# olcAttributeOptions
	# objectClasses
	'2.16.840.1.113730.3.2.6',	# referral
	'2.16.840.1.113730.3.1.34',	# ref (operational)
	'1.3.6.1.4.1.4203.666.11.1.4.0.0',	# olcConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.4',	# olcDatabaseConfig
	'1.3.6.1.4.1.4203.666.11.1.4.2.1.1',	# olcBdbConfig
	'1.3.6.1.4.1.4203.666.11.1.4.2.2.1',	# olcLdifConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.8',	# olcModuleList
	'1.3.6.1.4.1.4203.666.11.1.4.0.5',	# olcOverlayConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.7',	# olcFrontendConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.6',	# olcIncludeFile
	'1.3.6.1.4.1.4203.666.11.1.4.0.1',	# olcGlobal
	'1.3.6.1.4.1.4203.666.11.1.4.0.3',	# olcBackendConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.2',	# olcSchemaConfig
	# UCS 2.0
	'2.5.4.34', #seeAlso
	'0.9.2342.19200300.100.1.1', #userid
	'2.5.4.13',  #description
	'1.3.6.1.1.1.1.1', # gidNumber
	'1.3.6.1.1.1.1.0', #uidNumber
]

class LDIFObject:
	def __init__(self, file):
		self.fp = open(file, 'a')

	def __print_attribute(self, attribute, value):
		pos = len(attribute)+2 # +colon+space
		encode = 0
		if '\n' in value:
			encode = 1
		try:
			if type(value) == type(()):
				(newval,leng)=value
			else:
				newval=value
			newval=newval.encode('ascii')
		except UnicodeError:
			encode = 1
		if encode:
			pos += 1 # value will be base64 encoded, thus two colons
			print >>self.fp, '%s::' % attribute,
			value=base64.encodestring(value).replace('\n', '')
		else:
			print >>self.fp, '%s:' % attribute,

		while value:
			if pos == 1:
				# first column is space
				print >>self.fp, '',
			print >>self.fp, value[0:60-pos]
			value = value[60-pos:]
			pos = 1

	def __new_entry(self, dn):
		self.__print_attribute('dn', dn)
	def __end_entry(self):
		print >>self.fp
		self.fp.flush()
	def __new_section(self):
		pass
	def __end_section(self):
		print >>self.fp, '-'

	def add_s(self, dn, al):
		self.__new_entry(dn)
		self.__print_attribute('changetype', 'add')
		for attr, vals in al:
			for val in vals:
				self.__print_attribute(attr, val)
		self.__end_entry()

	def modify_s(self, dn, ml):
		self.__new_entry(dn)
		self.__print_attribute('changetype', 'modify')
		for type, attr, vals in ml:
			self.__new_section()
			if type == ldap.MOD_REPLACE:
				op = 'replace'
			elif type == ldap.MOD_ADD:
				op = 'add'
			elif type == ldap.MOD_DELETE:
				op = 'delete'
			self.__print_attribute(op, attr)
			for val in vals:
				self.__print_attribute(attr, val)
			self.__end_section()
		self.__end_entry()

	def delete_s(self, dn):
		self.__new_entry(dn)
		self.__print_attribute('changetype', 'delete')
		self.__end_entry()

reconnect=0
connection=None
def connect(ldif=0):
	global connection
	global reconnect

	if connection and not reconnect:
		return connection

	if not os.path.exists(LDIF_FILE) and not ldif:
		# ldap connection
		if os.path.exists('/var/run/ldapi.sock'):
			sock='/var/run/ldapi.sock'
		else:
			sock='/var/lib/ldapi.sock'

		if not os.path.exists('/etc/ldap/rootpw.conf'):
			pw=new_password()
			init_slapd('restart')
		else:
			pw=get_password()
			if not pw:
				pw=new_password()
				init_slapd('restart')

		listener.setuid(0)
		try:
			connection=ldap.open(sock)
			connection.simple_bind_s('cn=update,'+listener.baseConfig['ldap/base'], pw)
		finally:
			listener.unsetuid()
	else:
		listener.setuid(0)
		try:
			connection=LDIFObject(LDIF_FILE)
		finally:
			listener.unsetuid()

	reconnect=0
	return connection

def addlist(new):
	al=[]
	for key in new.keys():
		if key in EXCLUDE_ATTRIBUTES:
			continue
		al.append((key, new[key]))
	return al

def modlist(old, new):
	ml=[]
	for key in new.keys():
		if key in EXCLUDE_ATTRIBUTES:
			continue
		if not old.has_key(key):
			ml.append((ldap.MOD_ADD, key, new[key]))
		elif new[key] != old[key]:
			ml.append((ldap.MOD_REPLACE, key, new[key]))
	for key in old.keys():
		if key in EXCLUDE_ATTRIBUTES:
			continue
		if not new.has_key(key):
			ml.append((ldap.MOD_DELETE, key, []))
	return ml

def subschema_oids_with_sup(subschema, type, oid, result):
	if oid in BUILTIN_OIDS or oid in result:
		return

	obj = subschema.get_obj(type, oid)
	for i in obj.sup:
		sup_obj = subschema.get_obj(type, i)
		subschema_oids_with_sup(subschema, type, sup_obj.oid, result)
	result.append(oid)

def subschema_sort(subschema, type):

	result = []
	for oid in subschema.listall(type):
		subschema_oids_with_sup(subschema, type, oid, result)
	return result

def update_schema(attr):
	listener.setuid(0)
	try:
		fp = open('/var/lib/univention-ldap/schema.conf.new', 'w')
	finally:
		listener.unsetuid()

	queue = []

	print >>fp, '# This schema was automatically replicated from the master server'
	print >>fp, '# Please do not edit this file\n'
	subschema = ldap.schema.SubSchema(attr)

	for oid in subschema_sort(subschema, ldap.schema.AttributeType):
		if oid in BUILTIN_OIDS:
			continue
		obj = subschema.get_obj(ldap.schema.AttributeType, oid)
		print >>fp, 'attributetype', str(obj)

	for oid in subschema_sort(subschema, ldap.schema.ObjectClass):
		if oid in BUILTIN_OIDS:
			continue
		obj = subschema.get_obj(ldap.schema.ObjectClass, oid)
		print >>fp, 'objectclass', str(obj)

	fp.close()

	# move temporary file
	listener.setuid(0)
	try:
		os.rename('/var/lib/univention-ldap/schema.conf.new', '/var/lib/univention-ldap/schema.conf')
	finally:
		listener.unsetuid()

	init_slapd('restart')

def handler(dn, new, listener_old):
	global reconnect
	global slave
	if not slave:
		return 1

	if dn == 'cn=Subschema':
		return update_schema(new)

	connect_count=0
	connected=0

	while connect_count < 31 and not connected:
		try:
			l=connect()
		except ldap.LDAPError, msg:
			connect_count=connect_count+1
			if connect_count >= 30:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '%s: going into LDIF mode' % msg[0]['desc'])
				reconnect=1
				l=connect(ldif=1)
			else:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'Can not connect LDAP Server (%s), retry in 10 seconds' % msg[0]['desc'])
				time.sleep(10)
		else:
			connected=1
	try:
		# Read old entry directly from LDAP server
		if not isinstance(l, LDIFObject):
			try:
				res=l.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)', ['*', '+'])
			except ldap.NO_SUCH_OBJECT:
				old={}
			except ldap.SERVER_DOWN:
				old=listener_old
			else:
				if res:
					old=res[0][1]
				else:
					old={}

			# Check if both entries really match
			match=1
			if len(old) != len(listener_old):
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN,
					'LDAP keys=%s; listener keys=%s' % (str(old.keys()), str(listener_old.keys())))
				match=0
			else:
				for k in old.keys():
					if k in EXCLUDE_ATTRIBUTES:
						continue
					if not listener_old.has_key(k):
						univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN,
							'listener does not have key %s' % k)
						match=0
						break
					if len(old[k]) != len(listener_old[k]):
						univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN,
							'%s: LDAP values and listener values diff' % (k))
						match=0
						break
					for v in old[k]:
						if not v in listener_old[k]:
							univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'listener does not have value for key %s' % (k))
							match=0
							break
			if not match:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN,
						'replication: old entries from LDAP server and Listener do not match')
		else:
			old=listener_old

		# add
		if new and not old:
			al=addlist(new)
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ALL, 'add: %s' % dn)
			try:
				l.add_s(dn, al)
			except ldap.OBJECT_CLASS_VIOLATION, msg:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'replication: object class violation while adding %s' % dn)
		# delete
		elif old and not new:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ALL, 'delete: %s' % dn)
			try:
				l.delete_s(dn)
			except ldap.NOT_ALLOWED_ON_NONLEAF, msg:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'Failed to delete non leaf object: dn=[%s];' % dn)
				dns=[]
				for dn,attr in l.search_s(dn, ldap.SCOPE_SUBTREE, '(objectClass=*)'):
					dns.append(dn)
				dns.reverse()
				for dn in dns:
					l.delete_s(dn)
		# modify
		else:
			ml=modlist(old, new)
			if ml:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ALL, 'modify: %s' % dn)
				l.modify_s(dn, ml)
	except ldap.SERVER_DOWN, msg:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, '%s: retrying' % msg[0]['desc'])
		reconnect=1
		handler(dn, new, old)
	except ldap.ALREADY_EXISTS, msg:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, '%s: %s; trying to apply changes' % (msg[0]['desc'], dn))
		try:
			cur = l.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)')[0][1]
		except LDAPError, msg:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '%s: going into LDIF mode' % msg[0]['desc'])
			reconnect=1
			connect(ldif=1)
			handler(dn, new, old)
		handler(dn, new, cur)

	except ldap.CONSTRAINT_VIOLATION, msg:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Constraint violation: dn=%s: %s' % (dn,msg[0]['desc']))
	except ldap.LDAPError, msg:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'dn=%s: %s' % (dn,msg[0]['desc']))
		reconnect=1
		connect(ldif=1)
		handler(dn, new, old)

def clean():
	global slave
	if not slave:
		return 1
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'removing replica\'s cache')
	#init_slapd('stop')

	#FIXME
	listener.run('/usr/bin/killall', ['killall', '-9', 'slapd'], uid=0)
	time.sleep(1) #FIXME

	dir='/var/lib/univention-ldap/ldap'
	listener.setuid(0)
	try:
		for f in os.listdir(dir):
			file=os.path.join(dir, f)
			try:
				os.unlink(file)
			except OSError:
				pass
		if os.path.exists(LDIF_FILE):
			os.unlink(LDIF_FILE)
	finally:
		listener.unsetuid()
	listener.run('/usr/sbin/univention-baseconfig', ['univention-baseconfig','commit', '/var/lib/univention-ldap/ldap/DB_CONFIG'], uid=0)

def initialize():
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'REPLICATION:  initialize')
	global slave
	if not slave:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'REPLICATION:  not slave')
		return 1
	clean()
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'initializing replica\'s cache')
	new_password()
	init_slapd('start')

def new_password():
	pw=univention_baseconfig.randpw()

	listener.setuid(0)
	try:
		f = open('/etc/ldap/rootpw.conf', 'w')
		f.close()
		os.chmod('/etc/ldap/rootpw.conf', 0600)
		f = open('/etc/ldap/rootpw.conf', 'w')
		print >>f, 'rootpw "%s"' % pw
		f.close()
	finally:
		listener.unsetuid()

	return pw

def get_password():
	pwd=''
	listener.setuid(0)
	try:
		f = open('/etc/ldap/rootpw.conf', 'r')
		rootdn_pattern=re.compile('^rootpw[ \t]+"([^"]+)"')
		for line in f.readlines():
			line=line[0:-1]
			if rootdn_pattern.match(line):
				pwd = rootdn_pattern.findall(line)[0]
				break
		f.close()
	finally:
		listener.unsetuid()
	return pwd

def init_slapd(arg):
	listener.run('/etc/init.d/slapd', ['slapd', arg], uid=0)
	time.sleep(1)

if __name__ == '__main__':
	handler('foo', {'foo': 'bar'}, {'foo': 'baz'})
	handler('foo', {}, {'foo': 'baz'})
	handler('foo', {'foo': 'baz'}, {})
