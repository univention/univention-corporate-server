#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention AD Connector
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


import string
import ldap
import sys
import base64
import time
import os
import copy
import types
import re
import array
import ldap.sasl
import subprocess
import univention.uldap
import univention.connector
import univention.debug2 as ud
from ldap.controls import LDAPControl
from ldap.controls import SimplePagedResultsControl
from ldap.filter import escape_filter_chars
from samba.dcerpc import nbt
from samba.param import LoadParm
from samba.net import Net
from samba.credentials import Credentials, DONT_USE_KERBEROS
from samba import drs_utils
from samba.dcerpc import drsuapi, lsa, security
import samba.dcerpc.samr
from tempfile import NamedTemporaryFile


class kerberosAuthenticationFailed(Exception):
	pass


class netbiosDomainnameNotFound(Exception):
	pass


# page results
PAGE_SIZE = 1000
# microsoft ldap schema binary attributes
# -> ldbsearch --paged -H AD_SERVER -U CREDS --cross-ncs '(|(attributeSyntax=2.5.5.15)(attributeSyntax=2.5.5.10)(attributeSyntax=2.5.5.17)(attributeSyntax=2.5.5.7))' lDAPDisplayName
BINARY_ATTRIBUTES = [
	'addressEntryDisplayTable', 'addressEntryDisplayTableMSDOS', 'addressSyntax', 'assocNTAccount',
	'attributeCertificateAttribute', 'attributeSecurityGUID', 'audio',
	'auditingPolicy', 'authorityRevocationList', 'birthLocation',
	'cACertificate', 'categoryId', 'certificateRevocationList',
	'controlAccessRights', 'cRLPartitionedRevocationList', 'crossCertificatePair',
	'currentLocation', 'currentValue', 'currMachineId',
	'dBCSPwd', 'deltaRevocationList', 'dhcpClasses',
	'dhcpOptions', 'dhcpProperties', 'dNSProperty',
	'dnsRecord', 'domainWidePolicy', 'dSASignature',
	'eFSPolicy', 'foreignIdentifier', 'fRSExtensions',
	'fRSReplicaSetGUID', 'fRSRootSecurity', 'fRSVersionGUID',
	'groupMembershipSAM', 'helpData16', 'helpData32',
	'implementedCategories', 'invocationId', 'ipsecData',
	'jpegPhoto', 'lDAPIPDenyList', 'linkTrackSecret',
	'lmPwdHistory', 'logonHours', 'logonWorkstation',
	'machineWidePolicy', 'marshalledInterface', 'may',
	'meetingBlob', 'moniker', 'moveTreeState',
	'msAuthz-CentralAccessPolicyID', 'msCOM-ObjectId', 'msDFS-GenerationGUIDv2',
	'msDFS-LinkIdentityGUIDv2', 'msDFS-LinkSecurityDescriptorv2', 'msDFS-NamespaceIdentityGUIDv2',
	'msDFSR-ContentSetGuid', 'msDFSR-Extension', 'msDFSR-ReplicationGroupGuid',
	'msDFSR-Schedule', 'msDFS-TargetListv2', 'msDNS-DNSKEYRecords',
	'msDNS-SigningKeyDescriptors', 'msDNS-SigningKeys', 'msDRM-IdentityCertificate',
	'msDS-AllowedToActOnBehalfOfOtherIdentity', 'msDS-AzObjectGuid', 'msDS-BridgeHeadServersUsed',
	'msDS-ByteArray', 'msDS-Cached-Membership', 'mS-DS-ConsistencyGuid',
	'mS-DS-CreatorSID', 'msDS-ExecuteScriptPassword', 'msDS-GenerationId',
	'msDS-GroupMSAMembership', 'msDS-HasInstantiatedNCs', 'msDS-ManagedPassword',
	'msDS-ManagedPasswordId', 'msDS-ManagedPasswordPreviousId', 'msDS-OptionalFeatureGUID',
	'msDS-QuotaTrustee', 'mS-DS-ReplicatesNCReason', 'msDS-RetiredReplNCSignatures',
	'msDS-RevealedUsers', 'msDs-Schema-Extensions', 'msDS-Site-Affinity',
	'msDS-TransformationRulesCompiled', 'msDS-TrustForestTrustInfo', 'msExchBlockedSendersHash',
	'msExchDisabledArchiveGUID', 'msExchMailboxGuid', 'msExchMailboxSecurityDescriptor',
	'msExchMasterAccountSid', 'msExchSafeRecipientsHash', 'msExchSafeSendersHash',
	'msFVE-KeyPackage', 'msFVE-RecoveryGuid', 'msFVE-VolumeGuid',
	'msieee80211-Data', 'msImaging-PSPIdentifier', 'msImaging-ThumbprintHash',
	'msiScript', 'msKds-KDFParam', 'msKds-RootKeyData',
	'msKds-SecretAgreementParam', 'mSMQDigests', 'mSMQDigestsMig',
	'mSMQEncryptKey', 'mSMQOwnerID', 'mSMQQMID',
	'mSMQQueueType', 'mSMQSignCertificates', 'mSMQSignCertificatesMig',
	'mSMQSignKey', 'mSMQSiteID', 'mSMQSites',
	'mSMQUserSid', 'ms-net-ieee-80211-GP-PolicyReserved', 'ms-net-ieee-8023-GP-PolicyReserved',
	'msPKIAccountCredentials', 'msPKI-CredentialRoamingTokens', 'msPKIDPAPIMasterKeys',
	'msPKIRoamingTimeStamp', 'msRTCSIP-UserRoutingGroupId', 'msSPP-ConfigLicense',
	'msSPP-CSVLKSkuId', 'msSPP-IssuanceLicense', 'msSPP-KMSIds',
	'msSPP-OnlineLicense', 'msSPP-PhoneLicense', 'msTAPI-ConferenceBlob',
	'msTPM-SrkPubThumbprint', 'msWMI-TargetObject', 'netbootDUID',
	'netbootGUID', 'nTGroupMembers', 'ntPwdHistory',
	'nTSecurityDescriptor', 'objectGUID', 'objectSid',
	'oMObjectClass', 'oMTGuid', 'oMTIndxGuid',
	'originalDisplayTable', 'originalDisplayTableMSDOS', 'otherWellKnownObjects',
	'parentCACertificateChain', 'parentGUID', 'partialAttributeDeletionList',
	'partialAttributeSet', 'pekList', 'pendingCACertificates',
	'perMsgDialogDisplayTable', 'perRecipDialogDisplayTable', 'photo',
	'pKIEnrollmentAccess', 'pKIExpirationPeriod', 'pKIKeyUsage',
	'pKIOverlapPeriod', 'pKT', 'pKTGuid',
	'prefixMap', 'previousCACertificates', 'priorValue',
	'privateKey', 'productCode', 'proxiedObjectName',
	'publicKeyPolicy', 'registeredAddress', 'replicationSignature',
	'replPropertyMetaData', 'replUpToDateVector', 'repsFrom',
	'repsTo', 'requiredCategories', 'retiredReplDSASignatures',
	'samDomainUpdates', 'schedule', 'schemaIDGUID',
	'schemaInfo', 'searchGuide', 'securityIdentifier',
	'serviceClassID', 'serviceClassInfo', 'serviceInstanceVersion',
	'sIDHistory', 'siteGUID', 'supplementalCredentials',
	'supportedApplicationContext', 'syncWithSID', 'teletexTerminalIdentifier',
	'telexNumber', 'terminalServer', 'thumbnailLogo',
	'thumbnailPhoto', 'tokenGroups', 'tokenGroupsGlobalAndUniversal',
	'tokenGroupsNoGCAcceptable', 'trustAuthIncoming', 'trustAuthOutgoing',
	'unicodePwd', 'unixUserPassword', 'upgradeProductCode',
	'userCert', 'userCertificate', 'userPassword',
	'userPKCS12', 'userSMIMECertificate', 'volTableGUID',
	'volTableIdxGUID', 'wellKnownObjects', 'winsockAddresses',
]


def activate_user(connector, key, object):
	# set userAccountControl to 544
	for i in range(0, 10):
		try:
			connector.lo_ad.lo.modify_s(compatible_modstring(object['dn']), [(ldap.MOD_REPLACE, 'userAccountControl', ['544'])])
		except ldap.NO_SUCH_OBJECT:
			time.sleep(1)
			continue
		return True
	return False


def set_univentionObjectFlag_to_synced(connector, key, ucs_object):
	_d = ud.function('set_univentionObjectFlag_to_synced')  # noqa: F841

	if connector.baseConfig.is_true('ad/member', False):
		connector._object_mapping(key, ucs_object, 'ucs')

		ucs_result = connector.lo.search(base=ucs_object['dn'], attr=['univentionObjectFlag'])

		flags = ucs_result[0][1].get('univentionObjectFlag', [])
		if 'synced' not in flags:
			flags.append('synced')
			connector.lo.lo.lo.modify_s(univention.connector.ad.compatible_modstring(ucs_object['dn']), [(ldap.MOD_REPLACE, 'univentionObjectFlag', flags)])


def group_members_sync_from_ucs(connector, key, object):
	return connector.group_members_sync_from_ucs(key, object)


def object_memberships_sync_from_ucs(connector, key, object):
	return connector.object_memberships_sync_from_ucs(key, object)


def group_members_sync_to_ucs(connector, key, object):
	return connector.group_members_sync_to_ucs(key, object)


def object_memberships_sync_to_ucs(connector, key, object):
	return connector.object_memberships_sync_to_ucs(key, object)


def primary_group_sync_from_ucs(connector, key, object):
	return connector.primary_group_sync_from_ucs(key, object)


def primary_group_sync_to_ucs(connector, key, object):
	return connector.primary_group_sync_to_ucs(key, object)


def disable_user_from_ucs(connector, key, object):
	return connector.disable_user_from_ucs(key, object)


def set_userPrincipalName_from_ucr(connector, key, object):
	return connector.set_userPrincipalName_from_ucr(key, object)


def disable_user_to_ucs(connector, key, object):
	return connector.disable_user_to_ucs(key, object)


def encode_attrib(attrib):
	if not attrib or isinstance(attrib, type(u'')):  # referral or already unicode
		return attrib
	return unicode(attrib, 'utf8')


def encode_attriblist(attriblist):
	if not isinstance(attriblist, type([])):
		return encode_attrib(attriblist)
	else:
		for i in range(len(attriblist)):
			attriblist[i] = encode_attrib(attriblist[i])
		return attriblist


def encode_ad_object(ad_object):
	if isinstance(ad_object, type([])):
		return encode_attriblist(ad_object)
	else:
		for key in ad_object.keys():
			if key == 'objectSid':
				ad_object[key] = [decode_sid(ad_object[key][0])]
			elif key in BINARY_ATTRIBUTES:
				ud.debug(ud.LDAP, ud.INFO, "encode_ad_object: attrib %s ignored during encoding" % key)  # don't recode
			else:
				try:
					ad_object[key] = encode_attriblist(ad_object[key])
				except (ldap.SERVER_DOWN, SystemExit):
					raise
				except:  # FIXME: which exception is to be caught?
					ud.debug(ud.LDAP, ud.WARN, "encode_ad_object: encode attrib %s failed, ignored!" % key)
		return ad_object


def encode_ad_result(ad_result):
	'''
	encode an result from an python-ldap search
	'''
	return (encode_attrib(ad_result[0]), encode_ad_object(ad_result[1]))


def encode_ad_resultlist(ad_resultlist):
	'''
	encode an result from an python-ldap search
	'''
	for i in range(len(ad_resultlist)):
		ad_resultlist[i] = encode_ad_result(ad_resultlist[i])
	return ad_resultlist


def unix2ad_time(l):
	d = 116444736000000000L  # difference between 1601 and 1970
	return long(time.mktime(time.gmtime(time.mktime(time.strptime(l, "%Y-%m-%d")) + 90000))) * 10000000 + d  # 90000s are one day and one hour


def ad2unix_time(l):
	d = 116444736000000000L  # difference between 1601 and 1970
	return time.strftime("%d.%m.%y", time.gmtime((l - d) / 10000000))


def samba2ad_time(l):
	if l in [0, 1]:
		return l
	d = 116444736000000000L  # difference between 1601 and 1970
	return long(time.mktime(time.gmtime(l + 3600))) * 10000000 + d


def ad2samba_time(l):
	if l == 0:
		return l
	d = 116444736000000000L  # difference between 1601 and 1970
	return long(((l - d)) / 10000000)

# mapping funtions


def samaccountname_dn_mapping(connector, given_object, dn_mapping_stored, ucsobject, propertyname, propertyattrib, ocucs, ucsattrib, ocad, dn_attr=None):
	'''
	map dn of given object (which must have an samaccountname in AD)
	ocucs and ocad are objectclasses in UCS and AD
	'''
	object = copy.deepcopy(given_object)

	samaccountname = ''
	dn_attr_val = ''

	if object['dn'] is not None:
		if 'sAMAccountName' in object['attributes']:
			samaccountname = object['attributes']['sAMAccountName'][0]
		if dn_attr:
			if dn_attr in object['attributes']:
				dn_attr_val = object['attributes'][dn_attr][0]

	def dn_premapped(object, dn_key, dn_mapping_stored):
		if (dn_key not in dn_mapping_stored) or (not object[dn_key]):
			ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: not premapped (in first instance)")
			return False
		else:  # check if DN exists
			if ucsobject:
				if connector.get_object(object[dn_key]) is not None:
					ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: premapped AD object found")
					return True
				else:
					ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: premapped AD object not found")
					return False
			else:
				if connector.get_ucs_ldap_object(object[dn_key]) is not None:
					ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: premapped UCS object found")
					return True
				else:
					ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: premapped UCS object not found")
					return False

	for dn_key in ['dn', 'olddn']:
		ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: check newdn for key %s:" % dn_key)
		if dn_key in object and not dn_premapped(object, dn_key, dn_mapping_stored):

			dn = object[dn_key]

			# Skip Configuration objects with empty DNs
			if dn is None:
				break

			exploded_dn = ldap.dn.str2dn(dn)
			(_fst_rdn_attribute, fst_rdn_value, _flags) = exploded_dn[0][0]
			value = fst_rdn_value

			if ucsobject:
				# lookup the cn as sAMAccountName in AD to get corresponding DN, if not found create new
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: got an UCS-Object")

				if connector.property[propertyname].mapping_table and propertyattrib in connector.property[propertyname].mapping_table.keys():
					for ucsval, conval in connector.property[propertyname].mapping_table[propertyattrib]:
						if value.lower() == ucsval.lower():
							value = conval
							ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: map samaccountanme regarding to mapping-table")
							continue

				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: search in ad samaccountname=%s" % value)
				search_filter = format_escaped('(&(objectclass={0!e})(samaccountname={1!e}))', ocad, value)
				result = connector.lo_ad.search(filter=compatible_modstring(search_filter))
				if result and len(result) > 0 and result[0] and len(result[0]) > 0 and result[0][0]:  # no referral, so we've got a valid result
					addn = encode_attrib(result[0][0])
					if dn_key == 'olddn' or (dn_key == 'dn' and 'olddn' not in object):
						newdn = addn
					else:
						newdn_ad_rdn = ldap.dn.str2dn(addn)[0]
						newdn_ad = ldap.dn.dn2str([newdn_ad_rdn] + exploded_dn[1:])
						newdn = newdn_ad.lower().replace(connector.lo_ad.base.lower(), connector.lo.base.lower())

				else:
					newdn_rdn = [('cn', fst_rdn_value, ldap.AVA_STRING)]
					newdn = ldap.dn.dn2str([newdn_rdn] + exploded_dn[1:])  # new object, don't need to change

				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: newdn: %s" % newdn)
			else:
				# get the object to read the sAMAccountName in AD and use it as name
				# we have no fallback here, the given dn must be found in AD or we've got an error
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: got an AD-Object")
				i = 0

				while (not samaccountname):  # in case of olddn this is already set
					i = i + 1
					search_dn = dn
					if 'deleted_dn' in object:
						search_dn = object['deleted_dn']
					search_dn = compatible_modstring(search_dn)
					search_filter = format_escaped('(objectclass={0!e})', ocad)
					try:
						search_result = connector.lo_ad.search(base=search_dn, scope='base', filter=search_filter, attr=['sAMAccountName'])
						samaccountname = encode_attrib(search_result[0][1]['sAMAccountName'][0])
						ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: got samaccountname from AD")
					except ldap.NO_SUCH_OBJECT:  # AD may need time
						if i > 5:
							raise
						time.sleep(1)  # AD may need some time...

				if connector.property[propertyname].mapping_table and propertyattrib in connector.property[propertyname].mapping_table.keys():
					for ucsval, conval in connector.property[propertyname].mapping_table[propertyattrib]:
						if samaccountname.lower() == conval.lower():
							samaccountname = ucsval
							ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: map samaccountanme regarding to mapping-table")
							continue
						else:
							ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: samaccountname not in mapping-table")

				# search for object with this dn in ucs, needed if it lies in a different container
				ucsdn = ''
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: samaccountname is:%s" % samaccountname)

				search_filter = format_escaped(u'(&(objectclass={0!e})({1}={2!e}))', ocucs, ucsattrib, samaccountname)
				ucsdn_result = connector.search_ucs(filter=search_filter, base=connector.lo.base, scope='sub', attr=['objectClass'])

				if ucsdn_result and len(ucsdn_result) > 0 and ucsdn_result[0] and len(ucsdn_result[0]) > 0:
					ucsdn = ucsdn_result[0][0]

				if ucsdn and (dn_key == 'olddn' or (dn_key == 'dn' and 'olddn' not in object)):
					newdn = ucsdn
					ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: newdn is ucsdn")
				else:
					if dn_attr:
						newdn_rdn = [(dn_attr, dn_attr_val, ldap.AVA_STRING)]  # guess the old dn
					else:
						newdn_rdn = [(ucsattrib, samaccountname, ldap.AVA_STRING)]  # guess the old dn
					newdn = ldap.dn.dn2str([newdn_rdn] + exploded_dn[1:])
			try:
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: newdn for key %s:" % dn_key)
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: olddn: %s" % dn)
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: newdn: %s" % newdn)
			except:  # FIXME: which exception is to be caught?
				ud.debug(ud.LDAP, ud.INFO, "samaccount_dn_mapping: dn-print failed")

			object[dn_key] = encode_attrib(newdn)
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


def windowscomputer_dn_mapping(connector, given_object, dn_mapping_stored, isUCSobject):
	'''
	map dn of given windows computer using the samaccountname/uid
	connector is an instance of univention.connector.ad, given_object an object-dict,
	dn_mapping_stored a list of dn-types which are already mapped because they were stored in the config-file
	'''
	return samaccountname_dn_mapping(connector, given_object, dn_mapping_stored, isUCSobject, 'windowscomputer', u'samAccountName', u'posixAccount', 'uid', u'computer', 'cn')


def old_user_dn_mapping(connector, given_object):
	object = copy.deepcopy(given_object)

	# LDAP_SERVER_SHOW_DELETED_OID -> 1.2.840.113556.1.4.417
	ctrls = [LDAPControl('1.2.840.113556.1.4.417', criticality=1)]
	samaccountname = ''

	if 'sAMAccountName' in object:
		samaccountname = object['sAMAccountName']

	for dn_key in ['dn', 'olddn']:
		ud.debug(ud.LDAP, ud.INFO, "check newdn for key %s:" % dn_key)
		if dn_key in object:

			dn = object[dn_key]

			pos = string.find(dn, '=')
			pos2 = len(univention.connector.ad.explode_unicode_dn(dn)[0]) - 1
			attrib = dn[:pos]
			value = dn[pos + 1:pos2]

			if attrib == 'uid':
				# lookup the uid as sAMAccountName in AD to get corresponding DN, if not found create new User
				ud.debug(ud.LDAP, ud.INFO, "search in ad samaccountname=%s" % value)
				search_filter = format_escaped('(&(objectclass=user)(samaccountname={0!e}))', value)
				result = connector.lo_ad.search(filter=search_filter)
				ud.debug(ud.LDAP, ud.INFO, "search in result %s" % result)
				if result and len(result) > 0 and result[0] and len(result[0]) > 0 and result[0][0]:  # no referral, so we've got a valid result
					addn = encode_attrib(result[0][0])
					ud.debug(ud.LDAP, ud.INFO, "search in ad gave dn %s" % addn)
					# adpos2 = len(univention.connector.ad.explode_unicode_dn(addn)[0]) - 1
					# newdn = addn[:adpos2] + dn[pos2:]
					newdn = addn
				else:
					newdn = 'cn' + dn[pos:]

			else:
				# get the object to read the sAMAccountName in AD and use it as uid
				# we have no fallback here, the given dn must be found in AD or we've got an error
				i = 0
				while (not samaccountname):  # in case of olddn this is already set
					i = i + 1
					search_dn = dn
					if 'deleted_dn' in object:
						search_dn = object['deleted_dn']
					search_dn = compatible_modstring(search_dn)
					try:
						result = connector.lo_ad.search(
							base=search_dn,
							scope='base', filter='(objectClass=user)',
							attr=['sAMAccountName'], serverctrls=ctrls)
						samaccountname = encode_attrib(result[0][1]['sAMAccountName'][0])
					except ldap.NO_SUCH_OBJECT:  # AD may need time
						if i > 5:
							raise
						time.sleep(1)  # AD may need some time...

				pos = string.find(dn, '=')
				pos2 = len(univention.connector.ad.explode_unicode_dn(dn)[0]) - 1

				newdn = 'uid=' + samaccountname + dn[pos2:]
			try:
				ud.debug(ud.LDAP, ud.INFO, "newdn for key %s:" % dn_key)
				ud.debug(ud.LDAP, ud.INFO, "olddn: %s" % dn)
				ud.debug(ud.LDAP, ud.INFO, "newdn: %s" % newdn)
			except:  # FIXME: which exception is to be caught?
				pass

			object[dn_key] = newdn
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
	sid = 'S-'
	sid += "%d" % ord(value[0])

	sid_len = ord(value[1])

	sid += "-%d" % ord(value[7])

	for i in range(0, sid_len):
		res = ord(value[8 + (i * 4)]) + (ord(value[9 + (i * 4)]) << 8) + (ord(value[10 + (i * 4)]) << 16) + (ord(value[11 + (i * 4)]) << 24)
		sid += "-%u" % res

	return sid


def encode_sid(value):
	a = array.array('c')

	vlist = value.replace('S-', '').split('-')
	a.append(chr(int(vlist[0])))
	a.append(chr(len(vlist) - 2))
	a.append(chr(0))
	a.append(chr(0))
	a.append(chr(0))
	a.append(chr(0))
	a.append(chr(0))
	a.append(chr(int(vlist[1])))
	for i in range(2, len(vlist)):
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


def unicode_list(list, encoding):
	newlist = []
	if encoding:
		for val in list:
			newlist.append(unicode(val, encoding))
	else:
		for val in list:
			newlist.append(unicode(val))
	return newlist


def encode_modlist(list, encoding):
	newlist = []
	for (modtype, attr, values) in list:
		if hasattr(attr, 'encode'):
			newattr = attr.encode(encoding)
		else:
			newattr = attr
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
		if isinstance(values, type([])):
			newlist.append((newattr, decode_list(values, encoding)))
		else:
			newlist.append((newattr, decode_list(values, encoding)))
	return newlist


def compatible_list(list):
	return encode_list(decode_list(list, 'latin'), 'utf8')


def compatible_modlist(list):
	return encode_modlist(decode_modlist(list, 'latin'), 'utf8')


def compatible_addlist(list):
	return encode_addlist(decode_addlist(list, 'latin'), 'utf8')


def compatible_modstring(string):
	if hasattr(string, 'decode') and not isinstance(string, types.UnicodeType):
		string = string.decode('latin')
	if hasattr(string, 'encode'):
		string = string.encode('utf8')
	return string


def explode_unicode_dn(dn, notypes=0):
	ret = []
	last = -1
	last_found = 0
	while dn.find(',', last + 1) > 0:
		last = dn.find(',', last + 1)
		if dn[last - 1] != '\\':
			if notypes == 1:
				last_found = dn.find('=', last_found) + 1
			if dn[last_found] == ',':
				last_found += 1
			ret.append(dn[last_found:last])
			last_found = last
	ret.append(dn[last + 1:])

	return ret


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
	Convenience-wrapper arround `LDAPEscapeFormatter`.

	Use `!e` do denote format-field that should be escaped using
	`ldap.filter.escape_filter_chars()`'

	>>> format_escaped("{0!e}", "*")
	'\\2a'
	"""
	return LDAPEscapeFormatter().format(format_string, *args, **kwargs)


class Simple_AD_Connection():

	''' stripped down univention.connector.ad.ad class
		difference: accept "bindpwd" directly instead of "bindpw" filename
		difference: don't require mapping
		difference: Skip init_group_cache code (i.e. use init_group_cache=False)
		difference: don't use TLS
	'''

	def __init__(self, CONFIGBASENAME, ucr, host, port, base, binddn, bindpw, certificate):

		self.CONFIGBASENAME = CONFIGBASENAME

		self.host = host
		self.port = port
		self.base = base
		self.binddn = binddn
		self.bindpw = bindpw
		self.certificate = certificate
		self.ucr = ucr
		self.protocol = 'ldaps' if ucr.is_true('%s/ad/ldap/ldaps' % CONFIGBASENAME, False) else 'ldap'
		self.uri = "%s://%s:%d" % (self.protocol, self.host, int(self.port))

		if self.certificate:
			ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self.certificate)

		#ldap.set_option(ldap.OPT_DEBUG_LEVEL, 4095)
		#ldap._trace_level = 9
		#ldap.set_option(ldap.OPT_X_SASL_SSF_MIN, 1)
		#ldap.set_option(ldap.OPT_X_SASL_SECPROPS, "minssf=1")

		self.lo = ldap.ldapobject.ReconnectLDAPObject(self.uri, retry_max=10, retry_delay=1)

		if ucr.is_true('%s/ad/ldap/kerberos' % CONFIGBASENAME):
			princ = self.binddn
			if ldap.dn.is_dn(self.binddn):
				princ = ldap.dn.str2dn(self.binddn)[0][0][1]
			os.environ['KRB5CCNAME'] = '/var/cache/univention-ad-connector/krb5.cc.well'
			with NamedTemporaryFile('w') as tmp_file:
				tmp_file.write(self.bindpw)
				tmp_file.flush()
				p1 = subprocess.Popen(['kdestroy', ], close_fds=True)
				p1.wait()
				cmd_block = ['kinit', '--no-addresses', '--password-file=%s' % tmp_file.name, princ]
				p1 = subprocess.Popen(cmd_block, close_fds=True)
				stdout, stderr = p1.communicate()
				auth = ldap.sasl.gssapi("")
				self.lo.sasl_interactive_bind_s("", auth)
		else:
			self.lo.simple_bind_s(self.binddn, self.bindpw)

		self.lo.set_option(ldap.OPT_REFERRALS, 0)

		self.ad_sid = None
		result = self.lo.search_ext_s(self.base, ldap.SCOPE_BASE, 'objectclass=domain', ['objectSid'], timeout=-1, sizelimit=0)
		if 'objectSid' in result[0][1]:
			objectSid_blob = result[0][1]['objectSid'][0]
			self.ad_sid = univention.connector.ad.decode_sid(objectSid_blob)
		if self.ad_sid is None:
			raise Exception('Failed to get SID from AD!')


class ad(univention.connector.ucs):

	range_retrieval_pattern = re.compile("^([^;]+);range=(\d+)-(\d+|\*)$")

	def __init__(self, CONFIGBASENAME, property, baseConfig, ad_ldap_host, ad_ldap_port, ad_ldap_base, ad_ldap_binddn, ad_ldap_bindpw, ad_ldap_certificate, listener_dir, init_group_cache=True):

		univention.connector.ucs.__init__(self, CONFIGBASENAME, property, baseConfig, listener_dir)

		self.CONFIGBASENAME = CONFIGBASENAME

		self.ad_ldap_host = ad_ldap_host
		self.ad_ldap_port = ad_ldap_port
		self.ad_ldap_base = ad_ldap_base
		self.ad_ldap_binddn = ad_ldap_binddn
		self.ad_ldap_bindpw = ad_ldap_bindpw
		self.ad_ldap_certificate = ad_ldap_certificate
		self.baseConfig = baseConfig

		self.open_ad()

		# update binary attribute list
		global BINARY_ATTRIBUTES
		for attr in self.baseConfig.get('%s/ad/binary_attributes' % self.CONFIGBASENAME, '').split(','):
			attr = attr.strip()
			if attr not in BINARY_ATTRIBUTES:
				BINARY_ATTRIBUTES.append(attr)

		if not self.config.has_section('AD'):
			ud.debug(ud.LDAP, ud.INFO, "__init__: init add config section 'AD'")
			self.config.add_section('AD')

		if not self.config.has_section('AD rejected'):
			ud.debug(ud.LDAP, ud.INFO, "__init__: init add config section 'AD rejected'")
			self.config.add_section('AD rejected')

		if not self.config.has_option('AD', 'lastUSN'):
			ud.debug(ud.LDAP, ud.INFO, "__init__: init lastUSN with 0")
			self._set_config_option('AD', 'lastUSN', '0')
			self.__lastUSN = 0
		else:
			self.__lastUSN = int(self._get_config_option('AD', 'lastUSN'))

		if not self.config.has_section('AD GUID'):
			ud.debug(ud.LDAP, ud.INFO, "__init__: init add config section 'AD GUID'")
			self.config.add_section('AD GUID')

		# Save a list of objects just created, this is needed to
		# prevent the back sync of a password if it was changed just
		# after the creation
		self.creation_list = []

		# Build an internal cache with AD as key and the UCS object as cache
		self.group_mapping_cache_ucs = {}
		self.group_mapping_cache_con = {}

		# Save the old members of a group
		# The connector is object base, a least in the way AD/S4 to LDAP because we don't
		# have a local cache. group_members_cache_ucs and group_members_cache_con help to
		# determine if the group membership was already saved. For example, one group and
		# five users are created on UCS side. After two users have been synced to AD/S4,
		# the group is snyced. But in AD/S4 only existing members can be stored in the group.
		# Now the sync goes back from AD/S4 to LDAP and we should not remove the three users
		# from the group. For this we remove only members who are in the local cache.

		# UCS groups and UCS members
		self.group_members_cache_ucs = {}

		# S4 groups and S4 members
		self.group_members_cache_con = {}

		if init_group_cache:
			ud.debug(ud.LDAP, ud.PROCESS, 'Building internal group membership cache')
			ad_groups = self.__search_ad(filter='(objectClass=group)', attrlist=['member'])
			ud.debug(ud.LDAP, ud.INFO, "__init__: ad_groups: %s" % ad_groups)
			for ad_group in ad_groups:
				if not ad_group or not ad_group[0]:
					continue
				ad_group_dn, ad_group_attrs = ad_group
				group = ad_group_dn.lower()
				self.group_members_cache_con[group] = []
				if ad_group_attrs:
					ad_members = self.get_ad_members(ad_group_dn, ad_group_attrs)
					for member in ad_members:
						self.group_members_cache_con[group].append(member.lower())
			ud.debug(ud.LDAP, ud.INFO, "__init__: self.group_members_cache_con: %s" % self.group_members_cache_con)

			ucs_groups = self.search_ucs(filter='(objectClass=univentionGroup)', attr=['uniqueMember'])
			for ucs_group in ucs_groups:
				group = ucs_group[0].lower()
				self.group_members_cache_ucs[group] = []
				if ucs_group[1]:
					for member in ucs_group[1].get('uniqueMember'):
						self.group_members_cache_ucs[group].append(member.lower())
			ud.debug(ud.LDAP, ud.INFO, "__init__: self.group_members_cache_ucs: %s" % self.group_members_cache_ucs)

			ud.debug(ud.LDAP, ud.PROCESS, 'Internal group membership cache was created')

		if self.lo_ad.binddn:
			try:
				result = self.lo_ad.search(base=self.lo_ad.binddn, scope='base')
				self.ad_ldap_bind_username = result[0][1]['sAMAccountName'][0]
			except Exception, msg:
				print "Failed to get SID from AD: %s" % msg
				sys.exit(1)
		else:
			self.ad_ldap_bind_username = self.baseConfig['%s/ad/ldap/binddn' % self.CONFIGBASENAME]

		try:
			result = self.lo_ad.search(filter='(objectclass=domain)', base=ad_ldap_base, scope='base', attr=['objectSid'])
			object_sid = result[0][1]['objectSid'][0]
			self.ad_sid = univention.connector.ad.decode_sid(object_sid)
		except Exception, msg:
			print "Failed to get SID from AD: %s" % msg
			sys.exit(1)

		# Get NetBios Domain Name
		self.ad_netbios_domainname = self.baseConfig.get('%s/ad/netbiosdomainname' % self.CONFIGBASENAME, None)
		if not self.ad_netbios_domainname:
			lp = LoadParm()
			net = Net(creds=None, lp=lp)
			try:
				cldap_res = net.finddc(address=self.ad_ldap_host, flags=nbt.NBT_SERVER_LDAP | nbt.NBT_SERVER_DS | nbt.NBT_SERVER_WRITABLE)
				self.ad_netbios_domainname = cldap_res.domain_name
			except RuntimeError:
				ud.debug(ud.LDAP, ud.WARN, 'Failed to find Netbios domain name from AD server. Maybe the Windows Active Directory server is rebooting. Othwise please configure the NetBIOS setting  manually: "ucr set %s/ad/netbiosdomainname=<AD NetBIOS Domainname>"' % self.CONFIGBASENAME)
				raise
		if not self.ad_netbios_domainname:
			raise netbiosDomainnameNotFound('Failed to find Netbios domain name from AD server. Please configure it manually: "ucr set %s/ad/netbiosdomainname=<AD NetBIOS Domainname>"' % self.CONFIGBASENAME)

		ud.debug(ud.LDAP, ud.PROCESS, 'Using %s as AD Netbios domain name' % self.ad_netbios_domainname)

		self.drs = None
		self.samr = None

	def open_drs_connection(self):
		lp = LoadParm()
		Net(creds=None, lp=lp)

		repl_creds = Credentials()
		repl_creds.guess(lp)
		repl_creds.set_kerberos_state(DONT_USE_KERBEROS)
		repl_creds.set_username(self.ad_ldap_bind_username)
		repl_creds.set_password(self.lo_ad.bindpw)

		# binding_options = "seal,print"
		self.drs, self.drsuapi_handle, bind_supported_extensions = drs_utils.drsuapi_connect(self.ad_ldap_host, lp, repl_creds)

		dcinfo = drsuapi.DsGetDCInfoRequest1()
		dcinfo.level = 1
		dcinfo.domain_name = self.ad_netbios_domainname
		i, o = self.drs.DsGetDomainControllerInfo(self.drsuapi_handle, 1, dcinfo)
		computer_dn = o.array[0].computer_dn

		req = drsuapi.DsNameRequest1()
		names = drsuapi.DsNameString()
		names.str = computer_dn
		req.format_offered = drsuapi.DRSUAPI_DS_NAME_FORMAT_FQDN_1779
		req.format_desired = drsuapi.DRSUAPI_DS_NAME_FORMAT_GUID
		req.count = 1
		req.names = [names]
		i, o = self.drs.DsCrackNames(self.drsuapi_handle, 1, req)
		source_dsa_guid = o.array[0].result_name
		self.computer_guid = source_dsa_guid.replace('{', '').replace('}', '').encode('utf8')

	def open_samr(self):
		lp = LoadParm()
		lp.load('/dev/null')

		creds = Credentials()
		creds.guess(lp)
		creds.set_kerberos_state(DONT_USE_KERBEROS)

		creds.set_username(self.ad_ldap_bind_username)
		creds.set_password(self.lo_ad.bindpw)

		binding_options = "\pipe\samr"
		binding = "ncacn_np:%s[%s]" % (self.ad_ldap_host, binding_options)

		self.samr = samba.dcerpc.samr.samr(binding, lp, creds)
		handle = self.samr.Connect2(None, security.SEC_FLAG_MAXIMUM_ALLOWED)

		sam_domain = lsa.String()
		sam_domain.string = self.ad_netbios_domainname
		sid = self.samr.LookupDomain(handle, sam_domain)
		self.dom_handle = self.samr.OpenDomain(handle, security.SEC_FLAG_MAXIMUM_ALLOWED, sid)

	def get_kerberos_ticket(self):
		p1 = subprocess.Popen(['kdestroy', ], close_fds=True)
		p1.wait()
		cmd_block = ['kinit', '--no-addresses', '--password-file=%s' % self.baseConfig['%s/ad/ldap/bindpw' % self.CONFIGBASENAME], self.baseConfig['%s/ad/ldap/binddn' % self.CONFIGBASENAME]]
		p1 = subprocess.Popen(cmd_block, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
		stdout, stderr = p1.communicate()
		if p1.returncode != 0:
			raise kerberosAuthenticationFailed('The following command failed: "%s" (%s): %s' % (string.join(cmd_block), p1.returncode, stdout))

	def open_ad(self):
		tls_mode = 2
		if '%s/ad/ldap/ssl' % self.CONFIGBASENAME in self.baseConfig and self.baseConfig['%s/ad/ldap/ssl' % self.CONFIGBASENAME] == "no":
			ud.debug(ud.LDAP, ud.INFO, "__init__: The LDAP connection to AD does not use SSL (switched off by UCR \"%s/ad/ldap/ssl\")." % self.CONFIGBASENAME)
			tls_mode = 0
		ldaps = self.baseConfig.is_true('%s/ad/ldap/ldaps' % self.CONFIGBASENAME, False)  # tls or ssl

		# Determine ad_ldap_base with exact case
		try:
			self.lo_ad = univention.uldap.access(
				host=self.ad_ldap_host, port=int(self.ad_ldap_port),
				base='', binddn=None, bindpw=None, start_tls=tls_mode,
				use_ldaps=ldaps, ca_certfile=self.ad_ldap_certificate)
			default_naming_context = self._get_from_root_dse(['defaultNamingContext'])
			self.ad_ldap_base = default_naming_context['defaultNamingContext'][0]
		except Exception as ex:
			ud.debug(ud.LDAP, ud.ERROR, 'Failed to lookup AD LDAP base, using UCR value: %s' % ex)

		if self.baseConfig.is_true('%s/ad/ldap/kerberos' % self.CONFIGBASENAME):
			os.environ['KRB5CCNAME'] = '/var/cache/univention-ad-connector/krb5.cc'
			self.get_kerberos_ticket()
			auth = ldap.sasl.gssapi("")
			self.lo_ad = univention.uldap.access(host=self.ad_ldap_host, port=int(self.ad_ldap_port), base=self.ad_ldap_base, binddn=None, bindpw=self.ad_ldap_bindpw, start_tls=tls_mode, use_ldaps=ldaps, ca_certfile=self.ad_ldap_certificate, decode_ignorelist=['objectSid', 'objectGUID', 'repsFrom', 'replUpToDateVector', 'ipsecData', 'logonHours', 'userCertificate', 'dNSProperty', 'dnsRecord', 'member'])
			self.get_kerberos_ticket()
			self.lo_ad.lo.sasl_interactive_bind_s("", auth)
		else:
			self.lo_ad = univention.uldap.access(host=self.ad_ldap_host, port=int(self.ad_ldap_port), base=self.ad_ldap_base, binddn=self.ad_ldap_binddn, bindpw=self.ad_ldap_bindpw, start_tls=tls_mode, use_ldaps=ldaps, ca_certfile=self.ad_ldap_certificate, decode_ignorelist=['objectSid', 'objectGUID', 'repsFrom', 'replUpToDateVector', 'ipsecData', 'logonHours', 'userCertificate', 'dNSProperty', 'dnsRecord', 'member'])

		self.lo_ad.lo.set_option(ldap.OPT_REFERRALS, 0)

	# encode string to unicode
	def encode(self, string):
		try:
			return unicode(string)
		except:  # FIXME: which exception is to be caught?
			return unicode(string, 'Latin-1')

	def _get_lastUSN(self):
		_d = ud.function('ldap._get_lastUSN')  # noqa: F841
		return max(self.__lastUSN, int(self._get_config_option('AD', 'lastUSN')))

	def get_lastUSN(self):
		return self._get_lastUSN()

	def _commit_lastUSN(self):
		_d = ud.function('ldap._commit_lastUSN')  # noqa: F841
		self._set_config_option('AD', 'lastUSN', str(self.__lastUSN))

	def _set_lastUSN(self, lastUSN):
		_d = ud.function('ldap._set_lastUSN')  # noqa: F841
		ud.debug(ud.LDAP, ud.INFO, "_set_lastUSN: new lastUSN is: %s" % lastUSN)
		self.__lastUSN = lastUSN

	# save ID's
	def __check_base64(self, string):
		# check if base64 encoded string string has correct length
		if not len(string) & 3 == 0:
			string = string + "=" * (4 - len(string) & 3)
		return string

	def __encode_GUID(self, GUID):
		# GUID may be unicode
		if isinstance(GUID, type(u'')):
			return GUID.encode('ISO-8859-1').encode('base64')
		else:
			return unicode(GUID, 'latin').encode('ISO-8859-1').encode('base64')

	def _get_DN_for_GUID(self, GUID):
		_d = ud.function('ldap._get_DN_for_GUID')  # noqa: F841
		return self._decode_dn_from_config_option(self._get_config_option('AD GUID', self.__encode_GUID(GUID)))

	def _set_DN_for_GUID(self, GUID, DN):
		_d = ud.function('ldap._set_DN_for_GUID')  # noqa: F841
		self._set_config_option('AD GUID', self.__encode_GUID(GUID), self._encode_dn_as_config_option(DN))

	def _remove_GUID(self, GUID):
		_d = ud.function('ldap._remove_GUID')  # noqa: F841
		self._remove_config_option('AD GUID', self.__encode_GUID(GUID))

# handle rejected Objects

	def _save_rejected(self, id, dn):
		_d = ud.function('ldap._save_rejected')  # noqa: F841
		try:
			self._set_config_option('AD rejected', str(id), encode_attrib(dn))
		except UnicodeEncodeError:
			self._set_config_option('AD rejected', str(id), 'unknown')
			self._debug_traceback(ud.WARN, "failed to set dn in configfile (AD rejected)")

	def _get_rejected(self, id):
		_d = ud.function('ldap._get_rejected')  # noqa: F841
		return self._get_config_option('AD rejected', str(id))

	def _remove_rejected(self, id):
		_d = ud.function('ldap._remove_rejected')  # noqa: F841
		self._remove_config_option('AD rejected', str(id))

	def _list_rejected(self):
		_d = ud.function('ldap._list_rejected')  # noqa: F841
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

	def parse_range_retrieval_attrs(self, ad_attrs, attr):
		for k in ad_attrs:
			m = self.range_retrieval_pattern.match(k)
			if not m or m.group(1) != attr:
				continue

			key = k
			values = ad_attrs[key]
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

	def value_range_retrieval(self, ad_dn, ad_attrs, attr):
		(key, values, lower, upper) = self.parse_range_retrieval_attrs(ad_attrs, attr)
		ud.debug(ud.LDAP, ud.INFO, "value_range_retrieval: response:  %s" % (key,))
		if lower != 0:
			ud.debug(ud.LDAP, ud.ERROR, "value_range_retrieval: invalid range retrieval response:  %s" % (key,))
			raise ldap.PROTOCOL_ERROR
		all_values = values

		while upper != "*":
			next_key = "%s;range=%d-*" % (attr, upper + 1)
			ad_attrs = self.get_object(ad_dn, [next_key])
			returned_before = upper
			(key, values, lower, upper) = self.parse_range_retrieval_attrs(ad_attrs, attr)
			if lower != returned_before + 1:
				ud.debug(ud.LDAP, ud.ERROR, "value_range_retrieval: invalid range retrieval response: asked for %s but got %s" % (next_key, key))
				raise ldap.PARTIAL_RESULTS
			ud.debug(ud.LDAP, ud.INFO, "value_range_retrieval: response:  %s" % (key,))
			all_values.extend(values)
		return all_values

	def get_ad_members(self, ad_dn, ad_attrs):
		ad_members = ad_attrs.get('member')
		if ad_members is None:
			ad_members = []
		elif ad_members == []:
			del ad_attrs['member']
			ad_members = self.value_range_retrieval(ad_dn, ad_attrs, 'member')
			ad_attrs['member'] = ad_members
		return ad_members

	def get_object(self, dn, attrlist=None):
		_d = ud.function('ldap.get_object')  # noqa: F841
		try:
			ad_object = self.lo_ad.get(compatible_modstring(dn), attr=attrlist)
			try:
				ud.debug(ud.LDAP, ud.INFO, "get_object: got object: %s" % dn)
			except:  # FIXME: which exception is to be caught?
				ud.debug(ud.LDAP, ud.INFO, "get_object: got object: <print failed>")
			return encode_ad_object(ad_object)
		except (ldap.SERVER_DOWN, SystemExit):
			raise
		except:  # FIXME: which exception is to be caught?
			pass

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

	def __search_ad(self, base=None, scope=ldap.SCOPE_SUBTREE, filter='', attrlist=[], show_deleted=False):
		'''
		search ad
		'''
		_d = ud.function('ldap.__search_ad')  # noqa: F841
		if not base:
			base = self.lo_ad.base

		ctrls = []
		ctrls.append(SimplePagedResultsControl(True, PAGE_SIZE, ''))

		if show_deleted:
			# LDAP_SERVER_SHOW_DELETED_OID -> 1.2.840.113556.1.4.417
			ctrls.append(LDAPControl('1.2.840.113556.1.4.417', criticality=1))

		ud.debug(ud.LDAP, ud.INFO, "Search AD with filter: %s" % filter)
		msgid = self.lo_ad.lo.search_ext(base, scope, filter, attrlist, serverctrls=ctrls, timeout=-1, sizelimit=0)

		res = []
		pages = 0
		while True:
			pages += 1
			rtype, rdata, rmsgid, serverctrls = self.lo_ad.lo.result3(msgid)
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
						ud.debug(ud.LDAP, ud.PROCESS, "AD search continues, already found %s objects" % len(res))
					ctrls[0].cookie = cookie
					msgid = self.lo_ad.lo.search_ext(base, scope, filter, attrlist, serverctrls=ctrls, timeout=-1, sizelimit=0)
				else:
					break
			else:
				ud.debug(ud.LDAP, ud.WARN, "AD ignores PAGE_RESULTS")
				break

		return encode_ad_resultlist(res)

	def __search_ad_changes(self, show_deleted=False, filter=''):
		'''
		search ad for changes since last update (changes greater lastUSN)
		'''
		_d = ud.function('ldap.__search_ad_changes')  # noqa: F841
		lastUSN = self._get_lastUSN()
		# filter erweitern um "(|(uSNChanged>=lastUSN+1)(uSNCreated>=lastUSN+1))"
		# +1 da suche nur nach '>=', nicht nach '>' möglich

		def search_ad_changes_by_attribute(attribute, lowerUSN, higherUSN=''):
			if higherUSN:
				usn_filter_format = '(&({attribute}>={lower_usn!e})({attribute}<={higher_usn!e}))'
			else:
				usn_filter_format = '({attribute}>={lower_usn!e})'

			usnFilter = format_escaped(usn_filter_format, attribute=attribute, lower_usn=lowerUSN, higher_usn=higherUSN)

			if filter != '':
				usnFilter = '(&(%s)(%s))' % (filter, usnFilter)

			return self.__search_ad(filter=usnFilter, show_deleted=show_deleted)

		# search fpr objects with uSNCreated and uSNChanged in the known range

		returnObjects = []
		try:
			if lastUSN > 0:
				# During the init phase we have to search for created and changed objects
				# but we need to sync the objects only once
				returnObjects = search_ad_changes_by_attribute('uSNCreated', lastUSN + 1)
				for changedObject in search_ad_changes_by_attribute('uSNChanged', lastUSN + 1):
					if changedObject not in returnObjects:
						returnObjects.append(changedObject)
			else:
				# Every object has got a uSNCreated
				returnObjects = search_ad_changes_by_attribute('uSNCreated', lastUSN + 1)
		except (ldap.SERVER_DOWN, SystemExit):
			raise
		except ldap.SIZELIMIT_EXCEEDED:
			# The LDAP control page results was not sucessful. Without this control
			# AD does not return more than 1000 results. We are going to split the
			# search.
			highestCommittedUSN = self.__get_highestCommittedUSN()
			tmpUSN = lastUSN
			ud.debug(ud.LDAP, ud.PROCESS, "Need to split results. highest USN is %s, lastUSN is %s" % (highestCommittedUSN, lastUSN))
			while (tmpUSN != highestCommittedUSN):
				lastUSN = tmpUSN
				tmpUSN += 999
				if tmpUSN > highestCommittedUSN:
					tmpUSN = highestCommittedUSN

				ud.debug(ud.LDAP, ud.INFO, "__search_ad_changes: search between USNs %s and %s" % (lastUSN + 1, tmpUSN))

				if lastUSN > 0:
					returnObjects += search_ad_changes_by_attribute('uSNCreated', lastUSN + 1, tmpUSN)
					for changedObject in search_ad_changes_by_attribute('uSNChanged', lastUSN + 1, tmpUSN):
						if changedObject not in returnObjects:
							returnObjects.append(changedObject)
				else:
					# Every object has got a uSNCreated
					returnObjects += search_ad_changes_by_attribute('uSNCreated', lastUSN + 1, tmpUSN)

		return returnObjects

	def __search_ad_changeUSN(self, changeUSN, show_deleted=True, filter=''):
		'''
		search ad for change with id
		'''
		_d = ud.function('ldap.__search_ad_changeUSN')  # noqa: F841
		search_filter = format_escaped('(|(uSNChanged={0!e})(uSNCreated={0!e}))', changeUSN)
		if filter != '':
			search_filter = '(&({}){})'.format(filter, search_filter)
		return self.__search_ad(filter=search_filter, show_deleted=show_deleted)

	def __dn_from_deleted_object(self, object, GUID):
		'''
		gets dn for deleted object (original dn before the object was moved into the deleted objects container)
		'''
		_d = ud.function('ldap.__dn_from_deleted_object')  # noqa: F841

		# FIXME: should be called recursively, if containers are deleted subobjects have lastKnowParent in deletedObjects
		rdn = object['dn'][:string.find(object['dn'], 'DEL:') - 3]
		if 'lastKnownParent' in object['attributes']:
			try:
				ud.debug(ud.LDAP, ud.INFO, "__dn_from_deleted_object: get DN from lastKnownParent (%s) and rdn (%s)" % (object['attributes']['lastKnownParent'][0], rdn))
			except:  # FIXME: which exception is to be caught?
				ud.debug(ud.LDAP, ud.INFO, "__dn_from_deleted_object: get DN from lastKnownParent")
			return rdn + "," + object['attributes']['lastKnownParent'][0]
		else:
			ud.debug(ud.LDAP, ud.WARN, 'lastKnownParent attribute for deleted object rdn="%s" was not set, so we must ignore the object' % rdn)
			return None

	def __object_from_element(self, element):
		"""
		gets an object from an LDAP-element, implements necessary mapping

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
				ud.debug(ud.LDAP, ud.INFO, "object_from_element: detected move of AD-Object")
			else:
				object['modtype'] = 'modify'
				if olddn and not compatible_modstring(olddn).lower() == compatible_modstring(self.encode(element[0])).lower():  # modrdn
					object['olddn'] = olddn

		object['attributes'] = element[1]
		for key in object['attributes'].keys():
			vals = []
			for value in object['attributes'][key]:
				vals.append(self.encode(value))
			object['attributes'][key] = vals

		if deleted_object:  # dn is in deleted-objects-container, need to parse to original dn
			object['deleted_dn'] = object['dn']
			object['dn'] = self.__dn_from_deleted_object(object, GUID)
			ud.debug(ud.LDAP, ud.INFO, "object_from_element: DN of removed object: %s" % object['dn'])
			# self._remove_GUID(GUID) # cache is not needed anymore?

			if not object['dn']:
				return None
		return object

	def __identify(self, object):
		_d = ud.function('ldap.__identify')  # noqa: F841
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

	def _get_from_root_dse(self, attributes=[]):
		'''
		Get attributes from the `rootDSE` from AD.
		'''
		_d = ud.function('ldap._get_from_root_dse')  # noqa: F841
		# This will search for the `rootDSE` object. `uldap.get{Attr}()`
		# are not usable, as they don't permit emtpy DNs.
		result = self.lo_ad.lo.search_s('', ldap.SCOPE_BASE, '(objectClass=*)', attributes)
		if result:
			(_dn, attr) = result[0]
			return attr
		return None

	def __get_highestCommittedUSN(self):
		'''
		get highestCommittedUSN stored in AD
		'''
		_d = ud.function('ldap.__get_highestCommittedUSN')  # noqa: F841
		try:
			result = self._get_from_root_dse(['highestCommittedUSN'])
			usn = result['highestCommittedUSN'][0]
			return int(usn)
		except Exception:
			self._debug_traceback(ud.ERROR, "search for highestCommittedUSN failed")
			print "ERROR: initial search in AD failed, check network and configuration"
			return 0

	def set_primary_group_to_ucs_user(self, object_key, object_ucs):
		'''
		check if correct primary group is set to a fresh UCS-User
		'''
		_d = ud.function('ldap.set_primary_group_to_ucs_user')  # noqa: F841

		search_filter = format_escaped('(samaccountname={0!e})', compatible_modstring(object_ucs['username']))
		ad_group_rid_resultlist = self.__search_ad(filter=search_filter, attrlist=['dn', 'primaryGroupID'])

		if not ad_group_rid_resultlist[0][0] in ['None', '', None]:

			ad_group_rid = ad_group_rid_resultlist[0][1]['primaryGroupID'][0]

			ud.debug(ud.LDAP, ud.INFO, "set_primary_group_to_ucs_user: AD rid: %s" % ad_group_rid)
			object_sid_string = str(self.ad_sid) + "-" + str(ad_group_rid)

			search_filter = format_escaped('(objectSid={0!e})', object_sid_string)
			ldap_group_ad = self.__search_ad(filter=search_filter)

			if not ldap_group_ad[0][0]:
				ud.debug(ud.LDAP, ud.ERROR, "ad.set_primary_group_to_ucs_user: Primary Group in AD not found (not enough rights?), sync of this object will fail!")
			ucs_group = self._object_mapping('group', {'dn': ldap_group_ad[0][0], 'attributes': ldap_group_ad[0][1]}, object_type='con')

			object_ucs['primaryGroup'] = ucs_group['dn']

	def primary_group_sync_from_ucs(self, key, object):  # object mit ad-dn
		'''
		sync primary group of an ucs-object to ad
		'''
		_d = ud.function('ldap.primary_group_sync_from_ucs')  # noqa: F841

		object_key = key
		object_ucs = self._object_mapping(object_key, object)

		ldap_object_ucs = self.get_ucs_ldap_object(object_ucs['dn'])
		if not ldap_object_ucs:
			ud.debug(ud.LDAP, ud.PROCESS, 'primary_group_sync_from_ucs: The UCS object (%s) was not found. The object was removed.' % object_ucs['dn'])
			return

		ldap_object_ad = self.get_object(object['dn'])
		if not ldap_object_ad:
			ud.debug(ud.LDAP, ud.PROCESS, 'primary_group_sync_from_ucs: The AD object (%s) was not found. The object was removed.' % object['dn'])
			return

		ucs_group_id = ldap_object_ucs['gidNumber'][0]  # FIXME: fails if group does not exsist
		search_filter = format_escaped('(&(objectClass=univentionGroup)(gidNumber={0!e}))', ucs_group_id)
		ucs_group_ldap = self.search_ucs(filter=search_filter)  # is empty !?

		if ucs_group_ldap == []:
			ud.debug(ud.LDAP, ud.WARN, "primary_group_sync_from_ucs: failed to get UCS-Group with gid %s, can't sync to AD" % ucs_group_id)
			return

		member_key = 'group'  # FIXME: generate by identify-function ?
		ad_group_object = self._object_mapping(member_key, {'dn': ucs_group_ldap[0][0], 'attributes': ucs_group_ldap[0][1]}, 'ucs')
		ldap_object_ad_group = self.get_object(ad_group_object['dn'])
		rid = "513"  # FIXME: Fallback: should be configurable
		if ldap_object_ad_group and 'objectSid' in ldap_object_ad_group:
			sid = ldap_object_ad_group['objectSid'][0]
			rid = sid[string.rfind(sid, "-") + 1:]
		else:
			print "no SID !!!"

		# to set a valid primary group we need to:
		# - check if either the primaryGroupID is already set to rid or
		# - proove that the user is member of this group, so: at first we need the ad_object for this element
		# this means we need to map the user to get it's AD-DN which would call this function recursively

		if "primaryGroupID" in ldap_object_ad and ldap_object_ad["primaryGroupID"][0] == rid:
			ud.debug(ud.LDAP, ud.INFO, "primary_group_sync_from_ucs: primary Group is correct, no changes needed")
			return True  # nothing left to do
		else:
			is_member = False
			ad_members = self.get_ad_members(ad_group_object['dn'], ldap_object_ad_group)
			ad_members = map(compatible_modstring, ad_members)
			object_dn_modstring = compatible_modstring(object['dn'])
			for member in ad_members:
				if object_dn_modstring.lower() == member.lower():
					is_member = True
					break

			if not is_member:  # add as member
				ad_members.append(object_dn_modstring)
				self.lo_ad.lo.modify_s(compatible_modstring(ad_group_object['dn']), [(ldap.MOD_REPLACE, 'member', ad_members)])
				ud.debug(ud.LDAP, ud.INFO, "primary_group_sync_from_ucs: primary Group needed change of membership in AD")

			# set new primary group
			self.lo_ad.lo.modify_s(object_dn_modstring, [(ldap.MOD_REPLACE, 'primaryGroupID', rid)])
			ud.debug(ud.LDAP, ud.INFO, "primary_group_sync_from_ucs: changed primary Group in AD")

			# If the user is not member in UCS of the previous primary group, the user must
			# be removed from this group in AD: https://forge.univention.org/bugzilla/show_bug.cgi?id=26809
			prev_samba_primary_group_id = ldap_object_ad.get('primaryGroupID', [])[0]
			object_sid_string = str(self.ad_sid) + "-" + str(prev_samba_primary_group_id)

			search_filter = format_escaped('(objectSid={0!e})', object_sid_string)
			ad_group = self.__search_ad(filter=search_filter)

			ucs_group_object = self._object_mapping('group', {'dn': ad_group[0][0], 'attributes': ad_group[0][1]}, 'con')
			ucs_group = self.get_ucs_ldap_object(ucs_group_object['dn'])
			is_member = False
			for member in ucs_group.get('uniqueMember', []):
				if member.lower() == object_ucs['dn'].lower():
					is_member = True
					break
			if not is_member:
				# remove AD member from previous group
				self.lo_ad.lo.modify_s(ad_group[0][0], [(ldap.MOD_DELETE, 'member', [object_dn_modstring])])

			return True

	def primary_group_sync_to_ucs(self, key, object):  # object mit ucs-dn
		'''
		sync primary group of an ad-object to ucs
		'''
		_d = ud.function('ldap.primary_group_sync_to_ucs')  # noqa: F841

		object_key = key

		ad_object = self._object_mapping(object_key, object, 'ucs')
		ldap_object_ad = self.get_object(ad_object['dn'])
		ad_group_rid = ldap_object_ad['primaryGroupID'][0]
		ud.debug(ud.LDAP, ud.INFO, "primary_group_sync_to_ucs: AD rid: %s" % ad_group_rid)

		object_sid_string = str(self.ad_sid) + "-" + str(ad_group_rid)

		search_filter = format_escaped('(objectSid={0!e})', object_sid_string)
		ldap_group_ad = self.__search_ad(filter=search_filter)

		ucs_group = self._object_mapping('group', {'dn': ldap_group_ad[0][0], 'attributes': ldap_group_ad[0][1]})

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
		sync group membership in AD if object was changend in UCS
		"""
		_d = ud.function('ldap.object_memberships_sync_from_ucs')  # noqa: F841
		ud.debug(ud.LDAP, ud.INFO, "object_memberships_sync_from_ucs: object: %s" % object)

		# search groups in UCS which have this object as member

		object_ucs = self._object_mapping(key, object)

		# Exclude primary group
		search_filter = format_escaped('(&(objectClass=univentionGroup)(uniqueMember={0!e})(!(gidNumber={1!e})))', object_ucs['dn'], object_ucs['attributes'].get('gidNumber', [])[0])
		ucs_groups_ldap = self.search_ucs(filter=search_filter)

		if ucs_groups_ldap == []:
			ud.debug(ud.LDAP, ud.INFO, "object_memberships_sync_from_ucs: No group-memberships in UCS for %s" % object['dn'])
			return

		ud.debug(ud.LDAP, ud.INFO, "object_memberships_sync_from_ucs: is member in %s groups " % len(ucs_groups_ldap))

		for groupDN, attributes in ucs_groups_ldap:
			if groupDN not in ['None', '', None]:
				ad_object = {'dn': groupDN, 'attributes': attributes, 'modtype': 'modify'}
				if not self._ignore_object('group', ad_object):
					sync_object = self._object_mapping('group', ad_object, 'ucs')
					sync_object_ad = self.get_object(sync_object['dn'])
					ad_group_object = {'dn': sync_object['dn'], 'attributes': sync_object_ad}
					if sync_object_ad:
						# self.group_members_sync_from_ucs( 'group', sync_object )
						self.one_group_member_sync_from_ucs(ad_group_object, object)

			self.__group_cache_ucs_append_member(groupDN, object_ucs['dn'])

	def __group_cache_ucs_append_member(self, group, member):
		if not self.group_members_cache_ucs.get(group.lower()):
			self.group_members_cache_ucs[group.lower()] = []
		ud.debug(ud.LDAP, ud.INFO, "__group_cache_ucs_append_member: Append user %s to group ucs cache of %s" % (member.lower(), group.lower()))
		self.group_members_cache_ucs[group.lower()].append(member.lower())

	def group_members_sync_from_ucs(self, key, object):  # object mit ad-dn
		"""
		sync groupmembers in AD if changend in UCS
		"""
		_d = ud.function('ldap.group_members_sync_from_ucs')  # noqa: F841

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: %s" % object)

		object_key = key
		object_ucs = self._object_mapping(object_key, object)

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: type of object_ucs['dn']: %s" % type(object_ucs['dn']))
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: dn is: %s" % object_ucs['dn'])
		ldap_object_ucs = self.get_ucs_ldap_object(object_ucs['dn'])

		if not ldap_object_ucs:
			ud.debug(ud.LDAP, ud.PROCESS, 'group_members_sync_from_ucs:: The UCS object (%s) was not found. The object was removed.' % object_ucs['dn'])
			return

		if 'uniqueMember' in ldap_object_ucs:
			ucs_members = ldap_object_ucs['uniqueMember']
		else:
			ucs_members = []

		ud.debug(ud.LDAP, ud.INFO, "ucs_members: %s" % ucs_members)

		# remove members which have this group as primary group (set same gidNumber)
		search_filter = format_escaped('(gidNumber={0!e})', ldap_object_ucs['gidNumber'][0])
		prim_members_ucs = self.lo.search(filter=search_filter, attr=['gidNumber'])

		# all dn's need to be lower-case so we can compare them later and put them in the group ucs cache:
		self.group_members_cache_ucs[object_ucs['dn'].lower()] = []

		for prim_object in prim_members_ucs:
			if prim_object[0].lower() in ucs_members:
				ucs_members.remove(prim_object[0].lower())

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: clean ucs_members: %s" % ucs_members)

		ldap_object_ad = self.get_object(object['dn'])
		if not ldap_object_ad:
			ud.debug(ud.LDAP, ud.PROCESS, 'group_members_sync_from_ucs:: The AD object (%s) was not found. The object was removed.' % object['dn'])
			return

		ad_members = self.get_ad_members(object['dn'], ldap_object_ad)
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: ad_members %s" % ad_members)

		ad_members_from_ucs = []

		# map members from UCS to AD and check if they exist
		for member_dn in ucs_members:
			ad_dn = self.group_mapping_cache_ucs.get(member_dn.lower())
			if ad_dn and self.lo_ad.get(ad_dn, attr=['cn']):
				ud.debug(ud.LDAP, ud.INFO, "Found %s in group cache ucs" % member_dn)
				ad_members_from_ucs.append(ad_dn.lower())
				self.__group_cache_ucs_append_member(object_ucs['dn'], member_dn)
			else:
				ud.debug(ud.LDAP, ud.INFO, "Did not find %s in group cache ucs" % member_dn)
				member_object = {'dn': member_dn, 'modtype': 'modify', 'attributes': self.lo.get(member_dn)}

				# can't sync them if users have no posix-account
				if 'gidNumber' not in member_object['attributes']:
					continue

				# check if this is members primary group, if true it shouldn't be added to ad
				if 'gidNumber' in member_object['attributes'] and 'gidNumber' in ldap_object_ucs and \
					member_object['attributes']['gidNumber'] == ldap_object_ucs['gidNumber']:
					# is primary group
					continue

				# print 'member_object: %s '%member_object
				for k in self.property.keys():
					if self.modules[k].identify(member_dn, member_object['attributes']):
						key = k
						break
				# print 'object key: %s' % key
				ad_dn = self._object_mapping(key, member_object, 'ucs')['dn']
				# check if dn exists in ad
				try:
					if self.lo_ad.get(ad_dn, attr=['cn']):  # search only for cn to suppress coding errors
						ad_members_from_ucs.append(ad_dn.lower())
						self.group_mapping_cache_ucs[member_dn.lower()] = ad_dn
						self.__group_cache_ucs_append_member(object_ucs['dn'], member_dn)
				except (ldap.SERVER_DOWN, SystemExit):
					raise
				except:  # FIXME: which exception is to be caught?
					ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: failed to get dn from ad, assume object doesn't exist")

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: UCS-members in ad_members_from_ucs %s" % ad_members_from_ucs)

		# check if members in AD don't exist in UCS, if true they need to be added in AD
		for member_dn in ad_members:
			if not member_dn.lower() in ad_members_from_ucs:
				try:
					ad_object = self.get_object(member_dn)

					key = self.__identify({'dn': member_dn, 'attributes': ad_object})
					ucs_dn = self._object_mapping(key, {'dn': member_dn, 'attributes': ad_object})['dn']
					if not self.lo.get(ucs_dn, attr=['cn']):
						# ad_members_from_ucs.append(member_dn.lower())
						ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: Object exists only in AD [%s]" % ucs_dn)
					elif self._ignore_object(key, {'dn': member_dn, 'attributes': ad_object}):
						ad_members_from_ucs.append(member_dn.lower())
						ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: Object ignored in AD [%s], key = [%s]" % (ucs_dn, key))
				except (ldap.SERVER_DOWN, SystemExit):
					raise
				except:  # FIXME: which exception is to be caught?
					self._debug_traceback(ud.INFO, "group_members_sync_from_ucs: failed to get dn from ad which is groupmember")

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: UCS-and AD-members in ad_members_from_ucs %s" % ad_members_from_ucs)

		# compare lists and generate modlist
		# direct compare is not possible, because ad_members_from_ucs are all lowercase, ad_members are not, so we need to iterate...
		# FIXME: should be done in the last iteration (above)

		# need to remove users from ad_members which have this group as primary group. may failed earlier if groupnames are mapped
		try:
			object_dn = compatible_modstring(object['dn'])
			object_sid = self.lo_ad.getAttr(object_dn, 'objectSid')[0]
			group_rid = decode_sid(object_sid).split('-')[-1]
		except ldap.NO_SUCH_OBJECT:
			group_rid = None

		if group_rid:
			# search for members who have this as their primaryGroup
			search_filter = format_escaped('(primaryGroupID={0!e})', group_rid)
			prim_members_ad = self.__search_ad(filter=search_filter, attrlist=['cn'])

			for prim_dn, prim_object in prim_members_ad:
				if prim_dn not in ['None', '', None]:  # filter referrals
					if prim_dn.lower() in ad_members_from_ucs:
						ad_members_from_ucs.remove(prim_dn.lower())
					elif prim_dn in ad_members_from_ucs:
						ad_members_from_ucs.remove(prim_dn)

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: ad_members_from_ucs without members with this as their primary group: %s" % ad_members_from_ucs)

		add_members = ad_members_from_ucs
		del_members = []

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: members to add initialized: %s" % add_members)
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: members to del initialized: %s" % del_members)

		for member_dn in ad_members:
			ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: %s in ad_members_from_ucs?" % member_dn)
			if member_dn.lower() in ad_members_from_ucs:
				ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: Yes")
				add_members.remove(member_dn.lower())
			else:
				if object['modtype'] == 'add':
					ud.debug(ud.LDAP, ud.PROCESS, "group_members_sync_from_ucs: %s is newly added. For this case don't remove the membership." % (object['dn'].lower()))
				# remove member only if he was in the cache on AD side
				# otherwise it is possible that the user was just created on AD and we are on the way back
				elif (member_dn.lower() in self.group_members_cache_con.get(object['dn'].lower(), [])) or (self.property.get('group') and self.property['group'].sync_mode in ['write', 'none']):
					ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: No")
					del_members.append(member_dn)
				else:
					ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: %s was not found in group member con cache of %s, don't delete" % (member_dn.lower(), object['dn'].lower()))

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: members to add: %s" % add_members)
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: members to del: %s" % del_members)

		if add_members or del_members:
			ad_members = ad_members + add_members
			for member in del_members:
				ad_members.remove(member)
			ud.debug(ud.LDAP, ud.INFO, "group_members_sync_from_ucs: members result: %s" % ad_members)
			object_ucs['dn'].lower()

			modlist_members = []
			for member in ad_members:
				modlist_members.append(compatible_modstring(member))

			try:
				self.lo_ad.lo.modify_s(compatible_modstring(object['dn']), [(ldap.MOD_REPLACE, 'member', modlist_members)])
			except (ldap.SERVER_DOWN, SystemExit):
				raise
			except:  # FIXME: which exception is to be caught?
				ud.debug(ud.LDAP, ud.WARN, "group_members_sync_from_ucs: failed to sync members: (%s,%s)" % (object['dn'], [(ldap.MOD_REPLACE, 'member', modlist_members)]))
				raise

		return True

	def object_memberships_sync_to_ucs(self, key, object):
		"""
		sync group membership in UCS if object was changend in AD
		"""
		_d = ud.function('ldap.object_memberships_sync_to_ucs')  # noqa: F841
		# disable this debug line, see Bug #12031
		# ud.debug(ud.LDAP, ud.INFO, "object_memberships_sync_to_ucs: object: %s" % object)

		self._object_mapping(key, object)

		if 'memberOf' in object['attributes']:
			for groupDN in object['attributes']['memberOf']:
				ad_object = {'dn': groupDN, 'attributes': self.get_object(groupDN), 'modtype': 'modify'}
				if not self._ignore_object('group', ad_object):
					sync_object = self._object_mapping('group', ad_object)
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
					ud.debug(ud.LDAP, ud.INFO, "object_memberships_sync_to_ucs: Append user %s to group con cache of %s" % (dn.lower(), groupDN.lower()))
					self.group_members_cache_con[groupDN.lower()].append(dn.lower())
				else:
					ud.debug(ud.LDAP, ud.INFO, "object_memberships_sync_to_ucs: Failed to append user %s to group con cache of %s" % (object['dn'].lower(), groupDN.lower()))

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
		sync groupmembers in UCS if changend one member in AD
		"""
		# In AD the object['dn'] is member of the group sync_object

		ml = []
		if not self.__compare_lowercase(object['dn'], ucs_group_object['attributes'].get('uniqueMember', [])):
			ml.append((ldap.MOD_ADD, 'uniqueMember', [object['dn']]))

		if object['attributes'].get('uid'):
			uid = object['attributes'].get('uid', [])[0]
			if not self.__compare_lowercase(uid, ucs_group_object['attributes'].get('memberUid', [])):
				ml.append((ldap.MOD_ADD, 'memberUid', [uid]))

		if ml:
			try:
				self.lo.lo.modify_s(ucs_group_object['dn'], compatible_modlist(ml))
			except ldap.ALREADY_EXISTS:
				# The user is already member in this group or it is his primary group
				# This might happen, if we synchronize a rejected file with old informations
				# See Bug #25709 Comment #17: https://forge.univention.org/bugzilla/show_bug.cgi?id=25709#c17
				ud.debug(ud.LDAP, ud.INFO, "one_group_member_sync_to_ucs: User is already member of the group: %s modlist: %s" % (ucs_group_object['dn'], ml))

	def one_group_member_sync_from_ucs(self, ad_group_object, object):
		"""
		sync groupmembers in AD if changend one member in AD
		"""
		ml = []
		if not self.__compare_lowercase(object['dn'], ad_group_object['attributes'].get('member', [])):
			ml.append((ldap.MOD_ADD, 'member', [object['dn']]))

		if ml:
			try:
				self.lo_ad.lo.modify_s(ad_group_object['dn'], compatible_modlist(ml))
			except ldap.ALREADY_EXISTS:
				# The user is already member in this group or it is his primary group
				# This might happen, if we synchronize a rejected file with old informations
				# See Bug #25709 Comment #17: https://forge.univention.org/bugzilla/show_bug.cgi?id=25709#c17
				ud.debug(ud.LDAP, ud.INFO, "one_group_member_sync_from_ucs: User is already member of the group: %s modlist: %s" % (ad_group_object['dn'], ml))

		# The user has been removed from the cache. He must be added in any case
		ud.debug(ud.LDAP, ud.INFO, "one_group_member_sync_from_ucs: Append user %s to group con cache of %s" % (object['dn'].lower(), ad_group_object['dn'].lower()))
		if not self.group_members_cache_con.get(ad_group_object['dn'].lower()):
			self.group_members_cache_con[ad_group_object['dn'].lower()] = []
		self.group_members_cache_con[ad_group_object['dn'].lower()].append(object['dn'].lower())

	def __group_cache_con_append_member(self, group, member):
		if not self.group_members_cache_con.get(group.lower()):
			self.group_members_cache_con[group.lower()] = []
		ud.debug(ud.LDAP, ud.INFO, "__group_cache_con_append_member: Append user %s to group con cache of %s" % (member.lower(), group.lower()))
		self.group_members_cache_con[group.lower()].append(member.lower())

	def group_members_sync_to_ucs(self, key, object):
		"""
		sync groupmembers in UCS if changend in AD
		"""
		_d = ud.function('ldap.group_members_sync_to_ucs')  # noqa: F841
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: object: %s" % object)

		object_key = key

		ad_object = self._object_mapping(object_key, object, 'ucs')
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: ad_object (mapped): %s" % ad_object)

		ldap_object_ucs = self.get_ucs_ldap_object(object['dn'])
		if 'uniqueMember' in ldap_object_ucs:
			ucs_members = ldap_object_ucs['uniqueMember']
		else:
			ucs_members = []
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: ucs_members: %s" % ucs_members)

		# FIXME: does not use dn-mapping-function
		ldap_object_ad = self.get_object(ad_object['dn'])  # FIXME: may fail if object doesn't exist
		group_sid = ldap_object_ad['objectSid'][0]
		group_rid = group_sid[string.rfind(group_sid, "-") + 1:]

		ad_members = self.get_ad_members(ad_object['dn'], ldap_object_ad)

		# search for members who have this as their primaryGroup
		search_filter = format_escaped('(primaryGroupID={0!e})', group_rid)
		prim_members_ad = self.__search_ad(filter=search_filter)

		for prim_dn, prim_object in prim_members_ad:
			if prim_dn not in ['None', '', None]:  # filter referrals
				ad_members.append(prim_dn)

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: ad_members %s" % ad_members)

		ucs_members_from_ad = {'user': [], 'group': [], 'unknown': [], 'windowscomputer': [], }

		self.group_members_cache_con[ad_object['dn'].lower()] = []
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: Reset con cache")

		dn_mapping_ucs_member_to_ad = {}

		# map members from AD to UCS and check if they exist
		for member_dn in ad_members:
			ucs_dn = self.group_mapping_cache_con.get(member_dn.lower())
			if ucs_dn:
				ud.debug(ud.LDAP, ud.INFO, "Found %s in group cache ad: DN: %s" % (member_dn, ucs_dn))
				ucs_members_from_ad['unknown'].append(ucs_dn.lower())
				dn_mapping_ucs_member_to_ad[ucs_dn.lower()] = member_dn
				self.__group_cache_con_append_member(ad_object['dn'], member_dn)
			else:
				ud.debug(ud.LDAP, ud.INFO, "Did not find %s in group cache ad" % member_dn)
				member_object = self.get_object(member_dn)
				if member_object:
					mo_key = self.__identify({'dn': member_dn, 'attributes': member_object})
					if not mo_key:
						ud.debug(ud.LDAP, ud.WARN, "group_members_sync_to_ucs: failed to identify object type of ad member, ignore membership: %s" % member_dn)
						continue  # member is an object which will not be synced
					if self._ignore_object(mo_key, {'dn': member_dn, 'attributes': member_object}):
						ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: Object dn %s should be ignored, ignore membership" % member_dn)
						continue

					ucs_dn = self._object_mapping(mo_key, {'dn': member_dn, 'attributes': member_object})['dn']
					ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: mapped ad member to ucs DN %s" % ucs_dn)

					dn_mapping_ucs_member_to_ad[ucs_dn.lower()] = member_dn

					try:
						if self.lo.get(ucs_dn):
							ucs_members_from_ad['unknown'].append(ucs_dn.lower())
							self.group_mapping_cache_con[member_dn.lower()] = ucs_dn
							self.__group_cache_con_append_member(ad_object['dn'], member_dn)
						else:
							ud.debug(ud.LDAP, ud.INFO, "Failed to find %s via self.lo.get" % ucs_dn)
					except (ldap.SERVER_DOWN, SystemExit):
						raise
					except:  # FIXME: which exception is to be caught?
						ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: failed to get dn from ucs, assume object doesn't exist")

		# build an internal cache
		cache = {}

		# check if members in UCS don't exist in AD, if true they need to be added in UCS
		for member_dn in ucs_members:
			if not (member_dn.lower() in ucs_members_from_ad['user'] or member_dn.lower() in ucs_members_from_ad['group'] or member_dn.lower() in ucs_members_from_ad['unknown'] or member_dn.lower() in ucs_members_from_ad['windowscomputer']):
				try:
					cache[member_dn] = self.lo.get(member_dn)
					ucs_object = {'dn': member_dn, 'modtype': 'modify', 'attributes': cache[member_dn]}

					if self._ignore_object(key, object):
						continue

					for k in self.property.keys():
						if self.modules[k].identify(member_dn, ucs_object['attributes']):
							ad_dn = self._object_mapping(k, ucs_object, 'ucs')['dn']

							if not dn_mapping_ucs_member_to_ad.get(member_dn.lower()):
								dn_mapping_ucs_member_to_ad[member_dn.lower()] = ad_dn

							ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: search for: %s" % ad_dn)
							# search only for cn to suppress coding errors
							if not self.lo_ad.get(ad_dn, attr=['cn']):
								# member does not exist in AD but should
								# stay a member in UCS
								ucs_members_from_ad[k].append(member_dn.lower())
							break

				except (ldap.SERVER_DOWN, SystemExit):
					raise
				except:  # FIXME: which exception is to be caught?
					self._debug_traceback(ud.INFO, "group_members_sync_to_ucs: failed to get dn from ucs which is groupmember")

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: dn_mapping_ucs_member_to_ad=%s" % (dn_mapping_ucs_member_to_ad))
		add_members = copy.deepcopy(ucs_members_from_ad)
		del_members = {'user': [], 'group': [], 'windowscomputer': [], }

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: ucs_members: %s" % ucs_members)
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: ucs_members_from_ad: %s" % ucs_members_from_ad)

		for member_dn in ucs_members:
			if member_dn.lower() in ucs_members_from_ad['user']:
				add_members['user'].remove(member_dn.lower())
			elif member_dn.lower() in ucs_members_from_ad['group']:
				add_members['group'].remove(member_dn.lower())
			elif member_dn.lower() in ucs_members_from_ad['unknown']:
				add_members['unknown'].remove(member_dn.lower())
			elif member_dn.lower() in ucs_members_from_ad['windowscomputer']:
				add_members['windowscomputer'].remove(member_dn.lower())
			else:
				# remove member only if he was in the cache
				# otherwise it is possible that the user was just created on UCS

				if (member_dn.lower() in self.group_members_cache_ucs.get(object['dn'].lower(), [])) or (self.property.get('group') and self.property['group'].sync_mode in ['read', 'none']):
					ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: %s was found in group member ucs cache of %s" % (member_dn.lower(), object['dn'].lower()))
					ucs_object_attr = cache.get(member_dn)
					if not ucs_object_attr:
						ucs_object_attr = self.lo.get(member_dn)
						cache[member_dn] = ucs_object_attr
					ucs_object = {'dn': member_dn, 'modtype': 'modify', 'attributes': ucs_object_attr}

					for k in self.property.keys():
						# identify if DN is a user or a group (will be ignored it is a host)
						if self.modules[k].identify(member_dn, ucs_object['attributes']):
							if not self._ignore_object(k, ucs_object):
								del_members[k].append(member_dn)
							break
				else:
					ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: %s was not found in group member ucs cache of %s, don't delete" % (member_dn.lower(), object['dn'].lower()))

		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: members to add: %s" % add_members)
		ud.debug(ud.LDAP, ud.INFO, "group_members_sync_to_ucs: members to del: %s" % del_members)

		if add_members['user'] or add_members['group'] or del_members['user'] or del_members['group'] or add_members['unknown'] or add_members['windowscomputer'] or del_members['windowscomputer']:
			ucs_admin_object = univention.admin.objects.get(self.modules[object_key], co='', lo=self.lo, position='', dn=object['dn'])
			ucs_admin_object.open()

			uniqueMember_add = add_members['user'] + add_members['group'] + add_members['unknown'] + add_members['windowscomputer']
			uniqueMember_del = del_members['user'] + del_members['group'] + del_members['windowscomputer']
			memberUid_add = []
			memberUid_del = []
			for member in add_members['user']:
				(_attr, uid, _flags) = ldap.dn.str2dn(member)[0][0]
				memberUid_add.append(uid)
			for member in add_members['unknown'] + add_members['windowscomputer']:  # user or group?
				ucs_object_attr = self.lo.get(member)
				uid = ucs_object_attr.get('uid')
				if uid:
					memberUid_add.append(uid[0])
			for member in del_members['user']:
				(_attr, uid, _flags) = ldap.dn.str2dn(member)[0][0]
				memberUid_del.append(uid)
			for member in del_members['windowscomputer']:
				ucs_object_attr = self.lo.get(member)
				uid = ucs_object_attr.get('uid')
				if uid:
					memberUid_del.append(uid[0])
			if uniqueMember_del or memberUid_del:
				ucs_admin_object.fast_member_remove(uniqueMember_del, memberUid_del, ignore_license=1)
			if uniqueMember_add or memberUid_del:
				ucs_admin_object.fast_member_add(uniqueMember_add, memberUid_add)

	def set_userPrincipalName_from_ucr(self, key, object):
		object_key = key
		object_ucs = self._object_mapping(object_key, object)
		ldap_object_ad = self.get_object(object['dn'])
		modlist = None
		if 'userPrincipalName' not in ldap_object_ad:
			# add missing userPrincipalName
			kerberosdomain = self.baseConfig.get('%s/ad/mapping/kerberosdomain' % self.CONFIGBASENAME, None)
			if kerberosdomain:
				ucs_admin_object = univention.admin.objects.get(self.modules[object_key], co='', lo=self.lo, position='', dn=object_ucs['dn'])
				ucs_admin_object.open()
				userPrincipalName = "%s@%s" % (ucs_admin_object['username'], kerberosdomain)
				modlist = [(ldap.MOD_REPLACE, 'userPrincipalName', [userPrincipalName])]
		else:
			# update userPrincipalName
			if self.baseConfig.is_true('%s/ad/mapping/sync/userPrincipalName' % self.CONFIGBASENAME, True):
				ucs_admin_object = univention.admin.objects.get(self.modules[object_key], co='', lo=self.lo, position='', dn=object_ucs['dn'])
				ucs_admin_object.open()
				if ucs_admin_object['username'] + '@' not in ldap_object_ad['userPrincipalName'][0]:
					if '@' in ldap_object_ad['userPrincipalName'][0]:
						princ = ldap_object_ad['userPrincipalName'][0].split('@', 1)[1]
						modlist = [(ldap.MOD_REPLACE, 'userPrincipalName', [ucs_admin_object['username'] + '@' + princ])]
		if modlist:
			ud.debug(ud.LDAP, ud.INFO, "set_userPrincipalName_from_ucr: set kerberos principle for AD user %s with modlist %s " % (object['dn'], modlist))
			self.lo_ad.lo.modify_s(compatible_modstring(object['dn']), compatible_modlist(modlist))

	def disable_user_from_ucs(self, key, object):
		object_key = key

		object_ucs = self._object_mapping(object_key, object)
		ldap_object_ad = self.get_object(object['dn'])

		ucs_admin_object = univention.admin.objects.get(self.modules[object_key], co='', lo=self.lo, position='', dn=object_ucs['dn'])
		ucs_admin_object.open()

		modlist = []

		ud.debug(ud.LDAP, ud.INFO, "Disabled state: %s" % ucs_admin_object['disabled'].lower())
		if not (ucs_admin_object['disabled'].lower() in ['none', '0']):
			# user disabled in UCS
			if 'userAccountControl' in ldap_object_ad and (int(ldap_object_ad['userAccountControl'][0]) & 2) == 0:
				# user enabled in AD -> change
				res = str(int(ldap_object_ad['userAccountControl'][0]) | 2)
				modlist.append((ldap.MOD_REPLACE, 'userAccountControl', [res]))
		else:
			# user enabled in UCS
			if 'userAccountControl' in ldap_object_ad and (int(ldap_object_ad['userAccountControl'][0]) & 2) > 0:
				# user disabled in AD -> change
				res = str(int(ldap_object_ad['userAccountControl'][0]) - 2)
				modlist.append((ldap.MOD_REPLACE, 'userAccountControl', [res]))

		# account expires
		# This value represents the number of 100 nanosecond intervals since January 1, 1601 (UTC). A value of 0 or 0x7FFFFFFFFFFFFFFF (9223372036854775807) indicates that the account never expires.
		if not ucs_admin_object['userexpiry']:
			# ucs account not expired
			if 'accountExpires' in ldap_object_ad and (long(ldap_object_ad['accountExpires'][0]) != long(9223372036854775807) or ldap_object_ad['accountExpires'][0] == '0'):
				# ad account expired -> change
				modlist.append((ldap.MOD_REPLACE, 'accountExpires', ['9223372036854775807']))
		else:
			# ucs account expired
			if 'accountExpires' in ldap_object_ad and ldap_object_ad['accountExpires'][0] != unix2ad_time(ucs_admin_object['userexpiry']):
				# ad account not expired -> change
				modlist.append((ldap.MOD_REPLACE, 'accountExpires', [str(unix2ad_time(ucs_admin_object['userexpiry']))]))

		if modlist:
			self.lo_ad.lo.modify_s(compatible_modstring(object['dn']), compatible_modlist(modlist))

	def disable_user_to_ucs(self, key, object):
		object_key = key

		ad_object = self._object_mapping(object_key, object, 'ucs')

		self.get_ucs_ldap_object(object['dn'])
		ldap_object_ad = self.get_object(ad_object['dn'])

		modified = 0
		ucs_admin_object = univention.admin.objects.get(self.modules[object_key], co='', lo=self.lo, position='', dn=object['dn'])
		ucs_admin_object.open()

		if 'userAccountControl' in ldap_object_ad and (int(ldap_object_ad['userAccountControl'][0]) & 2) == 0:
			# user enabled in AD
			if not ucs_admin_object['disabled'].lower() in ['none', '0']:
				# user disabled in UCS -> change
				ucs_admin_object['disabled'] = '0'
				modified = 1
		else:
			# user disabled in AD
			if ucs_admin_object['disabled'].lower() in ['none', '0']:
				# user enabled in UCS -> change
				ucs_admin_object['disabled'] = '1'
				modified = 1
		if 'accountExpires' in ldap_object_ad and (long(ldap_object_ad['accountExpires'][0]) == long(9223372036854775807) or ldap_object_ad['accountExpires'][0] == '0'):
			# ad account not expired
			if ucs_admin_object['userexpiry']:
				# ucs account expired -> change
				ucs_admin_object['userexpiry'] = None
				modified = 1
		else:
			# ad account expired
			ud.debug(ud.LDAP, ud.INFO, "sync account_expire:      adtime: %s    unixtime: %s" % (long(ldap_object_ad['accountExpires'][0]), ucs_admin_object['userexpiry']))

			if ad2unix_time(long(ldap_object_ad['accountExpires'][0])) != ucs_admin_object['userexpiry']:
				# ucs account not expired -> change
				ucs_admin_object['userexpiry'] = ad2unix_time(long(ldap_object_ad['accountExpires'][0]))
				modified = 1

		if modified:
			ucs_admin_object.modify()

	def initialize(self):
		_d = ud.function('ldap.initialize')  # noqa: F841
		print "--------------------------------------"
		print "Initialize sync from AD"
		if self._get_lastUSN() == 0:  # we startup new
			ud.debug(ud.LDAP, ud.PROCESS, "initialize AD: last USN is 0, sync all")
			# query highest USN in LDAP
			highestCommittedUSN = self.__get_highestCommittedUSN()

			# poll for all objects without deleted objects
			self.poll(show_deleted=False)

			# compare highest USN from poll with highest before poll, if the last changes deletes
			# the highest USN from poll is to low
			self._set_lastUSN(max(highestCommittedUSN, self._get_lastUSN()))

			self._commit_lastUSN()
			ud.debug(ud.LDAP, ud.INFO, "initialize AD: sync of all objects finished, lastUSN is %d", self.__get_highestCommittedUSN())
		else:
			self.resync_rejected()
			self.poll()
			self._commit_lastUSN()
		print "--------------------------------------"

	def resync_rejected(self):
		'''
		tries to resync rejected dn
		'''
		print "--------------------------------------"

		_d = ud.function('ldap.resync_rejected')  # noqa: F841
		change_count = 0
		rejected = self._list_rejected()
		print "Sync %s rejected changes from AD to UCS" % len(rejected)
		sys.stdout.flush()
		if rejected:
			for id, dn in rejected:
				ud.debug(ud.LDAP, ud.PROCESS, 'sync to ucs: Resync rejected dn: %s' % (dn))
				try:
					sync_successfull = False
					elements = self.__search_ad_changeUSN(id, show_deleted=True)
					if not elements or len(elements) < 1 or not elements[0][0]:
						ud.debug(ud.LDAP, ud.INFO, "rejected change with id %s not found, don't need to sync" % id)
						self._remove_rejected(id)
					elif len(elements) > 1 and not (elements[1][0] == 'None' or elements[1][0] is None):  # all except the first should be referrals
						ud.debug(ud.LDAP, ud.WARN, "more than one rejected object with id %s found, can't proceed" % id)
					else:
						object = self.__object_from_element(elements[0])
						property_key = self.__identify(object)
						if not property_key:
							ud.debug(ud.LDAP, ud.INFO, "sync to ucs: Dropping reject for unidentified object %s" % dn)
							self._remove_rejected(id)
							continue
						mapped_object = self._object_mapping(property_key, object)
						try:
							if not self._ignore_object(property_key, mapped_object) and not self._ignore_object(property_key, object):
								sync_successfull = self.sync_to_ucs(property_key, mapped_object, dn)
							else:
								sync_successfull = True
						except (ldap.SERVER_DOWN, SystemExit):
							raise
						except:  # FIXME: which exception is to be caught?
							self._debug_traceback(ud.ERROR, "sync of rejected object failed \n\t%s" % (object['dn']))
							sync_successfull = False
						if sync_successfull:
							change_count += 1
							self._remove_rejected(id)
							self.__update_lastUSN(object)
							self._set_DN_for_GUID(elements[0][1]['objectGUID'][0], elements[0][0])
				except (ldap.SERVER_DOWN, SystemExit):
					raise
				except Exception:
					self._debug_traceback(ud.ERROR, "unexpected Error during ad.resync_rejected")
		print "restored %s rejected changes" % change_count
		print "--------------------------------------"
		sys.stdout.flush()

	def poll(self, show_deleted=True):
		'''
		poll for changes in AD
		'''
		_d = ud.function('ldap.poll')  # noqa: F841
		# search from last_usn for changes

		change_count = 0
		changes = []
		try:
			changes = self.__search_ad_changes(show_deleted=show_deleted)
		except (ldap.SERVER_DOWN, SystemExit):
			raise
		except:  # FIXME: which exception is to be caught?
			self._debug_traceback(ud.WARN, "Exception during search_ad_changes")

		print "--------------------------------------"
		print "try to sync %s changes from AD" % len(changes)
		print "done:",
		sys.stdout.flush()
		done_counter = 0
		object = None
		lastUSN = self._get_lastUSN()
		newUSN = lastUSN

		for element in changes:
			try:
				if element[0] == 'None':  # referrals
					continue
				old_element = copy.deepcopy(element)
				object = self.__object_from_element(element)
			except:  # FIXME: which exception is to be caught?
				# ud.debug(ud.LDAP, ud.ERROR, "Exception during poll/object-mapping, tried to map element: %s" % old_element[0])
				# ud.debug(ud.LDAP, ud.ERROR, "This object will not be synced again!")
				# debug-trace may lead to a segfault here :(
				self._debug_traceback(ud.ERROR, "Exception during poll/object-mapping, object will not be synced again!")

			if object:
				property_key = self.__identify(object)
				if property_key:

					if self._ignore_object(property_key, object):
						if object['modtype'] == 'move':
							ud.debug(ud.LDAP, ud.INFO, "object_from_element: Detected a move of an AD object into a ignored tree: dn: %s" % object['dn'])
							object['deleted_dn'] = object['olddn']
							object['dn'] = object['olddn']
							object['modtype'] = 'delete'
							# check the move target
						else:
							self.__update_lastUSN(object)
							done_counter += 1
							print "%s" % done_counter,
							continue

					if object['dn'].find('\\0ACNF:') > 0:
						ud.debug(ud.LDAP, ud.PROCESS, 'Ignore conflicted object: %s' % object['dn'])
						self.__update_lastUSN(object)
						done_counter += 1
						print "%s" % done_counter,
						continue

					sync_successfull = False
					try:
						mapped_object = self._object_mapping(property_key, object)
						if not self._ignore_object(property_key, mapped_object):
							sync_successfull = self.sync_to_ucs(property_key, mapped_object, object['dn'])
						else:
							sync_successfull = True
					except (ldap.SERVER_DOWN, SystemExit):
						raise
					except univention.admin.uexceptions.ldapError, msg:
						ud.debug(ud.LDAP, ud.INFO, "Exception during poll with message (1) %s" % msg)
						if msg == "Can't contact LDAP server":
							raise ldap.SERVER_DOWN
						else:
							self._debug_traceback(ud.WARN, "Exception during poll/sync_to_ucs")
					except univention.admin.uexceptions.ldapError, msg:
						ud.debug(ud.LDAP, ud.INFO, "Exception during poll with message (2) %s" % msg)
						if msg == "Can't contact LDAP server":
							raise ldap.SERVER_DOWN
						else:
							self._debug_traceback(ud.WARN, "Exception during poll")
					except:  # FIXME: which exception is to be caught?
						self._debug_traceback(ud.WARN, "Exception during poll/sync_to_ucs")

					if not sync_successfull:
						ud.debug(ud.LDAP, ud.WARN, "sync to ucs was not successfull, save rejected")
						ud.debug(ud.LDAP, ud.WARN, "object was: %s" % object['dn'])

					if sync_successfull:
						change_count += 1
						newUSN = max(self.__get_change_usn(object), newUSN)
						try:
							GUID = old_element[1]['objectGUID'][0]
							self._set_DN_for_GUID(GUID, old_element[0])
						except (ldap.SERVER_DOWN, SystemExit):
							raise
						except:  # FIXME: which exception is to be caught?
							self._debug_traceback(ud.WARN, "Exception during set_DN_for_GUID")

					else:
						self.save_rejected(object)
						self.__update_lastUSN(object)
				else:
					newUSN = max(self.__get_change_usn(object), newUSN)

				done_counter += 1
				print "%s" % done_counter,
			else:
				done_counter += 1
				print "(%s)" % done_counter,
			sys.stdout.flush()

		print ""

		if newUSN != lastUSN:
			self._set_lastUSN(newUSN)
			self._commit_lastUSN()

		# return number of synced objects
		rejected = self._list_rejected()
		if rejected:
			print "Changes from AD:  %s (%s saved rejected)" % (change_count, len(rejected))
		else:
			print "Changes from AD:  %s (%s saved rejected)" % (change_count, '0')
		print "--------------------------------------"
		sys.stdout.flush()
		return change_count

	def sync_from_ucs(self, property_type, object, pre_mapped_ucs_dn, old_dn=None, old_ucs_object=None):
		_d = ud.function('ldap.__sync_from_ucs')  # noqa: F841
		# Diese Methode erhaelt von der UCS Klasse ein Objekt,
		# welches hier bearbeitet wird und in das AD geschrieben wird.
		# object ist brereits vom eingelesenen UCS-Objekt nach AD gemappt, old_dn ist die alte UCS-DN
		ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: sync object: %s" % object['dn'])

		# if sync is read (sync from AD) or none, there is nothing to do
		if self.property[property_type].sync_mode in ['read', 'none']:
			ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs ignored, sync_mode is %s" % self.property[property_type].sync_mode)
			return True

		pre_mapped_ucs_old_dn = old_dn

		if old_dn:
			ud.debug(ud.LDAP, ud.INFO, "move %s from [%s] to [%s]" % (property_type, old_dn, object['dn']))
			if hasattr(self.property[property_type], 'dn_mapping_function'):
				tmp_object = copy.deepcopy(object)
				tmp_object['dn'] = old_dn
				for function in self.property[property_type].dn_mapping_function:
					tmp_object = function(self, tmp_object, [], isUCSobject=True)
				old_dn = tmp_object['dn']
			if hasattr(self.property[property_type], 'position_mapping'):
				for mapping in self.property[property_type].position_mapping:
					old_dn = self._subtree_replace(old_dn.lower(), mapping[0].lower(), mapping[1].lower())
				old_dn = self._subtree_replace(old_dn, self.lo.base, self.lo_ad.base)

			# the old object was moved in UCS, but does this object exist in AD?
			try:
				old_object = self.lo_ad.get(compatible_modstring(old_dn))
			except (ldap.SERVER_DOWN, SystemExit):
				raise
			except:
				old_object = None

			if old_object:
				ud.debug(ud.LDAP, ud.INFO, "move %s from [%s] to [%s]" % (property_type, old_dn, object['dn']))
				try:
					self.lo_ad.rename(unicode(old_dn), object['dn'])
				except ldap.NO_SUCH_OBJECT:  # check if object is already moved (we may resync now)
					new = self.lo_ad.get(compatible_modstring(object['dn']))
					if not new:
						raise
				# need to actualise the GUID and DN-Mapping
				guid = self.lo_ad.getAttr(compatible_modstring(object['dn']), 'objectGUID')[0]
				self._set_DN_for_GUID(guid, object['dn'])
				self._remove_dn_mapping(pre_mapped_ucs_old_dn, unicode(old_dn))
				self._check_dn_mapping(pre_mapped_ucs_dn, object['dn'])

		ud.debug(ud.LDAP, ud.PROCESS, 'sync from ucs: [%14s] [%10s] %s' % (property_type, object['modtype'], object['dn']))

		if 'olddn' in object:
			object.pop('olddn')  # not needed anymore, will fail object_mapping in later functions
		old_dn = None

		addlist = []
		modlist = []

		if self.group_mapping_cache_con.get(object['dn'].lower()) and object['modtype'] != 'delete':
			ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: remove %s from group cache" % object['dn'])
			self.group_mapping_cache_con[object['dn'].lower()] = None

		ad_object = self.get_object(object['dn'])

		#
		# ADD
		#
		if (object['modtype'] == 'add' and not ad_object) or (object['modtype'] == 'modify' and not ad_object):
			ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: add object: %s" % object['dn'])

			self.addToCreationList(object['dn'])

			# objectClass
			if self.property[property_type].con_create_objectclass:
				addlist.append(('objectClass', self.property[property_type].con_create_objectclass))

			# fixed Attributes
			if self.property[property_type].con_create_attributes:
				addlist += self.property[property_type].con_create_attributes

			if hasattr(self.property[property_type], 'attributes') and self.property[property_type].attributes is not None:
				for attr, value in object['attributes'].items():
					for attr_key in self.property[property_type].attributes.keys():
						attribute = self.property[property_type].attributes[attr_key]
						if attr not in (attribute.con_attribute, attribute.con_other_attribute):
							continue
						addlist.append((attr, value))
			if hasattr(self.property[property_type], 'post_attributes') and self.property[property_type].post_attributes is not None:
				for attr, value in object['attributes'].items():
					for attr_key in self.property[property_type].post_attributes.keys():
						post_attribute = self.property[property_type].post_attributes[attr_key]
						if post_attribute.reverse_attribute_check:
							if not object['attributes'].get(post_attribute.ldap_attribute):
								continue
						if attr not in (post_attribute.con_attribute, post_attribute.con_other_attribute):
							continue

						if value:
							modlist.append((ldap.MOD_REPLACE, attr, value))

			ud.debug(ud.LDAP, ud.INFO, "to add: %s" % object['dn'])
			ud.debug(ud.LDAP, ud.ALL, "sync_from_ucs: addlist: %s" % addlist)
			self.lo_ad.lo.add_s(compatible_modstring(object['dn']), compatible_addlist(addlist))  # FIXME encoding

			if property_type == 'group':
				self.group_members_cache_con[object['dn'].lower()] = []
				ud.debug(ud.LDAP, ud.INFO, "group_members_cache_con[%s]: []" % (object['dn'].lower()))

			if hasattr(self.property[property_type], "post_con_create_functions"):
				for f in self.property[property_type].post_con_create_functions:
					f(self, property_type, object)

			ud.debug(ud.LDAP, ud.INFO, "to modify: %s" % object['dn'])
			if modlist:
				ud.debug(ud.LDAP, ud.ALL, "sync_from_ucs: modlist: %s" % modlist)
				try:
					self.lo_ad.lo.modify_s(compatible_modstring(object['dn']), compatible_modlist(modlist))
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
		elif (object['modtype'] == 'modify' and ad_object) or (object['modtype'] == 'add' and ad_object):
			ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: modify object: %s" % object['dn'])
			attr_list = []
			if hasattr(self.property[property_type], 'attributes') and self.property[property_type].attributes is not None:
				for attr, value in object['attributes'].items():
					attr_list.append(attr)
					for attr_key in self.property[property_type].attributes.keys():
						attribute = self.property[property_type].attributes[attr_key]
						if attr not in (attribute.con_attribute, attribute.con_other_attribute):
							continue

						if attribute.sync_mode not in ['write', 'sync']:
							ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: %s is in not in write or sync mode. Skipping" % attr_key)
							continue

						if attr not in ad_object:
							if value:
								modlist.append((ldap.MOD_ADD, attr, value))
						else:
							if attribute.compare_function:
								equal = attribute.compare_function(value, ad_object[attr])
							else:
								equal = univention.connector.compare_lowercase(value, ad_object[attr])
							if not equal:
								if attribute.con_value_merge_function:
									value = attribute.con_value_merge_function(value, ad_object[attr])
								modlist.append((ldap.MOD_REPLACE, attr, value))
			if hasattr(self.property[property_type], 'post_attributes') and self.property[property_type].post_attributes is not None:
				for attr, value in object['attributes'].items():
					attr_list.append(attr)
					for attr_key in self.property[property_type].post_attributes.keys():
						post_attribute = self.property[property_type].post_attributes[attr_key]
						if attr not in (post_attribute.con_attribute, post_attribute.con_other_attribute):
							continue

						if post_attribute.sync_mode not in ['write', 'sync']:
							ud.debug(ud.LDAP, ud.INFO, "sync_from_ucs: %s is in not in write or sync mode. Skipping" % attr_key)
							continue

						if post_attribute.reverse_attribute_check:
							if not object['attributes'].get(post_attribute.ldap_attribute):
								continue
						if attr not in ad_object:
							if value:
								modlist.append((ldap.MOD_ADD, attr, value))
						else:
							if post_attribute.compare_function:
								equal = post_attribute.compare_function(value, ad_object[attr])
							else:
								equal = univention.connector.compare_lowercase(value, ad_object[attr])
							if not equal:
								if post_attribute.con_value_merge_function:
									value = post_attribute.con_value_merge_function(value, ad_object[attr])
								modlist.append((ldap.MOD_REPLACE, attr, value))

			attrs_which_should_be_mapped = []
			attrs_to_remove_from_ad_object = []

			if hasattr(self.property[property_type], 'attributes') and self.property[property_type].attributes is not None:
				for ac in self.property[property_type].attributes.keys():
					if not self.property[property_type].attributes[ac].con_attribute in attrs_which_should_be_mapped:
						attrs_which_should_be_mapped.append(self.property[property_type].attributes[ac].con_attribute)
					if self.property[property_type].attributes[ac].con_other_attribute:
						if not self.property[property_type].attributes[ac].con_other_attribute in attrs_which_should_be_mapped:
							attrs_which_should_be_mapped.append(self.property[property_type].attributes[ac].con_other_attribute)

			if hasattr(self.property[property_type], 'post_attributes') and self.property[property_type].post_attributes is not None:
				for ac in self.property[property_type].post_attributes.keys():
					if not self.property[property_type].post_attributes[ac].con_attribute in attrs_which_should_be_mapped:
						if self.property[property_type].post_attributes[ac].reverse_attribute_check:
							if object['attributes'].get(self.property[property_type].post_attributes[ac].ldap_attribute):
								attrs_which_should_be_mapped.append(self.property[property_type].post_attributes[ac].con_attribute)
							elif ad_object.get(self.property[property_type].post_attributes[ac].con_attribute):
								modlist.append((ldap.MOD_DELETE, self.property[property_type].post_attributes[ac].con_attribute, None))
						else:
							attrs_which_should_be_mapped.append(self.property[property_type].post_attributes[ac].con_attribute)
					if self.property[property_type].post_attributes[ac].con_other_attribute:
						if not self.property[property_type].post_attributes[ac].con_other_attribute in attrs_which_should_be_mapped:
							attrs_which_should_be_mapped.append(self.property[property_type].post_attributes[ac].con_other_attribute)

			for expected_attribute in attrs_which_should_be_mapped:
				if expected_attribute not in object['attributes']:
					attrs_to_remove_from_ad_object.append(expected_attribute)

				if modlist:
					for modified_attrs in modlist:
						if modified_attrs[1] in attrs_to_remove_from_ad_object and len(modified_attrs[2]) > 0:
							attrs_to_remove_from_ad_object.remove(modified_attrs[1])

			for yank_empty_attr in attrs_to_remove_from_ad_object:
				if yank_empty_attr in ad_object:
					if value is not None:
						modlist.append((ldap.MOD_DELETE, yank_empty_attr, None))

			if not modlist:
				ud.debug(ud.LDAP, ud.ALL, "nothing to modify: %s" % object['dn'])
			else:
				ud.debug(ud.LDAP, ud.INFO, "to modify: %s" % object['dn'])
				ud.debug(ud.LDAP, ud.ALL, "sync_from_ucs: modlist: %s" % modlist)
				try:
					self.lo_ad.lo.modify_s(compatible_modstring(object['dn']), compatible_modlist(modlist))
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
			self.delete_in_ad(object)

		else:
			ud.debug(ud.LDAP, ud.WARN, "unknown modtype (%s : %s)" % (object['dn'], object['modtype']))
			return False

		self._check_dn_mapping(pre_mapped_ucs_dn, object['dn'])

		ud.debug(ud.LDAP, ud.ALL, "sync from ucs return True")
		return True  # FIXME: return correct False if sync fails

	def _get_objectGUID(self, dn):
		ad_object = self.get_object(dn, ['objectGUID'])
		if not ad_object:
			ud.debug(ud.LDAP, ud.WARN, "Failed to search objectGUID for %s" % dn)
			return ''
		return ad_object.get('objectGUID')[0]

	def delete_in_ad(self, object):
		_d = ud.function('ldap.delete_in_ad')  # noqa: F841
		try:
			objectGUID = self._get_objectGUID(object['dn'])
			self.lo_ad.lo.delete_s(compatible_modstring(object['dn']))
			entryUUID = object.get('attributes').get('entryUUID')[0]
			self.update_deleted_cache_after_removal(entryUUID, objectGUID)
		except ldap.NO_SUCH_OBJECT:
			pass  # object already deleted
		except ldap.NOT_ALLOWED_ON_NONLEAF:
			ud.debug(ud.LDAP, ud.INFO, "remove object from AD failed, need to delete subtree")
			object_dn = compatible_modstring(object['dn'])
			for result in self.lo_ad.search(base=object_dn):
				if univention.connector.compare_lowercase(result[0], object['dn']):
					continue
				ud.debug(ud.LDAP, ud.INFO, "delete: %s" % result[0])
				subobject = {'dn': result[0], 'modtype': 'delete', 'attributes': result[1]}
				key = None
				for k in self.property.keys():
					if self.modules[k].identify(result[0], result[1]):
						key = k
						break
				object_mapping = self._object_mapping(key, subobject)
				ud.debug(ud.LDAP, ud.WARN, "delete subobject: %s" % object_mapping['dn'])
				if not self._ignore_object(key, object_mapping):
					if not self.sync_from_ucs(key, subobject, object_mapping['dn']):
						try:
							ud.debug(ud.LDAP, ud.WARN, "delete of subobject failed: %s" % result[0])
						except (ldap.SERVER_DOWN, SystemExit):
							raise
						except:  # FIXME: which exception is to be caught?
							ud.debug(ud.LDAP, ud.WARN, "delete of subobject failed")
						return False

			return self.delete_in_ad(object)
