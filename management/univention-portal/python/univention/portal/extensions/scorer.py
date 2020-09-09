#!/usr/bin/python2.7
#
# Univention Portal
#
# Copyright 2020 Univention GmbH
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

from univention.portal import Plugin

from six import with_metaclass


class Scorer(with_metaclass(Plugin)):
	"""
	Base class for portal scoring

	The idea is that when multiple portals are configured, their scorers
	decide which portal is to be used for a request.

	`score`: Gets a Tornado request and returns a number. The highest score wins.
	"""
	def __init__(self):
		pass

	def score(self, request):
		return 1


class DomainScorer(Scorer):
	"""
	Specialized Scorer that reponds if the request went against the configured domain.
	For this to work you have to make your portal system available under different domains.

	domain:
		Name of the domain, e.g. "myportal2.fqdn.com"
	"""
	def __init__(self, domain):
		self.domain = domain

	def score(self, request):
		if request.host == self.domain:
			return 10
		return 0


class PathScorer(Scorer):
	"""
	Specialized Scorer that reponds if the request went against the configured path.
	For this to work you have to make your portal available under different paths, e.g.
	"/univention/portal" and "/univention/portal2".

	path:
		The path. Does not have to match exactly, but the request's path needs to start
		with this value, e.g. "/portal2".
	"""
	def __init__(self, path):
		self.path = path

	def score(self, request):
		if request.path.startswith(self.path):
			return 10
		return 0
