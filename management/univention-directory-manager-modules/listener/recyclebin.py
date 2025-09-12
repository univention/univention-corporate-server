#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""listener script for recyclebin objects."""

import datetime
import json
import syslog

import ldap
import ldap.dn
import ldap.filter
from ldap.extop.dds import RefreshRequest

import univention.admin.modules
import univention.admin.uldap
import univention.config_registry
import univention.debug
import univention.debug as ud
import univention.dn
import univention.uldap
from univention.listener import ListenerModuleHandler

import listener


class RecycleBinListener(ListenerModuleHandler):

    class Configuration:
        name = 'recyclebin'
        description = 'Recyclebin listener'
        ldap_filter = '(|(univentionObjectType=users/user)(univentionObjectType=groups/group))'
        attributes = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Global cache for deleted objects DNs
        self.deleted_objects_cache = set()
        self._initialize_cache()

    def _initialize_cache(self):
        """Initialize the deleted objects cache."""
        ud.debug(ud.LISTENER, ud.INFO, "RECYCLEBIN INIT: Starting initialization")

        ucr = univention.config_registry.ConfigRegistry()
        ucr.load()

        server_role = ucr.get('server/role')
        ud.debug(ud.LISTENER, ud.INFO, f"RECYCLEBIN INIT: Server role is {server_role}")

        if server_role != 'domaincontroller_master':
            ud.debug(ud.LISTENER, ud.INFO, "RECYCLEBIN INIT: Not master, skipping initialization")
            return

        try:
            main_lo, _ = univention.admin.uldap.getAdminConnection()

            deleted_dns = main_lo.searchDn(
                base='cn=recyclebin,cn=internal',
                scope='one',
                filter='(objectClass=univentionRecycleBinObject)',
            )

            self.deleted_objects_cache.clear()
            for dn in deleted_dns:
                try:
                    self.deleted_objects_cache.add(univention.dn.DN(dn))
                except Exception as e:
                    ud.debug(ud.LISTENER, ud.WARNING, f"RECYCLEBIN: Error adding DN to cache: {dn}, {e}")

            ud.debug(ud.LISTENER, ud.INFO, f"RECYCLEBIN: Initialized cache with {len(self.deleted_objects_cache)} deleted objects")

        except Exception as e:
            ud.debug(ud.LISTENER, ud.ERROR, f"RECYCLEBIN: Error initializing deleted objects cache: {e}")
            self.deleted_objects_cache.clear()

        ud.debug(ud.LISTENER, ud.INFO, "RECYCLEBIN INIT: Initialization complete")

        univention.debug.debug(
            univention.debug.LISTENER,
            univention.debug.INFO,
            f"recyclebin listener: Initializing on {server_role}",
        )

    def _should_process_object(self, attrs):
        """Check if the object should be processed by the recyclebin."""
        ucr = univention.config_registry.ConfigRegistry()
        ucr.load()

        server_role = ucr.get('server/role')
        if server_role != 'domaincontroller_master':
            return False, None

        if not attrs:
            return False, None

        # Determine object type
        obj_type_attr = attrs.get('univentionObjectType')
        if obj_type_attr:
            object_type = obj_type_attr[0].decode('utf-8')
        else:
            object_classes = attrs.get('objectClass', [])
            object_classes = [oc.decode('utf-8') for oc in object_classes]

            if 'inetOrgPerson' in object_classes or 'posixAccount' in object_classes:
                object_type = 'users/user'
            elif 'univentionGroup' in object_classes or 'posixGroup' in object_classes:
                object_type = 'groups/group'
            else:
                object_type = None

        if object_type not in ['users/user', 'groups/group']:
            return False, None

        return True, object_type

    def create(self, dn: str, new: dict[str, list[bytes]]) -> None:
        """Handle object creation - no action needed for recyclebin."""
        should_process, object_type = self._should_process_object(new)
        if should_process:
            ud.debug(ud.LISTENER, ud.INFO, f"RECYCLEBIN: Object created {object_type}: {dn}")

    def modify(self, dn: str, old: dict[str, list[bytes]], new: dict[str, list[bytes]], old_dn: str | None) -> None:
        """Handle object modification - check for group membership changes."""
        should_process, object_type = self._should_process_object(new or old)
        if not should_process:
            return

        ud.debug(ud.LISTENER, ud.INFO, f"RECYCLEBIN: Processing modify for {object_type}: {dn}")

        if object_type == 'groups/group':
            self._handle_group_membership_changes(dn, new, old)

    def remove(self, dn: str, old: dict[str, list[bytes]]) -> None:
        """Handle object removal - move to recyclebin."""
        should_process, object_type = self._should_process_object(old)
        if not should_process:
            return

        ud.debug(ud.LISTENER, ud.INFO, f"RECYCLEBIN: Processing removal for {object_type}: {dn}")

        moved_to_recyclebin = self._move_deleted_object_to_recyclebin(dn, old)

        if moved_to_recyclebin:
            try:
                recyclebin_dn = self._get_recyclebin_dn_for_original(dn)
                self.deleted_objects_cache.add(univention.dn.DN(recyclebin_dn))
                ud.debug(ud.LISTENER, ud.INFO, f"RECYCLEBIN: Added to cache: {recyclebin_dn}")
            except Exception as e:
                ud.debug(ud.LISTENER, ud.ERROR, f"RECYCLEBIN: Error adding to cache: {e}")
        else:
            ud.debug(ud.LISTENER, ud.INFO, f"RECYCLEBIN: Object {dn} was not moved to recyclebin - not adding to cache")

    def _get_recyclebin_dn_for_original(self, original_dn):
        """Generate recyclebin DN for original object."""
        object_id = ldap.dn.dn2str(ldap.dn.str2dn(original_dn))
        escaped_object_id = ldap.dn.escape_dn_chars(object_id)
        return f'univentionRecycleBinOriginalDN={escaped_object_id},cn=recyclebin,cn=internal'

    def _handle_group_membership_changes(self, group_dn, new_attrs, old_attrs):
        """
        Handle group membership changes for deleted objects.

        When a group is modified:
        1. Check if this is a group (already validated by caller)
        2. Get the users/groups that are removed from the group
        3. Check if there are deleted objects for these users or groups
        4. If yes, add the group as "memberOf" on this deleted object
        """
        try:
            # Step 2: Get users/groups that are removed from the group
            old_members = set()
            new_members = set()

            # Handle uniqueMember attribute (for groups)
            if old_attrs and 'uniqueMember' in old_attrs:
                for member_bytes in old_attrs['uniqueMember']:
                    member_dn = member_bytes.decode('utf-8')
                    old_members.add(member_dn)

            if new_attrs and 'uniqueMember' in new_attrs:
                for member_bytes in new_attrs['uniqueMember']:
                    member_dn = member_bytes.decode('utf-8')
                    new_members.add(member_dn)

            # Handle memberUid attribute (for POSIX groups)
            old_member_uids = set()
            new_member_uids = set()

            if old_attrs and 'memberUid' in old_attrs:
                for uid_bytes in old_attrs['memberUid']:
                    uid = uid_bytes.decode('utf-8')
                    old_member_uids.add(uid)

            if new_attrs and 'memberUid' in new_attrs:
                for uid_bytes in new_attrs['memberUid']:
                    uid = uid_bytes.decode('utf-8')
                    new_member_uids.add(uid)

            # Find removed members (both DN-based and UID-based)
            removed_member_dns = old_members - new_members
            removed_member_uids = old_member_uids - new_member_uids

            if not removed_member_dns and not removed_member_uids:
                return

            ud.debug(ud.LISTENER, ud.INFO, f"RECYCLEBIN: Group {group_dn} removed {len(removed_member_dns)} DN members and {len(removed_member_uids)} UID members")

            # Step 3 & 4: Check if there are deleted objects and add group as memberOf
            self._update_deleted_objects_with_group_membership(group_dn, removed_member_dns, removed_member_uids)

        except Exception as e:
            ud.debug(ud.LISTENER, ud.ERROR, f"RECYCLEBIN: Error in _handle_group_membership_changes: {e}")

    def _update_deleted_objects_with_group_membership(self, group_dn, removed_member_dns, removed_member_uids):
        """Update deleted objects with group membership information."""
        try:
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

                # Handle DN-based members (users and groups)
                for member_dn in removed_member_dns:
                    self._add_group_to_deleted_object_by_dn(internal_lo, group_dn, member_dn)

                # Handle UID-based members (POSIX users)
                for member_uid in removed_member_uids:
                    self._add_group_to_deleted_object_by_uid(internal_lo, group_dn, member_uid)

            finally:
                listener.unsetuid()

        except Exception as e:
            ud.debug(ud.LISTENER, ud.ERROR, f"RECYCLEBIN: Error updating deleted objects with group membership: {e}")

    def _add_group_to_deleted_object_by_dn(self, internal_lo, group_dn, member_dn):
        """Add group as memberOf to deleted object identified by DN."""
        try:
            # Step 3: Check if there is a deleted object for this member DN
            recyclebin_dn = self._get_recyclebin_dn_for_original(member_dn)
            recyclebin_dn_obj = univention.dn.DN(recyclebin_dn)

            # Check both cache and LDAP to ensure the deleted object exists
            if recyclebin_dn_obj in self.deleted_objects_cache:
                # Verify the object actually exists in LDAP
                try:
                    deleted_attrs = internal_lo.get(recyclebin_dn, attr=['objectClass'])
                    if deleted_attrs and b'univentionRecycleBinObject' in deleted_attrs.get('objectClass', []):
                        # Step 4: Add the group as "memberOf" on this deleted object
                        modlist = [('seeAlso', ldap.MOD_ADD, [group_dn.encode('utf-8')])]
                        internal_lo.modify(recyclebin_dn, modlist)

                        ud.debug(ud.LISTENER, ud.INFO, f"RECYCLEBIN: Successfully added group {group_dn} as memberOf to deleted object {recyclebin_dn} (original: {member_dn})")
                    else:
                        ud.debug(ud.LISTENER, ud.WARNING, f"RECYCLEBIN: Deleted object {recyclebin_dn} exists in cache but not in LDAP")
                        # Remove from cache if it doesn't exist in LDAP
                        self.deleted_objects_cache.discard(recyclebin_dn_obj)

                except ldap.NO_SUCH_OBJECT:
                    ud.debug(ud.LISTENER, ud.INFO, f"RECYCLEBIN: Deleted object {recyclebin_dn} no longer exists, removing from cache")
                    self.deleted_objects_cache.discard(recyclebin_dn_obj)

                except ldap.TYPE_OR_VALUE_EXISTS:
                    ud.debug(ud.LISTENER, ud.ALL, f"RECYCLEBIN: Group {group_dn} already exists as memberOf in deleted object {recyclebin_dn}")

            else:
                ud.debug(ud.LISTENER, ud.ALL, f"RECYCLEBIN: No deleted object found for member {member_dn}")

        except Exception as e:
            ud.debug(ud.LISTENER, ud.ERROR, f"RECYCLEBIN: Error adding group to deleted object for member {member_dn}: {e}")

    def _add_group_to_deleted_object_by_uid(self, internal_lo, group_dn, member_uid):
        """Add group as memberOf to deleted object identified by UID."""
        try:
            # Step 3: Search for deleted objects with this UID
            ucr = univention.config_registry.ConfigRegistry()
            ucr.load()

            # Search for deleted user objects with the given UID
            search_filter = f"(&(objectClass=univentionRecycleBinObject)(uid={ldap.filter.escape_filter_chars(member_uid)}))"

            try:
                results = internal_lo.search(
                    base='cn=recyclebin,cn=internal',
                    scope='subtree',
                    filter=search_filter,
                    attr=['univentionRecycleBinOriginalDN', 'objectClass'],
                )

                for deleted_dn, deleted_attrs in results:
                    if deleted_attrs and b'univentionRecycleBinObject' in deleted_attrs.get('objectClass', []):
                        original_dn = deleted_attrs.get('univentionRecycleBinOriginalDN', [b''])[0].decode('utf-8')

                        # Step 4: Add the group as "memberOf" on this deleted object
                        try:
                            modlist = [('seeAlso', ldap.MOD_ADD, [group_dn.encode('utf-8')])]
                            internal_lo.modify(deleted_dn, modlist)

                            ud.debug(ud.LISTENER, ud.INFO, f"RECYCLEBIN: Successfully added group {group_dn} as memberOf to deleted object {deleted_dn} (original: {original_dn}, uid: {member_uid})")

                            # Update cache
                            self.deleted_objects_cache.add(univention.dn.DN(deleted_dn))

                        except ldap.TYPE_OR_VALUE_EXISTS:
                            ud.debug(ud.LISTENER, ud.ALL, f"RECYCLEBIN: Group {group_dn} already exists as memberOf in deleted object {deleted_dn}")

            except ldap.LDAPError as e:
                ud.debug(ud.LISTENER, ud.WARNING, f"RECYCLEBIN: LDAP error searching for deleted objects with UID {member_uid}: {e}")

        except Exception as e:
            ud.debug(ud.LISTENER, ud.ERROR, f"RECYCLEBIN: Error adding group to deleted object for UID {member_uid}: {e}")

    def _move_deleted_object_to_recyclebin(self, original_dn, original_attrs):
        """
        Move deleted object to recyclebin.

        Returns:
            bool: True if object was moved to recyclebin, False if skipped due to no policy
        """
        ud.debug(ud.LISTENER, ud.INFO, f"RECYCLEBIN MOVE: Starting move to recyclebin for {original_dn}")
        listener.setuid(0)
        try:
            lo, position = univention.admin.uldap.getAdminConnection()
            position.setBase('cn=internal')

            univention.admin.modules.update()

            original_type = self._determine_object_type(original_attrs)

            self._create_recyclebin_entry(
                lo=lo,
                original_dn=original_dn,
                original_attrs=original_attrs,
                original_type=original_type,
            )

            return True

        except Exception as e:
            ud.debug(ud.LISTENER, ud.ERROR, f"RECYCLEBIN: Error moving {original_dn} to recyclebin: {e}")
            return False
        finally:
            listener.unsetuid()

    def _determine_object_type(self, attrs):
        """Determine the object type from attributes."""
        object_type = attrs.get('univentionObjectType')
        if object_type:
            return object_type[0].decode('utf-8')
        return 'generic/object'

    def _get_recyclebin_retention_days(self, original_dn, original_type, old_attrs=None):
        """Get retention time in days from recyclebin policy, or None if no policy applies."""
        try:
            main_lo, _ = univention.admin.uldap.getAdminConnection()

            if old_attrs and 'univentionPolicyReference' in old_attrs:
                policy_refs = old_attrs['univentionPolicyReference']

                for policy_ref in policy_refs:
                    policy_dn = policy_ref.decode('utf-8')

                    try:
                        policy_attrs = main_lo.get(policy_dn)
                        if policy_attrs and b'univentionRecycleBinPolicy' in policy_attrs.get('objectClass', []):
                            covered_modules = policy_attrs.get('univentionRecycleBinUDMModules', [])
                            covered_modules = [m.decode('utf-8') for m in covered_modules]

                            if original_type in covered_modules:
                                retention_time = policy_attrs.get('univentionRecycleBinRetentionTime', [b'30'])
                                retention_days = int(retention_time[0].decode('utf-8'))

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
                            policy_dn = policy_ref.decode('utf-8')

                            try:
                                policy_attrs = main_lo.get(policy_dn)
                                if policy_attrs and b'univentionRecycleBinPolicy' in policy_attrs.get('objectClass', []):
                                    covered_modules = policy_attrs.get('univentionRecycleBinUDMModules', [])
                                    covered_modules = [m.decode('utf-8') for m in covered_modules]

                                    if original_type in covered_modules:
                                        retention_time = policy_attrs.get('univentionRecycleBinRetentionTime', [b'30'])
                                        retention_days = int(retention_time[0].decode('utf-8'))

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
                    covered_modules = [m.decode('utf-8') for m in covered_modules]

                    if original_type in covered_modules:
                        retention_time = policy_attrs.get('univentionRecycleBinRetentionTime', [b'30'])
                        retention_days = int(retention_time[0].decode('utf-8'))

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

        # No recyclebin policy found - do not create deleted object
        univention.debug.debug(
            univention.debug.LISTENER,
            univention.debug.INFO,
            f"recyclebin listener: No recyclebin policy found for {original_type} - object will not be moved to recyclebin",
        )
        return None

    def _create_recyclebin_entry(self, lo, original_dn, original_attrs, original_type):
        """Create recyclebin entry for deleted object."""
        object_id = ldap.dn.dn2str(ldap.dn.str2dn(original_dn))
        escaped_object_id = ldap.dn.escape_dn_chars(object_id)
        recyclebin_base = 'cn=recyclebin,cn=internal'
        deleted_dn = f'univentionRecycleBinOriginalDN={escaped_object_id},{recyclebin_base}'

        now = datetime.datetime.now(datetime.UTC)
        deletion_time = now.strftime('%Y%m%d%H%M%SZ')

        retention_days = self._get_recyclebin_retention_days(original_dn, original_type, original_attrs)

        if retention_days is None:
            ud.debug(ud.LISTENER, ud.INFO, f"RECYCLEBIN: No recyclebin policy found for {original_type} - skipping recyclebin creation for {original_dn}")
            return False

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


def _refresh_ttl_for_dds(lo, dn, ucr):
    """
    Use the DDS refresh extended operation to set TTL on a dynamic object.

    Required because entryTtl attribute is NO-USER-MODIFICATION per RFC 2589.

    :param lo: LDAP connection object
    :param str dn: Distinguished name of the object to refresh
    :param ucr: UCR configuration registry object
    """
    try:

        default_ttl = int(ucr.get('ldap/database/internal/dds/default-ttl', str(30 * 86400)))
        max_ttl = int(ucr.get('ldap/database/internal/dds/max-ttl', '31536000'))
        min_ttl = int(ucr.get('ldap/database/internal/dds/min-ttl', '86400'))

        ttl = max(min_ttl, min(default_ttl, max_ttl))

        refresh_req = RefreshRequest(entryName=dn, requestTtl=ttl)
        lo.lo.extop_s(refresh_req, serverctrls=[])

        syslog.syslog(syslog.LOG_INFO, f"RECYCLEBIN DDS: Successfully set TTL to {ttl} seconds for {dn} via DDS refresh")

    except ldap.LDAPError as e:
        syslog.syslog(syslog.LOG_ERR, f"RECYCLEBIN DDS: Failed to refresh TTL for {dn}: {e}")
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"RECYCLEBIN DDS: Unexpected error refreshing TTL for {dn}: {e}")


def _create_recyclebin_entry(lo, original_dn, original_attrs, original_type, referenced_by, group_memberships=None):
    object_id = ldap.dn.dn2str(ldap.dn.str2dn(original_dn))
    escaped_object_id = ldap.dn.escape_dn_chars(object_id)
    recyclebin_base = 'cn=recyclebin,cn=internal'
    deleted_dn = f'univentionRecycleBinOriginalDN={escaped_object_id},{recyclebin_base}'

    now = datetime.datetime.now(datetime.UTC)
    deletion_time = now.strftime('%Y%m%d%H%M%SZ')

    retention_days = _get_recyclebin_policy_settings(original_dn, original_type)
    delete_at = now + datetime.timedelta(days=retention_days)
    delete_at_time = delete_at.strftime('%Y%m%d%H%M%SZ')

    ucr = univention.config_registry.ConfigRegistry()
    ucr.load()
    dds_enabled = ucr.is_true('ldap/database/internal/overlay/dds', False)

    object_classes = [b'top', b'extensibleObject', b'univentionRecycleBinObject']
    if dds_enabled:
        object_classes.append(b'dynamicObject')
        syslog.syslog(syslog.LOG_INFO, f"RECYCLEBIN DDS: Adding dynamicObject class for automatic purging of {original_dn}")

    ldap_attrs = [
        ('objectClass', object_classes),
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

        # Refresh TTL for DDS if enabled
        if dds_enabled:
            _refresh_ttl_for_dds(lo, existing_dn, ucr)
    else:
        lo.add(deleted_dn, ldap_attrs)

        univention.debug.debug(
            univention.debug.LISTENER,
            univention.debug.INFO,
            f"recyclebin listener: Created new recyclebin entry: {deleted_dn}",
        )

        # Refresh TTL for DDS if enabled
        if dds_enabled:
            _refresh_ttl_for_dds(lo, deleted_dn, ucr)
