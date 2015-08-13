#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app wrapper for udm functions
#
# Copyright 2015 Univention GmbH
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
#

import os
import base64

from ldap.filter import escape_filter_chars
from ldap.dn import explode_dn

from univention.config_registry import ConfigRegistry
import univention.admin.objects as udm_objects
import univention.admin.modules as udm_modules
import univention.admin.uexceptions as udm_errors
from univention.uldap import access as base_access
from univention.admin.uldap import getMachineConnection, getAdminConnection, access, position

udm_modules.update()

_initialized = set()
def _get_module(module, lo, pos):
	mod = udm_modules.get(module)
	if module not in _initialized:
		udm_modules.init(lo, pos, mod)
		_initialized.add(module)
	return mod

def init_object(module, lo, pos, dn=''):
	module = _get_module(module, lo, pos)
	obj = udm_objects.get(module, None, lo, pos, dn)
	udm_objects.open(obj)
	return obj

def remove_object_if_exists(module, lo, pos, dn):
	obj = init_object(module, lo, pos, dn)
	try:
		obj.remove()
	except udm_errors.noObject:
		pass
	else:
		udm_objects.performCleanup(obj)

def create_object_if_not_exists(module, lo, pos, **kwargs):
	obj = init_object(module, lo, pos)
	if 'policies' in kwargs:
		obj.policies = kwargs.pop('policies')
	for key, value in kwargs.iteritems():
		obj.info[key] = value
	try:
		obj.create()
	except udm_errors.objectExists:
		pass
	else:
		return obj

def search_objects(module, lo, pos, base='', **kwargs):
	module = _get_module(module, lo, pos)
	filter_str = ''
	for key, value in kwargs.iteritems():
		filter_str = '%s=%s' % (key, escape_filter_chars(value))
	objs = module.lookup(None, lo, filter_str, base=base)
	for obj in objs:
		udm_objects.open(obj)
	return objs

def get_machine_connection():
	return getMachineConnection()

def get_admin_connection():
	return getAdminConnection()

def get_connection(userdn, password):
	ucr = ConfigRegistry()
	ucr.load()
	port = int(ucr.get('ldap/server/port', '7389'))
	host = ucr['ldap/server/name']
	base = ucr['ldap/base']
	lo = base_access(host=host, port=port, base=base, binddn=userdn, bindpw=password)
	lo = access(lo=lo)
	pos = position(lo.base)
	return lo, pos

class ApplicationLDAPObject(object):
	def __init__(self, app, lo, pos, ucr, create_if_not_exists=False):
		self._localhost = '%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))
		self._udm_obj = None
		self._rdn = '%s_%s' % (app.id, app.version)
		self._container = 'cn=%s,cn=apps,cn=univention,%s' % (app.id, ucr.get('ldap/base'))
		self._lo = lo
		self._pos = pos
		self._reload(app, ucr, create_if_not_exists)

	def __nonzero__(self):
		return self._udm_obj is not None

	def _reload(self, app, ucr, create_if_not_exists=False):
		result = search_objects('appcenter/app', self._lo, self._pos, id=self._rdn)
		if result:
			self._udm_obj = result[0]
			self._udm_obj.open()
		elif create_if_not_exists:
			self._create_obj(app, ucr)

	def _create_obj(self, app, ucr):
		containers = explode_dn(self._container, 1)
		containers = containers[0:containers.index('apps')]
		base = 'cn=apps,cn=univention,%s' % ucr.get('ldap/base')
		self._pos.setDn(base)
		for container in reversed(containers):
			if not search_objects('container/cn', self._lo, self._pos, base, cn=container):
				create_object_if_not_exists('container/cn', self._lo, self._pos, name=container)
			base = 'cn=%s,%s' % (container, base)
			self._pos.setDn(base)
		base64icon = ''
		try:
			from univention.appcenter.actions.umc_update import FRONTEND_ICONS_DIR
			with open(os.path.join(FRONTEND_ICONS_DIR, '50x50', app.icon)) as f:
				base64icon = base64.b64encode(f.read())
		except (ImportError, IOError):
			pass
		attrs = {
			'id' : self._rdn,
			'name' : app.get_localised_list('name'),
			'version' : app.version,
			'shortDescription' : app.get_localised_list('description'),
			'longDescription' : app.get_localised_list('long_description'),
			'contact' : app.contact,
			'maintainer' : app.maintainer,
			'website' : app.get_localised_list('website'),
			'websiteVendor' : app.get_localised_list('website_vendor'),
			'websiteMaintainer' : app.get_localised_list('website_maintainer'),
			'screenshot' : app.screenshot,
			'icon' : base64icon,
			'category' : app.get_localised('categories'),
			'webInterface' : app.web_interface,
			'webInterfaceName' : app.web_interface_name,
			'conflictingApps' : app.conflicted_apps,
			'conflictingSystemPackages' : app.conflicted_system_packages,
			'defaultPackages' : app.default_packages,
			'defaultPackagesMaster' : app.default_packages_master,
			'umcModuleName' : app.umc_module_name,
			'umcModuleFlavor' : app.umc_module_flavor,
			'serverRole' : app.server_role,
		}
		obj = create_object_if_not_exists('appcenter/app', self._lo, self._pos, **attrs)
		if obj:
			self._reload(app, ucr, create_if_not_exists=False)

	def add_localhost(self):
		self._udm_obj.info.setdefault('server', [])
		if self._localhost not in self._udm_obj.info['server']:
			self._udm_obj.info['server'].append(self._localhost)
			self._udm_obj.modify()

	def remove_localhost(self):
		try:
			self._udm_obj.info.setdefault('server', [])
			self._udm_obj.info['server'].remove(self._localhost)
		except ValueError:
			pass
		else:
			self._udm_obj.modify()

	def remove_from_directory(self):
		self._udm_obj.remove()

	def installed_on_servers(self):
		if not self:
			return []
		return self._udm_obj.info.get('server', [])

	def anywhere_installed(self):
		return bool(self.installed_on_servers())

def get_app_ldap_object(app, lo=None, pos=None, ucr=None, or_create=False):
	if lo is None or pos is None:
		lo, pos = get_machine_connection()
	if ucr is None:
		ucr = ConfigRegistry()
		ucr.load()
	return ApplicationLDAPObject(app, lo, pos, ucr, or_create)

