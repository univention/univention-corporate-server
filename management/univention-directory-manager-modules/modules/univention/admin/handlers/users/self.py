# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2023 Univention GmbH
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

"""|UDM| module for the user himself"""


from ldap.filter import filter_format

import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.users.user as udm_user
import univention.admin.localization
from univention.admin.layout import Tab


translation = univention.admin.localization.translation('univention.admin.handlers.users')
_ = translation.translate

module = 'users/self'
operations = ['edit', 'search']

virtual = True
options = udm_user.options
property_descriptions = udm_user.property_descriptions  # TODO: strip down the properties to some configured "profile" subset e.g. from UCRv self-service/udm_attributes
mapping = udm_user.mapping
layout = [Tab(_('General'), layout=[])]  # TODO: load a layout structure from a JSON file.

childs = False
short_description = _('User: Self')
object_name = _('Self')
object_name_plural = _('Self')
long_description = ''


class object(univention.admin.handlers.users.user.object):
    module = module

    def __init__(self, co, lo, position, dn=u'', superordinate=None, attributes=None):
        super(object, self).__init__(co, lo, position, dn=dn, superordinate=superordinate, attributes=attributes)
        if self._exists and (not self.lo.compare_dn(self.dn, self.lo.whoami()) or not univention.admin.modules.recognize('users/user', self.dn, self.oldattr)):
            raise univention.admin.uexceptions.wrongObjectType('%s is not recognized as %s.' % (self.dn, self.module))

    @classmethod
    def lookup_filter(cls, filter_s=None, lo=None):
        if lo:
            dn = lo.whoami()
            filter_p = univention.admin.filter.parse(filter_format('(&(entryDN=%s))', [dn]))
            module = univention.admin.modules.get_module(cls.module)
            filter_p.append_unmapped_filter_string(filter_s, cls.rewrite_filter, module.mapping)
            return filter_p
        return super(object, cls).lookup_filter(filter_s, lo)

    @classmethod
    def lookup(cls, co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):
        dn = lo.whoami()
        return [user for user in udm_user.lookup(co, lo, filter_s, base, superordinate, scope=scope, unique=unique, required=required, timeout=timeout, sizelimit=sizelimit, serverctrls=serverctrls, response=response) if lo.compare_dn(dn, user.dn)]

    @classmethod
    def identify(cls, dn, attr, canonical=False):
        return False


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
