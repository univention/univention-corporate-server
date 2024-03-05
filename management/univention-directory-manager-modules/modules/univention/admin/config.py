# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2024 Univention GmbH
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

"""
|UDM| configuration basics

.. deprecated:: UCS 4.4
"""

from __future__ import absolute_import

from types import ModuleType  # noqa: F401

import six

import univention.admin.modules
import univention.admin.uldap


class config(object):
    """
    |UDM| configuration object.

    .. deprecated:: UCS 4.4
            use `None` instead
    """

    def __init__(self, host=''):
        # type: (str) -> None
        base = univention.admin.uldap.getBaseDN(host)
        self.data = {
            'ldap/base': base,
            'ldap/base/dns': 'cn=dns,' + base,
            'ldap/base/dhcp': 'cn=dhcp,' + base,
        }

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    if six.PY2:
        def has_key(self, key):  # noqa: FURB118
            return key in self

    def __contains__(self, key):
        return key in self.data

    def items(self):
        return self.data.items()


def getDefaultContainer(lo, module):
    # type: (univention.admin.uldap.access, ModuleType | str) -> str | None
    """
    Return any random default container for a UDM module.

    .. deprecated:: UCS 4.4

    :param lo: A LDAP connection object.
    :param module: The name of a UDM module.
    :returns: A distinguished name.
    """
    if module == 'dns/':
        module = 'dns/dns'
    try:
        return univention.admin.modules.get(module).object.get_default_containers(lo)[0]
    except IndexError:
        return None


def getDefaultValue(lo, name, position=None):
    # type: (univention.admin.uldap.access, str, univention.admin.uldap.position) -> str | None
    """
    Return the default value for a UDM module.

    :param univention.admin.uldap.access lo: A LDAP connection object.
    :param str name: The name of a property.
    :param univention.admin.uldap.position position: A UDM position specifying the LDAP base container.
    :returns: The default value.
    """
    if name == 'group':
        att = 'univentionDefaultGroup'
    elif name == 'computerGroup':
        att = 'univentionDefaultComputerGroup'
    else:
        att = name

    if position:
        _dn, attrs = lo.search(filter='objectClass=univentionDefault', attr=[att], base=position.getDomain(), scope='domain', unique=True, required=True)[0]
    else:
        _dn, attrs = lo.search(filter='objectClass=univentionDefault', attr=[att], scope='domain', unique=True, required=True)[0]
    result = attrs.get(att, [None])[0]
    if result is not None:
        return result.decode('UTF-8')
