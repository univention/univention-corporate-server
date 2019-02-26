# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  python module
#
# Copyright 2010-2019 Univention GmbH
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
from __future__ import absolute_import
import sys
import gettext
import socket
import threading
import urlparse
from functools import reduce
try:
	from typing import List  # noqa
except ImportError:
	pass


__all__ = [
	'_',
	'N_',
	'TranslatableException',
	'ms',
	'FQDN',
	'uri_encode',
	'uri_decode',
	'TimeoutError',
	'timeout',
]


def N_(msg):
	return msg


_ = gettext.translation('univention-virtual-machine-manager', fallback=True).ugettext


class TranslatableException(Exception):

	"""Translatable exception (translatable_text, dict, key=value)."""

	def __init__(self, translatable_text, dict={}, **args):
		if isinstance(translatable_text, TranslatableException):
			translatable_text, dict2 = translatable_text.args
			dict2.update(dict)
			dict = dict2
		dict.update(args)
		Exception.__init__(self, translatable_text, dict)

	def __str__(self):
		translatable_text, dict = self.args
		return translatable_text % dict

	@property
	def translatable_text(self):
		return self.args[0]

	@property
	def dict(self):
		return self.args[1]


def ms(ms):
	"""
	Format milli seconds as readable string.
	>>> ms(((12*60+34)*60+56)*1000+789)
	'12:34:56.789'
	"""
	hm, s = divmod(ms, 60000)
	h, m = divmod(hm, 60)
	return "%d:%02d:%06.3f" % (h, m, s / 1000.0)


def tuple2version(version):
	"""
	Convert version-as-tuple to version-as-string (as used by libvirt)
	>>> tuple2version((1, 2, 3))
	1002003
	"""
	return reduce(lambda a, b: a * 1000 + b, version, 0)


FQDN = socket.getfqdn()


def uri_encode(uri):
	"""
	Encode URI for file-system compatibility.
	>>> uri_encode('qemu+ssh://user:univention@test.knut.univention.de/system?no_verify=1')
	'qemu%2bssh%3a%2f%2fuser%3aunivention%40test%2eknut%2eunivention%2ede%2fsystem%3fno%5fverify%3d1'
	"""
	return ''.join([c.isalnum() and c or '%%%02x' % ord(c) for c in uri])


def uri_decode(uri):
	"""
	Decode URI for file-system compatibility.
	>>> uri_decode('qemu%2bssh%3a%2f%2fuser%3aunivention%40test%2eknut%2eunivention%2ede%2fsystem%3fno%5fverify%3d1')
	'qemu+ssh://user:univention@test.knut.univention.de/system?no_verify=1'
	"""
	i = uri.find('%')
	if i >= 0:
		return uri[:i] + chr(int(uri[i + 1:i + 3], 16)) + uri_decode(uri[i + 3:])
	else:
		return uri


class TimeoutError(Exception):
	pass


class timeout(object):

	"""
	Call a function in another thread and wait for its completion.  If the
	functions doesn't return in the maximum allowed time, raise an
	TimeoutError.

	>>> timeout(time.sleep, timeout=2.0)(1.0)
	>>> timeout(time.sleep, timeout=1.0)(-1.0)
	Traceback (most recent call last):
	IOError: [Errno 22] Invalid argument
	>>> timeout(time.sleep, timeout=1.0)(2.0)
	Traceback (most recent call last):
	TimeoutError: <built-in function sleep>
	"""

	def __init__(self, target, timeout=10.0):
		self.target = target
		self.timeout = timeout
		self.result = None
		self.exception = None

	def __call__(self, *args, **kwargs):
		thread = threading.Thread(target=self.run, args=args, kwargs=kwargs)
		thread.daemon = True
		thread.start()
		thread.join(self.timeout)
		if thread.isAlive():
			raise TimeoutError(self.target)
		elif self.exception:
			raise self.exception[0], self.exception[1], self.exception[2]
		else:
			return self.result

	def run(self, *args, **kwargs):
		try:
			self.result = self.target(*args, **kwargs)
		except Exception:
			self.exception = sys.exc_info()


"""
Extension of urlparse for node URIs

example:
import urlparse

> urlparse.urlsplit('qemu://host.domain.tld/system')
SplitResult(scheme='qemu', netloc='host.domain.tld', path='/system', query='', fragment='')
"""

__all = []  # type: List[str]
__all += ['lxc']
__all += ['vpx', 'esx', 'gsx']
__all += ['vmwareplayer']
__all += ['vmwarews%s' % v for v in ['', '+tcp', '+ssh']]
__all += ['openvz%s' % v for v in ['', '+unix', '+tcp', '+ssh']]
__all += ['qemu%s' % v for v in ['', '+unix', '+tcp', '+ssh']]
__all += ['test%s' % v for v in ['', '+unix', '+tcp', '+ssh']]
__all += ['uml%s' % v for v in ['', '+unix', '+tcp', '+ssh']]
__all += ['vbox%s' % v for v in ['', '+unix', '+tcp', '+ssh']]
__all += ['xen%s' % v for v in ['', '+unix', '+tcp', '+ssh']]

urlparse.uses_netloc += __all
urlparse.uses_query += __all
urlparse.uses_fragment += __all


if __name__ == '__main__':
	import doctest
	doctest.testmod()
