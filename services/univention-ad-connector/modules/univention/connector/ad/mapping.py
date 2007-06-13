#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  some mapping helper functions
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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

import string
import univention_baseconfig
import univention.debug

baseConfig=univention_baseconfig.baseConfig()
baseConfig.load()



def ucs2ad_sid(connector, key, object):
	_d=univention.debug.function('mapping.ucs2ad_sid -- not implemented')
	pass

def ad2ucs_sid(connector, key, object):
	_d=univention.debug.function('mapping.ad2ucs_sid')
	return univention.connector.ad.decode_sid(object['objectSid'])

def ucs2ad_givenName(connector, key, object):
	_d=univention.debug.function('mapping.ucs2ad_givenName')
	if object.has_key('firstname') and object.has_key('lastname'):
		return '%s %s' % (object['firstname'], object['lastname'])
	elif object.has_key('firstname'):
		return object['firstname']
	elif object.has_key('lastname'):
		return object['lastname']

def ad2ucs_givenName(connector, key, object):
	_d=univention.debug.function('mapping.ad2ucs_givenName -- not implemented')
	pass

def ucs2ad_dn_string(dn):
	_d=univention.debug.function('mapping.ucs2ad_dn_string')
	return string.replace(dn,baseConfig['ldap/base'],baseConfig['connector/ad/ldap/base'])

def ucs2ad_dn(connector, key, object):
	_d=univention.debug.function('mapping.ucs2ad_dn')
	return ucs2ad_dn_string(object.dn)

def ad2ucs_dn_string(dn):
	_d=univention.debug.function('mapping.ad2ucs_dn_string')
	return string.replace(dn,baseConfig['connector/ad/ldap/base'],baseConfig['ldap/base'])

def ad2ucs_dn(connector, key, object):
	_d=univention.debug.function('mapping.ad2ucs_dn')
	return ad2ucs_dn_string(object.dn)

def ucs2ad_user_dn(connector, key, object):
	_d=univention.debug.function('mapping.ucs2ad_user_dn')
	return string.replace(ucs2ad_dn(connector, key, object),"uid=","cn=")

def ad2ucs_user_dn(connector, key, object):
	_d=univention.debug.function('mapping.ad2ucs_user_dn')
	return string.replace(ad2ucs_dn(connector, key, object),"cn=","uid=")

def ucs2ad_sambaGroupType(connector, key, object):
	_d=univention.debug.function('mapping.ucs2ad_sambaGroupType -- not implemented')
	return "-2147483644"

def ad2ucs_sambaGroupType(connector, key, object):
	_d=univention.debug.function('mapping.ad2ucs_sambaGroupType -- not implemented')
	pass

