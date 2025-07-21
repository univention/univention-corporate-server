# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| functions to handle deleted objects in recyclebin"""

import string
from collections import namedtuple
from typing import Self
from urllib.parse import quote, unquote

import ldap.filter

import univention.admin.filter
import univention.admin.localization
from univention.admin._ucr import configRegistry
from univention.admin.log import log as admin_log


RECYCLEBIN_BASE = 'cn=recyclebin,cn=internal'
IGNORE_ATTRS = {
    'objectclass',
    'univentionobjecttype',
    'univentionobjectidentifier',
    'memberof',
}

translation = univention.admin.localization.translation('univention.admin.handlers')
_ = translation.translate


class Reference(namedtuple('Reference', ['source_attr', 'target_module', 'target_property', 'lookup_attribute', 'lookup_value'])):

    __slots__ = ()
    SAFE_CHARS = string.printable.replace(':', '').replace('%', '')

    @classmethod
    def parse(cls, reference: str) -> Self | None:
        """
        Parse a univentionRecycleBinReference value.

        Format: source_attr:target_module:target_property:lookup_attribute:lookup_value
        Example: dn:groups/group:users:uuid:550e8400-e29b-41d4-a716-446655440000
        which reads as:
        The LDAP attribute `DN` of the to-be-restored object should go into the `users` UDM property of the `groups/group` object identified by the LDAP attribute `uuid` $UUID.
        Some LDAP attributes have aliases: uuid = univentionObjectIdentifier, dn = 1.1.

        Fields are URL-encoded to handle special characters like colons.

        Returns dict with keys: source_attr, target_module, target_property, lookup_attribute, lookup_value
        Returns None if invalid format
        """
        parts = reference.split(':')
        if len(parts) < 5:
            return None
        return cls(*(unquote(p) for p in parts[:5]))

    def __str__(self) -> str:
        """
        Format a univentionRecycleBinReference value.

        Format: source_attr:target_module:target_property:lookup_attribute:lookup_value

        Fields are URL-encoded to handle special characters like colons.
        """
        return ':'.join(quote(field, safe=self.SAFE_CHARS) for field in self)

    def __bytes__(self) -> bytes:
        return str(self).encode('UTF-8')

    def resolve(self, lo: univention.admin.uldap.access, verify_exists: bool = True, include_recyclebin: bool = False) -> dict | None:
        """
        Resolve a single reference string to its target DN.

        :param lo: LDAP connection
        :param verify_exists: Whether to verify the target object exists
        :param include_recyclebin: Whether to also search in the recyclebin for deleted objects
        :return: str target_dn, or None if not found
        """
        lookup_attribute_aliases = {'uuid': 'univentionObjectIdentifier'}
        ldap_attr = lookup_attribute_aliases.get(self.lookup_attribute, self.lookup_attribute)

        target_dn = None

        if self.lookup_attribute == 'dn':
            target_dn = self.lookup_value
            if verify_exists:
                results = lo.authz_connection.getAttr(target_dn, 'objectClass')
                if not results:
                    target_dn = None
        else:
            # TODO: doesn't respect self.target_module
            filter_str = ldap.filter.filter_format('(%s=%s)', [ldap_attr, self.lookup_value])
            results = lo.authz_connection.searchDn(base=configRegistry['ldap/base'], filter=filter_str)
            if results:
                target_dn = results[0]

        # if not found in normal LDAP, search in recyclebin if requested
        if not target_dn and include_recyclebin:
            ldap_attr = {'dn': 'univentionRecycleBinOriginalDN'}.get(ldap_attr, ldap_attr)
            filter_str = ldap.filter.filter_format('(&(objectClass=univentionRecycleBinObject)(%s=%s))', [ldap_attr, self.lookup_value])

            from univention.admin.handlers.recyclebin.deletedobject import RECYCLEBIN_BASE

            results = lo.authz_connection.searchDn(base=RECYCLEBIN_BASE, filter=filter_str)
            if results:
                target_dn = results[0]

        return target_dn


def create_references(lo, object_type: str, oldattr: dict[str, list[bytes]]):
    """Create univentionRecycleBinReference for a given object."""
    refs = []
    # TODO: move into some definition of groups/group
    # handle group references (memberOf)
    if member_of := oldattr.get('memberOf'):
        groups = [x.decode('UTF-8') for x in member_of]
        refs.extend(
            Reference('dn', 'groups/group', {'groups/group': 'nestedGroup', 'users/user': 'users'}.get(object_type), *to_uuid(dn, lo))
            for dn in groups
        )
    return refs


def to_uuid(dn: str, lo: univention.admin.uldap.access) -> tuple[str, str]:
    """
    Convert list of groups to list of univentionRecycleBinReference.

    Tries to store references by UUID for stability. Search order:
    1. Active LDAP - get UUID from current object
    2. Recyclebin - get UUID from deleted object
    3. Fallback - store DN
    """
    ref = lo.authz_connection.get(dn, attr=['univentionObjectIdentifier'])
    if ref and 'univentionObjectIdentifier' in ref:
        return 'uuid', ref['univentionObjectIdentifier'][0].decode('utf-8')

    recyclebin_filter = ldap.filter.filter_format(
        '(&(objectClass=univentionRecycleBinObject)(univentionRecycleBinOriginalDN=%s))', [dn],
    )
    results = lo.authz_connection.search(
        base=RECYCLEBIN_BASE,
        scope='one',
        filter=recyclebin_filter,
        attr=['univentionRecycleBinOriginalUniventionObjectIdentifier'],
    )
    if results and results[0][1].get('univentionRecycleBinOriginalUniventionObjectIdentifier'):
        uuid = results[0][1]['univentionRecycleBinOriginalUniventionObjectIdentifier'][0].decode('utf-8')
        admin_log.debug('Found UUID in recyclebin', dn=dn, uuid=uuid)
        return 'uuid', uuid

    admin_log.debug('Storing reference by DN (UUID not found)', dn=dn)
    return 'dn', dn
