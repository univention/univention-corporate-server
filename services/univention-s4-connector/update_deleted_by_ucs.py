#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Univention Directory Listener script for the s4 connector
#
# Copyright 2004-2020 Univention GmbH
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

from __future__ import absolute_import
import cPickle
import listener
import os
import time
import shutil
import univention.debug
import ldap
import sys
import subprocess
import univention.s4connector.s4
from univention.s4connector import configdb

name = 'update_deleted_by_ucs'
description = 'Updates the S4 Connector cache of objects which were removed by UCS'
filter = '(objectClass=*)'
attributes = []
modrdn = '1'


def recode_attribs(s4, attribs):
	s4.initialize_ucs(False)
	nattribs = {}
	for key in attribs.keys():
		if key in s4.ucs_no_recode:
			nattribs[key] = attribs[key]
		else:
			try:
				nvals = []
				for val in attribs[key]:
					nvals.append(unicode(val, 'utf8'))
				nattribs[unicode(key, 'utf8')] = nvals
			except UnicodeDecodeError:
				nattribs[key] = attribs[key]

	return nattribs


def map_dn_to_s4(s4, old, ucs_dn):
	old = recode_attribs(s4, old)
	key = s4.identify_udm_object(ucs_dn, old)
	dn_mapped = ucs_dn
	dn_mapped = s4.dn_mapped_to_base(ucs_dn, s4.lo_s4.base)
	if s4._get_dn_by_ucs(dn_mapped):
		dn_mapped = s4._get_dn_by_ucs(dn_mapped)
		dn_mapped = s4.dn_mapped_to_base(dn_mapped, s4.lo_s4.base)
	if key and hasattr(s4.property[key], 'position_mapping'):
		for mapping in s4.property[key].position_mapping:
			dn_mapped = s4._subtree_replace(dn_mapped, mapping[0], mapping[1])
		if dn_mapped == ucs_dn:
			if not (s4.lo_s4.base.lower() == dn_mapped[-len(s4.lo_s4.base):].lower() and len(s4.lo_s4.base) > len(s4.lo.base)):
				dn_mapped = s4._subtree_replace(dn_mapped, s4.lo.base, s4.lo_s4.base)
	return dn_mapped


def load_mapping(configbasename='connector'):
		old_sys_path = sys.path[:]
		sys.path.append('/etc/univention/{}/s4/'.format(configbasename))
		try:
			import mapping
		finally:
			sys.path = old_sys_path
		return mapping.s4_mapping


def get_s4_connector(configbasename='connector'):
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	if '%s/s4/ldap/certificate' % configbasename not in configRegistry or True:
		if configRegistry.is_true('%s/s4/ldap/ssl' % configbasename):
			MODULE.error('Missing Configuration Key %s/s4/ldap/certificate' % configbasename)
			raise MissingConfigurationKey('%s/s4/ldap/certificate' % configbasename)

	if configRegistry.get('%s/s4/ldap/bindpw' % configbasename):
		with open(configRegistry['%s/s4/ldap/bindpw' % configbasename]) as fob:
			s4_ldap_bindpw = fob.read().rstrip('\n')
	else:
		s4_ldap_bindpw = None

	try:
		s4 = univention.s4connector.s4.s4(
			configbasename,
			load_mapping(configbasename),
			configRegistry,
			configRegistry['%s/s4/ldap/host' % configbasename],
			configRegistry['%s/s4/ldap/port' % configbasename],
			configRegistry['%s/s4/ldap/base' % configbasename],
			configRegistry.get('%s/s4/ldap/binddn' % configbasename),
			s4_ldap_bindpw,
			configRegistry['%s/s4/ldap/certificate' % configbasename],
			configRegistry['%s/s4/listener/dir' % configbasename],
			False
		)
	except KeyError as error:
		MODULE.error('Missing Configuration key %s' % error.message)
		raise MissingConfigurationKey(error.message)
	else:
		return s4

class MissingConfigurationKey(KeyError):
	def __str__(s4):
		return '{}: {}'.format(self.__class__.__name__, self.message)

def _is_module_disabled():
	return listener.baseConfig.is_true('connector/s4/listener/disabled', False)

listener.setuid(0)
s4 = get_s4_connector()

def handler(dn, new, old, operation):
	global s4
	listener.setuid(0)
	if s4 and old.get('entryDN') and operation == 'd':
		s4_dn = map_dn_to_s4(s4, old, old.get('entryDN')[0])
		objectGUID = s4._get_objectGUID(s4_dn)
		if objectGUID and old.get('entryUUID'):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "update_deleted_by_ucs: updating deleted by UCS s4Connector cache")
			s4.update_deleted_cache_after_removal(old.get('entryUUID')[0], objectGUID)
		else:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "Could not update deleted cache of object %s, since an objectGUID cold not be determined. objectGUID: %s" % (dn, objectGUID,))

