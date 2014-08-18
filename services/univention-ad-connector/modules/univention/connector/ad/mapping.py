#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  some mapping helper functions
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

import string
import univention_baseconfig
import univention.debug2 as ud

baseConfig=univention_baseconfig.baseConfig()
baseConfig.load()



def ucs2ad_sid(connector, key, object):
	_d=ud.function('mapping.ucs2ad_sid -- not implemented')
	pass

def ad2ucs_sid(connector, key, object):
	_d=ud.function('mapping.ad2ucs_sid')
	return univention.connector.ad.decode_sid(object['objectSid'])

def ucs2ad_givenName(connector, key, object):
	_d=ud.function('mapping.ucs2ad_givenName')
	if object.has_key('firstname') and object.has_key('lastname'):
		return '%s %s' % (object['firstname'], object['lastname'])
	elif object.has_key('firstname'):
		return object['firstname']
	elif object.has_key('lastname'):
		return object['lastname']

def ad2ucs_givenName(connector, key, object):
	_d=ud.function('mapping.ad2ucs_givenName -- not implemented')
	pass

def ucs2ad_dn_string(dn):
	_d=ud.function('mapping.ucs2ad_dn_string')
	return string.replace(dn,baseConfig['ldap/base'],baseConfig['connector/ad/ldap/base'])

def ucs2ad_dn(connector, key, object):
	_d=ud.function('mapping.ucs2ad_dn')
	return ucs2ad_dn_string(object.dn)

def ad2ucs_dn_string(dn):
	_d=ud.function('mapping.ad2ucs_dn_string')
	return string.replace(dn,baseConfig['connector/ad/ldap/base'],baseConfig['ldap/base'])

def ad2ucs_dn(connector, key, object):
	_d=ud.function('mapping.ad2ucs_dn')
	return ad2ucs_dn_string(object.dn)

def ucs2ad_user_dn(connector, key, object):
	_d=ud.function('mapping.ucs2ad_user_dn')
	return string.replace(ucs2ad_dn(connector, key, object),"uid=","cn=")

def ad2ucs_user_dn(connector, key, object):
	_d=ud.function('mapping.ad2ucs_user_dn')
	return string.replace(ad2ucs_dn(connector, key, object),"cn=","uid=")

def ucs2ad_sambaGroupType(connector, key, object):
	_d=ud.function('mapping.ucs2ad_sambaGroupType -- not implemented')
	return "-2147483644"

def ad2ucs_sambaGroupType(connector, key, object):
	_d=ud.function('mapping.ad2ucs_sambaGroupType -- not implemented')
	pass

