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
import base64
import univention.debug2 as ud


map_prefdev = ['any', 'mhs', 'physical', 'telex', 'teletex', 'g3fax', 'g4fax', 'ia5', 'videotex', 'telephone']


def prefdev_sync_s4_to_ucs(s4connector, key, s4_object):
	attr = 'preferredDeliveryMethod'
	s4_prefdev = s4_object['attributes'].get(attr)

	if s4_prefdev is None:
		return

	ucs_pref = ''
	for pref in s4_prefdev:
		try:
			ucs_pref += map_prefdev[int(pref)] + ' $ '
		except (IndexError, ValueError) as exc:
			ud.debug(ud.LDAP, ud.WARN, "Ignoring invalid value %r of attribute preferredDeliveryMethod. Value must be a number between 0 and 10." % (pref,))
	ucs_pref = ucs_pref[:-3]
	return [ucs_pref]


def prefdev_sync_ucs_to_s4(s4connector, key, ucs_object):
	attr = 'preferredDeliveryMethod'

	ucs_prefdev = ucs_object['attributes'].get(attr)
	if ucs_prefdev is None:
		return

	s4_prefdev = []
	try:
		for pref in ucs_prefdev:
			int(pref)
	except ValueError:
		# map values
		for pref in ucs_prefdev[0].replace(' ', '').split('$'):
			if pref in map_prefdev:
				s4_prefdev.append(str(map_prefdev.index(pref)))
	else:
		# just return the already mapped value
		return ucs_prefdev
	return s4_prefdev


def userCertificate_sync_s4_to_ucs(s4connector, key, s4_object):
	attr = 'userCertificate'
	s4_cert = s4_object['attributes'].get(attr)
	if s4_cert is None:
		return
	ucs_cert = base64.b64encode(s4_cert[0])
	return [ucs_cert]


def userCertificate_sync_ucs_to_s4(s4connector, key, ucs_object):
	attr = 'userCertificate;binary'
	try:
		ucs_cert = ucs_object['attributes'][attr][0]
	except Exception:
		return
	return [ucs_cert]


def jpegPhoto_sync_s4_to_ucs(s4connector, key, s4_object):
	attr = 'jpegPhoto'

	s4_photo = s4_object['attributes'].get(attr)
	if s4_photo is None:
		return

	ucs_photo = []
	for photo in s4_photo:
		ucs_photo.append(base64.b64encode(photo))
	return ucs_photo


def jpegPhoto_sync_ucs_to_s4(s4connector, key, ucs_object):
	attr = 'jpegPhoto'

	ucs_photo = ucs_object['attributes'].get(attr)
	if ucs_photo is None:
		return
	s4_photo = []
	for photo in ucs_photo:
		s4_photo.append(photo)
	return s4_photo


def secretary_sync_s4_to_ucs(s4connector, key, s4_object):
	attr = 'secretary'

	s4_secretary = s4_object['attributes'].get(attr)
	if s4_secretary is None:
		return
	else:
		ucs_secretary = []
		for s4_dn in s4_secretary:
			dn_mapped = s4_dn
			if s4connector._get_dn_by_con(s4_dn):
				dn_mapped = s4connector._get_dn_by_con(s4_dn)
				dn_mapped = s4connector.dn_mapped_to_base(dn_mapped, s4connector.lo.base)
			if hasattr(s4connector.property['user'], 'position_mapping'):
				for mapping in s4connector.property['user'].position_mapping:
					dn_mapped = s4connector._subtree_replace(dn_mapped, mapping[1], mapping[0])
				if dn_mapped == s4_dn:
					if not (s4connector.lo.base.lower() == dn_mapped[-len(s4connector.lo.base):].lower() and len(s4connector.lo.base) > len(s4connector.lo_s4.base)):
						dn_mapped = s4connector._subtree_replace(dn_mapped, s4connector.lo_s4.base, s4connector.lo.base)
			ucs_secretary.append(dn_mapped)
		# remove multiples
		ucs_secretary = list(dict.fromkeys(ucs_secretary))
		return ucs_secretary


def secretary_sync_ucs_to_s4(s4connector, key, ucs_object):
	attr = 'secretary'

	ucs_secretary = ucs_object['attributes'][attr]
	if ucs_secretary is None:
		return
	else:
		s4_secretary = []
		for ucs_dn in ucs_secretary:
			dn_mapped = ucs_dn
			if s4connector._get_dn_by_ucs(ucs_dn):
				dn_mapped = s4connector._get_dn_by_ucs(ucs_dn)
				dn_mapped = s4connector.dn_mapped_to_base(dn_mapped, s4connector.lo_s4.base)
			if hasattr(s4connector.property['user'], 'position_mapping'):
				for mapping in s4connector.property['user'].position_mapping:
					dn_mapped = s4connector._subtree_replace(dn_mapped, mapping[0], mapping[1])
				if dn_mapped == ucs_dn:
					if not (s4connector.lo_s4.base.lower() == dn_mapped[-len(s4connector.lo_s4.base):].lower() and len(s4connector.lo_s4.base) > len(s4connector.lo.base)):
						dn_mapped = s4connector._subtree_replace(dn_mapped, s4connector.lo.base, s4connector.lo_s4.base)
			s4_secretary.append(dn_mapped)
		# remove multiples
		s4_secretary = list(dict.fromkeys(s4_secretary))
		return s4_secretary
