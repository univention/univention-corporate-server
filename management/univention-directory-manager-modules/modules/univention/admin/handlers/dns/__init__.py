# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for dns records
#
# Copyright 2017-2019 Univention GmbH
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
# vim: set fileencoding=utf-8 et sw=4 ts=4 :

__path__ = __import__('pkgutil').extend_path(__path__, __name__)

ARPA_IP4 = '.in-addr.arpa'
ARPA_IP6 = '.ip6.arpa'


def makeContactPerson(obj, arg):
	"""Create contact Email-address for domain."""
	domain = obj.position.getDomain()
	return 'root@%s.' % (domain.replace('dc=', '').replace(',', '.'),)


def unescapeSOAemail(email):
	r"""
	Un-escape Email-address from DNS SOA record.
	>>> unescapeSOAemail(r'first\.last.domain.tld')
	'first.last@domain.tld'
	"""
	ret = ''
	i = 0
	while i < len(email):
		if email[i] == '\\':
			i += 1
			if i >= len(email):
				raise ValueError()
		elif email[i] == '.':
			i += 1
			if i >= len(email):
				raise ValueError()
			ret += '@'
			ret += email[i:]
			return ret
		ret += email[i]
		i += 1
	raise ValueError()


def escapeSOAemail(email):
	r"""
	Escape Email-address for DNS SOA record.
	>>> escapeSOAemail('first.last@domain.tld')
	'first\\.last.domain.tld'
	"""
	SPECIAL_CHARACTERS = set('"(),.:;<>@[\\]')
	if '@' not in email:
		raise ValueError()
	(local, domain) = email.rsplit('@', 1)
	tmp = ''
	for c in local:
		if c in SPECIAL_CHARACTERS:
			tmp += '\\'
		tmp += c
	local = tmp
	return local + '.' + domain


def stripDot(old):
	"""
	>>> stripDot(['example.com.', 'example.com'])
	['example.com', 'example.com']
	>>> stripDot('example.com.')
	'example.com'
	>>> stripDot([])
	[]
	>>> stripDot('')
	''
	>>> stripDot(None)
	"""
	if isinstance(old, list):
		return [stripDot(_) for _ in old]
	return old[:-1] if isinstance(old, basestring) and old.endswith('.') else old


if __name__ == '__main__':
	import doctest
	doctest.testmod()
