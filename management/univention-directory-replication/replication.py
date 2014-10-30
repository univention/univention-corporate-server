# -*- coding: utf-8 -*-
#
# Univention Directory Replication
#  listener module for Directory replication
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
# Univention Directory Listener replication module

# Possible initialization scenarios:
# 1. New slave
#    pull complete database from master
# 2. Master is degraded to slave
#    use existing database

__package__='' 	# workaround for PEP 366
import listener
import os
import pwd
import ldap
import ldap.schema
# import ldif as ldifparser since the local module already uses ldif as variable
import ldif as ldifparser
import re
import time
import base64
import univention.debug
import smtplib
from email.MIMEText import MIMEText
import univention.uldap
import sys


name='replication'
description='LDAP slave replication'
filter='(objectClass=*)' # default filter - may be overwritten later
attributes=[]
modrdn='1'

slave=0
if listener.baseConfig['ldap/server/type'] == 'slave':
	slave=1

if listener.baseConfig['ldap/slave/filter']:
	filter=listener.baseConfig['ldap/slave/filter']

#
# init flatmode if enabled
#
flatmode = False
flatmode_ldap={ 'lo': None }
flatmode_mapping = []
flatmode_container = {}
flatmode_module_prefix = 'ldap/replication/flatmode/module/'
flatmode_container_prefix = 'ldap/replication/flatmode/container/'

univention.debug.debug(
	univention.debug.LISTENER,
	univention.debug.INFO,
	'replication flatmode enabled by UCR: %s' % listener.baseConfig.get('ldap/replication/flatmode','no'))

if listener.baseConfig.is_true('ldap/replication/flatmode', False):
	# flatmode is enabled
	try:
		import univention.admin.uldap
		import univention.admin.objects
		import univention.admin.modules
	except Exception, ex:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'cannot import univention directory manager modules: %s' % str(ex))
	else:
		# all modules imported
		for	key_mod in listener.baseConfig.keys():
			# iterate over all UCR variables
			if key_mod.startswith( flatmode_module_prefix ):
				# found module entry
				id=key_mod[ len( flatmode_module_prefix ) : ]
				val_mod = listener.baseConfig[ key_mod ]
				# find container entry
				key_cn = '%s%s' % (flatmode_container_prefix, id)
				if listener.baseConfig.get(key_cn):
					val_cn = listener.baseConfig[ key_cn ]
					# get module
					mod = univention.admin.modules.get( val_mod )
					if not mod:
						univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'replication flatmode: could not get module %s' % val_mod)
					else:
						entry = { 'module': mod, 'type': val_mod, 'container': val_cn }
						univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'replication flatmode: saving objects of type %s in %s' % (val_mod, val_cn))
						flatmode_mapping.append( entry )
						flatmode_container[ val_cn ] = False
						flatmode = True
				else:
					univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'replication flatmode: cannot find UCR variable %s' % key_cn)

univention.debug.debug(
	univention.debug.LISTENER,
	univention.debug.INFO,
	'replication flatmode activated: %s' % flatmode)

STATE_DIR = '/var/lib/univention-directory-replication'
LDIF_FILE = os.path.join(STATE_DIR, 'failed.ldif')

EXCLUDE_ATTRIBUTES=['subschemaSubentry', 'hasSubordinates', 'entryDN', 'MEMBEROF', 'pwdChangedTime', 'PWDCHANGEDTIME', 'pwdAccountLockedTime', 'PWDACCOUNTLOCKEDTIME', 'pwdFailureTime', 'PWDFAILURETIME', 'pwdHistory', 'PWDHISTORY', 'pwdGraceUseTime', 'PWDGRACEUSETIME', 'pwdReset', 'PWDRESET', 'pwdPolicySubentry', 'PWDPOLICYSUBENTRY']

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
	# old OIDs from OpenLDAP 2.3 Experimental OID space
	'1.3.6.1.4.1.4203.666.1.33',    # entryDN (OL 2.3)
	'1.3.6.1.4.1.4203.666.11.1.3.0.1',	# olcAccess
	'1.3.6.1.4.1.4203.666.11.1.3.0.2',	# olcAllows
	'1.3.6.1.4.1.4203.666.11.1.3.0.3',	# olcArgsFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.4',	# olcAttributeTypes
	'1.3.6.1.4.1.4203.666.11.1.3.0.5',	# olcAttributeOptions
	'1.3.6.1.4.1.4203.666.11.1.3.0.6',	# olcAuthIDRewrite
	'1.3.6.1.4.1.4203.666.11.1.3.0.7',	# olcAuthzPolicy
	'1.3.6.1.4.1.4203.666.11.1.3.0.8',	# olcAuthzRegexp
	'1.3.6.1.4.1.4203.666.11.1.3.0.9',	# olcBackend
	'1.3.6.1.4.1.4203.666.11.1.3.0.10',	# olcConcurrency
	'1.3.6.1.4.1.4203.666.11.1.3.0.11',	# olcConnMaxPending
	'1.3.6.1.4.1.4203.666.11.1.3.0.12',	# olcConnMaxPendingAuth
	'1.3.6.1.4.1.4203.666.11.1.3.0.13',	# olcDatabase
	'1.3.6.1.4.1.4203.666.11.1.3.0.14',	# olcDefaultSearchBase
	'1.3.6.1.4.1.4203.666.11.1.3.0.15',	# olcDisallows
	'1.3.6.1.4.1.4203.666.11.1.3.0.16',	# olcDitContentRules
	'1.3.6.1.4.1.4203.666.11.1.3.0.17',	# olcGentleHUP
	'1.3.6.1.4.1.4203.666.11.1.3.0.18',	# olcIdleTimeout
	'1.3.6.1.4.1.4203.666.11.1.3.0.19',	# olcInclude
	'1.3.6.1.4.1.4203.666.11.1.3.0.20',	# olcIndexSubstrIfMinLen
	'1.3.6.1.4.1.4203.666.11.1.3.0.21',	# olcIndexSubstrIfMaxLen
	'1.3.6.1.4.1.4203.666.11.1.3.0.22',	# olcIndexSubstrAnyLen
	'1.3.6.1.4.1.4203.666.11.1.3.0.23',	# olcIndexSubstrAnyStep
	'1.3.6.1.4.1.4203.666.11.1.3.0.26',	# olcLocalSSF
	'1.3.6.1.4.1.4203.666.11.1.3.0.27',	# olcLogFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.28',	# olcLogLevel
	'1.3.6.1.4.1.4203.666.11.1.3.0.30',	# olcModuleLoad
	'1.3.6.1.4.1.4203.666.11.1.3.0.31',	# olcModulePath
	'1.3.6.1.4.1.4203.666.11.1.3.0.32',	# olcObjectClasses
	'1.3.6.1.4.1.4203.666.11.1.3.0.33',	# olcObjectIdentifier
	'1.3.6.1.4.1.4203.666.11.1.3.0.34',	# olcOverlay
	'1.3.6.1.4.1.4203.666.11.1.3.0.35',	# olcPasswordCryptSaltFormat
	'1.3.6.1.4.1.4203.666.11.1.3.0.36',	# olcPasswordHash
	'1.3.6.1.4.1.4203.666.11.1.3.0.37',	# olcPidFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.38',	# olcPlugin
	'1.3.6.1.4.1.4203.666.11.1.3.0.39',	# olcPluginLogFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.40',	# olcReadOnly
	'1.3.6.1.4.1.4203.666.11.1.3.0.41',	# olcReferral
	'1.3.6.1.4.1.4203.666.11.1.3.0.43',	# olcReplicaArgsFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.44',	# olcReplicaPidFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.45',	# olcReplicationInterval
	'1.3.6.1.4.1.4203.666.11.1.3.0.46',	# olcReplogFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.47',	# olcRequires
	'1.3.6.1.4.1.4203.666.11.1.3.0.48',	# olcRestrict
	'1.3.6.1.4.1.4203.666.11.1.3.0.49',	# olcReverseLookup
	'1.3.6.1.4.1.4203.666.11.1.3.0.51',	# olcRootDSE
	'1.3.6.1.4.1.4203.666.11.1.3.0.53',	# olcSaslHost
	'1.3.6.1.4.1.4203.666.11.1.3.0.54',	# olcSaslRealm
	'1.3.6.1.4.1.4203.666.11.1.3.0.56',	# olcSaslSecProps
	'1.3.6.1.4.1.4203.666.11.1.3.0.58',	# olcSchemaDN
	'1.3.6.1.4.1.4203.666.11.1.3.0.59',	# olcSecurity
	'1.3.6.1.4.1.4203.666.11.1.3.0.60',	# olcSizeLimit
	'1.3.6.1.4.1.4203.666.11.1.3.0.61',	# olcSockbufMaxIncoming
	'1.3.6.1.4.1.4203.666.11.1.3.0.62',	# olcSockbufMaxIncomingAuth
	'1.3.6.1.4.1.4203.666.11.1.3.0.63',	# olcSrvtab
	'1.3.6.1.4.1.4203.666.11.1.3.0.66',	# olcThreads
	'1.3.6.1.4.1.4203.666.11.1.3.0.67',	# olcTimeLimit
	'1.3.6.1.4.1.4203.666.11.1.3.0.68',	# olcTLSCACertificateFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.69',	# olcTLSCACertificatePath
	'1.3.6.1.4.1.4203.666.11.1.3.0.70',	# olcTLSCertificateFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.71',	# olcTLSCertificateKeyFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.72',	# olcTLSCipherSuite
	'1.3.6.1.4.1.4203.666.11.1.3.0.73',	# olcTLSCRLCheck
	'1.3.6.1.4.1.4203.666.11.1.3.0.74',	# olcTLSRandFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.75',	# olcTLSVerifyClient
	'1.3.6.1.4.1.4203.666.11.1.3.0.77',	# olcTLSDHParamFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.78',	# olcConfigFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.79',	# olcConfigDir
	'1.3.6.1.4.1.4203.666.11.1.3.0.80',	# olcToolThreads
	'1.3.6.1.4.1.4203.666.11.1.3.0.81',	# olcServerID
	'1.3.6.1.4.1.4203.666.11.1.3.0.82',	# olcTLSCRLFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.83',	# olcSortVals
	'1.3.6.1.4.1.4203.666.11.1.3.0.84',	# olcIndexIntLen
	'1.3.6.1.4.1.4203.666.11.1.3.0.85',	# olcLdapSyntaxes
	'1.3.6.1.4.1.4203.666.11.1.3.0.86',	# olcAddContentAcl
	'1.3.6.1.4.1.4203.666.11.1.3.0.87',	# olcTLSProtocolMin
	'1.3.6.1.4.1.4203.666.11.1.3.0.88',	# olcWriteTimeout
	'1.3.6.1.4.1.4203.666.11.1.3.0.89',	# olcSaslAuxprops
	'1.3.6.1.4.1.4203.666.11.1.3.0.90',	# olcTCPBuffer
	'1.3.6.1.4.1.4203.666.11.1.3.0.93',	# olcListenerThreads
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.1',	# olcDbDirectory
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.2',	# olcDbIndex
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.3',	# olcDbMode
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.4',	# olcLastMod
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.5',	# olcLimits
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.6',	# olcMaxDerefDepth
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.7',	# olcReplica
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.8',	# olcRootDN
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.9',	# olcRootPW
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.10',	# olcSuffix
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.11',	# olcSyncrepl
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.12',	# olcUpdateDN
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.13',	# olcUpdateRef
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.15',	# olcSubordinate
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.16',	# olcMirrorMode
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.17',	# olcHidden
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.18',	# olcMonitoring
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.19',	# olcSyncUseSubentry
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.1',	# olcDbCacheSize
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.2',	# olcDbCheckpoint
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.3',	# olcDbConfig
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.4',	# olcDbNoSync
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.5',	# olcDbDirtyRead
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.6',	# olcDbIDLcacheSize
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.7',	# olcDbLinearIndex
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.8',	# olcDbLockDetect
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.9',	# olcDbSearchStack
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.10',	# olcDbShmKey
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.11',	# olcDbCacheFree
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.12',	# olcDbDNcacheSize
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.13',	# olcDbCryptFile
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.14',	# olcDbCryptKey
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.15',	# olcDbPageSize
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.16',	# olcDbChecksum
	# new OIDs in official OpenLDAP 2.4 OID space
	'1.3.6.1.1.20',			# entryDN (OL 2.4)
	'1.3.6.1.4.1.4203.1.12.2.3.0.1',	# olcAccess
	'1.3.6.1.4.1.4203.1.12.2.3.0.2',	# olcAllows
	'1.3.6.1.4.1.4203.1.12.2.3.0.3',	# olcArgsFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.4',	# olcAttributeTypes
	'1.3.6.1.4.1.4203.1.12.2.3.0.5',	# olcAttributeOptions
	'1.3.6.1.4.1.4203.1.12.2.3.0.6',	# olcAuthIDRewrite
	'1.3.6.1.4.1.4203.1.12.2.3.0.7',	# olcAuthzPolicy
	'1.3.6.1.4.1.4203.1.12.2.3.0.8',	# olcAuthzRegexp
	'1.3.6.1.4.1.4203.1.12.2.3.0.9',	# olcBackend
	'1.3.6.1.4.1.4203.1.12.2.3.0.10',	# olcConcurrency
	'1.3.6.1.4.1.4203.1.12.2.3.0.11',	# olcConnMaxPending
	'1.3.6.1.4.1.4203.1.12.2.3.0.12',	# olcConnMaxPendingAuth
	'1.3.6.1.4.1.4203.1.12.2.3.0.13',	# olcDatabase
	'1.3.6.1.4.1.4203.1.12.2.3.0.14',	# olcDefaultSearchBase
	'1.3.6.1.4.1.4203.1.12.2.3.0.15',	# olcDisallows
	'1.3.6.1.4.1.4203.1.12.2.3.0.16',	# olcDitContentRules
	'1.3.6.1.4.1.4203.1.12.2.3.0.17',	# olcGentleHUP
	'1.3.6.1.4.1.4203.1.12.2.3.0.18',	# olcIdleTimeout
	'1.3.6.1.4.1.4203.1.12.2.3.0.19',	# olcInclude
	'1.3.6.1.4.1.4203.1.12.2.3.0.20',	# olcIndexSubstrIfMinLen
	'1.3.6.1.4.1.4203.1.12.2.3.0.21',	# olcIndexSubstrIfMaxLen
	'1.3.6.1.4.1.4203.1.12.2.3.0.22',	# olcIndexSubstrAnyLen
	'1.3.6.1.4.1.4203.1.12.2.3.0.23',	# olcIndexSubstrAnyStep
	'1.3.6.1.4.1.4203.1.12.2.3.0.26',	# olcLocalSSF
	'1.3.6.1.4.1.4203.1.12.2.3.0.27',	# olcLogFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.28',	# olcLogLevel
	'1.3.6.1.4.1.4203.1.12.2.3.0.30',	# olcModuleLoad
	'1.3.6.1.4.1.4203.1.12.2.3.0.31',	# olcModulePath
	'1.3.6.1.4.1.4203.1.12.2.3.0.32',	# olcObjectClasses
	'1.3.6.1.4.1.4203.1.12.2.3.0.33',	# olcObjectIdentifier
	'1.3.6.1.4.1.4203.1.12.2.3.0.34',	# olcOverlay
	'1.3.6.1.4.1.4203.1.12.2.3.0.35',	# olcPasswordCryptSaltFormat
	'1.3.6.1.4.1.4203.1.12.2.3.0.36',	# olcPasswordHash
	'1.3.6.1.4.1.4203.1.12.2.3.0.37',	# olcPidFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.38',	# olcPlugin
	'1.3.6.1.4.1.4203.1.12.2.3.0.39',	# olcPluginLogFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.40',	# olcReadOnly
	'1.3.6.1.4.1.4203.1.12.2.3.0.41',	# olcReferral
	'1.3.6.1.4.1.4203.1.12.2.3.0.43',	# olcReplicaArgsFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.44',	# olcReplicaPidFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.45',	# olcReplicationInterval
	'1.3.6.1.4.1.4203.1.12.2.3.0.46',	# olcReplogFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.47',	# olcRequires
	'1.3.6.1.4.1.4203.1.12.2.3.0.48',	# olcRestrict
	'1.3.6.1.4.1.4203.1.12.2.3.0.49',	# olcReverseLookup
	'1.3.6.1.4.1.4203.1.12.2.3.0.51',	# olcRootDSE
	'1.3.6.1.4.1.4203.1.12.2.3.0.53',	# olcSaslHost
	'1.3.6.1.4.1.4203.1.12.2.3.0.54',	# olcSaslRealm
	'1.3.6.1.4.1.4203.1.12.2.3.0.56',	# olcSaslSecProps
	'1.3.6.1.4.1.4203.1.12.2.3.0.58',	# olcSchemaDN
	'1.3.6.1.4.1.4203.1.12.2.3.0.59',	# olcSecurity
	'1.3.6.1.4.1.4203.1.12.2.3.0.60',	# olcSizeLimit
	'1.3.6.1.4.1.4203.1.12.2.3.0.61',	# olcSockbufMaxIncoming
	'1.3.6.1.4.1.4203.1.12.2.3.0.62',	# olcSockbufMaxIncomingAuth
	'1.3.6.1.4.1.4203.1.12.2.3.0.63',	# olcSrvtab
	'1.3.6.1.4.1.4203.1.12.2.3.0.66',	# olcThreads
	'1.3.6.1.4.1.4203.1.12.2.3.0.67',	# olcTimeLimit
	'1.3.6.1.4.1.4203.1.12.2.3.0.68',	# olcTLSCACertificateFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.69',	# olcTLSCACertificatePath
	'1.3.6.1.4.1.4203.1.12.2.3.0.70',	# olcTLSCertificateFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.71',	# olcTLSCertificateKeyFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.72',	# olcTLSCipherSuite
	'1.3.6.1.4.1.4203.1.12.2.3.0.73',	# olcTLSCRLCheck
	'1.3.6.1.4.1.4203.1.12.2.3.0.74',	# olcTLSRandFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.75',	# olcTLSVerifyClient
	'1.3.6.1.4.1.4203.1.12.2.3.0.77',	# olcTLSDHParamFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.78',	# olcConfigFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.79',	# olcConfigDir
	'1.3.6.1.4.1.4203.1.12.2.3.0.80',	# olcToolThreads
	'1.3.6.1.4.1.4203.1.12.2.3.0.81',	# olcServerID
	'1.3.6.1.4.1.4203.1.12.2.3.0.82',	# olcTLSCRLFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.83',	# olcSortVals
	'1.3.6.1.4.1.4203.1.12.2.3.0.84',	# olcIndexIntLen
	'1.3.6.1.4.1.4203.1.12.2.3.0.85',	# olcLdapSyntaxes
	'1.3.6.1.4.1.4203.1.12.2.3.0.86',	# olcAddContentAcl
	'1.3.6.1.4.1.4203.1.12.2.3.0.87',	# olcTLSProtocolMin
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.1',	# olcDbDirectory
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.2',	# olcDbIndex
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.3',	# olcDbMode
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.4',	# olcLastMod
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.5',	# olcLimits
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.6',	# olcMaxDerefDepth
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.7',	# olcReplica
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.8',	# olcRootDN
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.9',	# olcRootPW
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.10',	# olcSuffix
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.11',	# olcSyncrepl
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.12',	# olcUpdateDN
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.13',	# olcUpdateRef
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.15',	# olcSubordinate
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.16',	# olcMirrorMode
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.17',	# olcHidden
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.18',	# olcMonitoring
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.1',	# olcDbCacheSize
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.2',	# olcDbCheckpoint
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.3',	# olcDbConfig
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.4',	# olcDbNoSync
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.5',	# olcDbDirtyRead
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.6',	# olcDbIDLcacheSize
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.7',	# olcDbLinearIndex
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.8',	# olcDbLockDetect
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.9',	# olcDbSearchStack
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.10',	# olcDbShmKey
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.11',	# olcDbCacheFree
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.12',	# olcDbDNcacheSize
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.13',	# olcDbCryptFile
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.14',	# olcDbCryptKey
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.15',	# olcDbPageSize
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.16',	# olcDbChecksum
	# objectClasses
	'2.16.840.1.113730.3.2.6',	# referral
	'2.16.840.1.113730.3.1.34',	# ref (operational)
	# old OIDs from OpenLDAP 2.3 Experimental OID space
	'1.3.6.1.4.1.4203.666.11.1.4.0.0',	# olcConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.1',	# olcGlobal
	'1.3.6.1.4.1.4203.666.11.1.4.0.2',	# olcSchemaConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.3',	# olcBackendConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.4',	# olcDatabaseConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.5',	# olcOverlayConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.6',	# olcIncludeFile
	'1.3.6.1.4.1.4203.666.11.1.4.0.7',	# olcFrontendConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.8',	# olcModuleList
	'1.3.6.1.4.1.4203.666.11.1.4.2.1.1',	# olcBdbConfig
	'1.3.6.1.4.1.4203.666.11.1.4.2.2.1',	# olcLdifConfig
	'1.3.6.1.4.1.4203.1.12.2.4.2.12.1',   # olcMdbConfig
	'1.3.6.1.4.1.4203.666.11.1.4.2.12.1', # olcMdbConfig
	'1.3.6.1.4.1.4203.1.12.2.3.2.12.1',	  # olcDbMaxReaders
	'1.3.6.1.4.1.4203.666.11.1.3.2.12.1', # olcDbMaxReaders
	'1.3.6.1.4.1.4203.1.12.2.3.2.12.2',	  # olcDbMaxSize
	'1.3.6.1.4.1.4203.666.11.1.3.2.12.2', # olcDbMaxSize
	'1.3.6.1.4.1.4203.1.12.2.3.2.12.3',	  # olcDbEnvFlags
	'1.3.6.1.4.1.4203.666.11.1.3.2.12.3', # olcDbEnvFlags
	# new OIDs in official OpenLDAP 2.4 OID space
	'1.3.6.1.4.1.4203.1.12.2.4.0.0',	# olcConfig
	'1.3.6.1.4.1.4203.1.12.2.4.0.1',	# olcGlobal
	'1.3.6.1.4.1.4203.1.12.2.4.0.2',	# olcSchemaConfig
	'1.3.6.1.4.1.4203.1.12.2.4.0.3',	# olcBackendConfig
	'1.3.6.1.4.1.4203.1.12.2.4.0.4',	# olcDatabaseConfig
	'1.3.6.1.4.1.4203.1.12.2.4.0.5',	# olcOverlayConfig
	'1.3.6.1.4.1.4203.1.12.2.4.0.6',	# olcIncludeFile
	'1.3.6.1.4.1.4203.1.12.2.4.0.7',	# olcFrontendConfig
	'1.3.6.1.4.1.4203.1.12.2.4.0.8',	# olcModuleList
	'1.3.6.1.4.1.4203.1.12.2.4.2.1.1',	# olcBdbConfig
	'1.3.6.1.4.1.4203.1.12.2.4.2.2.1',	# olcLdifConfig
	# UCS 3.0
	'1.3.6.1.4.1.4203.666.11.1.3.0.93', # olcListenerThreads
	# UCS 3.1
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.20',	# olcExtraAttrs
	# UCS 2.0
	'2.5.4.34', #seeAlso
	'0.9.2342.19200300.100.1.1', #userid
	'2.5.4.13',  #description
	'1.3.6.1.1.1.1.1', # gidNumber
	'1.3.6.1.1.1.1.0', #uidNumber
	# memberOf overlay
	'1.2.840.113556.1.2.102',  # memberOf
	# ppolicy overlay
	'1.3.6.1.4.1.42.2.27.8.1.16', # pwdChangedTime
	'1.3.6.1.4.1.42.2.27.8.1.17', # pwdAccountLockedTime
	'1.3.6.1.4.1.42.2.27.8.1.19', # pwdFailureTime
	'1.3.6.1.4.1.42.2.27.8.1.20', # pwdHistory
	'1.3.6.1.4.1.42.2.27.8.1.21', # pwdGraceUseTime
	'1.3.6.1.4.1.42.2.27.8.1.22', # pwdReset
	'1.3.6.1.4.1.42.2.27.8.1.23', # pwdPolicySubentry
]

class LDIFObject:
	def __init__(self, file):
		self.fp = open(file, 'a')
		os.chmod(file, 0600)

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

		if not value:
			print >>self.fp

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
		if not os.path.exists('/etc/ldap/rootpw.conf'):
			pw=new_password()
			init_slapd('restart')
		else:
			pw=get_password()
			if not pw:
				pw=new_password()
				init_slapd('restart')

		listener.setuid(0)

		local_ip='127.0.0.1'
		local_port=listener.baseConfig.get('slapd/port', '7389').split(',')[0]
		
		try:
			connection=ldap.open(local_ip, int(local_port))
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
		if key not in old:
			ml.append((ldap.MOD_ADD, key, new[key]))
		elif new[key] != old[key]:
			ml.append((ldap.MOD_REPLACE, key, new[key]))
	for key in old.keys():
		if key in EXCLUDE_ATTRIBUTES:
			continue
		if key not in new:
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

# get "old" from local ldap server
# "ldapconn": connection to local ldap server
def getOldValues( ldapconn, dn ):
	if not isinstance(ldapconn, LDIFObject):
		try:
			res=ldapconn.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)', ['*', '+'])
		except ldap.NO_SUCH_OBJECT:
			old={}
		except ldap.SERVER_DOWN:
			old={}
		else:
			if res:
				old=res[0][1]
			else:
				old={}
	else:
		old={}

	return old

# check if target container exists; this function creates required containers if they are missing
def flatmodeCreateContainer( ldapconn, dn ):
	if dn in flatmode_container:
		if flatmode_container[dn]:
			return

	univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'replication flatmode: testing required container: %s' % dn)
	old = getOldValues( ldapconn, dn )

	if not old:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'replication flatmode: required container does not exist: %s' % dn)
		tmpdn=''
		dnparts = univention.admin.uldap.explodeDn(dn, 0)
		dnparts.reverse()
		for dnpart in dnparts:
			if tmpdn:
				tmpdn = '%s,%s' % (dnpart, tmpdn)
			else:
				tmpdn = dnpart

			tmpold = {}
			tmpnew = {}
			objtype, objname = dnpart.split('=',1)
			if objtype == 'cn' or objtype == 'ou':
				# check if object exists in local ldap tree
				tmpold = getOldValues( ldapconn, tmpdn )

			if objtype == 'cn' and not tmpold:
				tmpnew = { 'cn': [ objname ], 'objectClass': [ 'top', 'organizationalRole' ] }
			elif objtype == 'ou' and not tmpold:
				tmpnew = { 'ou': [ objname ], 'objectClass': [ 'top', 'organizationalUnit' ] }

			if tmpnew:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'replication flatmode: creating required container: %s' % tmpdn)
				univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'replication flatmode: calling handle( %s, tmpnew, tmpold ):\ntmpnew=%s' % (tmpdn, tmpnew))
				handler( tmpdn, tmpnew, tmpold )
	flatmode_container[dn] = True


# This function converts object dn and object attributes for flatmode.
# Special convertions for aach module type have to be added here.
# "new" is modified "by reference"
# the new value for "dn" is returned ("call by value")
def flatmodeConvertObject( entry, dn, new ):
	global flatmode_mapping

	# map DN
	rdn = univention.admin.uldap.explodeDn(dn, 0)[0]
	dn = '%s,%s' % (rdn, entry['container'])

	# correct entryDN
	if new:
		new['entryDN'][0] = dn

	if new.get('uniqueMember'):
		if flatmode_ldap['lo'] is None:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'replication flatmode: second ldap connection is not established - local replica may be corrupt!')
		else:
			newMemberDNs = []
			# convert all existing uniqueMember DNs
			for memberdn in new['uniqueMember']:
				try:
					obj = flatmode_ldap['lo'].get(memberdn,[])
				except Exception, ex:
					univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'replication flatmode: could not get member %s' % memberdn)
					obj = None

				newmember = memberdn
				if obj:
					for entry in flatmode_mapping:
						# test if memberdn should also be remapped
						if entry['module'].identify( memberdn, obj ) or entry['module'].identify( memberdn, obj ):

							rdn = univention.admin.uldap.explodeDn(memberdn, 0)[0]
							newmember = '%s,%s' % (rdn, entry['container'])
							break

				newMemberDNs.append( newmember )
			# set new DNs
			new['uniqueMember'] = newMemberDNs

	return dn

# if flatmode is enabled handlerFlatmode checks for every object if mapping is required
# if examined object matches to mapping "dn" and "new" are converted by flatmodeConvertObject
def handlerFlatmode( ldapconn, dn, new, old ):
	global flatmode
	global flatmode_mapping
	global flatmode_container

	if not flatmode:
		return dn
	newdn = dn

	if dn in flatmode_container:
		flatmode_container[dn] = True

	for entry in flatmode_mapping:
		if entry['module'].identify( dn, new ) or entry['module'].identify( dn, old ):

			newdn = flatmodeConvertObject( entry, dn, new )

			# test if required container is present
			if not flatmode_container[ entry['container'] ]:
				flatmodeCreateContainer( ldapconn, entry['container'] )

			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'replication flatmode: mapped %s to %s' % (dn, newdn))
			return newdn

	return newdn


def flatmode_reconnect():
	univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'replication flatmode: ldap reconnect triggered')
	if ( flatmode_ldap.get('ldapserver') and \
		 flatmode_ldap.get('basedn') and \
		 flatmode_ldap.get('binddn') and \
		 flatmode_ldap.get('bindpw')):
		try:
			flatmode_ldap['lo'] = univention.uldap.access( host = flatmode_ldap['ldapserver'],
														   base = flatmode_ldap['basedn'],
														   binddn = flatmode_ldap['binddn'],
														   bindpw = flatmode_ldap['bindpw'],
														   start_tls = 2 )
		except Exception, ex:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'replication flatmode: ldap reconnect failed: %s' % str(ex))
			flatmode_ldap['lo'] = None
		else:
			if flatmode_ldap['lo'] is None:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'replication flatmode: ldap reconnect failed')

def _delete_dn_recursive(l, dn):
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
	except ldap.NO_SUCH_OBJECT, msg:
		pass

def _backup_dn_recursive(l, dn):
	backup_directory = '/var/univention-backup/replication'
	if not os.path.exists(backup_directory):
		os.makedirs(backup_directory)
		os.chmod(backup_directory, 0700)
	
	backup_file = os.path.join(backup_directory, str(time.time()))
	fd = open(backup_file, 'w+')
	fd.close()
	os.chmod(backup_file, 0600)
	univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, 'replication: dump %s to %s' % (dn, backup_file))
	
	fd = open(backup_file, 'w+')
	ldif_writer = ldifparser.LDIFWriter(fd)
	for dn,entry in l.search_s(dn, ldap.SCOPE_SUBTREE, '(objectClass=*)', attrlist=['*', '+']):
		ldif_writer.unparse(dn,entry)
	fd.close()
		
def _get_current_modrdn_link():
	return os.path.join(STATE_DIR, 'current_modrdn')

def _remove_current_modrdn_link():
	current_modrdn_link = _get_current_modrdn_link()
	try:
		os.remove(current_modrdn_link)
	except Exception, e:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'replication: failed to remove current_modrdn file %s: %s' % (current_modrdn_link, str(e)))

def _add_object_from_new(l, dn, new):
	al=addlist(new)
	try:
		l.add_s(dn, al)
	except ldap.OBJECT_CLASS_VIOLATION, msg:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'replication: object class violation while adding %s' % dn)

def _modify_object_from_old_and_new(l, dn, old, new):
	ml=modlist(old, new)
	if ml:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ALL, 'replication: modify: %s' % dn)
		l.modify_s(dn, ml)

def _read_dn_from_file(filename):
	old_dn = None

	try:
		with open(filename,'r') as f:
			old_dn = f.read()
	except Exception, e:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'replication: failed to open/read modrdn file %s: %s' % (filename, str(e)))

	return old_dn

def handler(dn, new, listener_old, operation):
	global reconnect
	global slave
	global flatmode
	if not slave:
		return 1

	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'replication: Running handler for: %s' % dn)
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
				if 'info' in msg[0]:
					univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '\tadditional info: %s' % msg[0]['info'])
				if 'matched' in msg[0]:
					univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '\tmachted dn: %s' % msg[0]['matched'])
				reconnect=1
				l=connect(ldif=1)
			else:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'Can not connect LDAP Server (%s), retry in 10 seconds' % msg[0]['desc'])
				if 'info' in msg[0]:
					univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '\tadditional info: %s' % msg[0]['info'])
				if 'matched' in msg[0]:
					univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '\tmachted dn: %s' % msg[0]['matched'])
				time.sleep(10)
		else:
			connected=1

	if 'pwdAttribute' in new.keys():
		if new['pwdAttribute'][0] == 'userPassword':
			new['pwdAttribute'] = ['2.5.4.35']

	if flatmode:
		dn = handlerFlatmode( l, dn, new, listener_old )

	try:

		if listener.baseConfig.get('ldap/replication/filesystem/check', 'false').lower() in ['true', 'yes']:
			df = os.popen('df -P /var/lib/univention-ldap/').readlines()
			free_space = float(df[1].strip().split()[3])*1024*1024 # free space in MB
			limit = float(listener.baseConfig.get('ldap/replication/filesystem/limit', '10'))
			if limit < free_space:

				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Critical disk space. The Univention LDAP Listener was stopped')
				msg = MIMEText('The Univention Listener process was stopped on %s.%s.\n\n\nThe result of df:\n%s\n\nPlease free up some disk space and restart the Univention LDAP Listener with the following command:\n/etc/init.d/univention-directory-listener start' %(listener.baseConfig['hostname'], listener.baseConfig['domainname'], ' '.join(df)))
				msg['Subject'] = 'Alert: Critical disk space on %s.%s' % (listener.baseConfig['hostname'], listener.baseConfig['domainname'])
				sender = 'root'
				recipient = listener.baseConfig.get('ldap/replication/filesystem/recipient', sender)

				msg['From'] = sender
				msg['To'] = recipient

				s = smtplib.SMTP()
				s.connect()
				s.sendmail(sender, [recipient], msg.as_string())
				s.close()

				listener.setuid(0)
				os.system('/etc/init.d/univention-directory-listener stop')
				listener.unsetuid()

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
				univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO,
					'LDAP keys=%s; listener keys=%s' % (str(old.keys()), str(listener_old.keys())))
				match=0
			else:
				for k in old.keys():
					if k in EXCLUDE_ATTRIBUTES:
						continue
					if k not in listener_old:
						univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO,
							'listener does not have key %s' % k)
						match=0
						break
					if len(old[k]) != len(listener_old[k]):
						univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO,
							'%s: LDAP values and listener values diff' % (k))
						match=0
						break
					for v in old[k]:
						if not v in listener_old[k]:
							univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'listener does not have value for key %s' % (k))
							match=0
							break
			if not match:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO,
						'replication: old entries from LDAP server and Listener do not match')
		else:
			old=listener_old

		# add
		if new:
			new_entryUUID = new['entryUUID'][0]
			modrdn_cache = os.path.join(STATE_DIR, new_entryUUID)

			current_modrdn_link = _get_current_modrdn_link()
			if os.path.exists(current_modrdn_link):
				target_uuid_file = os.readlink(current_modrdn_link)
				if modrdn_cache == target_uuid_file and os.path.exists(modrdn_cache):
					univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, 'replication: rename phase II: %s (entryUUID=%s)' % (dn, new_entryUUID))
					listener.setuid(0)

					old_dn = _read_dn_from_file(modrdn_cache)

					new_parent = ','.join(ldap.explode_dn(dn)[1:])
					new_rdn = ldap.explode_rdn(dn)[0]

					if old:
						# this means the target already exists, we have to delete this old object
						univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, 'replication: the rename target already exists in the local LDAP, backup and remove the dn: %s' % (dn))
						_backup_dn_recursive(l, dn)
						_delete_dn_recursive(l, dn)

					if getOldValues(l, old_dn):
						# the normal rename is possible
						univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, 'replication: rename from %s to %s,%s' % (old_dn, new_rdn, new_parent))
						l.rename_s(old_dn, new_rdn, new_parent)
					else:
						# the old object does not exists, so we have to re-create the new object
						univention.debug.debug(univention.debug.LISTENER, univention.debug.ALL, 'replication: the local target does not exist, so the object will be added: %s' % dn)
						_add_object_from_new(l, dn, new)
					try:
						os.remove(modrdn_cache)
					except Exception, e:
						univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'replication: failed to remove modrdn file %s: %s' % (modrdn_cache, str(e)))
					_remove_current_modrdn_link()
					listener.unsetuid()
				else: #current_modrdn points to a different file
					listener.setuid(0)
					univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, 'replication: the current modrdn points to a different entryUUID: %s' % os.readlink(current_modrdn_link))

					old_dn = _read_dn_from_file(current_modrdn_link)

					if old_dn:
						univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, 'replication: the DN %s from the current_modrdn_link has to be backuped and removed' % (old_dn))
						try:
							_backup_dn_recursive(l, old_dn)
						except AttributeError:
							# The backup will fail in LDIF mode
							pass
						_delete_dn_recursive(l, old_dn)
					else:
						univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'replication: no old dn has been found')
					
					if not old:
						_add_object_from_new(l, dn, new)
					elif old:
						_modify_object_from_old_and_new(l, dn, old, new)

					_remove_current_modrdn_link()

					listener.unsetuid()

			elif old: # modify: new and old
				_modify_object_from_old_and_new(l, dn, old, new)

			else: # add: new and not old
				_add_object_from_new(l, dn, new)

		# delete
		elif old and not new:
			if operation == 'r':	## check for modrdn phase 1
				old_entryUUID = old['entryUUID'][0]
				univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, 'replication: rename phase I: %s (entryUUID=%s)' % (dn, old_entryUUID))
				modrdn_cache = os.path.join(STATE_DIR, old_entryUUID)
				listener.setuid(0)
				try:
					with open(modrdn_cache, 'w') as f:
						os.chmod(modrdn_cache, 0600)
						f.write(dn)
					current_modrdn_link = os.path.join(STATE_DIR, 'current_modrdn')
					if os.path.exists(current_modrdn_link):
						os.remove(current_modrdn_link)
					os.symlink(modrdn_cache, current_modrdn_link)
					listener.unsetuid()
					## that's it for now for command 'r' ==> modrdn will follow in the next step
					return
				except Exception, e:
					## d'oh! output some message and continue doing a delete+add instead
					univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'replication: failed to open/write modrdn file %s: %s' % (modrdn_cache, str(e)))
				listener.unsetuid()

			univention.debug.debug(univention.debug.LISTENER, univention.debug.ALL, 'replication: delete: %s' % dn)
			_delete_dn_recursive(l, dn)
	except ldap.SERVER_DOWN, msg:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, '%s: retrying' % msg[0]['desc'])
		if 'info' in msg[0]:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, '\tadditional info: %s' % msg[0]['info'])
		if 'matched' in msg[0]:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, '\tmachted dn: %s' % msg[0]['matched'])
		reconnect=1
		handler(dn, new, listener_old, operation)
	except ldap.ALREADY_EXISTS, msg:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, '%s: %s; trying to apply changes' % (msg[0]['desc'], dn))
		if 'info' in msg[0]:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, '\tadditional info: %s' % msg[0]['info'])
		if 'matched' in msg[0]:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, '\tmachted dn: %s' % msg[0]['matched'])
		try:
			cur = l.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)')[0][1]
		except ldap.LDAPError, msg:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '%s: going into LDIF mode' % msg[0]['desc'])
			if 'info' in msg[0]:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '\tadditional info: %s' % msg[0]['info'])
			if 'matched' in msg[0]:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '\tmachted dn: %s' % msg[0]['matched'])
			reconnect=1
			connect(ldif=1)
			handler(dn, new, listener_old, operation)
		else:
			handler(dn, new, cur, operation)

	except ldap.CONSTRAINT_VIOLATION, msg:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Constraint violation: dn=%s: %s' % (dn,msg[0]['desc']))
	except ldap.LDAPError, msg:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'dn=%s: %s' % (dn,msg[0]['desc']))
		if 'info' in msg[0]:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '\tadditional info: %s' % msg[0]['info'])
		if 'matched' in msg[0]:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, '\tmachted dn: %s' % msg[0]['matched'])
		if listener.baseConfig.get('ldap/replication/fallback', 'ldif') == 'restart':
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Uncaught LDAPError exception during modify operation. Exiting Univention Directory Listener to retry replication with an updated copy of the current upstream object.')
			sys.exit(1)	## retry a bit later after restart via runsv
		else:
			reconnect=1
			connect(ldif=1)
			handler(dn, new, listener_old, operation)

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
	listener.run('/usr/sbin/univention-config-registry', ['univention-config-registry','commit', '/var/lib/univention-ldap/ldap/DB_CONFIG'], uid=0)

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


def randpw(length=8):
    """Create random password.
    >>> randpw().isalnum()
    True
    """
    password = []
    rand = open('/dev/urandom', 'r')
    try:
        for _ in xrange(length):
            octet = ord(rand.read(1))
            octet %= len(randpw.VALID)  # pylint: disable-msg=E1101
            char = randpw.VALID[octet]  # pylint: disable-msg=E1101
            password.append(char)
    finally:
        rand.close()
    return ''.join(password)
randpw.VALID = ('0123456789' +  # pylint: disable-msg=W0612
        'abcdefghijklmnopqrstuvwxyz' +
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ')


def new_password():
	pw = randpw()

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

def setdata(key, value):
	if key == 'bindpw':
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'replication: listener passed key="%s" value="<HIDDEN>"' % key)
	else:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'replication: listener passed key="%s" value="%s"' % (key, value))

	if key in [ 'ldapserver', 'basedn', 'binddn', 'bindpw' ]:
		flatmode_ldap[ key ] = value
	else:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'replication: listener passed unknown data (key="%s" value="%s")' % (key, value))

	if key == 'ldapserver':
		univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'replication: ldap server changed to %s' % value)
		if flatmode:
			flatmode_reconnect()

if __name__ == '__main__':
	handler('foo', {'foo': 'bar'}, {'foo': 'baz'})
	handler('foo', {}, {'foo': 'baz'})
	handler('foo', {'foo': 'baz'}, {})
