# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright 2010-2015 Univention GmbH
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

import univention.admin.uldap as udm_uldap
import univention.admin.uexceptions as udm_errors

from ldap import LDAPError

# decorator for LDAP connections
_ldap_connection = None
_ldap_position = None


class LDAP_ConnectionError(Exception):
	"""
	Error connecting LDAP server.
	"""
	pass


def LDAP_Connection(func):
	"""
	This decorator function provides an open LDAP connection that can
	be accessed via the variable ldap_connection and a vaild position
	within the LDAP directory in the variable ldap_position. It reuses
	an already open connection or creates a new one. If the function
	fails with an LDAP error the decorators tries to reopen the LDAP
	connection and invokes the function again. if it still fails an
	LDAP_ConnectionError is raised.

	When using the decorator the method gets two additional keyword arguments.

	example:
	  @LDAP_Connection
	  def do_ldap_stuff(arg1, arg2, ldap_connection=None, ldap_positio=None):
		  ...
		  ldap_connection.searchDn(..., position=ldap_position)
		  ...
	"""
	def wrapper_func(*args, **kwargs):
		global _ldap_connection, _ldap_position

		if _ldap_connection is not None:
			lo = _ldap_connection
			po = _ldap_position
		else:
			try:
				lo, po = udm_uldap.getMachineConnection(ldap_master=False)
			except LDAPError, ex:
				raise LDAP_ConnectionError('Opening LDAP connection failed: %s' % (ex,))

		kwargs['ldap_connection'] = lo
		kwargs['ldap_position'] = po
		try:
			ret = func(*args, **kwargs)
			_ldap_connection = lo
			_ldap_position = po
			return ret
		except udm_errors.base as ex:
			raise LDAP_ConnectionError(str(ex))

		return []

	return wrapper_func
