#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  some mapping helper functions
#
# Copyright 2004-2012 Univention GmbH
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

import string
import univention.config_registry as ucr
import univention.debug2 as ud
import univention.s4connector.s4

configRegistry=ucr.ConfigRegistry()
configRegistry.load()


def ucs2s4_sid(s4connector, key, object):
	_d=ud.function('mapping.ucs2s4_sid -- not implemented')
	pass

def s42ucs_sid(s4connector, key, object):
	_d=ud.function('mapping.s42ucs_sid')
	return univention.s4connector.s4.decode_sid(object['objectSid'])

def ucs2s4_givenName(s4connector, key, object):
	_d=ud.function('mapping.ucs2s4_givenName')
	if object.has_key('firstname') and object.has_key('lastname'):
		return '%s %s' % (object['firstname'], object['lastname'])
	elif object.has_key('firstname'):
		return object['firstname']
	elif object.has_key('lastname'):
		return object['lastname']

def s42ucs_givenName(s4connector, key, object):
	_d=ud.function('mapping.s42ucs_givenName -- not implemented')
	pass

def ucs2s4_dn_string(dn):
	_d=ud.function('mapping.ucs2s4_dn_string')
	return string.replace(dn,configRegistry['ldap/base'],configRegistry['connector/s4/ldap/base'])

def ucs2s4_dn(s4connector, key, object):
	_d=ud.function('mapping.ucs2s4_dn')
	return ucs2s4_dn_string(object.dn)

def s42ucs_dn_string(dn):
	_d=ud.function('mapping.s42ucs_dn_string')
	return string.replace(dn,configRegistry['connector/s4/ldap/base'],configRegistry['ldap/base'])

def s42ucs_dn(s4connector, key, object):
	_d=ud.function('mapping.s42ucs_dn')
	return s42ucs_dn_string(object.dn)

def ucs2s4_user_dn(s4connector, key, object):
	_d=ud.function('mapping.ucs2s4_user_dn')
	return string.replace(ucs2s4_dn(s4connector, key, object),"uid=","cn=")

def s42ucs_user_dn(s4connector, key, object):
	_d=ud.function('mapping.s42ucs_user_dn')
	return string.replace(s42ucs_dn(s4connector, key, object),"cn=","uid=")

def ucs2s4_sambaGroupType(s4connector, key, object):
	_d=ud.function('mapping.ucs2s4_sambaGroupType -- not implemented')
	return "-2147483644"

def s42ucs_sambaGroupType(s4connector, key, object):
	_d=ud.function('mapping.s42ucs_sambaGroupType -- not implemented')
	pass

