#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  sid sync
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2022 Univention GmbH
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
'''
	Helper function to create the SID mapping definition.
'''

from __future__ import print_function
import ldap
import univention.debug2 as ud
from ldap.controls import LDAPControl
from samba.dcerpc import security
from samba.ndr import ndr_pack
from univention.s4connector.s4 import decode_sid


def sid_to_s4_mapping(s4connector, key, object):
	ud.debug(ud.LDAP, ud.INFO, "sid_to_s4_mapping")
	sidAttribute = 'sambaSID'
	if s4connector.configRegistry.is_false('connector/s4/mapping/sid', False):
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_s4: SID mapping is disabled via UCR: connector/s4/mapping/sid')
		sidAttribute = 'univentionSamba4SID'

	sambaSID = object['attributes'][sidAttribute]

	# Two different cases are possible, the user sid contains the
	# domain sid or not.
	if sambaSID[0].startswith(b'S-'):
		new_objectSid_ndr = ndr_pack(security.dom_sid(sambaSID[0].decode('ASCII')))
	else:
		new_objectSid_ndr = ndr_pack(security.dom_sid(u'%s-%s' % (s4connector.s4_sid, sambaSID[0].decode('ASCII'))))

	return [new_objectSid_ndr]


def sid_to_ucs_mapping(s4connector, key, s4_object):
	ud.debug(ud.LDAP, ud.INFO, "sid_to_ucs_mapping")
	object_sid = decode_sid(s4_object['attributes']['objectSid'][0])
	return [object_sid.split('-')[-1].encode('ASCII')]


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

	sambaSID = object['attributes'][sidAttribute][0].decode('ASCII')
	# get the ad sid
	(s4_dn, s4_attributes) = s4connector.lo_s4.lo.search_s(s4_dn, ldap.SCOPE_BASE, '(objectSid=*)', ['objectSid'])[0]
	objectSid = s4_attributes.get('objectSid')
	if objectSid:
		decoded_s4_sid = decode_sid(objectSid[0])
		if decoded_s4_sid == sambaSID:
			ud.debug(ud.LDAP, ud.INFO, 'sid_to_s4: objectSid and %s are equal' % sidAttribute)
			return

		# change objectSID
		#	http://serverfault.com/questions/53717/how-can-i-change-the-sid-of-a-user-account-in-the-active-directory
		#	http://technet.microsoft.com/en-us/library/cc961998.aspx

		ud.debug(ud.LDAP, ud.INFO, 'sid_to_s4: changing objectSid from %r to %r' % (decoded_s4_sid, sambaSID))
		new_objectSid_ndr = ndr_pack(security.dom_sid(sambaSID))
		modlist.append((ldap.MOD_REPLACE, 'objectSid', new_objectSid_ndr))

		# objectSid modification for an Samba4 object is only possible with the "provision" control:
		LDB_CONTROL_PROVISION_OID = '1.3.6.1.4.1.7165.4.3.16'
		controls = [LDAPControl(LDB_CONTROL_PROVISION_OID, criticality=0)]
		s4connector.lo_s4.lo.modify_ext_s(s4_dn, modlist, serverctrls=controls)


def sid_to_ucs(s4connector, key, s4_object):
	ud.debug(ud.LDAP, ud.INFO, "sid_to_ucs S4 object: %r" % s4_object)
	ud.debug(ud.LDAP, ud.INFO, "sid_to_ucs S4 key: %r" % key)

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

	objectSid = s4_object['attributes'].get('objectSid', [None])[0]
	if objectSid:
		objectSid = decode_sid(objectSid)
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_ucs: objectSid found: %r' % (objectSid,))
	else:
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_ucs: objectSid not found in attributes!')
		return

	(ucs_dn, ucs_attributes) = s4connector.lo.lo.search(base=ucs_dn, scope='base', attr=[sidAttribute, 'objectClass'])[0]

	if not ucs_dn:
		ud.debug(ud.LDAP, ud.WARN, 'sid_to_ucs: UCS object (%s) not found' % ucs_dn)
		return

	sambaSID = ucs_attributes.get(sidAttribute)
	if not sambaSID or objectSid.encode('ASCII') not in sambaSID:
		ml.append((sidAttribute, sambaSID, s4_object['attributes'].get('objectSid')))
		s4_ocs = s4_object['attributes'].get('objectClass', [])
		ucs_ocs = ucs_attributes.get('objectClass')
		if b'user' in s4_ocs:
			if b'sambaSamAccount' not in ucs_ocs:
				ml.append(('objectClass', ucs_ocs, ucs_ocs + [b'sambaSamAccount']))
		if b'group' in s4_ocs:
			if b'sambaGroupMapping' not in ucs_ocs:
				ml.append(('objectClass', ucs_ocs, ucs_ocs + [b'sambaGroupMapping']))
	if ml:
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_ucs: modlist = %r' % (ml,))
		s4connector.lo.lo.modify(ucs_dn, ml)
