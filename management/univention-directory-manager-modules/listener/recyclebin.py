#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Listener module for creating recyclebin objects and keep references updated."""

import datetime
from dataclasses import dataclass

import ldap.dn
from ldap.extop.dds import RefreshRequest, RefreshResponse
from ldap.filter import filter_format

import univention.admin.modules
from univention.admin.recyclebin import RECYCLEBIN_BASE, create_references
from univention.admin.uexceptions import noObject
from univention.config_registry import ucr
from univention.listener import ListenerModuleHandler


@dataclass
class Policy:
    """Recyclebin policy settings"""

    retention_days: int
    ignored_object_classes: list[str]


class RecycleBinListener(ListenerModuleHandler):
    """Listener module to move removed objects into the recyclebin and keep references in sync."""

    class Configuration:
        name = 'recyclebin'
        description = 'Recyclebin listener'
        ldap_filter = '(|(univentionObjectType=users/user)(univentionObjectType=groups/group))'  # TODO: automatically add all supported modules
        _ldap_filter = '(%s)' % '|'.join([filter_format('(univentionObjectType=%s)', [mod.module]) for mod in univention.admin.modules.modules.values() if getattr(mod, 'supports_recyclebin', False)])
        attributes = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deleted_objects_cache = {}
        self._admin_lo = None
        self._cache_initialized = False
        univention.admin.modules.update()

        # initialize cache
        try:
            self._populate_cache()
            self._cache_initialized = True
        except noObject:
            # during update the recyclebin container may not yet exists
            pass

    @property
    def admin_lo(self):
        """LDAP connection with admin privileges for recyclebin operations."""
        if not self._admin_lo:
            with self.as_root():
                self._admin_lo, _ = univention.admin.uldap.getAdminConnection()
        return self._admin_lo

    def _populate_cache(self):
        """Populate the deleted objects cache from LDAP."""
        if ucr.get('server/role') != 'domaincontroller_master':
            return

        dn_attr = 'univentionRecycleBinOriginalDN'.lower()
        oid_attr = 'univentionRecycleBinOriginalUniventionObjectIdentifier'.lower()
        for dn in self.admin_lo.searchDn(base=RECYCLEBIN_BASE, scope='one', filter='(objectClass=univentionRecycleBinObject)'):
            exploded = ldap.dn.str2dn(dn)
            orig_dn = next((v for a, v, _ in exploded[0] if a.lower() == dn_attr), None)
            uoid = next((v for a, v, _ in exploded[0] if a.lower() == oid_attr), None)
            if orig_dn and uoid:
                self.deleted_objects_cache[orig_dn] = uoid

        self.logger.info('Cache populated: %d deleted objects', len(self.deleted_objects_cache))

    def _should_process_object(self, dn, attrs):
        """Check if the object should be processed by the recyclebin."""
        if ucr.get('server/role') != 'domaincontroller_master':
            return False, None

        if not attrs:
            return False, None

        object_types = univention.admin.modules.identify(dn, attrs)
        if not object_types:
            return False, None

        object_type = object_types[0].module

        return True, object_type

    def remove(self, dn: str, old: dict[str, list[bytes]]) -> None:
        """Handle object removal - move to recyclebin."""
        should_process, object_type = self._should_process_object(dn, old)
        if not should_process:
            return

        if not self._cache_initialized:
            self._populate_cache()
            self._cache_initialized = True

        recyclebin_dn = self._move_deleted_object_to_recyclebin(dn, old, object_type)
        if recyclebin_dn:
            self.deleted_objects_cache[dn] = old['univentionObjectIdentifier'][0].decode('UTF-8')

    def _move_deleted_object_to_recyclebin(self, original_dn, original_attrs, original_type):
        """
        Move deleted object to recyclebin.

        Returns:
            dn: DN of deleted object or False
        """
        policy = self._select_recyclebin_policy(original_dn, original_type, original_attrs)
        if policy is None:
            self.logger.debug('Object not moved to recyclebin (no policy): %s', original_dn)
            return False

        actual_ocs = {x.decode('UTF-8').lower() for x in original_attrs['objectClass']}
        prohibited_ocs = {x.lower() for x in policy.ignored_object_classes}
        if actual_ocs & prohibited_ocs:
            self.logger.debug('Object not moved to recyclebin (forbidden object class): %s', original_dn)
            return False

        now = datetime.datetime.now(datetime.UTC)
        deletion_time = now.strftime('%Y%m%d%H%M%SZ')
        delete_at = now + datetime.timedelta(days=policy.retention_days)
        delete_at_time = delete_at.strftime('%Y%m%d%H%M%SZ')

        mod = univention.admin.modules.get('recyclebin/removedobject')
        position = univention.admin.uldap.position(RECYCLEBIN_BASE)
        obj = mod.object(None, self.admin_lo, position)
        obj.open()
        obj['originalDN'] = original_dn
        obj['purgeAt'] = delete_at_time
        obj['removalDate'] = deletion_time
        obj['originalObjectType'] = original_type
        obj['originalUniventionObjectIdentifier'] = original_attrs['univentionObjectIdentifier'][0].decode('UTF-8')
        obj['originalEntryUUID'] = original_attrs['entryUUID'][0].decode('UTF-8')
        obj['originalObjectClasses'] = [x.decode('UTF-8') for x in original_attrs['objectClass']]
        obj.oldattr = original_attrs
        dn = obj.create(ignore_license=True)

        self.logger.info('Created deleted object: %s (retention: %d days)', dn, policy.retention_days)

        # Set TTL for DDS automatic purging based on retention policy
        ttl_seconds = policy.retention_days * 60 * 60 * 24
        refresh_req = RefreshRequest(entryName=dn.encode('UTF-8'), requestTtl=ttl_seconds)
        self.admin_lo.lo.lo.extop_s(refresh_req, extop_resp_class=RefreshResponse)

        return dn

    def _select_recyclebin_policy(self, original_dn, original_type, old_attrs=None):
        """Get retention time in days from recyclebin policy, or None if no policy applies or policy is disabled."""
        if old_attrs and 'univentionPolicyReference' in old_attrs:
            for policy_ref in old_attrs['univentionPolicyReference']:
                policy = self._get_recyclebin_policy(policy_ref.decode('utf-8'), original_type)
                if policy is not None:
                    return policy

        current_dn = original_dn
        while current_dn:
            attrs = self.admin_lo.get(current_dn)

            if attrs and 'univentionPolicyReference' in attrs:
                for policy_ref in attrs['univentionPolicyReference']:
                    policy = self._get_recyclebin_policy(policy_ref.decode('utf-8'), original_type)
                    if policy is not None:
                        return policy

            current_dn = self.admin_lo.parentDn(current_dn)

        default_policy_dn = f'cn=default-recyclebin-policy,cn=recyclebin,cn=policies,{ucr["ldap/base"]}'
        policy = self._get_recyclebin_policy(default_policy_dn, original_type)
        if policy is not None:
            return policy

        return None

    def _get_recyclebin_policy(self, policy_dn, original_type):
        """Check a single policy for retention settings. Returns retention days or None."""
        policy_filter = filter_format('(&(objectClass=univentionRecycleBinPolicy)(univentionRecycleBinPolicyEnabled=TRUE)(univentionRecycleBinPolicyUDMModules=%s))', [original_type])
        try:
            for _dn, attr in self.admin_lo.search(policy_filter, base=policy_dn, scope='base', attr=['univentionRecycleBinPolicyRetentionDays', 'univentionRecycleBinPolicyIgnoredObjectClasses']):
                return Policy(
                    retention_days=int(attr.get('univentionRecycleBinPolicyRetentionDays', [b'180'])[0].decode('ASCII')),
                    ignored_object_classes=[x.decode('ASCII') for x in attr.get('univentionRecycleBinPolicyIgnoredObjectClasses', [])],
                )
        except noObject:
            return None

    def modify(self, dn: str, old: dict[str, list[bytes]], new: dict[str, list[bytes]], old_dn: str | None) -> None:
        """Handle object modification - check for group membership changes."""
        should_process, object_type = self._should_process_object(dn, new or old)
        if not should_process:
            return

        if object_type == 'groups/group':
            self._handle_group_membership_changes(dn, new, old)

    def _handle_group_membership_changes(self, group_dn, new_attrs, old_attrs):
        """
        Handle group membership changes for deleted objects.

        When a group is modified:
        1. Check if this is a group (already validated by caller)
        2. Get the users/groups that are removed from the group
        3. Check if there are deleted objects for these users or groups
        4. If yes, add the group reference to the deleted object
        """
        # Step 2: Get users/groups that are removed from the group
        old_members = {x.decode('utf-8') for x in old_attrs.get('uniqueMember', [])}
        new_members = {x.decode('utf-8') for x in new_attrs.get('uniqueMember', [])}
        removed_member_dns = old_members - new_members
        if not removed_member_dns:
            return

        # Step 3 & 4: Check if there are deleted objects and add group reference
        for member_dn in removed_member_dns:
            uoid = self.deleted_objects_cache.get(member_dn)
            if not uoid:
                continue
            deleted_object_dn = self._get_recyclebin_dn(member_dn, uoid)
            deleted_object_attrs = self.admin_lo.get(deleted_object_dn, attr=['univentionRecycleBinOriginalType', 'univentionRecycleBinReference'])
            if deleted_object_attrs and 'univentionRecycleBinOriginalType' in deleted_object_attrs:
                object_type = deleted_object_attrs['univentionRecycleBinOriginalType'][0].decode('UTF-8')
                refs = [
                    bytes(ref) for ref in create_references(self.admin_lo, object_type, None, {'memberOf': [group_dn.encode('UTF-8')]})
                    if bytes(ref) not in deleted_object_attrs.get('univentionRecycleBinReference', [])
                ]
                if refs:
                    self.admin_lo.modify(deleted_object_dn, [('univentionRecycleBinReference', None, refs)])
                    self.logger.info('Added group reference to deleted object: %s', deleted_object_dn)

    def _get_recyclebin_dn(self, dn, uoid):
        """Generate recyclebin DN for original object."""
        rdn = ldap.dn.dn2str([[
            ('univentionRecycleBinOriginalDN', dn, ldap.AVA_STRING),
            ('univentionRecycleBinOriginalUniventionObjectIdentifier', uoid, ldap.AVA_STRING),
        ]])
        return f'{rdn},{RECYCLEBIN_BASE}'


listener_module = RecycleBinListener
