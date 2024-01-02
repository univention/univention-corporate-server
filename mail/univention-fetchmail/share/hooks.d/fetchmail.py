# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2023-2024 Univention GmbH
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

import json

import univention.debug as ud
from univention.admin.hook import AttributeHook, simpleHook


def map_value(value):
    ret = []
    for elem in value:
        entry = []
        for param in elem:
            entry.append(param if isinstance(param, str) else param.decode())
        ret.append(json.dumps(entry).encode('UTF-8'))
    return ret


def unmap_value(value):
    try:
        entries = [json.loads(v) for v in value]
    except ValueError:
        # try the previous format. This should only happen once as
        # the next time the values will be already json formatted (#56008).
        entries = [[w.strip('"') for w in v.decode('UTF-8').split('";"')] for v in value]
    return entries


if not hasattr(AttributeHook, 'version'):
    # TODO: remove in UCS 5.1 - Bug #56036
    class AttributeHook(simpleHook):
        """
        Convenience Hook that essentially implements a mapping
        between |UDM| and |LDAP| for your extended attributes.
        Derive from this class, set :py:attr:`attribute_name` to the name of
        the |UDM| attribute and implement :py:meth:`map_attribute_value_to_udm`
        and :py:meth:`map_attribute_value_to_ldap`.
        """

        udm_attribute_name = None
        ldap_attribute_name = None

        version = 2

        def hook_open(self, obj):
            """
            Open |UDM| object by loading value from |LDAP|.

            :param obj: The |UDM| object instance.
            """
            ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.AttributeHook: Mapping %s (LDAP) -> %s (UDM)' % (self.ldap_attribute_name, self.udm_attribute_name))
            old_value = obj.oldattr.get(self.ldap_attribute_name, [])
            new_value = self.map_attribute_value_to_udm(old_value)
            ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.AttributeHook: Setting UDM value from %r to %r' % (old_value, new_value))
            obj[self.udm_attribute_name] = new_value

        def hook_ldap_addlist(self, obj, al):
            """
            Extend |LDAP| add list.

            :param obj: The |UDM| object instance.
            :param al: The add list to extend.
            :returns: The extended add list.
            """
            return self.hook_ldap_modlist(obj, al)

        def hook_ldap_modlist(self, obj, ml):
            """
            Extend |LDAP| modification list.

            :param obj: The |UDM| object instance.
            :param ml: The modification list to extend.
            :returns: The extended modification list.
            """
            new_ml = [x for x in ml if x[0] != self.ldap_attribute_name]

            if obj.hasChanged(self.udm_attribute_name):
                old_value = obj.oldattr.get(self.ldap_attribute_name, [])
                new_value = obj.info.get(self.udm_attribute_name)
                if new_value is not None:
                    new_value = self.map_attribute_value_to_ldap(new_value)
                new_ml.append((self.ldap_attribute_name, old_value, new_value))
            return new_ml

        def map_attribute_value_to_ldap(self, value):
            """
            Return value as it shall be saved in |LDAP|.

            :param value: The |UDM| value.
            :returns: The |LDAP| value.
            """
            return value

        def map_attribute_value_to_udm(self, value):
            """
            Return value as it shall be used in |UDM| objects.

            The mapped value needs to be syntax compliant.

            :param value: The |LDAP| value.
            :returns: The |UDM| value.
            """
            return value


class FetchMailSingleHook(AttributeHook):
    version = 2
    udm_attribute_name = 'FetchMailSingle'
    ldap_attribute_name = 'univentionFetchmailSingle'

    def map_attribute_value_to_ldap(self, value):
        return map_value(value)

    def map_attribute_value_to_udm(self, value):
        return unmap_value(value)


class FetchMailMultiHook(AttributeHook):
    version = 2
    udm_attribute_name = 'FetchMailMulti'
    ldap_attribute_name = 'univentionFetchmailMulti'

    def map_attribute_value_to_ldap(self, value):
        return map_value(value)

    def map_attribute_value_to_udm(self, value):
        return unmap_value(value)
