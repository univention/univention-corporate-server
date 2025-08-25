#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""listener script for recyclebin objects."""

import datetime
import json
import time

import ldap
import ldap.filter

import univention.admin.modules
import univention.admin.uldap
import univention.config_registry
import univention.debug
import univention.uldap

import listener


name = 'recyclebin'
description = 'Secure recyclebin operations via listener'
filter = '(objectClass=*)'
modrdn = True


def initialize():
    """Initialize the listener module."""
    ucr = univention.config_registry.ConfigRegistry()
    ucr.load()

    server_role = ucr.get('server/role')
    if server_role != 'domaincontroller_master':
        return

    univention.debug.debug(
        univention.debug.LISTENER,
        univention.debug.INFO,
        f"recyclebin listener: Initializing on {server_role}",
    )


def handler(dn, new, old, command=''):
    if new and not old:
        command = 'a'
    elif new and old:
        command = 'm'
    elif old and not new:
        command = 'd'
    else:
        command = 'unknown'

    ucr = univention.config_registry.ConfigRegistry()
    ucr.load()

    server_role = ucr.get('server/role')
    if server_role != 'domaincontroller_master':
        return

    if command != 'd' or old is None:
        return

    if 'cn=recyclebin,cn=internal' in dn:
        return

    system_containers = [
        f'cn=computers,{ucr.get("ldap/base", "")}',
        f'cn=dns,{ucr.get("ldap/base", "")}',
        f'cn=dhcp,{ucr.get("ldap/base", "")}',
        f'cn=policies,{ucr.get("ldap/base", "")}',
        f'cn=shares,{ucr.get("ldap/base", "")}',
        f'cn=printers,{ucr.get("ldap/base", "")}',
        f'cn=mail,{ucr.get("ldap/base", "")}',
        f'cn=groups,{ucr.get("ldap/base", "")}',
        f'cn=users,{ucr.get("ldap/base", "")}',
        f'cn=licenses,cn=univention,{ucr.get("ldap/base", "")}',
    ]

    # Skip admin user specifically and system containers (but not their contents)
    if dn in system_containers or dn == f'cn=admin,cn=users,{ucr.get("ldap/base", "")}':
        return

    _move_deleted_object_to_recyclebin(dn, old)


def _move_deleted_object_to_recyclebin(original_dn, original_attrs):
    listener.setuid(0)
    try:
        ucr = univention.config_registry.ConfigRegistry()
        ucr.load()

        internal_lo = univention.uldap.access(
            host=ucr.get('ldap/server/name', 'localhost'),
            port=int(ucr.get('ldap/server/port', '7389')),
            base='cn=internal',
            binddn=f"cn=admin,{ucr.get('ldap/base')}",
            bindpw=open('/etc/ldap.secret').read().strip(),
        )

        univention.admin.modules.update()

        original_type = _determine_object_type(original_attrs)

        main_lo, _ = univention.admin.uldap.getAdminConnection()
        referenced_by = _find_references_with_admin_privileges(original_dn, main_lo)

        _create_recyclebin_entry(
            lo=internal_lo,
            original_dn=original_dn,
            original_attrs=original_attrs,
            original_type=original_type,
            referenced_by=referenced_by,
        )
    finally:
        listener.unsetuid()


def _determine_object_type(attrs):
    object_type = attrs.get('univentionObjectType')
    if object_type:
        return object_type[0].decode('utf-8') if isinstance(object_type[0], bytes) else object_type[0]
    return 'generic/object'


def _find_references_with_admin_privileges(target_dn, lo):
    referenced_by = []

    escaped_dn = ldap.filter.escape_filter_chars(target_dn)

    dn_attributes = [
        'member', 'uniqueMember', 'memberOf',
        'manager', 'secretary', 'owner',
        'seeAlso', 'roleOccupant',
        'univentionMemberOf', 'univentionGroupMembership',
    ]

    for attr in dn_attributes:
        try:
            search_filter = f"({attr}={escaped_dn})"
            results = lo.search(
                base=lo.base,
                scope='subtree',
                filter=search_filter,
                attr=[],
                unique=False,
                required=False,
            )

            for dn, attrs in results:
                if dn != target_dn:
                    reference_info = {
                        'dn': dn,
                        'module': _determine_object_type(attrs),
                        'property': attr,
                        'ldap_attribute': attr,
                        'timestamp': int(time.time()),
                    }
                    referenced_by.append(reference_info)

        except ldap.LDAPError as e:
            univention.debug.debug(
                univention.debug.LISTENER,
                univention.debug.WARNING,
                f"recyclebin listener: Error finding references for {target_dn}: {e}",
            )
            continue

    return referenced_by


def _get_recyclebin_policy_settings(original_dn, original_type):
    try:
        main_lo, _ = univention.admin.uldap.getAdminConnection()

        dn_parts = ldap.dn.str2dn(original_dn)

        for i in range(len(dn_parts)):
            search_dn = ldap.dn.dn2str(dn_parts[i:])

            try:
                attrs = main_lo.get(search_dn)
                if attrs and 'univentionPolicyReference' in attrs:
                    policy_refs = attrs['univentionPolicyReference']

                    for policy_ref in policy_refs:
                        policy_dn = policy_ref.decode('utf-8') if isinstance(policy_ref, bytes) else policy_ref

                        try:
                            policy_attrs = main_lo.get(policy_dn)
                            if policy_attrs and b'univentionRecycleBinPolicy' in policy_attrs.get('objectClass', []):
                                covered_modules = policy_attrs.get('univentionRecycleBinUDMModules', [])
                                covered_modules = [m.decode('utf-8') if isinstance(m, bytes) else m for m in covered_modules]

                                if original_type in covered_modules:
                                    retention_time = policy_attrs.get('univentionRecycleBinRetentionTime', [b'30'])
                                    retention_days = int(retention_time[0].decode('utf-8') if isinstance(retention_time[0], bytes) else retention_time[0])

                                    univention.debug.debug(
                                        univention.debug.LISTENER,
                                        univention.debug.INFO,
                                        f"recyclebin listener: Found policy {policy_dn} with retention {retention_days} days for {original_type}",
                                    )
                                    return retention_days
                        except ldap.LDAPError:
                            continue
            except ldap.LDAPError:
                continue

        ucr = univention.config_registry.ConfigRegistry()
        ucr.load()
        default_policy_dn = f"cn=default-recyclebin-policy,cn=recyclebin,cn=policies,{ucr.get('ldap/base')}"

        try:
            policy_attrs = main_lo.get(default_policy_dn)
            if policy_attrs and b'univentionRecycleBinPolicy' in policy_attrs.get('objectClass', []):
                covered_modules = policy_attrs.get('univentionRecycleBinUDMModules', [])
                covered_modules = [m.decode('utf-8') if isinstance(m, bytes) else m for m in covered_modules]

                if original_type in covered_modules:
                    retention_time = policy_attrs.get('univentionRecycleBinRetentionTime', [b'30'])
                    retention_days = int(retention_time[0].decode('utf-8') if isinstance(retention_time[0], bytes) else retention_time[0])

                    univention.debug.debug(
                        univention.debug.LISTENER,
                        univention.debug.INFO,
                        f"recyclebin listener: Using default policy with retention {retention_days} days for {original_type}",
                    )
                    return retention_days
        except ldap.LDAPError:
            pass

    except Exception as e:
        univention.debug.debug(
            univention.debug.LISTENER,
            univention.debug.WARNING,
            f"recyclebin listener: Error retrieving policy settings: {e}",
        )

    # Final fallback: 180 days
    univention.debug.debug(
        univention.debug.LISTENER,
        univention.debug.INFO,
        f"recyclebin listener: Using fallback retention time of 180 days for {original_type}",
    )
    return 180


def _create_recyclebin_entry(lo, original_dn, original_attrs, original_type, referenced_by):
    object_id = ldap.dn.dn2str(ldap.dn.str2dn(original_dn))
    escaped_object_id = ldap.dn.escape_dn_chars(object_id)
    recyclebin_base = 'cn=recyclebin,cn=internal'
    deleted_dn = f'univentionRecycleBinOriginalDN={escaped_object_id},{recyclebin_base}'

    now = datetime.datetime.now(datetime.UTC)
    deletion_time = now.strftime('%Y%m%d%H%M%SZ')

    retention_days = _get_recyclebin_policy_settings(original_dn, original_type)
    delete_at = now + datetime.timedelta(days=retention_days)
    delete_at_time = delete_at.strftime('%Y%m%d%H%M%SZ')

    ldap_attrs = [
        ('objectClass', [b'top', b'extensibleObject', b'univentionRecycleBinObject']),
        ('univentionRecycleBinOriginalDN', [original_dn.encode('utf-8')]),
        ('univentionRecycleBinOriginalType', [original_type.encode('utf-8')]),
        ('univentionRecycleBinDeletionDate', [deletion_time.encode('utf-8')]),
        ('univentionRecycleBinDeleteAt', [delete_at_time.encode('utf-8')]),
        ('univentionRecycleBinDeletedBy', [b'cn=admin,dc=ucs,dc=test']),  # TODO: get actual user
    ]

    excluded_attrs = {
        'dn', 'entrycsn', 'modifytimestamp',
        'createtimestamp', 'structuralobjectclass', 'hassubordinates',
        'subschemasubentry', 'entrydn', 'creatorsname', 'modifiersname',
        'pwdaccountlockedtime', 'pwdchangedtime', 'pwdfailuretime',
        'pwdhistory', 'numsubordinates',
    }

    # Attributes that should be stored with the univentionRecycleBinOriginal prefix
    prefixed_attrs = {'entryuuid', 'univentionobjectidentifier', 'objectclass'}

    for attr, values in original_attrs.items():
        attr_lower = attr.lower()
        if attr_lower not in excluded_attrs:
            if attr_lower in prefixed_attrs:
                prefixed_attr = f'univentionRecycleBinOriginal{attr}'
                ldap_attrs.append((prefixed_attr, values))
            else:
                ldap_attrs.append((attr, values))

    if referenced_by:
        for ref_info in referenced_by:
            reference_json = json.dumps(ref_info).encode('utf-8')
            ldap_attrs.append(('referencedBy', [reference_json]))

    search_filter = f"(univentionRecycleBinOriginalDN={ldap.filter.escape_filter_chars(original_dn)})"
    existing_entries = lo.search(
        base=recyclebin_base,
        filter=search_filter,
        scope='subtree',
    )

    if existing_entries:
        existing_dn = existing_entries[0][0]

        modlist = []
        for attr, values in ldap_attrs[1:]:
            modlist.append((ldap.MOD_REPLACE, attr, values))

        lo.modify(existing_dn, modlist)

        univention.debug.debug(
            univention.debug.LISTENER,
            univention.debug.INFO,
            f"recyclebin listener: Updated existing recyclebin entry: {existing_dn}",
        )
    else:
        lo.add(deleted_dn, ldap_attrs)

        univention.debug.debug(
            univention.debug.LISTENER,
            univention.debug.INFO,
            f"recyclebin listener: Created new recyclebin entry: {deleted_dn}",
        )
