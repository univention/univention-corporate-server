# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  write an interpreted token structure to a file
#
# Copyright 2007-2019 Univention GmbH
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

import cgi

import univention.admin.uldap as ua_ldap
import univention.admin.objects as ua_objects
import univention.admin.modules as ua_modules
import univention.admin.mapping as ua_mapping
import univention.admin.uexceptions as ua_exceptions
from univention.config_registry import ConfigRegistry

import univention.debug as ud

from univention.directory.reports.filter import filter_get

__all__ = ['connect', 'get_object', 'cache_object', 'connected', 'identify', 'set_format']

_admin = None

TEX_ESCAPE = {
	u'€': 'EUR',
	'"': "''",
	'\\': '\\textbackslash{}',
	'&': '\\&',
	'%': '\\%',
	'#': '\\#',
	'_': '\\_',
	'{': '\\{',
	'}': '\\}',
	'~': '\\textasciitilde{}',
	'^': '\\^{\,}',
	'$': '\\$',
	u'°': '$^{\\circ}$',
	u'´': '',
}


def texClean(str):
	u"""Escape string for use in LaTeX.

	>>> texClean('Test')
	'Test'
	>>> texClean('"\\&%#_{}~^$')
	"''\\\\textbackslash{}\\\\&\\\\%\\\\#\\\\_\\\\{\\\\}\\\\textasciitilde{}\\\\^{\\\\,}\\\\$"
	>>> texClean('€°´')
	'EUR$^{\\\\circ}$'
	"""
	esc = ''.join([TEX_ESCAPE.get(c, c) for c in str])
	# str is NOT unicode, so '€°´' are non-ASCII characters, which use multiple bytes. See Bug #16637
	esc = esc.replace('€', 'EUR')
	esc = esc.replace('°', '$^{\\circ}$')
	esc = esc.replace('´', '')
	return esc


class AdminConnection(object):

	def __init__(self, userdn=None, password=None, host='localhost', base=None, start_tls=2, access=None, format=None):
		self._cached = {}
		self._modules = {}
		self._policies = {}
		self._format = format
		self._bc = ConfigRegistry()
		self._bc.load()
		self.__reverse = {}
		if not base:
			self._base = self._bc['ldap/base']
		else:
			self._base = base
		self._position = ua_ldap.position(self._base)
		if access:
			self._access = access
		else:
			self._access = ua_ldap.access(host=host, base=self._base, binddn=userdn, bindpw=password, start_tls=start_tls)
		ua_modules.update()

	def __repr__(self):
		fmt = '%s(userdn=%r, password=%r, host=%r, base=%r, start_tls=%r, access=%r, format=%r)'
		val = (self.__class__.__name__, self._access.binddn, self._access.bindpw, self._access.host, self._access.base, self._access.start_tls, self._access, self._format)
		return fmt % val

	def cache_object(self, obj):
		return self.get_object(ua_objects.module(obj), obj.dn)

	def clear_cache(self):
		del self._cached
		self._cached = {}

	def get_object(self, module, dn):
		if dn in self.__reverse:  # this value has been escaped => use <self.__reverse> to unescape
			possible_real_DNs = set()
			for possible_real_DN_set in self.__reverse[dn].values():
				possible_real_DNs |= possible_real_DN_set  # collect every distinct possible value
			possible_real_DNs = tuple(possible_real_DNs)
			if not len(possible_real_DNs) == 1:
				raise ValueError('ambiguous DNs, cannot unescape %s (possibilities: %s)' % (repr(dn), repr(possible_real_DNs)))
			dn = possible_real_DNs[0]
		try:
			return self.get_object_real(module, dn)
		except ua_exceptions.noObject:
			return None

	def get_object_real(self, module, dn):
		if dn in self._cached:
			return self._cached[dn]
		if isinstance(module, basestring):
			if module in self._modules:
				module = self._modules[module]
			else:
				name = module
				module = ua_modules.get(name)
				ua_modules.init(self._access, self._position, module)
				self._modules[name] = module
		elif module is None:
			module = self.identify(dn)
			if not module:
				return None
			ua_modules.init(self._access, self._position, module)
		new = ua_objects.get(module, None, self._access, position=self._position, dn=dn)
		# if the object is not valid it should be displayed as an empty object
		try:
			new.open()
		except Exception:
			# write the traceback in the logfile
			import traceback

			ud.debug(ud.ADMIN, ud.ERROR, 'The object %s could not be opened' % dn)
			try:
				tb = traceback.format_exc().encode('ascii', 'replace').replace('%', '?')
				# this might fail because of problems with univention.debug
				ud.debug(ud.ADMIN, ud.ERROR, 'Traceback: %s' % tb)
			except:
				pass
		for key, value in new.items():
			from univention.directory.reports.document import Document
			if self._format in (Document.TYPE_LATEX, Document.TYPE_RML):
				i, j = self.format_property(new.descriptions, key, value)
				new.info[i] = j
			else:
				new.info[key] = value

		self._get_policies(new)
		self._cached[dn] = new

		return new

	def identify(self, dn):
		res = self._access.search(base=dn, scope='base')
		if res:
			mods = ua_modules.identify(dn, res[0][1])
			if mods:
				return mods[0]
		return None

	# store the old value of every attribute (if it is a string) in <self.__reverse> to enable <get_object()> to reverse the escaping
	def format_property(self, props, oldkey, oldvalue):
		(newkey, newvalue) = self.format_property_real(props, oldkey, oldvalue)
		assert newkey == oldkey
		key = oldkey
		if isinstance(newvalue, (list, tuple)):  # multivalue => unpack
			for (newv, oldv) in zip(newvalue, oldvalue):
				if isinstance(oldv, str) and newv != oldv:  # only consider strings, because DNs are always strings
					if newv not in self.__reverse:
						self.__reverse[newv] = {}
					oldvalues = self.__reverse[newv].get(key, set())
					oldvalues.add(oldv)
					self.__reverse[newv][key] = oldvalues
		else:
			if isinstance(oldvalue, str) and newvalue != oldvalue:  # only consider strings, because DNs are always strings
				if newvalue not in self.__reverse:
					self.__reverse[newvalue] = {}
				oldvalues = self.__reverse[newvalue].get(key, set())
				oldvalues.add(oldvalue)
				self.__reverse[newvalue][key] = oldvalues
		return (key, newvalue)

	def format_property_real(self, props, key, value):
		prop = props.get(key, None)

		if not prop:
			return (key, value)
		else:
			if isinstance(value, (list, tuple)):
				result = []
				for v in value:
					if isinstance(v, (list, tuple)):
						for i in v:
							result.append(self.escape(str(i)))
					else:
						result.append(self.escape(str(v)))
				value = result
			elif value:
				value = self.escape(value)
			filter = filter_get(prop.syntax)
			if filter:
				return filter(prop, key, value)

		return (key, value)

	def escape(self, value):
		from univention.directory.reports.document import Document
		if self._format == Document.TYPE_LATEX:
			return texClean(value)
		elif self._format == Document.TYPE_RML:
			return cgi.escape(value, quote=True)
		return value

	def _get_policies(self, obj):
		dict = {}
		policies = self._access.getPolicies(obj.dn)
		for policy_oc, attrs in policies.items():
			module_name = ua_objects.ocToType(policy_oc)
			module = ua_modules.get(module_name)
			if not module:
				continue
			for attr_name, value_dict in attrs.items():
				dict[attr_name] = value_dict['value']

			for key, value in ua_mapping.mapDict(module.mapping, dict).items():
				from univention.directory.reports.document import Document
				if self._format in (Document.TYPE_LATEX, Document.TYPE_RML):
					i, j = self.format_property(module.property_descriptions, key, value)
					obj.info[i] = j
				else:
					obj.info[key] = value


def connect(userdn=None, password=None, host='localhost', base=None, start_tls=2, access=None):
	global _admin
	if _admin:
		return
	_admin = AdminConnection(userdn, password, host, base, start_tls, access)


def cache_object(obj):
	global _admin
	if not _admin:
		return None
	return _admin.cache_object(obj)


def clear_cache():
	global _admin
	if not _admin:
		return
	_admin.clear_cache()


def get_object(module, dn):
	global _admin
	if not _admin:
		return None
	try:
		return _admin.get_object(module, dn)
	except ua_exceptions.ldapError:
		return None


def set_format(format):
	global _admin
	if _admin:
		_admin._format = format


def identify(dn):
	global _admin
	return _admin.identfy(dn)


def connected():
	global _admin
	return _admin is not None


if __name__ == '__main__':
	import doctest
	doctest.testmod()
