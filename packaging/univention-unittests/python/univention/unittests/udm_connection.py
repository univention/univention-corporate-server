#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2021 Univention GmbH
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

from copy import deepcopy

from univentionunittests.udm_filter import make_filter

try:
	from mock import MagicMock
except ImportError:
	from unittest.mock import MagicMock


def get_domain():
	return 'dc=intranet,dc=example,dc=de'


class MockedAccess(MagicMock):
	def search(self, filter=u'(objectClass=*)', base=u'', scope=u'sub', attr=[], unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):
		if base is None:
			base = get_domain()
		res = []
		ldap_filter = make_filter(filter)
		for obj in self.database:
			if not obj.dn.endswith(base):
				continue
			if not ldap_filter.matches(obj):
				continue
			if attr:
				attrs = {}
				for att in attr:
					if att in obj.attrs:
						attrs[att] = deepcopy(obj.attrs[att])
			else:
				attrs = deepcopy(obj.attrs)
			result = obj.dn, attrs
			res.append(result)
		return res

	def searchDn(self, filter=u'(objectClass=*)', base=u'', scope=u'sub', unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):
		res = []
		for dn, attrs in self.search(filter, base):
			res.append(dn)
		return res

	def modify(self, dn, changes, exceptions=False, ignore_license=0, serverctrls=None, response=None):
		self.database.modify(dn, changes)

	def get(self, dn, attr=[], required=False, exceptions=False):
		return self.database.get(dn)

	def parentDn(self, dn):
		idx = dn.find(',')
		return dn[idx + 1:]

	@classmethod
	def compare_dn(cls, a, b):
		return a.lower() == b.lower()

	def getAttr(self, dn, attr, required=False, exceptions=False):
		obj = self.database.objs.get(dn)
		if obj:
			return obj.attrs.get(attr)


class MockedPosition(object):
	def __init__(self):
		self.dn = get_domain()

	def getDn(self):
		return self.dn

	def getDomain(self):
		return get_domain()

	def getDomainConfigBase(self):
		return 'cn=univention,%s' % self.getDomain()
