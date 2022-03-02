# -*- coding: utf-8 -*-
#
# Copyright 2018-2022 Univention GmbH
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
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

"""
Univention Directory Manager Modules (UDM) API

This is a simplified API for accessing UDM objects.
It consists of UDM modules and UDM object.
UDM modules are factories for UDM objects.
UDM objects manipulate LDAP objects.

The :py:class:`UDM` class is a LDAP connection and UDM module factory.

Usage::

	from univention.udm import UDM

	user_mod = UDM.admin().version(2).get('users/user')

or::

	user_mod = UDM.machine().version(2).get('users/user')

or::

	user_mod = UDM.credentials('myuser', 's3cr3t').version(2).get('users/user')

	obj = user_mod.get(dn)
	obj.props.firstname = 'foo'  # modify property
	obj.position = 'cn=users,cn=example,dc=com'  # move LDAP object
	obj.save()  # apply changes

	obj = user_mod.get(dn)
	obj.delete()

	obj = user_mod.new()
	obj.props.username = 'bar'
	obj.props.lastname = 'baz'
	obj.props.password = 'v3r7s3cr3t'
	obj.props.unixhome = '/home/bar'
	obj.save()

	for obj in user_mod.search('uid=a*'):  # search() returns a generator
		print(obj.props.firstname, obj.props.lastname)

A shortcut exists to get UDM objects directly, without knowing their
univention object type::

	UDM.admin().version(2).obj_by_dn(dn)

A shortcut exists to get UDM objects directly, knowing their univention object
type, but without knowing their DN::

	UDM.admin().version(2).get('groups/group').get_by_id('Domain Users')

The API is versioned. A fixed version must be hard coded in your code. Supply
it as argument to the UDM module factory or via :py:meth:`version()`::

    UDM(lo, 0)              # use API version 0 and an existing LDAP connection object
	UDM.admin().version(1)  # use API version 1
	UDM.credentials('myuser', 's3cr3t').version(2).obj_by_dn(dn)  # get object using API version 2

* Version 0: values of UDM properties are the same as with the low level UDM API: mostly strings.
* Version 1: values of (most) UDM properties are de/encoded to useful Python types (e.g. "0" -> 0 or False)
* Version 2: an encoder for settings/portal_category properties was added.

The LDAP connection to use must be supplies as an argument to the UDM module factory or set via
:py:meth:`admin()`, :py:meth:`machine()`, or :py:meth:`credentials()`::

    UDM(lo)        # use an already existing uldap connection object
    UDM.admin()    # cn=admin connection
    UDM.machine()  # machine connection
    UDM.credentials(identity, password, base=None, server=None, port=None)  # custom connection,
        # `identity` is either a username or a DN. LDAP base, server FQDN/IP and port are optional.
        # If it is a username, a machine connection is used to retrieve the DN it belongs to.
"""

from __future__ import absolute_import
from .udm import UDM
from .exceptions import (
	CreateError, DeleteError, DeletedError, NotYetSavedError, ModifyError, MoveError, MultipleObjects, NoObject,
	UdmError, UnknownProperty, UnknownModuleType, WrongObjectType, ConnectionError, NoSuperordinate,
	NoApiVersionSet, ApiVersionNotSupported, ApiVersionMustNotChange,
)

__all__ = [
	'UDM',
	'CreateError', 'DeleteError', 'DeletedError', 'NotYetSavedError', 'ModifyError', 'MoveError', 'MultipleObjects',
	'NoObject', 'UdmError', 'UnknownProperty', 'UnknownModuleType', 'WrongObjectType', 'ConnectionError', 'NoSuperordinate',
	'NoApiVersionSet', 'ApiVersionNotSupported', 'ApiVersionMustNotChange',
]
