#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the user himself"""

from __future__ import annotations

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

    def __init__(
        self,
        co: None,
        lo: univention.admin.uldap.access,
        position: univention.admin.uldap.position | None,
        dn: str = '',
        superordinate: univention.admin.handlers.simpleLdap | None = None,
        attributes: univention.admin.handlers._Attributes | None = None,
    ) -> None:
        super().__init__(co, lo, position, dn=dn, superordinate=superordinate, attributes=attributes)
        if self._exists and (not self.lo.compare_dn(self.dn, self.lo.whoami()) or not univention.admin.modules.recognize('users/user', self.dn, self.oldattr)):
            raise univention.admin.uexceptions.wrongObjectType('%s is not recognized as %s.' % (self.dn, self.module))

    @classmethod
    def lookup_filter(cls, filter_s: str | None = None, lo: univention.admin.uldap.access | None = None) -> univention.admin.filter.conjunction:
        if lo:
            dn = lo.whoami()
            filter_p = univention.admin.filter.parse(filter_format('(&(entryDN=%s))', [dn]))
            module = univention.admin.modules._get(cls.module)
            filter_p.append_unmapped_filter_string(filter_s, cls.rewrite_filter, module.mapping)
            return filter_p
        return super().lookup_filter(filter_s, lo)

    @classmethod
    def lookup(
        cls,
        co: None,
        lo: univention.admin.uldap.access,
        filter_s: str,
        base: str = '',
        superordinate: univention.admin.handlers.simpleLdap | None = None,
        scope: str = 'sub',
        unique: bool = False,
        required: bool = False,
        timeout: int = -1,
        sizelimit: int = 0,
        serverctrls: list | None = None,
        response: dict | None = None,
    ) -> list[univention.admin.handlers.simpleLdap]:
        dn = lo.whoami()
        return [user for user in udm_user.lookup(co, lo, filter_s, base, superordinate, scope=scope, unique=unique, required=required, timeout=timeout, sizelimit=sizelimit, serverctrls=serverctrls, response=response) if lo.compare_dn(dn, user.dn)]

    @classmethod
    def identify(cls, dn: str, attr: univention.admin.handlers._Attributes, canonical: bool = False) -> bool:
        return False


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
