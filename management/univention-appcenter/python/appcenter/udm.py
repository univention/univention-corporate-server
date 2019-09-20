#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app wrapper for udm functions
#
# Copyright 2015-2019 Univention GmbH
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
#

import os
import base64

from ldap.filter import escape_filter_chars
from ldap.dn import explode_dn, escape_dn_chars

import univention.admin.objects as udm_objects
import univention.admin.modules as udm_modules
import univention.admin.filter as udm_filter
import univention.admin.uexceptions as udm_errors
from univention.uldap import access as base_access
from univention.admin.uldap import getMachineConnection, getAdminConnection, access, position

from univention.appcenter.ucr import ucr_get

_initialized = set()


class FakeApp(object):

	def __init__(self, id, version):
		self.id = id
		self.version = version


def _update_modules():
	if not _initialized:
		udm_modules.update()


def _get_module(module, lo, pos):
	_update_modules()
	mod = udm_modules.get(module)
	if module not in _initialized:
		udm_modules.init(lo, pos, mod)
		_initialized.add(module)
	return mod


def init_object(module, lo, pos, dn='', attrs=None):
	module = _get_module(module, lo, pos)
	obj = udm_objects.get(module, None, lo, pos, dn)
	udm_objects.open(obj)
	if attrs:
		if 'policies' in attrs:
			obj.policies = attrs.pop('policies')
		for key, value in attrs.iteritems():
			obj[key] = value
	return obj


def remove_object_if_exists(module, lo, pos, dn):
	try:
		obj = init_object(module, lo, pos, dn)
		obj.remove()
	except udm_errors.noObject:
		pass
	else:
		udm_objects.performCleanup(obj)


def create_object_if_not_exists(_module, _lo, _pos, **kwargs):
	obj = init_object(_module, _lo, _pos, attrs=kwargs)
	dn = obj._ldap_dn()
	try:
		init_object(_module, _lo, _pos, dn)
	except udm_errors.noObject:
		obj.create()
		return obj
	else:
		# dn already exists
		return


def modify_object(_module, _lo, _pos, _dn, **kwargs):
	try:
		obj = init_object(_module, _lo, _pos, _dn, attrs=kwargs)
	except udm_errors.noObject:
		return
	else:
		obj.modify()
		return obj


def search_objects(_module, _lo, _pos, _base='', **kwargs):
	module = _get_module(_module, _lo, _pos)
	expressions = []
	conj = udm_filter.conjunction('&', expressions)
	for key, value in kwargs.iteritems():
		expressions.append(udm_filter.expression(key, escape_filter_chars(value), '='))
	try:
		objs = module.lookup(None, _lo, str(conj), base=_base)
	except udm_errors.noObject:
		objs = []
	for obj in objs:
		udm_objects.open(obj)
	return objs


def dn_exists(dn, lo):
	try:
		lo.searchDn(base=dn, scope='base')
	except udm_errors.noObject:
		return False
	else:
		return True


def get_machine_connection():
	return getMachineConnection()


def get_admin_connection():
	return getAdminConnection()


def get_connection(userdn, password):
	port = int(ucr_get('ldap/master/port', '7389'))
	host = ucr_get('ldap/master')
	base = ucr_get('ldap/base')
	lo = base_access(host=host, port=port, base=base, binddn=userdn, bindpw=password)
	lo = access(lo=lo)
	pos = position(lo.base)
	return lo, pos


def get_read_connection(userdn, password):
	port = int(ucr_get('ldap/server/port', '7389'))
	host = ucr_get('ldap/server/name')
	base = ucr_get('ldap/base')
	lo = base_access(host=host, port=port, base=base, binddn=userdn, bindpw=password)
	lo = access(lo=lo)
	pos = position(lo.base)
	return lo, pos


class ApplicationLDAPObject(object):

	def __init__(self, app, lo, pos, create_if_not_exists=False):
		self._localhost = '%s.%s' % (ucr_get('hostname'), ucr_get('domainname'))
		self._udm_obj = None
		self._rdn = '%s_%s' % (app.id, app.version)
		self._container = 'cn=%s,cn=apps,cn=univention,%s' % (escape_dn_chars(app.id), ucr_get('ldap/base'))
		self._lo = lo
		self._pos = pos
		self._reload(app, create_if_not_exists)

	def __nonzero__(self):
		return self._udm_obj is not None

	@property
	def dn(self):
		return 'univentionAppID=%s,%s' % (escape_dn_chars(self._rdn), self._container)

	def _reload(self, app, create_if_not_exists=False):
		try:
			self._udm_obj = init_object('appcenter/app', self._lo, self._pos, self.dn)
		except udm_errors.noObject:
			self._udm_obj = None
			if create_if_not_exists:
				self._create_obj(app)

	def _create_obj(self, app):
		create_recursive_container(self._container, self._lo, self._pos)
		self._pos.setDn(self._container)
		base64icon = ''
		icon_file = app.get_cache_file('logo')
		if os.path.exists(icon_file):
			try:
				with open(icon_file) as f:
					base64icon = base64.b64encode(f.read())
			except IOError:
				pass
		attrs = {
			'id': self._rdn,
			'name': app.get_localised_list('name'),
			'version': app.version,
			'shortDescription': app.get_localised_list('description'),
			'longDescription': app.get_localised_list('long_description'),
			'contact': app.contact,
			'maintainer': app.maintainer,
			'website': app.get_localised_list('website'),
			'websiteVendor': app.get_localised_list('website_vendor'),
			'websiteMaintainer': app.get_localised_list('website_maintainer'),
			'icon': base64icon,
			'category': app.get_localised('categories'),
			'webInterface': app.web_interface,
			'webInterfaceName': app.web_interface_name,
			'conflictingApps': app.conflicted_apps,
			'conflictingSystemPackages': app.conflicted_system_packages,
			'defaultPackages': app.default_packages,
			'defaultPackagesMaster': app.default_packages_master,
			'umcModuleName': app.umc_module_name,
			'umcModuleFlavor': app.umc_module_flavor,
			'serverRole': app.server_role,
		}
		obj = create_object_if_not_exists('appcenter/app', self._lo, self._pos, **attrs)
		if obj:
			self._reload(app, create_if_not_exists=False)

	@classmethod
	def from_udm_obj(cls, udm_obj, lo, pos):
		app_id = explode_dn(udm_obj.dn, 1)[1]
		app = FakeApp(id=app_id, version=udm_obj.info.get('version'))
		return cls(app, lo, pos)

	def add_localhost(self):
		self._udm_obj.info.setdefault('server', [])
		if self._localhost not in self._udm_obj.info['server']:
			self._udm_obj.info['server'].append(self._localhost)
			self._udm_obj.modify()
		for ldap_object in self.get_siblings():
			if not self._lo.compare_dn(self.dn, ldap_object.dn):
				app_obj = self.from_udm_obj(ldap_object, self._lo, self._pos)
				app_obj.remove_localhost()

	def remove_localhost(self):
		try:
			self._udm_obj.info.setdefault('server', [])
			self._udm_obj.info['server'].remove(self._localhost)
		except ValueError:
			pass
		else:
			self._udm_obj.modify()
			if not self.anywhere_installed():
				self.remove_from_directory()

	def remove_from_directory(self):
		remove_object_if_exists('appcenter/app', self._lo, self._pos, self.dn)

	def installed_on_servers(self):
		if not self:
			return []
		return self._udm_obj.info.get('server', [])

	def get_siblings(self):
		return search_objects('appcenter/app', self._lo, self._pos, self._container)

	def anywhere_installed(self):
		return bool(self.installed_on_servers())


def get_app_ldap_object(app, lo=None, pos=None, or_create=False):
	if lo is None or pos is None:
		lo, pos = get_machine_connection()
	return ApplicationLDAPObject(app, lo, pos, or_create)


def create_recursive_container(dn, lo, pos):
	if dn_exists(dn, lo):
		return
	position_parts = explode_dn(dn)
	previous_position = ','.join(position_parts[1:])
	create_recursive_container(previous_position, lo, pos)
	pos.setDn(previous_position)
	name = explode_dn(position_parts[0], 1)[0]
	if dn.startswith('ou'):
		module = 'container/ou'
	else:
		module = 'container/cn'
	create_object_if_not_exists(module, lo, pos, name=name)
