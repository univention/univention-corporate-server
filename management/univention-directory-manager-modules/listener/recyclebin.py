#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""listener script for recyclebin objects."""

import datetime
import json
import syslog
import time

import ldap
import ldap.dn
import ldap.filter

import univention.admin.modules
import univention.admin.uldap
import univention.config_registry
import univention.debug
import univention.dn
import univention.uldap

import listener


# Global cache for deleted objects DNs
deleted_objects_cache = set()


name = 'recyclebin'
description = 'Secure recyclebin operations via listener'
filter = '(objectClass=*)'
modrdn = True


def initialize():
    """Initialize the listener module."""
    syslog.syslog(syslog.LOG_INFO, "RECYCLEBIN INIT: Starting initialization")

    ucr = univention.config_registry.ConfigRegistry()
    ucr.load()

    server_role = ucr.get('server/role')
    syslog.syslog(syslog.LOG_INFO, f"RECYCLEBIN INIT: Server role is {server_role}")

    if server_role != 'domaincontroller_master':
        syslog.syslog(syslog.LOG_INFO, "RECYCLEBIN INIT: Not master, skipping initialization")
        return

    try:
        main_lo, _ = univention.admin.uldap.getAdminConnection()

        deleted_dns = main_lo.searchDn(
            base='cn=recyclebin,cn=internal',
            scope='one',
            filter='(objectClass=univentionRecycleBinObject)',
        )

        deleted_objects_cache.clear()
        for dn in deleted_dns:
            try:
                deleted_objects_cache.add(univention.dn.DN(dn))
            except Exception as e:
                syslog.syslog(syslog.LOG_WARNING, f"RECYCLEBIN: Error adding DN to cache: {dn}, {e}")

        syslog.syslog(syslog.LOG_INFO, f"RECYCLEBIN: Initialized cache with {len(deleted_objects_cache)} deleted objects")

    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"RECYCLEBIN: Error initializing deleted objects cache: {e}")
        deleted_objects_cache.clear()

    syslog.syslog(syslog.LOG_INFO, "RECYCLEBIN INIT: Initialization complete")

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

    object_type = None
    attrs_to_check = new or old
    if attrs_to_check:
        obj_type_attr = attrs_to_check.get('univentionObjectType')
        if obj_type_attr:
            object_type = obj_type_attr[0].decode('utf-8') if isinstance(obj_type_attr[0], bytes) else obj_type_attr[0]
        else:
            object_classes = attrs_to_check.get('objectClass', [])
            object_classes = [oc.decode('utf-8') if isinstance(oc, bytes) else oc for oc in object_classes]

            if 'inetOrgPerson' in object_classes or 'posixAccount' in object_classes:
                object_type = 'users/user'
            elif 'univentionGroup' in object_classes or 'posixGroup' in object_classes:
                object_type = 'groups/group'

    if object_type not in ['users/user', 'groups/group']:
        return

    syslog.syslog(syslog.LOG_INFO, f"RECYCLEBIN: Processing {command} for {object_type}: {dn}")

    if command == 'd':
        _move_deleted_object_to_recyclebin(dn, old)

        try:
            recyclebin_dn = _get_recyclebin_dn_for_original(dn)
            deleted_objects_cache.add(univention.dn.DN(recyclebin_dn))
            syslog.syslog(syslog.LOG_INFO, f"RECYCLEBIN: Added to cache: {recyclebin_dn}")
        except Exception as e:
            syslog.syslog(syslog.LOG_ERR, f"RECYCLEBIN: Error adding to cache: {e}")

    elif command == 'm' and object_type == 'groups/group':
        _handle_group_membership_changes(dn, new, old)


def _get_recyclebin_dn_for_original(original_dn):
    object_id = ldap.dn.dn2str(ldap.dn.str2dn(original_dn))
    escaped_object_id = ldap.dn.escape_dn_chars(object_id)
    return f'univentionRecycleBinOriginalDN={escaped_object_id},cn=recyclebin,cn=internal'


def _handle_group_membership_changes(group_dn, new_attrs, old_attrs):
    try:
        old_members = set()
        new_members = set()

        if old_attrs and 'uniqueMember' in old_attrs:
            for member_bytes in old_attrs['uniqueMember']:
                member_dn = member_bytes.decode('utf-8') if isinstance(member_bytes, bytes) else member_bytes
                old_members.add(member_dn)

        if new_attrs and 'uniqueMember' in new_attrs:
            for member_bytes in new_attrs['uniqueMember']:
                member_dn = member_bytes.decode('utf-8') if isinstance(member_bytes, bytes) else member_bytes
                new_members.add(member_dn)

        removed_members = old_members - new_members

        if not removed_members:
            return

        syslog.syslog(syslog.LOG_INFO, f"RECYCLEBIN: Group {group_dn} removed {len(removed_members)} members")

        for member_dn in removed_members:
            try:
                recyclebin_dn = _get_recyclebin_dn_for_original(member_dn)
                recyclebin_dn_obj = univention.dn.DN(recyclebin_dn)

                if recyclebin_dn_obj in deleted_objects_cache:
                    syslog.syslog(syslog.LOG_INFO, f"RECYCLEBIN: Updating deleted object {recyclebin_dn} with group membership {group_dn}")

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

                        modlist = [('seeAlso', ldap.MOD_ADD, [group_dn.encode('utf-8')])]
                        internal_lo.modify(recyclebin_dn, modlist)

                        syslog.syslog(syslog.LOG_INFO, f"RECYCLEBIN: Successfully added group {group_dn} to deleted object {recyclebin_dn}")
                    finally:
                        listener.unsetuid()

            except Exception as e:
                syslog.syslog(syslog.LOG_ERR, f"RECYCLEBIN: Error updating deleted object for member {member_dn}: {e}")

    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"RECYCLEBIN: Error in _handle_group_membership_changes: {e}")


def _move_deleted_object_to_recyclebin(original_dn, original_attrs):
    syslog.syslog(syslog.LOG_INFO, f"RECYCLEBIN MOVE: Starting move to recyclebin for {original_dn}")
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

        group_memberships = []
        if 'memberOf' in original_attrs:
            for group_bytes in original_attrs['memberOf']:
                group_dn = group_bytes.decode('utf-8') if isinstance(group_bytes, bytes) else group_bytes
                group_memberships.append(group_dn)
        else:
            group_memberships = _find_user_group_memberships(original_dn, main_lo)

        _create_recyclebin_entry(
            lo=internal_lo,
            original_dn=original_dn,
            original_attrs=original_attrs,
            original_type=original_type,
            referenced_by=referenced_by,
            group_memberships=group_memberships,
        )

    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"RECYCLEBIN: Error moving {original_dn} to recyclebin: {e}")
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


def _find_user_group_memberships(user_dn, lo):
    try:
        group_dns = []

        escaped_user_dn = ldap.filter.escape_filter_chars(user_dn)

        try:
            username = ldap.dn.str2dn(user_dn)[0][0][1]  # First RDN, first AVA, value
            escaped_username = ldap.filter.escape_filter_chars(username)
        except (IndexError, ldap.LDAPError):
            username = None
            escaped_username = None

        search_filters = [f"(uniqueMember={escaped_user_dn})"]
        if escaped_username:
            search_filters.append(f"(memberUid={escaped_username})")

        combined_filter = f"(|{''.join(search_filters)})"

        results = lo.search(
            base=lo.base,
            scope='subtree',
            filter=combined_filter,
            attr=['dn'],
            unique=False,
            required=False,
        )

        for group_dn, group_attrs in results:
            if group_dn and group_dn != user_dn:  # Avoid self-references
                group_dns.append(group_dn)

        return group_dns

    except Exception as e:
        syslog.syslog(syslog.LOG_WARNING, f"RECYCLEBIN: Error finding group memberships for {user_dn}: {e}")
        return []


def _get_recyclebin_policy_settings(original_dn, original_type, old_attrs=None):
    try:
        main_lo, _ = univention.admin.uldap.getAdminConnection()

        if old_attrs and 'univentionPolicyReference' in old_attrs:
            policy_refs = old_attrs['univentionPolicyReference']

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
                                f"recyclebin listener: Found direct policy {policy_dn} with retention {retention_days} days for {original_type}",
                            )
                            return retention_days
                except ldap.LDAPError:
                    continue

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
                                        f"recyclebin listener: Found inherited policy {policy_dn} with retention {retention_days} days for {original_type}",
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


def _create_recyclebin_entry(lo, original_dn, original_attrs, original_type, referenced_by, group_memberships=None):
    object_id = ldap.dn.dn2str(ldap.dn.str2dn(original_dn))
    escaped_object_id = ldap.dn.escape_dn_chars(object_id)
    recyclebin_base = 'cn=recyclebin,cn=internal'
    deleted_dn = f'univentionRecycleBinOriginalDN={escaped_object_id},{recyclebin_base}'

    now = datetime.datetime.now(datetime.UTC)
    deletion_time = now.strftime('%Y%m%d%H%M%SZ')

    retention_days = _get_recyclebin_policy_settings(original_dn, original_type, original_attrs)
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
        'memberof',
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

    if group_memberships:
        group_memberships_encoded = [group_dn.encode('utf-8') for group_dn in group_memberships]
        ldap_attrs.append(('seeAlso', group_memberships_encoded))

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
