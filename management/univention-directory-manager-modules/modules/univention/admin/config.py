#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
|UDM| configuration basics

.. deprecated:: UCS 4.4
"""


from types import ModuleType  # noqa: F401

import ldap

import univention.admin.modules
import univention.admin.uldap


class config:
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
        return univention.admin.modules._get(module).object.get_default_containers(lo)[0]
    except IndexError:
        return None


DEFAULT_ATTRIBUTE_MAP = {
    'group': 'univentionDefaultGroup',
    'computerGroup': 'univentionDefaultComputerGroup',
    'domainControllerGroup': 'univentionDefaultDomainControllerGroup',
}


def getDefaultValue(lo, name, position=None):
    # type: (univention.admin.uldap.access, str, univention.admin.uldap.position | None) -> str | None
    """
    Return the default value for a specific property of an UDM module.
    The default value is stored in a `settings/default` UDM object or in any of the parent container of the objects position.

    :param univention.admin.uldap.access lo: A LDAP connection object.
    :param str name: The name of a property.
    :param univention.admin.uldap.position position: A UDM position specifying the LDAP base container.
    :returns: The default value.
    """
    att = DEFAULT_ATTRIBUTE_MAP.get(name, name)

    if position:
        parent_dn = position.getDn()
        limit_dn = position.getDomain()

        current_search_dn = parent_dn
        while current_search_dn:
            try:
                res_list = lo.authz_connection.search(
                    filter='(|(objectClass=univentionDefault)(objectClass=univentionContainerDefault))',
                    base=current_search_dn,
                    attr=[att],
                    scope='base',
                    unique=True,
                    required=False,
                )
            except (ldap.NO_SUCH_OBJECT, ldap.INAPPROPRIATE_MATCHING):
                pass
            else:
                if res_list:
                    _dn, search_result = res_list[0]
                    if search_result and search_result.get(att):
                        value = search_result[att][0]
                        if value is not None:
                            return value.decode('UTF-8')

            if lo.compare_dn(current_search_dn.lower(), limit_dn.lower()):
                break

            next_parent_dn = lo.parentDn(current_search_dn)
            if not next_parent_dn or lo.compare_dn(current_search_dn.lower(), next_parent_dn.lower()):
                break
            current_search_dn = next_parent_dn

    try:
        fallback_base = 'cn=univention,%s' % (lo.base,)
        res_list_fallback = lo.authz_connection.search(
            filter='(|(objectClass=univentionDefault)(objectClass=univentionContainerDefault))',
            attr=[att],
            base=fallback_base,
            scope='sub',
            unique=True,
            required=True,
        )
    except (ldap.NO_SUCH_OBJECT, ldap.INAPPROPRIATE_MATCHING, IndexError):
        pass
    else:
        if res_list_fallback:
            _dn_fallback, attrs_fallback = res_list_fallback[0]
            value_fallback = attrs_fallback.get(att, [None])[0]
            if value_fallback is not None:
                return value_fallback.decode('UTF-8')

    return None
