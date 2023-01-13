# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2023 Univention GmbH
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

from univention.admin.hook import AttributeHook


def map_value(value):
    return [';'.join('"{}"'.format(w.decode('UTF-8')) for w in v).encode('UTF-8') for v in value]


def unmap_value(value):
    return [[w.strip('\"') for w in v.split(';')] for v in value]


class FetchMailSingleHook(AttributeHook):
    udm_attribute_name = 'FetchMailSingle'
    ldap_attribute_name = 'univentionFetchmailSingle'

    def map_attribute_value_to_ldap(self, value):
        return map_value(value)

    def map_attribute_value_to_udm(self, value):
        return unmap_value(value)


class FetchMailMultiHook(AttributeHook):
    udm_attribute_name = 'FetchMailMulti'
    ldap_attribute_name = 'univentionFetchmailMulti'

    def map_attribute_value_to_ldap(self, value):
        return map_value(value)

    def map_attribute_value_to_udm(self, value):
        return unmap_value(value)
