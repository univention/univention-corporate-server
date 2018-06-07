# -*- coding: utf-8 -*-
#
# Copyright 2018 Univention GmbH
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
# <http://www.gnu.org/licenses/>.

"""
Univention Directory Manager Modules (UDM) API

This is a simplified API for accessing UDM objects.
It consists of UDM modules and UDM object.
UDM modules are factories for UDM objects.
UDM objects manipulate LDAP objects.

Usage:

from univention.udm import Udm
udm = Udm.get_admin()
user_mod = udm('users/user')

obj = user_mod.get(dn)
obj.props.firstname = 'foo'
obj.position = 'cn=users,cn=example,dc=com'
obj.save()

obj = user_mod.get(dn)
obj.delete()

obj = user_mod.new()
obj.props.username = 'bar'
obj.save().refresh()

for obj in user_mod.search('uid=a*'):
	print(obj.dn)
"""

from __future__ import absolute_import
from .udm import Udm
from .exceptions import DeletedError, FirstUseError, ModifyError, MoveError, NoObject, UdmError, UnknownProperty, WrongObjectType

__all__ = [
	'Udm',
	'DeletedError', 'FirstUseError', 'ModifyError', 'MoveError', 'NoObject', 'UdmError', 'UnknownProperty', 'WrongObjectType',
]
