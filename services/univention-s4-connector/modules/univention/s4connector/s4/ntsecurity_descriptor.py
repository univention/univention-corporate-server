#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  nTSecurityDescriptor sync
#
# Copyright 2014-2019 Univention GmbH
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


import ldap
import univention.debug2 as ud
from samba.dcerpc import security
from samba.ndr import ndr_pack, ndr_unpack
from ldap.controls.readentry import PostReadControl


def encode_sddl_to_sd_in_ndr(domain_sid, ntsd_sddl):
	ntsd = security.descriptor.from_sddl(ntsd_sddl, domain_sid)
	ntsd_ndr = ndr_pack(ntsd)
	return ntsd_ndr


def decode_sd_in_ndr_to_sddl(domain_sid, value):
	ntsd = ndr_unpack(security.descriptor, value)
	return ntsd.as_sddl(domain_sid)


# Post-create/modify functions


def ntsd_to_s4(s4connector, key, object):
	ud.debug(ud.LDAP, ud.INFO, "ntsd_to_s4 object: %s" % object)

	# object dn was already mapped to the s4 DN:
	s4_dn = object['dn']
	modlist = []

	# search the ucs object via
	if 'msNTSecurityDescriptor' not in object['attributes']:
		ud.debug(ud.LDAP, ud.INFO, 'ntsd_to_s4: UCS object does not have a msNTSecurityDescriptor')
		return

	ucs_ntsd_sddl = object['attributes']['msNTSecurityDescriptor'][0]
	s4_attributes = s4connector.lo_s4.get(s4_dn, attr=['nTSecurityDescriptor'])
	ntsd_ndr = s4_attributes.get('nTSecurityDescriptor')

	if ntsd_ndr:
		domain_sid = security.dom_sid(s4connector.s4_sid)
		s4_ntsd_sddl = decode_sd_in_ndr_to_sddl(domain_sid, ntsd_ndr[0])
		if s4_ntsd_sddl == ucs_ntsd_sddl:
			ud.debug(ud.LDAP, ud.INFO, 'ntsd_to_s4: nTSecurityDescriptors are equal')
			return

		ud.debug(ud.LDAP, ud.INFO, 'ntsd_to_s4: changing nTSecurityDescriptor from %s to %s' % (s4_ntsd_sddl, ucs_ntsd_sddl))

		ucs_ntsd_ndr = encode_sddl_to_sd_in_ndr(domain_sid, ucs_ntsd_sddl)
		modlist.append((ldap.MOD_REPLACE, 'nTSecurityDescriptor', ucs_ntsd_ndr))

		s4connector.lo_s4.lo.modify_ext_s(s4_dn, modlist)


def ntsd_to_ucs(s4connector, key, s4_object):
	ud.debug(ud.LDAP, ud.INFO, "ntsd_to_ucs S4 object: %s" % s4_object)
	ud.debug(ud.LDAP, ud.INFO, "ntsd_to_ucs S4 key: %s" % key)

	# modlist
	ml = []

	# search Samba DS expicitly for hidden attribute
	# object dn is already mapped to the UCS DN:
	s4_dn = s4_object.get('dn')
	if not s4_dn:
		return  # ignore

	try:
		s4_attributes = s4connector.lo_s4.get(s4_dn, attr=['nTSecurityDescriptor'], required=True)
	except ldap.NO_SUCH_OBJECT:
		ud.debug(ud.LDAP, ud.WARN, 'ntsd_to_ucs: S4 object (%s) not found' % s4_dn)
		return

	ntsd_ndr = s4_attributes.get('nTSecurityDescriptor')
	if not ntsd_ndr:
		ud.debug(ud.LDAP, ud.INFO, 'ntsd_to_ucs: nTSecurityDescriptor not found in attributes!')
		return

	# search in UCS/OpenLDAP DS to determine modify/add
	ucs_dn = s4_dn
	try:
		ucs_attributes = s4connector.lo.get(ucs_dn, attr=['msNTSecurityDescriptor'])
	except ldap.NO_SUCH_OBJECT:
		ud.debug(ud.LDAP, ud.WARN, 'sid_to_ucs: UCS object (%s) not found' % ucs_dn)
		return

	domain_sid = security.dom_sid(s4connector.s4_sid)
	s4_ntsd_sddl = decode_sd_in_ndr_to_sddl(domain_sid, ntsd_ndr[0])
	ucs_ntsd_sddl = ucs_attributes.get('msNTSecurityDescriptor', [None])[0]
	if not ucs_ntsd_sddl or ucs_ntsd_sddl != s4_ntsd_sddl:
		ml.append(('msNTSecurityDescriptor', ucs_ntsd_sddl, s4_ntsd_sddl))
	if ml:
		ud.debug(ud.LDAP, ud.INFO, 'ntsd_to_ucs: modlist = %s' % ml)
		serverctrls = [PostReadControl(True, ['entryUUID', 'entryCSN'])]
		response = {}
		s4connector.lo.lo.modify(ucs_dn, ml, serverctrls=serverctrls, response=response)
		for c in response.get('ctrls', []):   # If the modify actually did something
			if c.controlType == PostReadControl.controlType:
				entryUUID = c.entry['entryUUID'][0]
				entryCSN = c.entry['entryCSN'][0]
				s4connector._remember_entryCSN_commited_by_connector(entryUUID, entryCSN)
