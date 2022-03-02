#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
"""Handle UCR network configuration."""
#
# Copyright 2010-2022 Univention GmbH
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

# pylint: disable-msg=W0142,C0103,R0201,R0904
from __future__ import absolute_import

import re
from sys import maxsize
from functools import wraps
from univention.config_registry.backend import ConfigRegistry

from ipaddress import IPv4Address, IPv6Address, IPv4Interface, IPv6Interface

try:
	from typing import Any, Callable, Dict, Iterator, Optional, Union, Tuple, Type  # noqa F401
	from ipaddress import _IPAddressBase  # noqa F401
except ImportError:  # pragma: no cover
	pass

__all__ = ['RE_IFACE', 'forgiving', 'cmp_alnum', 'Interfaces']

_SKIP = {
	'interfaces/handler',
	'interfaces/primary',
	'interfaces/restart/auto',
}
RE_IFACE = re.compile(r'''^
		(?!(?:%s)$) # _SKIP
		interfaces/ # prefix
		([^/]+)/    # iface name
		(
			(?:ipv6/([0-9A-Za-z]+)/)? # IPv6 name
			.*)        # suffix
		$''' % ('|'.join(_SKIP)), re.VERBOSE)


def forgiving(translation=None):
	# type: (Dict[Type[Exception], Any]) -> Callable[[Callable], Callable]
	"""
	Decorator to translate exceptions into return values.

	:param translation: Mapping from Exception class to return value.
	"""
	if translation is None:
		translation = {}

	def decorator(func):
		# type: (Callable) -> Callable
		"""Wrap function and translate exceptions."""

		@wraps(func)
		def inner(self, *args, **kwargs):
			"""Run function and translate exceptions."""
			try:
				return func(self, *args, **kwargs)
			except Exception as ex:
				best = None
				for cls, _value in translation.items():
					if isinstance(ex, cls):
						if best is None or issubclass(cls, best):
							best = cls
				if best:
					return translation[best]
				raise

		return inner

	return decorator


forgiving_addr = forgiving({ValueError: False, KeyError: None})
"""Decorator to translate errors from IP address parsing to `None` instead of raising an exception."""


def cmp_alnum(value):
	# type: (str) -> Tuple
	"""
	Sort value split by digits / non-digits.

	:param value: The value to sort.
	:returns: value split into tuple.
	"""
	value = str(value)
	key = []
	for num, text in RE_ALNUM.findall(value):
		key.append(int(num or maxsize))
		key.append(text)
	return tuple(key)


RE_ALNUM = re.compile(r'([0-9]+)|([^0-9]+)')


class _Iface(dict):
	"""Single network interface."""

	def __init__(self, *args, **kwargs):
		dict.__init__(self, *args, **kwargs)
		self.ipv6_names = set()

	@property
	def name(self):
		# type: () -> str
		"""Return interface name."""
		return self['name'].replace('_', ':')

	@property  # type: ignore
	@forgiving({KeyError: maxsize, ValueError: maxsize})
	def order(self):
		# type: () -> int
		"""Return interface order."""
		return int(self['order'])

	@property
	def type(self):
		# type: () -> str
		"""Return interface handler."""
		return self.get('type', '')

	@property
	def start(self):
		# type: () -> bool
		"""Return automatic interface start."""
		return ConfigRegistry().is_true(value=self.get('start', '1'))

	@property  # type: ignore
	@forgiving_addr
	def network(self):
		# type: () -> IPv4Address
		"""Return network address."""
		return IPv4Address(u'%(network)s' % self)

	@property  # type: ignore
	@forgiving_addr
	def broadcast(self):
		# type: () -> IPv4Address
		"""Return broadcast address."""
		return IPv4Address(u'%(broadcast)s' % self)

	@forgiving_addr
	def ipv4_address(self):
		# type: () -> IPv4Interface
		"""Return IPv4 address."""
		return IPv4Interface(u'%(address)s/%(netmask)s' % self)

	@forgiving_addr
	def ipv6_address(self, name='default'):
		# type: (str) -> IPv6Interface
		"""Return IPv6 address."""
		key = u'%%(ipv6/%s/address)s/%%(ipv6/%s/prefix)s' % (name, name)
		return IPv6Interface(key % self)

	@property
	def routes(self):
		# type: () -> Iterator[str]
		"""Return interface routes."""
		for k, v in sorted(self.items()):
			if not k.startswith('route/'):
				continue
			if v.startswith('host ') or v.startswith('net '):
				yield v

	@property
	def options(self):
		# type: () -> Iterator[str]
		"""Return interface options."""
		for k, v in sorted(self.items()):
			if not k.startswith('options/'):
				continue
			yield v


class VengefulConfigRegistry(ConfigRegistry):
	"""
	Instance wrapper for Config Registry throwing exceptions.

	:param base_object: UCR instance.

	<https://forge.univention.org/bugzilla/show_bug.cgi?id=28276>
	<http://stackoverflow.com/questions/1443129/>
	"""

	def __init__(self, base_object):
		self.__class__ = type(base_object.__class__.__name__, (self.__class__, base_object.__class__), {})
		self.__dict__ = base_object.__dict__

	def __getitem__(self, key):
		# type: (str) -> str
		"""
		Return registry value.

		Compared with :py:meth:`ConfigRegistry.__getitem__` this raises an exception instead of returning `None`.

		:param key: UCR variable name.
		:returns: the value.
		:raises: KeyError when the value is not found.
		"""
		for _reg, registry in self._walk():
			try:
				value = registry[key]
				return value
			except KeyError:
				continue
		raise KeyError(key)


class Interfaces(object):
	"""
	Handle network interfaces configured by UCR.

	:param ucr: UCR instance.
	"""

	def __init__(self, ucr=None):
		# type: (ConfigRegistry) -> None
		if ucr is None:
			ucr = ConfigRegistry()
			ucr.load()
		if isinstance(ucr, ConfigRegistry):
			ucr = VengefulConfigRegistry(ucr)

		self.primary = ucr.get('interfaces/primary', 'eth0')
		try:
			self.ipv4_gateway = IPv4Address(u"%(gateway)s" % ucr)  # type: Union[IPv4Address, None, bool]
		except KeyError:
			self.ipv4_gateway = None
		except ValueError:
			self.ipv4_gateway = False
		try:
			# <https://tools.ietf.org/html/rfc4007#section-11>
			# As a common notation to specify the scope zone, an
			# implementation SHOULD support the following format:
			# <address>%<zone_id>
			parts = ucr['ipv6/gateway'].rsplit('%', 1)
			gateway = parts.pop(0)
			zone_index = parts[0] if parts else None
			self.ipv6_gateway = IPv6Address(u"%s" % (gateway,))  # type: Union[IPv6Address, None, bool]
			self.ipv6_gateway_zone_index = zone_index
		except KeyError:
			self.ipv6_gateway = None
			self.ipv6_gateway_zone_index = None
		except ValueError:
			self.ipv6_gateway = False
			self.ipv6_gateway_zone_index = None

		self._all_interfaces = {}  # type: Dict[str, _Iface]
		for key, value in ucr.items():
			if not value:
				continue
			match = RE_IFACE.match(key)
			if not match:
				continue
			iface, subkey, ipv6_name = match.groups()
			data = self._all_interfaces.setdefault(iface, _Iface(name=iface))
			data[subkey] = value
			if ipv6_name:
				data.ipv6_names.add(ipv6_name)

	def _cmp_order(self, iface):
		# type: (_Iface) -> Tuple[Tuple, Tuple]
		"""
		Compare interfaces by order.

		:param iface: Other interface.
		:returns: A tuple to be used as a key for sorting.
		"""
		return (
			cmp_alnum(iface.order),
			cmp_alnum(iface.name),
		)

	def _cmp_primary(self, iface):
		# type: (_Iface) -> Tuple[int, Tuple, Tuple]
		"""
		Compare interfaces by primary.

		:param iface: Other interface.
		:returns: 3-tuple to be used as a key for sorting.
		"""
		try:
			primary = self.primary.index(iface.name)
		except ValueError:
			primary = maxsize
		return (
			primary,
			cmp_alnum(iface.order),
			cmp_alnum(iface.name),
		)

	def _cmp_name(self, iname):
		# type: (str) -> str
		"""
		Compare IPv6 sub-interfaces by name.

		:param name: Interface name.
		:returns: string used as a key for sorting.
		"""
		return '' if iname == 'default' else iname

	@property
	def all_interfaces(self):
		# type: () -> Iterator[Tuple[str, _Iface]]
		"""Yield IPv4 interfaces."""
		for name_settings in sorted(self._all_interfaces.items(), key=lambda name_iface: self._cmp_order(name_iface[1])):
			yield name_settings

	@property
	def ipv4_interfaces(self):
		# type: () -> Iterator[Tuple[str, _Iface]]
		"""Yield IPv4 interfaces."""
		for name, iface in sorted(self._all_interfaces.items(), key=lambda _name_iface: self._cmp_order(_name_iface[1])):
			if iface.ipv4_address() is not None:
				yield (name, iface)

	@property
	def ipv6_interfaces(self):
		# type: () -> Iterator[Tuple[_Iface, str]]
		"""Yield names of IPv6 interfaces."""
		for iface in sorted(self._all_interfaces.values(), key=self._cmp_order):
			for name in sorted(iface.ipv6_names, key=self._cmp_name):
				if iface.ipv6_address(name):
					yield (iface, name)

	def get_default_ip_address(self):
		# type: () -> Optional[_IPAddressBase]
		"""returns the default IP address."""
		for iface in sorted(self._all_interfaces.values(), key=self._cmp_primary):
			addr = iface.ipv4_address()
			if addr:
				return addr
			for name in sorted(iface.ipv6_names, key=self._cmp_name):
				addr = iface.ipv6_address(name)
				if addr:
					return addr

		return None

	def get_default_ipv4_address(self):
		# type: () -> Optional[IPv4Interface]
		"""returns the default IPv4 address."""
		for iface in sorted(self._all_interfaces.values(), key=self._cmp_primary):
			addr = iface.ipv4_address()
			if addr:
				return addr

		return None

	def get_default_ipv6_address(self):
		# type: () -> Optional[IPv6Interface]
		"""returns the default IPv6 address."""
		for iface in sorted(self._all_interfaces.values(), key=self._cmp_primary):
			for name in sorted(iface.ipv6_names, key=self._cmp_name):
				addr = iface.ipv6_address(name)
				if addr:
					return addr

		return None

# vim:set sw=4 ts=4 noet:
