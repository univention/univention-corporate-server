# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| functions to handle deleted objects in Recycle Bin"""

import string
from collections import namedtuple
from typing import Self
from urllib.parse import quote, unquote

from ldap.filter import filter_format

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
    'authTimestamp',  # might be enabled on the fly
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
            filter_str = filter_format('(%s=%s)', [ldap_attr, self.lookup_value])
            results = lo.authz_connection.searchDn(base=configRegistry['ldap/base'], filter=filter_str)
            if results:
                target_dn = results[0]

        # if not found in normal LDAP, search in Recycle Bin if requested
        if not target_dn and include_recyclebin:
            ldap_attr = {'dn': 'univentionRecycleBinOriginalDN'}.get(ldap_attr, ldap_attr)
            filter_str = filter_format('(&(objectClass=univentionRecycleBinObject)(%s=%s))', [ldap_attr, self.lookup_value])

            from univention.admin.handlers.recyclebin.deletedobject import RECYCLEBIN_BASE

            results = lo.authz_connection.searchDn(base=RECYCLEBIN_BASE, filter=filter_str)
            if results:
                target_dn = results[0]

        return target_dn


def create_references(lo, object_type: str, original_dn: str | None, oldattr: dict[str, list[bytes]]):
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

    # handle groups references, where the group was deleted first and is already in the Recycle Bin
    if object_type in ('users/user', 'groups/group') and original_dn:
        results = lo.authz_connection.search(
            base=RECYCLEBIN_BASE,
            scope='one',
            filter=filter_format(
                '(&(objectClass=univentionRecycleBinObject)(univentionRecycleBinOriginalType=groups/group)(uniqueMember=%s))',
                [original_dn],
            ),
            attr=['univentionRecycleBinOriginalDN', 'univentionRecycleBinOriginalUniventionObjectIdentifier'],
        )
        for _dn, attrs in results:
            group_original_dn = attrs.get('univentionRecycleBinOriginalDN', [b''])[0].decode('UTF-8')
            group_uuid = attrs.get('univentionRecycleBinOriginalUniventionObjectIdentifier', [b''])[0].decode('UTF-8')
            if group_uuid:
                admin_log.debug('Found deleted group with member', group_dn=group_original_dn, member=original_dn, uuid=group_uuid)
                refs.append(
                    Reference('dn', 'groups/group', {'groups/group': 'nestedGroup', 'users/user': 'users'}.get(object_type), 'uuid', group_uuid),
                )

    return refs


def to_uuid(dn: str, lo: univention.admin.uldap.access) -> tuple[str, str]:
    """
    Convert list of groups to list of univentionRecycleBinReference.

    Tries to store references by UUID for stability. Search order:
    1. Active LDAP - get UUID from current object
    2. Recycle Bin - get UUID from deleted object
    3. Fallback - store DN
    """
    ref = lo.authz_connection.get(dn, attr=['univentionObjectIdentifier'])
    if ref and 'univentionObjectIdentifier' in ref:
        return 'uuid', ref['univentionObjectIdentifier'][0].decode('utf-8')

    results = lo.authz_connection.search(
        base=RECYCLEBIN_BASE,
        scope='one',
        filter=filter_format(
            '(&(objectClass=univentionRecycleBinObject)(univentionRecycleBinOriginalDN=%s))', [dn],
        ),
        attr=['univentionRecycleBinOriginalUniventionObjectIdentifier'],
    )
    if results and results[0][1].get('univentionRecycleBinOriginalUniventionObjectIdentifier'):
        uuid = results[0][1]['univentionRecycleBinOriginalUniventionObjectIdentifier'][0].decode('utf-8')
        admin_log.debug('Found UUID in Recycle Bin', dn=dn, uuid=uuid)
        return 'uuid', uuid

    admin_log.debug('Storing reference by DN (UUID not found)', dn=dn)
    return 'dn', dn
