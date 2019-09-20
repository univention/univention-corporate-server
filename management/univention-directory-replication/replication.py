# -*- coding: utf-8 -*-
#
# Univention Directory Replication
#  listener module for Directory replication
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
# Univention Directory Listener replication module

# Possible initialization scenarios:
# 1. New slave
#    pull complete database from master
# 2. Master is degraded to slave
#    use existing database

__package__ = ''  # workaround for PEP 366
import listener
import os
import ldap
import ldap.schema
# import ldif as ldifparser since the local module already uses ldif as variable
import ldif as ldifparser
import re
import time
import base64
import subprocess
import univention.debug as ud
import smtplib
from email.MIMEText import MIMEText
import sys
from errno import ENOENT


name = 'replication'
description = 'LDAP slave replication'
filter = '(objectClass=*)'  # default filter - may be overwritten later
attributes = []
modrdn = '1'

slave = listener.baseConfig['ldap/server/type'] == 'slave'

if listener.baseConfig['ldap/slave/filter']:
	filter = listener.baseConfig['ldap/slave/filter']

LDAP_DIR = '/var/lib/univention-ldap/'
STATE_DIR = '/var/lib/univention-directory-replication'
BACKUP_DIR = '/var/univention-backup/replication'
LDIF_FILE = os.path.join(STATE_DIR, 'failed.ldif')
ROOTPW_FILE = '/etc/ldap/rootpw.conf'
CURRENT_MODRDN = os.path.join(STATE_DIR, 'current_modrdn')

EXCLUDE_ATTRIBUTES = [
	'subschemaSubentry',
	'hasSubordinates',
	'entryDN',
	'memberOf', 'MEMBEROF',
	'pwdChangedTime', 'PWDCHANGEDTIME',
	'pwdAccountLockedTime', 'PWDACCOUNTLOCKEDTIME',
	'pwdFailureTime', 'PWDFAILURETIME',
	'pwdHistory', 'PWDHISTORY',
	'pwdGraceUseTime', 'PWDGRACEUSETIME',
	'pwdReset', 'PWDRESET',
	'pwdPolicySubentry', 'PWDPOLICYSUBENTRY',
]

# don't use built-in OIDs from slapd
BUILTIN_OIDS = [
	# attributeTypes
	'1.3.6.1.1.4',                  # vendorName
	'1.3.6.1.1.5',                  # vendorVersion
	'1.3.6.1.4.1.250.1.57',         # labeledURI
	'1.3.6.1.4.1.250.1.32',         # krbName
	'1.3.6.1.4.1.1466.101.119.2',   # dynamicObject
	'1.3.6.1.4.1.1466.101.119.3',   # entryTtl
	'1.3.6.1.4.1.1466.101.119.4',   # dynamicSubtrees
	'1.3.6.1.4.1.1466.101.120.5',   # namingContexts
	'1.3.6.1.4.1.1466.101.120.6',   # altServer
	'1.3.6.1.4.1.1466.101.120.7',   # supportedExtension
	'1.3.6.1.4.1.1466.101.120.13',  # supportedControla
	'1.3.6.1.4.1.1466.101.120.14',  # supportedSASLMechanisms
	'1.3.6.1.4.1.1466.101.120.15',  # supportedLDAPVersion
	'1.3.6.1.4.1.1466.101.120.16',  # ldapSyntaxes (operational)
	'1.3.6.1.4.1.1466.101.120.111',  # extensibleObject
	'1.3.6.1.4.1.4203.1.4.1',       # OpenLDAProotDSE
	'1.3.6.1.4.1.4203.1.3.1',       # entry
	'1.3.6.1.4.1.4203.1.3.2',       # children
	'1.3.6.1.4.1.4203.1.3.3',       # supportedAuthPasswordSchemes
	'1.3.6.1.4.1.4203.1.3.4',       # authPassword
	'1.3.6.1.4.1.4203.1.3.5',       # supportedFeatures
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
	'2.5.4.0',                      # objectClass
	'2.5.4.1',                      # aliasedObjectName
	'2.5.4.3',                      # cn
	'2.5.4.35',                     # userPassword
	'2.5.4.41',                     # name
	'2.5.4.49',                     # dn
	'2.5.6.0',                      # top
	'2.5.6.1',                      # alias
	'2.5.17.0',                     # subentry
	'2.5.17.2',                     # collectiveAttributeSubentry
	'2.5.18.1',                     # createTimestamp
	'2.5.18.2',                     # modifyTimestamp
	'2.5.18.3',                     # creatorsName
	'2.5.18.4',                     # modifiersName
	'2.5.18.5',                     # administrativeRole
	'2.5.18.6',                     # subtreeSpecification
	'2.5.18.7',                     # collectiveExclusions
	'2.5.18.9',                     # hasSubordinates
	'2.5.18.10',                    # subschemaSubentry
	'2.5.18.12',                    # collectiveAttributeSubentries
	'2.5.20.1',                     # subschema
	'2.5.21.1',                     # ditStructureRules
	'2.5.21.2',                     # ditContentRules
	'2.5.21.4',                     # matchingRules
	'2.5.21.5',                     # attributeTypes
	'2.5.21.6',                     # objectClasses
	'2.5.21.7',                     # nameForms
	'2.5.21.8',                     # matchingRuleUse
	'2.5.21.9',                     # structuralObjectClass
	'1.3.6.1.1.16.4',               # entryUUID
	# old OIDs from OpenLDAP 2.3 Experimental OID space
	'1.3.6.1.4.1.4203.666.1.33',    # entryDN (OL 2.3)
	'1.3.6.1.4.1.4203.666.11.1.3.0.1',  # olcAccess
	'1.3.6.1.4.1.4203.666.11.1.3.0.2',  # olcAllows
	'1.3.6.1.4.1.4203.666.11.1.3.0.3',  # olcArgsFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.4',  # olcAttributeTypes
	'1.3.6.1.4.1.4203.666.11.1.3.0.5',  # olcAttributeOptions
	'1.3.6.1.4.1.4203.666.11.1.3.0.6',  # olcAuthIDRewrite
	'1.3.6.1.4.1.4203.666.11.1.3.0.7',  # olcAuthzPolicy
	'1.3.6.1.4.1.4203.666.11.1.3.0.8',  # olcAuthzRegexp
	'1.3.6.1.4.1.4203.666.11.1.3.0.9',  # olcBackend
	'1.3.6.1.4.1.4203.666.11.1.3.0.10',  # olcConcurrency
	'1.3.6.1.4.1.4203.666.11.1.3.0.11',  # olcConnMaxPending
	'1.3.6.1.4.1.4203.666.11.1.3.0.12',  # olcConnMaxPendingAuth
	'1.3.6.1.4.1.4203.666.11.1.3.0.13',  # olcDatabase
	'1.3.6.1.4.1.4203.666.11.1.3.0.14',  # olcDefaultSearchBase
	'1.3.6.1.4.1.4203.666.11.1.3.0.15',  # olcDisallows
	'1.3.6.1.4.1.4203.666.11.1.3.0.16',  # olcDitContentRules
	'1.3.6.1.4.1.4203.666.11.1.3.0.17',  # olcGentleHUP
	'1.3.6.1.4.1.4203.666.11.1.3.0.18',  # olcIdleTimeout
	'1.3.6.1.4.1.4203.666.11.1.3.0.19',  # olcInclude
	'1.3.6.1.4.1.4203.666.11.1.3.0.20',  # olcIndexSubstrIfMinLen
	'1.3.6.1.4.1.4203.666.11.1.3.0.21',  # olcIndexSubstrIfMaxLen
	'1.3.6.1.4.1.4203.666.11.1.3.0.22',  # olcIndexSubstrAnyLen
	'1.3.6.1.4.1.4203.666.11.1.3.0.23',  # olcIndexSubstrAnyStep
	'1.3.6.1.4.1.4203.666.11.1.3.0.26',  # olcLocalSSF
	'1.3.6.1.4.1.4203.666.11.1.3.0.27',  # olcLogFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.28',  # olcLogLevel
	'1.3.6.1.4.1.4203.666.11.1.3.0.30',  # olcModuleLoad
	'1.3.6.1.4.1.4203.666.11.1.3.0.31',  # olcModulePath
	'1.3.6.1.4.1.4203.666.11.1.3.0.32',  # olcObjectClasses
	'1.3.6.1.4.1.4203.666.11.1.3.0.33',  # olcObjectIdentifier
	'1.3.6.1.4.1.4203.666.11.1.3.0.34',  # olcOverlay
	'1.3.6.1.4.1.4203.666.11.1.3.0.35',  # olcPasswordCryptSaltFormat
	'1.3.6.1.4.1.4203.666.11.1.3.0.36',  # olcPasswordHash
	'1.3.6.1.4.1.4203.666.11.1.3.0.37',  # olcPidFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.38',  # olcPlugin
	'1.3.6.1.4.1.4203.666.11.1.3.0.39',  # olcPluginLogFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.40',  # olcReadOnly
	'1.3.6.1.4.1.4203.666.11.1.3.0.41',  # olcReferral
	'1.3.6.1.4.1.4203.666.11.1.3.0.43',  # olcReplicaArgsFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.44',  # olcReplicaPidFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.45',  # olcReplicationInterval
	'1.3.6.1.4.1.4203.666.11.1.3.0.46',  # olcReplogFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.47',  # olcRequires
	'1.3.6.1.4.1.4203.666.11.1.3.0.48',  # olcRestrict
	'1.3.6.1.4.1.4203.666.11.1.3.0.49',  # olcReverseLookup
	'1.3.6.1.4.1.4203.666.11.1.3.0.51',  # olcRootDSE
	'1.3.6.1.4.1.4203.666.11.1.3.0.53',  # olcSaslHost
	'1.3.6.1.4.1.4203.666.11.1.3.0.54',  # olcSaslRealm
	'1.3.6.1.4.1.4203.666.11.1.3.0.56',  # olcSaslSecProps
	'1.3.6.1.4.1.4203.666.11.1.3.0.58',  # olcSchemaDN
	'1.3.6.1.4.1.4203.666.11.1.3.0.59',  # olcSecurity
	'1.3.6.1.4.1.4203.666.11.1.3.0.60',  # olcSizeLimit
	'1.3.6.1.4.1.4203.666.11.1.3.0.61',  # olcSockbufMaxIncoming
	'1.3.6.1.4.1.4203.666.11.1.3.0.62',  # olcSockbufMaxIncomingAuth
	'1.3.6.1.4.1.4203.666.11.1.3.0.63',  # olcSrvtab
	'1.3.6.1.4.1.4203.666.11.1.3.0.66',  # olcThreads
	'1.3.6.1.4.1.4203.666.11.1.3.0.67',  # olcTimeLimit
	'1.3.6.1.4.1.4203.666.11.1.3.0.68',  # olcTLSCACertificateFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.69',  # olcTLSCACertificatePath
	'1.3.6.1.4.1.4203.666.11.1.3.0.70',  # olcTLSCertificateFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.71',  # olcTLSCertificateKeyFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.72',  # olcTLSCipherSuite
	'1.3.6.1.4.1.4203.666.11.1.3.0.73',  # olcTLSCRLCheck
	'1.3.6.1.4.1.4203.666.11.1.3.0.74',  # olcTLSRandFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.75',  # olcTLSVerifyClient
	'1.3.6.1.4.1.4203.666.11.1.3.0.77',  # olcTLSDHParamFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.78',  # olcConfigFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.79',  # olcConfigDir
	'1.3.6.1.4.1.4203.666.11.1.3.0.80',  # olcToolThreads
	'1.3.6.1.4.1.4203.666.11.1.3.0.81',  # olcServerID
	'1.3.6.1.4.1.4203.666.11.1.3.0.82',  # olcTLSCRLFile
	'1.3.6.1.4.1.4203.666.11.1.3.0.83',  # olcSortVals
	'1.3.6.1.4.1.4203.666.11.1.3.0.84',  # olcIndexIntLen
	'1.3.6.1.4.1.4203.666.11.1.3.0.85',  # olcLdapSyntaxes
	'1.3.6.1.4.1.4203.666.11.1.3.0.86',  # olcAddContentAcl
	'1.3.6.1.4.1.4203.666.11.1.3.0.87',  # olcTLSProtocolMin
	'1.3.6.1.4.1.4203.666.11.1.3.0.88',  # olcWriteTimeout
	'1.3.6.1.4.1.4203.666.11.1.3.0.89',  # olcSaslAuxprops
	'1.3.6.1.4.1.4203.666.11.1.3.0.90',  # olcTCPBuffer
	'1.3.6.1.4.1.4203.666.11.1.3.0.93',  # olcListenerThreads
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.1',  # olcDbDirectory
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.2',  # olcDbIndex
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.3',  # olcDbMode
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.4',  # olcLastMod
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.5',  # olcLimits
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.6',  # olcMaxDerefDepth
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.7',  # olcReplica
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.8',  # olcRootDN
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.9',  # olcRootPW
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.10',  # olcSuffix
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.11',  # olcSyncrepl
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.12',  # olcUpdateDN
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.13',  # olcUpdateRef
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.15',  # olcSubordinate
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.16',  # olcMirrorMode
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.17',  # olcHidden
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.18',  # olcMonitoring
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.19',  # olcSyncUseSubentry
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.1',  # olcDbCacheSize
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.2',  # olcDbCheckpoint
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.3',  # olcDbConfig
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.4',  # olcDbNoSync
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.5',  # olcDbDirtyRead
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.6',  # olcDbIDLcacheSize
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.7',  # olcDbLinearIndex
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.8',  # olcDbLockDetect
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.9',  # olcDbSearchStack
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.10',  # olcDbShmKey
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.11',  # olcDbCacheFree
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.12',  # olcDbDNcacheSize
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.13',  # olcDbCryptFile
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.14',  # olcDbCryptKey
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.15',  # olcDbPageSize
	'1.3.6.1.4.1.4203.666.11.1.3.2.1.16',  # olcDbChecksum
	# new OIDs in official OpenLDAP 2.4 OID space
	'1.3.6.1.1.20',                    # entryDN (OL 2.4)
	'1.3.6.1.4.1.4203.1.12.2.3.0.1',   # olcAccess
	'1.3.6.1.4.1.4203.1.12.2.3.0.2',   # olcAllows
	'1.3.6.1.4.1.4203.1.12.2.3.0.3',   # olcArgsFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.4',   # olcAttributeTypes
	'1.3.6.1.4.1.4203.1.12.2.3.0.5',   # olcAttributeOptions
	'1.3.6.1.4.1.4203.1.12.2.3.0.6',   # olcAuthIDRewrite
	'1.3.6.1.4.1.4203.1.12.2.3.0.7',   # olcAuthzPolicy
	'1.3.6.1.4.1.4203.1.12.2.3.0.8',   # olcAuthzRegexp
	'1.3.6.1.4.1.4203.1.12.2.3.0.9',   # olcBackend
	'1.3.6.1.4.1.4203.1.12.2.3.0.10',  # olcConcurrency
	'1.3.6.1.4.1.4203.1.12.2.3.0.11',  # olcConnMaxPending
	'1.3.6.1.4.1.4203.1.12.2.3.0.12',  # olcConnMaxPendingAuth
	'1.3.6.1.4.1.4203.1.12.2.3.0.13',  # olcDatabase
	'1.3.6.1.4.1.4203.1.12.2.3.0.14',  # olcDefaultSearchBase
	'1.3.6.1.4.1.4203.1.12.2.3.0.15',  # olcDisallows
	'1.3.6.1.4.1.4203.1.12.2.3.0.16',  # olcDitContentRules
	'1.3.6.1.4.1.4203.1.12.2.3.0.17',  # olcGentleHUP
	'1.3.6.1.4.1.4203.1.12.2.3.0.18',  # olcIdleTimeout
	'1.3.6.1.4.1.4203.1.12.2.3.0.19',  # olcInclude
	'1.3.6.1.4.1.4203.1.12.2.3.0.20',  # olcIndexSubstrIfMinLen
	'1.3.6.1.4.1.4203.1.12.2.3.0.21',  # olcIndexSubstrIfMaxLen
	'1.3.6.1.4.1.4203.1.12.2.3.0.22',  # olcIndexSubstrAnyLen
	'1.3.6.1.4.1.4203.1.12.2.3.0.23',  # olcIndexSubstrAnyStep
	'1.3.6.1.4.1.4203.1.12.2.3.0.26',  # olcLocalSSF
	'1.3.6.1.4.1.4203.1.12.2.3.0.27',  # olcLogFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.28',  # olcLogLevel
	'1.3.6.1.4.1.4203.1.12.2.3.0.30',  # olcModuleLoad
	'1.3.6.1.4.1.4203.1.12.2.3.0.31',  # olcModulePath
	'1.3.6.1.4.1.4203.1.12.2.3.0.32',  # olcObjectClasses
	'1.3.6.1.4.1.4203.1.12.2.3.0.33',  # olcObjectIdentifier
	'1.3.6.1.4.1.4203.1.12.2.3.0.34',  # olcOverlay
	'1.3.6.1.4.1.4203.1.12.2.3.0.35',  # olcPasswordCryptSaltFormat
	'1.3.6.1.4.1.4203.1.12.2.3.0.36',  # olcPasswordHash
	'1.3.6.1.4.1.4203.1.12.2.3.0.37',  # olcPidFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.38',  # olcPlugin
	'1.3.6.1.4.1.4203.1.12.2.3.0.39',  # olcPluginLogFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.40',  # olcReadOnly
	'1.3.6.1.4.1.4203.1.12.2.3.0.41',  # olcReferral
	'1.3.6.1.4.1.4203.1.12.2.3.0.43',  # olcReplicaArgsFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.44',  # olcReplicaPidFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.45',  # olcReplicationInterval
	'1.3.6.1.4.1.4203.1.12.2.3.0.46',  # olcReplogFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.47',  # olcRequires
	'1.3.6.1.4.1.4203.1.12.2.3.0.48',  # olcRestrict
	'1.3.6.1.4.1.4203.1.12.2.3.0.49',  # olcReverseLookup
	'1.3.6.1.4.1.4203.1.12.2.3.0.51',  # olcRootDSE
	'1.3.6.1.4.1.4203.1.12.2.3.0.53',  # olcSaslHost
	'1.3.6.1.4.1.4203.1.12.2.3.0.54',  # olcSaslRealm
	'1.3.6.1.4.1.4203.1.12.2.3.0.56',  # olcSaslSecProps
	'1.3.6.1.4.1.4203.1.12.2.3.0.58',  # olcSchemaDN
	'1.3.6.1.4.1.4203.1.12.2.3.0.59',  # olcSecurity
	'1.3.6.1.4.1.4203.1.12.2.3.0.60',  # olcSizeLimit
	'1.3.6.1.4.1.4203.1.12.2.3.0.61',  # olcSockbufMaxIncoming
	'1.3.6.1.4.1.4203.1.12.2.3.0.62',  # olcSockbufMaxIncomingAuth
	'1.3.6.1.4.1.4203.1.12.2.3.0.63',  # olcSrvtab
	'1.3.6.1.4.1.4203.1.12.2.3.0.66',  # olcThreads
	'1.3.6.1.4.1.4203.1.12.2.3.0.67',  # olcTimeLimit
	'1.3.6.1.4.1.4203.1.12.2.3.0.68',  # olcTLSCACertificateFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.69',  # olcTLSCACertificatePath
	'1.3.6.1.4.1.4203.1.12.2.3.0.70',  # olcTLSCertificateFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.71',  # olcTLSCertificateKeyFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.72',  # olcTLSCipherSuite
	'1.3.6.1.4.1.4203.1.12.2.3.0.73',  # olcTLSCRLCheck
	'1.3.6.1.4.1.4203.1.12.2.3.0.74',  # olcTLSRandFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.75',  # olcTLSVerifyClient
	'1.3.6.1.4.1.4203.1.12.2.3.0.77',  # olcTLSDHParamFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.78',  # olcConfigFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.79',  # olcConfigDir
	'1.3.6.1.4.1.4203.1.12.2.3.0.80',  # olcToolThreads
	'1.3.6.1.4.1.4203.1.12.2.3.0.81',  # olcServerID
	'1.3.6.1.4.1.4203.1.12.2.3.0.82',  # olcTLSCRLFile
	'1.3.6.1.4.1.4203.1.12.2.3.0.83',  # olcSortVals
	'1.3.6.1.4.1.4203.1.12.2.3.0.84',  # olcIndexIntLen
	'1.3.6.1.4.1.4203.1.12.2.3.0.85',  # olcLdapSyntaxes
	'1.3.6.1.4.1.4203.1.12.2.3.0.86',  # olcAddContentAcl
	'1.3.6.1.4.1.4203.1.12.2.3.0.87',  # olcTLSProtocolMin
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.1',  # olcDbDirectory
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.2',  # olcDbIndex
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.3',  # olcDbMode
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.4',  # olcLastMod
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.5',  # olcLimits
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.6',  # olcMaxDerefDepth
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.7',  # olcReplica
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.8',  # olcRootDN
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.9',  # olcRootPW
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.10',  # olcSuffix
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.11',  # olcSyncrepl
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.12',  # olcUpdateDN
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.13',  # olcUpdateRef
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.15',  # olcSubordinate
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.16',  # olcMirrorMode
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.17',  # olcHidden
	'1.3.6.1.4.1.4203.1.12.2.3.2.0.18',  # olcMonitoring
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.1',  # olcDbCacheSize
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.2',  # olcDbCheckpoint
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.3',  # olcDbConfig
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.4',  # olcDbNoSync
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.5',  # olcDbDirtyRead
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.6',  # olcDbIDLcacheSize
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.7',  # olcDbLinearIndex
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.8',  # olcDbLockDetect
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.9',  # olcDbSearchStack
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.10',  # olcDbShmKey
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.11',  # olcDbCacheFree
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.12',  # olcDbDNcacheSize
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.13',  # olcDbCryptFile
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.14',  # olcDbCryptKey
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.15',  # olcDbPageSize
	'1.3.6.1.4.1.4203.1.12.2.3.2.1.16',  # olcDbChecksum
	# objectClasses
	'2.16.840.1.113730.3.2.6',  # referral
	'2.16.840.1.113730.3.1.34',  # ref (operational)
	# old OIDs from OpenLDAP 2.3 Experimental OID space
	'1.3.6.1.4.1.4203.666.11.1.4.0.0',  # olcConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.1',  # olcGlobal
	'1.3.6.1.4.1.4203.666.11.1.4.0.2',  # olcSchemaConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.3',  # olcBackendConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.4',  # olcDatabaseConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.5',  # olcOverlayConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.6',  # olcIncludeFile
	'1.3.6.1.4.1.4203.666.11.1.4.0.7',  # olcFrontendConfig
	'1.3.6.1.4.1.4203.666.11.1.4.0.8',  # olcModuleList
	'1.3.6.1.4.1.4203.666.11.1.4.2.1.1',  # olcBdbConfig
	'1.3.6.1.4.1.4203.666.11.1.4.2.2.1',  # olcLdifConfig
	'1.3.6.1.4.1.4203.1.12.2.4.2.12.1',   # olcMdbConfig
	'1.3.6.1.4.1.4203.666.11.1.4.2.12.1',  # olcMdbConfig
	'1.3.6.1.4.1.4203.1.12.2.3.2.12.1',      # olcDbMaxReaders
	'1.3.6.1.4.1.4203.666.11.1.3.2.12.1',  # olcDbMaxReaders
	'1.3.6.1.4.1.4203.1.12.2.3.2.12.2',      # olcDbMaxSize
	'1.3.6.1.4.1.4203.666.11.1.3.2.12.2',  # olcDbMaxSize
	'1.3.6.1.4.1.4203.1.12.2.3.2.12.3',      # olcDbEnvFlags
	'1.3.6.1.4.1.4203.666.11.1.3.2.12.3',  # olcDbEnvFlags
	# new OIDs in official OpenLDAP 2.4 OID space
	'1.3.6.1.4.1.4203.1.12.2.4.0.0',  # olcConfig
	'1.3.6.1.4.1.4203.1.12.2.4.0.1',  # olcGlobal
	'1.3.6.1.4.1.4203.1.12.2.4.0.2',  # olcSchemaConfig
	'1.3.6.1.4.1.4203.1.12.2.4.0.3',  # olcBackendConfig
	'1.3.6.1.4.1.4203.1.12.2.4.0.4',  # olcDatabaseConfig
	'1.3.6.1.4.1.4203.1.12.2.4.0.5',  # olcOverlayConfig
	'1.3.6.1.4.1.4203.1.12.2.4.0.6',  # olcIncludeFile
	'1.3.6.1.4.1.4203.1.12.2.4.0.7',  # olcFrontendConfig
	'1.3.6.1.4.1.4203.1.12.2.4.0.8',  # olcModuleList
	'1.3.6.1.4.1.4203.1.12.2.4.2.1.1',  # olcBdbConfig
	'1.3.6.1.4.1.4203.1.12.2.4.2.2.1',  # olcLdifConfig
	# UCS 3.0
	'1.3.6.1.4.1.4203.666.11.1.3.0.93',  # olcListenerThreads
	# UCS 3.1
	'1.3.6.1.4.1.4203.666.11.1.3.2.0.20',  # olcExtraAttrs
	# UCS 2.0
	'2.5.4.34',  # seeAlso
	'0.9.2342.19200300.100.1.1',  # userid
	'2.5.4.13',  # description
	'1.3.6.1.1.1.1.1',  # gidNumber
	'1.3.6.1.1.1.1.0',  # uidNumber
	# memberOf overlay
	'1.2.840.113556.1.2.102',  # memberOf
	# ppolicy overlay
	'1.3.6.1.4.1.42.2.27.8.1.16',  # pwdChangedTime
	'1.3.6.1.4.1.42.2.27.8.1.17',  # pwdAccountLockedTime
	'1.3.6.1.4.1.42.2.27.8.1.19',  # pwdFailureTime
	'1.3.6.1.4.1.42.2.27.8.1.20',  # pwdHistory
	'1.3.6.1.4.1.42.2.27.8.1.21',  # pwdGraceUseTime
	'1.3.6.1.4.1.42.2.27.8.1.22',  # pwdReset
	'1.3.6.1.4.1.42.2.27.8.1.23',  # pwdPolicySubentry
]


class LDIFObject:

	def __init__(self, filename):
		self.fp = open(filename, 'a')
		os.chmod(filename, 0o600)

	def __print_attribute(self, attribute, value):
		pos = len(attribute) + 2  # +colon+space
		encode = 0
		if '\n' in value:
			encode = 1
		try:
			if isinstance(value, tuple):
				(newval, leng) = value
			else:
				newval = value
			newval = newval.encode('ascii')
		except UnicodeError:
			encode = 1
		if encode:
			pos += 1  # value will be base64 encoded, thus two colons
			print >>self.fp, '%s::' % attribute,
			value = base64.encodestring(value).replace('\n', '')
		else:
			print >>self.fp, '%s:' % attribute,

		if not value:
			print >>self.fp

		while value:
			if pos == 1:
				# first column is space
				print >>self.fp, '',
			print >>self.fp, value[0:60 - pos]
			value = value[60 - pos:]
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
		for ldap_op, attr, vals in ml:
			self.__new_section()
			if ldap_op == ldap.MOD_REPLACE:
				op = 'replace'
			elif ldap_op == ldap.MOD_ADD:
				op = 'add'
			elif ldap_op == ldap.MOD_DELETE:
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

	def rename_s(self, dn, newrdn, newsuperior=None, delold=1, serverctrls=None, clientctrls=None):
		self.__new_entry(dn)
		self.__print_attribute('changetype', 'modrdn')
		self.__print_attribute('newrdn', newrdn)
		if newsuperior:
			self.__print_attribute('newsuperior', newsuperior)
		self.__print_attribute('deleteoldrdn', '1' if delold else '0')
		self.__end_entry()


reconnect = 0
connection = None


def connect(ldif=0):
	global connection
	global reconnect

	if connection and not reconnect:
		return connection

	if not os.path.exists(LDIF_FILE) and not ldif:
		# ldap connection
		if not os.path.exists('/etc/ldap/rootpw.conf'):
			pw = new_password()
			init_slapd('restart')
		else:
			pw = get_password()
			if not pw:
				pw = new_password()
				init_slapd('restart')

		local_ip = '127.0.0.1'
		local_port = listener.baseConfig.get('slapd/port', '7389').split(',')[0]

		connection = ldap.open(local_ip, int(local_port))
		connection.simple_bind_s('cn=update,' + listener.baseConfig['ldap/base'], pw)
	else:
		connection = LDIFObject(LDIF_FILE)

	reconnect = 0
	return connection


def addlist(new):
	al = []
	for key in new.keys():
		if key in EXCLUDE_ATTRIBUTES:
			continue
		al.append((key, new[key]))
	return al


def modlist(old, new):
	ml = []
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


def subschema_oids_with_sup(subschema, ldap_type, oid, result):
	if oid in BUILTIN_OIDS or oid in result:
		return

	obj = subschema.get_obj(ldap_type, oid)
	for i in obj.sup:
		sup_obj = subschema.get_obj(ldap_type, i)
		subschema_oids_with_sup(subschema, ldap_type, sup_obj.oid, result)
	result.append(oid)


def subschema_sort(subschema, ldap_type):
	result = []
	for oid in subschema.listall(ldap_type):
		subschema_oids_with_sup(subschema, ldap_type, oid, result)
	return result


def update_schema(attr):

	def _insert_linebereak(obj):
		# Bug 46743: Ensure lines are not longer than 2000 characters or slapd fails to start
		max_length = 2000
		obj_lines = []
		while len(obj) > max_length:
			linebreak_postion = obj.rindex(' ', 0, max_length)
			obj_lines.append(obj[:linebreak_postion])
			obj = obj[linebreak_postion + 1:]
		obj_lines.append(obj)
		return '\n '.join(obj_lines)

	listener.setuid(0)
	try:
		fp = open('/var/lib/univention-ldap/schema.conf.new', 'w')
	finally:
		listener.unsetuid()

	print >>fp, '# This schema was automatically replicated from the master server'
	print >>fp, '# Please do not edit this file\n'
	subschema = ldap.schema.SubSchema(attr)

	for oid in subschema_sort(subschema, ldap.schema.AttributeType):
		if oid in BUILTIN_OIDS:
			continue
		obj = _insert_linebereak(str(subschema.get_obj(ldap.schema.AttributeType, oid)))
		print >>fp, 'attributetype %s' % (obj,)

	for oid in subschema_sort(subschema, ldap.schema.ObjectClass):
		if oid in BUILTIN_OIDS:
			continue
		obj = _insert_linebereak(str(subschema.get_obj(ldap.schema.ObjectClass, oid)))
		print >>fp, 'objectclass %s' % (obj,)

	fp.close()

	# move temporary file
	listener.setuid(0)
	try:
		os.rename('/var/lib/univention-ldap/schema.conf.new', '/var/lib/univention-ldap/schema.conf')
	finally:
		listener.unsetuid()

	init_slapd('restart')


def getOldValues(ldapconn, dn):
	"""
	get "old" from local ldap server
	"ldapconn": connection to local ldap server
	"""
	if not isinstance(ldapconn, LDIFObject):
		try:
			res = ldapconn.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)', ['*', '+'])
		except ldap.NO_SUCH_OBJECT as ex:
			ud.debug(ud.LISTENER, ud.ALL, "replication: LOCAL not found: %s %s" % (dn, ex))
			old = {}
		else:
			try:
				((_dn, old),) = res
				entryCSN = old.get('entryCSN', None)
				ud.debug(ud.LISTENER, ud.ALL, "replication: LOCAL found result: %s %s" % (dn, entryCSN))
			except (TypeError, ValueError) as ex:
				ud.debug(ud.LISTENER, ud.ALL, "replication: LOCAL empty result: %s" % (dn,))
				old = {}
	else:
		ud.debug(ud.LISTENER, ud.ALL, "replication: LDIF empty result: %s" % (dn,))
		old = {}

	return old


def _delete_dn_recursive(l, dn):
	try:
		l.delete_s(dn)
	except ldap.NOT_ALLOWED_ON_NONLEAF:
		ud.debug(ud.LISTENER, ud.WARN, 'replication: Failed to delete non leaf object: dn=[%s];' % dn)
		dns = [dn2 for dn2, _attr in l.search_s(dn, ldap.SCOPE_SUBTREE, '(objectClass=*)', attrlist=['dn'], attrsonly=1)]
		dns.reverse()
		for dn in dns:
			l.delete_s(dn)
	except ldap.NO_SUCH_OBJECT:
		pass


def _backup_dn_recursive(l, dn):
	if isinstance(l, LDIFObject):
		return

	backup_file = os.path.join(BACKUP_DIR, str(time.time()))
	ud.debug(ud.LISTENER, ud.PROCESS, 'replication: dump %s to %s' % (dn, backup_file))
	with open(backup_file, 'w+') as fd:
		os.fchmod(fd.fileno(), 0o600)
		ldif_writer = ldifparser.LDIFWriter(fd)
		for dn, entry in l.search_s(dn, ldap.SCOPE_SUBTREE, '(objectClass=*)', attrlist=['*', '+']):
			ldif_writer.unparse(dn, entry)


def _remove_file(pathname):
	ud.debug(ud.LISTENER, ud.ALL, 'replication: removing %s' % (pathname,))
	try:
		os.remove(pathname)
	except EnvironmentError as ex:
		if ex.errno != ENOENT:
			ud.debug(ud.LISTENER, ud.ERROR, 'replication: failed to remove %s: %s' % (pathname, ex))


def _add_object_from_new(l, dn, new):
	al = addlist(new)
	try:
		l.add_s(dn, al)
	except ldap.OBJECT_CLASS_VIOLATION as ex:
		log_ldap(ud.ERROR, 'object class violation while adding', ex, dn=dn)


def _modify_object_from_old_and_new(l, dn, old, new):
	ml = modlist(old, new)
	if ml:
		ud.debug(ud.LISTENER, ud.ALL, 'replication: modify: %s' % dn)
		l.modify_s(dn, ml)


def _read_dn_from_file(filename):
	old_dn = None

	try:
		with open(filename, 'r') as f:
			old_dn = f.read()
	except EnvironmentError as ex:
		ud.debug(ud.LISTENER, ud.ERROR, 'replication: failed to open/read modrdn file %s: %s' % (filename, ex))

	return old_dn


def check_file_system_space():
	if not listener.baseConfig.is_true('ldap/replication/filesystem/check'):
		return

	stat = os.statvfs(LDAP_DIR)
	free_space = stat.f_bavail * stat.f_frsize
	limit = float(listener.baseConfig.get('ldap/replication/filesystem/limit', '10')) * 1024.0 * 1024.0
	if free_space >= limit:
		return

	fqdn = '%(hostname)s.%(domainname)s' % listener.baseConfig
	ud.debug(ud.LISTENER, ud.ERROR, 'replication: Critical disk space. The Univention LDAP Listener was stopped')
	msg = MIMEText(
		'The Univention LDAP Listener process was stopped on %s.\n\n\n'
		'The result of statvfs(%s):\n'
		' %r\n\n'
		'Please free up some disk space and restart the Univention LDAP Listener with the following command:\n'
		' /etc/init.d/univention-directory-listener start' % (fqdn, LDAP_DIR, stat))
	msg['Subject'] = 'Alert: Critical disk space on %s' % (fqdn,)
	sender = 'root'
	recipient = listener.baseConfig.get('ldap/replication/filesystem/recipient', sender)

	msg['From'] = sender
	msg['To'] = recipient

	s = smtplib.SMTP()
	s.connect()
	s.sendmail(sender, [recipient], msg.as_string())
	s.close()

	listener.run('/etc/init.d/univention-directory-listener', ['univention-directory-listener', 'stop'], uid=0, wait=True)


def handler(dn, new, listener_old, operation):
	global reconnect
	if not slave:
		return 1

	check_file_system_space()

	ud.debug(ud.LISTENER, ud.INFO, 'replication: Running handler %s for: %s' % (operation, dn))
	if dn == 'cn=Subschema':
		return update_schema(new)

	connect_count = 0
	connected = 0

	while connect_count < 31 and not connected:
		try:
			l = connect()
		except ldap.LDAPError as ex:
			connect_count += 1
			if connect_count >= 30:
				log_ldap(ud.ERROR, 'going into LDIF mode', ex)
				reconnect = 1
				l = connect(ldif=1)
			else:
				log_ldap(ud.WARN, 'Can not connect LDAP Server, retry in 10 seconds', ex)
				reconnect = 1
				time.sleep(10)
		else:
			connected = 1

	if 'pwdAttribute' in new.keys():
		if new['pwdAttribute'][0] == 'userPassword':
			new['pwdAttribute'] = ['2.5.4.35']

	try:
		# Read old entry directly from LDAP server
		if not isinstance(l, LDIFObject):
			old = getOldValues(l, dn)

			# Check if both entries really match
			match = 1
			if len(old) != len(listener_old):
				ud.debug(ud.LISTENER, ud.INFO, 'replication: LDAP keys=%s; listener keys=%s' % (old.keys(), listener_old.keys()))
				match = 0
			else:
				for k in old.keys():
					if k in EXCLUDE_ATTRIBUTES:
						continue
					if k not in listener_old:
						ud.debug(ud.LISTENER, ud.INFO, 'replication: listener does not have key %s' % (k,))
						match = 0
						break
					if len(old[k]) != len(listener_old[k]):
						ud.debug(ud.LISTENER, ud.INFO, 'replication: LDAP and listener values diff for %s' % (k,))
						match = 0
						break
					for v in old[k]:
						if v not in listener_old[k]:
							ud.debug(ud.LISTENER, ud.INFO, 'replication: listener does not have value for key %s' % (k,))
							match = 0
							break
			if not match:
				ud.debug(ud.LISTENER, ud.INFO, 'replication: old entries from LDAP server and Listener do not match')
		else:
			old = listener_old

		# add
		if new:
			if os.path.exists(CURRENT_MODRDN) and not isinstance(l, LDIFObject):
				target_uuid_file = os.readlink(CURRENT_MODRDN)
				old_dn = _read_dn_from_file(CURRENT_MODRDN)

				new_entryUUID = new['entryUUID'][0]
				modrdn_cache = os.path.join(STATE_DIR, new_entryUUID)
				if modrdn_cache == target_uuid_file:
					ud.debug(ud.LISTENER, ud.PROCESS, 'replication: rename phase II: %s (entryUUID=%s)' % (dn, new_entryUUID))

					if old:
						# this means the target already exists, we have to delete this old object
						ud.debug(ud.LISTENER, ud.PROCESS, 'replication: the rename target already exists in the local LDAP, backup and remove the dn: %s' % (dn,))
						_backup_dn_recursive(l, dn)
						_delete_dn_recursive(l, dn)

					if getOldValues(l, old_dn):
						# the normal rename is possible
						new_dn = ldap.dn.str2dn(dn)
						new_parent = ldap.dn.dn2str(new_dn[1:])
						new_rdn = ldap.dn.dn2str([new_dn[0]])

						delold = 0
						for (key, value, _typ) in ldap.dn.str2dn(old_dn)[0]:
							if key not in new:
								ud.debug(ud.LISTENER, ud.ALL, 'replication: move: attr %s not present' % (key,))
								delold = 1
							elif value not in new[key]:
								ud.debug(ud.LISTENER, ud.ALL, 'replication: move: val %s not present in attr %s' % (value, new[key]))
								delold = 1

						ud.debug(ud.LISTENER, ud.PROCESS, 'replication: rename from %s to %s' % (old_dn, dn))
						l.rename_s(old_dn, new_rdn, new_parent, delold=delold)
						_remove_file(modrdn_cache)
					else:
						# the old object does not exists, so we have to re-create the new object
						ud.debug(ud.LISTENER, ud.ALL, 'replication: the local target does not exist, so the object will be added: %s' % dn)
						_add_object_from_new(l, dn, new)
						_remove_file(modrdn_cache)
				else:  # current_modrdn points to a different file
					ud.debug(ud.LISTENER, ud.PROCESS, 'replication: the current modrdn points to a different entryUUID: %s' % (target_uuid_file,))

					if old_dn:
						ud.debug(ud.LISTENER, ud.PROCESS, 'replication: the DN %s from the %s has to be backuped and removed' % (old_dn, CURRENT_MODRDN))
						_backup_dn_recursive(l, old_dn)
						_delete_dn_recursive(l, old_dn)
					else:
						ud.debug(ud.LISTENER, ud.WARN, 'replication: no old dn has been found')

					if not old:
						_add_object_from_new(l, dn, new)
					elif old:
						_modify_object_from_old_and_new(l, dn, old, new)

				_remove_file(CURRENT_MODRDN)

			elif old:  # modify: new and old
				_modify_object_from_old_and_new(l, dn, old, new)

			else:  # add: new and not old
				_add_object_from_new(l, dn, new)

		# delete
		elif old and not new:
			if operation == 'r':  # check for modrdn phase 1
				old_entryUUID = old['entryUUID'][0]
				ud.debug(ud.LISTENER, ud.PROCESS, 'replication: rename phase I: %s (entryUUID=%s)' % (dn, old_entryUUID))
				modrdn_cache = os.path.join(STATE_DIR, old_entryUUID)
				try:
					with open(modrdn_cache, 'w') as f:
						os.fchmod(f.fileno(), 0o600)
						f.write(dn)
					_remove_file(CURRENT_MODRDN)
					os.symlink(modrdn_cache, CURRENT_MODRDN)
					# that's it for now for command 'r' ==> modrdn will follow in the next step
					return
				except EnvironmentError as ex:
					# d'oh! output some message and continue doing a delete+add instead
					ud.debug(ud.LISTENER, ud.ERROR, 'replication: failed to open/write modrdn file %s: %s' % (modrdn_cache, ex))

			ud.debug(ud.LISTENER, ud.ALL, 'replication: delete: %s' % dn)
			_delete_dn_recursive(l, dn)
	except ldap.SERVER_DOWN as ex:
		log_ldap(ud.WARN, 'retrying', ex)
		reconnect = 1
		handler(dn, new, listener_old, operation)
	except ldap.ALREADY_EXISTS as ex:
		log_ldap(ud.WARN, 'trying to apply changes', ex, dn=dn)
		try:
			cur = l.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)')[0][1]
		except ldap.LDAPError as ex:
			log_ldap(ud.ERROR, 'going into LDIF mode', ex)
			reconnect = 1
			connect(ldif=1)
			handler(dn, new, listener_old, operation)
		else:
			handler(dn, new, cur, operation)
	except ldap.CONSTRAINT_VIOLATION as ex:
		log_ldap(ud.ERROR, 'Constraint violation', ex, dn=dn)
	except ldap.LDAPError as ex:
		log_ldap(ud.ERROR, 'Error', ex, dn=dn)
		if listener.baseConfig.get('ldap/replication/fallback', 'ldif') == 'restart':
			ud.debug(ud.LISTENER, ud.ERROR, 'replication: Uncaught LDAPError. Exiting Univention Directory Listener to retry replication with an updated copy of the current upstream object.')
			sys.exit(1)  # retry a bit later after restart via runsv
		else:
			reconnect = 1
			connect(ldif=1)
			handler(dn, new, listener_old, operation)


def log_ldap(severity, msg, ex, dn=None):
	ud.debug(ud.LISTENER, severity, 'replication: %s%s: %s' % (ex[0]['desc'], '; dn="%s"' % (dn,) if dn else '', msg))
	try:
		ud.debug(ud.LISTENER, severity, '\tadditional info: %s' % ex[0]['info'])
	except LookupError:
		pass
	try:
		ud.debug(ud.LISTENER, severity, '\tmachted dn: %s' % ex[0]['matched'])
	except LookupError:
		pass


def clean():
	global slave
	if not slave:
		return 1
	ud.debug(ud.LISTENER, ud.INFO, 'replication: removing cache')
	# init_slapd('stop')

	# FIXME
	listener.run('/usr/bin/killall', ['killall', '-9', 'slapd'], uid=0)
	time.sleep(1)  # FIXME

	dirname = '/var/lib/univention-ldap/ldap'
	listener.setuid(0)
	try:
		for f in os.listdir(dirname):
			filename = os.path.join(dirname, f)
			try:
				os.unlink(filename)
			except OSError:
				pass
		if os.path.exists(LDIF_FILE):
			os.unlink(LDIF_FILE)
	finally:
		listener.unsetuid()
	listener.run('/usr/sbin/univention-config-registry', ['univention-config-registry', 'commit', '/var/lib/univention-ldap/ldap/DB_CONFIG'], uid=0)


def initialize():
	ud.debug(ud.LISTENER, ud.INFO, 'replication: initialize')
	if not slave:
		ud.debug(ud.LISTENER, ud.INFO, 'replication: not slave')
		return 1
	clean()
	ud.debug(ud.LISTENER, ud.INFO, 'replication: initializing cache')
	new_password()
	init_slapd('start')


def randpw(length=64):
	"""Create random password.
	>>> randpw().isalnum()
	True
	"""
	password = subprocess.check_output([
		'pwgen',
		'--numerals',
		'--capitalize',
		'--secure',
		str(length),
		'1',
	]).strip()
	return password


def new_password():
	pw = randpw()

	listener.setuid(0)
	try:
		with open(ROOTPW_FILE, 'w') as fd:
			os.fchmod(fd.fileno(), 0o600)
			print >>fd, 'rootpw "%s"' % (pw.replace('\\', '\\\\').replace('"', '\\"'),)
	finally:
		listener.unsetuid()

	return pw


def get_password():
	listener.setuid(0)
	try:
		with open(ROOTPW_FILE, 'r') as fd:
			for line in fd:
				match = get_password.RE_ROOTDN.match(line)
				if match:
					return match.group(1).replace('\\"', '"').replace('\\\\', '\\')
			else:
				return ''
	finally:
		listener.unsetuid()


get_password.RE_ROOTDN = re.compile(r'^rootpw[ \t]+"((?:[^"\\]|\\["\\])+)"')


def init_slapd(arg):
	listener.run('/etc/init.d/slapd', ['slapd', arg], uid=0)
	time.sleep(1)
