#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  sid sync
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
import ldap
import univention.debug2 as ud
from ldap.controls import LDAPControl
from samba.dcerpc import security
from samba.ndr import ndr_pack, ndr_unpack

'''
	Helper function to create the SID mapping definition.
'''


def print_sid_mapping(configRegistry):
	"""
		.. deprecated:: UCS 4.4
	"""
	# TODO: remove this function, it's not used anymore (but maybe by customers?)
	sync_mode = 'sync'
	if configRegistry.is_true('connector/s4/mapping/sid', True):
		if configRegistry.is_true('connector/s4/mapping/sid_to_s4', False):
			mapping_str = 'univention.s4connector.s4.sid_mapping.sid_to_s4_mapping,'
		else:
			mapping_str = 'None, '
			sync_mode = 'read'
		if configRegistry.is_true('connector/s4/mapping/sid_to_ucs', True):
			mapping_str += 'univention.s4connector.s4.sid_mapping.sid_to_ucs_mapping'
		else:
			mapping_str += 'None'
			sync_mode = 'write'
		print('''
					'sid': univention.s4connector.attribute (
						sync_mode='%s',
						mapping=(%s),
						ldap_attribute='sambaSID',
						ucs_attribute='sambaRID',
						con_attribute='objectSid',
						single_value=True,
						compare_function=univention.s4connector.s4.compare_sid_lists,
					), ''' % (sync_mode, mapping_str))


def sid_to_s4_mapping(s4connector, key, object):
	ud.debug(ud.LDAP, ud.INFO, "sid_to_s4_mapping")
	sidAttribute = 'sambaSID'
	if s4connector.configRegistry.is_false('connector/s4/mapping/sid', False):
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_s4: SID mapping is disabled via UCR: connector/s4/mapping/sid')
		sidAttribute = 'univentionSamba4SID'

	sambaSID = object['attributes'][sidAttribute]

	# Two different cases are possible, the user sid contains the
	# domain sid or not.
	if sambaSID[0].startswith('S-'):
		new_objectSid_ndr = ndr_pack(security.dom_sid('%s' % (sambaSID[0])))
	else:
		new_objectSid_ndr = ndr_pack(security.dom_sid('%s-%s' % (s4connector.s4_sid, sambaSID[0])))

	return [new_objectSid_ndr]


def sid_to_ucs_mapping(s4connector, key, s4_object):
	ud.debug(ud.LDAP, ud.INFO, "sid_to_ucs_mapping")
	object_sid = s4_object['attributes']['objectSid'][0]
	return object_sid.split('-')[-1]


def sid_to_s4(s4connector, key, object):
	ud.debug(ud.LDAP, ud.INFO, "sid_to_s4 object: %s" % object)

	sidAttribute = 'sambaSID'
	if s4connector.configRegistry.is_false('connector/s4/mapping/sid', False):
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_s4: SID mapping is disabled via UCR: connector/s4/mapping/sid')
		sidAttribute = 'univentionSamba4SID'
	else:
		# This case will be handled by direct mapping
		return

	# object dn was already mapped to the s4 DN:
	s4_dn = object['dn']
	modlist = []

	# search the ucs object via
	if sidAttribute not in object['attributes']:
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_s4: UCS object does not have a %s' % sidAttribute)
		return

	sambaSID = object['attributes'][sidAttribute]
	# get the ad sid
	(s4_dn, s4_attributes) = s4connector.lo_s4.lo.search_s(s4_dn, ldap.SCOPE_BASE, '(objectSid=*)', ['objectSid'])[0]
	objectSid = s4_attributes.get('objectSid')
	if objectSid:
		# decoded_s4_sid = univention.s4connector.s4.decode_sid(objectSid[0])
		s4_objectSid = ndr_unpack(security.dom_sid, objectSid[0])
		decoded_s4_sid = str(s4_objectSid)
		if decoded_s4_sid == sambaSID[0]:
			ud.debug(ud.LDAP, ud.INFO, 'sid_to_s4: objectSid and %s are equal' % sidAttribute)
			return

		# change objectSID
		#	http://serverfault.com/questions/53717/how-can-i-change-the-sid-of-a-user-account-in-the-active-directory
		#	http://technet.microsoft.com/en-us/library/cc961998.aspx

		ud.debug(ud.LDAP, ud.INFO, 'sid_to_s4: changing objectSid from %s to %s' % (decoded_s4_sid, sambaSID[0]))
		new_objectSid_ndr = ndr_pack(security.dom_sid(sambaSID[0]))
		modlist.append((ldap.MOD_REPLACE, 'objectSid', new_objectSid_ndr))

		# objectSid modification for an Samba4 object is only possible with the "provision" control:
		LDB_CONTROL_PROVISION_OID = '1.3.6.1.4.1.7165.4.3.16'
		controls = [LDAPControl(LDB_CONTROL_PROVISION_OID, criticality=0)]
		s4connector.lo_s4.lo.modify_ext_s(s4_dn, modlist, serverctrls=controls)


def sid_to_ucs(s4connector, key, s4_object):
	ud.debug(ud.LDAP, ud.INFO, "sid_to_ucs S4 object: %s" % s4_object)
	ud.debug(ud.LDAP, ud.INFO, "sid_to_ucs S4 key: %s" % key)

	sidAttribute = 'sambaSID'
	if s4connector.configRegistry.is_false('connector/s4/mapping/sid', False):
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_ucs: SID mapping is disabled via UCR: connector/s4/mapping/sid')
		sidAttribute = 'univentionSamba4SID'
	else:
		# This case will be handled by direct mapping
		return

	# modlist
	ml = []

	# object dn is already mapped to the UCS DN:
	if not s4_object.get('dn'):
		return  # ignore
	ucs_dn = s4_object['dn']
	ud.debug(ud.LDAP, ud.INFO, "sid_to_s4: UCS DN %s" % ucs_dn)

	if 'attributes' in s4_object and 'objectSid' in s4_object['attributes']:
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_ucs: objectSid found: %s' % s4_object['attributes']['objectSid'])
	else:
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_ucs: objectSid not found in attributes!')
		return

	(ucs_dn, ucs_attributes) = s4connector.lo.lo.search(base=ucs_dn, scope='base', attr=[sidAttribute, 'objectClass'])[0]

	if not ucs_dn:
		ud.debug(ud.LDAP, ud.WARN, 'sid_to_ucs: UCS object (%s) not found' % ucs_dn)
		return

	objectSid = s4_object['attributes'].get('objectSid')
	sambaSID = ucs_attributes.get(sidAttribute)
	if not sambaSID or objectSid != sambaSID:
		ml.append((sidAttribute, sambaSID, s4_object['attributes'].get('objectSid')))
		if 'user' in s4_object['attributes'].get('objectClass', []):
			if 'sambaSamAccount' not in ucs_attributes.get('objectClass'):
				ml.append(('objectClass', ucs_attributes.get('objectClass'), ucs_attributes.get('objectClass') + ['sambaSamAccount']))
		if 'group' in s4_object['attributes'].get('objectClass', []):
			if 'sambaGroupMapping' not in ucs_attributes.get('objectClass'):
				ml.append(('objectClass', ucs_attributes.get('objectClass'), ucs_attributes.get('objectClass') + ['sambaGroupMapping']))
	if ml:
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_ucs: modlist = %s' % ml)
		s4connector.lo.lo.modify(ucs_dn, ml)

	return
