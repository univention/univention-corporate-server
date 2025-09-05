# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| functions to handle recyclebin bin deleted objects"""

import datetime
import json
from logging import getLogger

import ldap
import ldap.dn
import ldap.filter
from ldap.controls.simple import RelaxRulesControl

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.uexceptions
from univention.admin.handlers import simpleLdap


RECYCLEBIN_BASE = 'cn=recyclebin,cn=internal'

log = getLogger('ADMIN')
translation = univention.admin.localization.translation('univention.admin.handlers')
_ = translation.translate


class fixme_object(simpleLdap):

    def get_original_dn(self):
        rdn = ldap.dn.str2dn(self.dn)[0][0]
        assert rdn[0] == 'univentionRecycleBinOriginalDN', f"Expected univentionRecycleBinOriginalDN RDN, got {rdn[0]}"

        return rdn[1]

    def __getitem__(self, key):
        if key == 'originalDN':
            return self.get_original_dn()
        return super().__getitem__(key)

    @classmethod
    def _calculate_delete_at_timestamp(cls, lo, original_type):
        default_retention_days = 30
        retention_days = default_retention_days

        try:
            policy_results = lo.search(
                base=lo.base,
                scope='subtree',
                filter='(&(objectClass=univentionRecycleBinPolicy)(univentionRecycleBinEnabled=TRUE))',
                attr=['univentionRecycleBinRetentionTime', 'univentionRecycleBinUDMModules'],
            )

            for policy_dn, policy_attrs in policy_results:
                udm_modules = policy_attrs.get('univentionRecycleBinUDMModules', [])
                if udm_modules:
                    modules_list = [mod.decode('utf-8') for mod in udm_modules]
                    if original_type in modules_list or '*' in modules_list:
                        retention_attr = policy_attrs.get('univentionRecycleBinRetentionTime', [])
                        if retention_attr:
                            retention_days = int(retention_attr[0].decode('utf-8'))
                            break
                else:
                    retention_attr = policy_attrs.get('univentionRecycleBinRetentionTime', [])
                    if retention_attr:
                        retention_days = int(retention_attr[0].decode('utf-8'))
                        break

        except Exception as e:
            log.warning("Error reading recyclebin policy, using default retention: %s", e)
            retention_days = default_retention_days

        now = datetime.datetime.utcnow()
        delete_at = now + datetime.timedelta(days=retention_days)

        return delete_at.strftime('%Y%m%d%H%M%SZ')

    def get_parsed_references(self):
        referenced_by = self.get('referencedBy', [])
        parsed_refs = []

        for ref in referenced_by:
            ref_data = json.loads(ref)
            parsed_refs.append({
                'dn': ref_data.get('dn', ''),
                'module': ref_data.get('module', 'unknown'),
                'property': ref_data.get('property', 'unknown'),
                'ldap_attribute': ref_data.get('ldap_attribute', 'unknown'),
            })

        return parsed_refs

    def restore(self):
        if not self.exists():
            raise univention.admin.uexceptions.noObject(self.dn)

        original_dn = self.get_original_dn()
        if not original_dn:
            raise univention.admin.uexceptions.valueInvalidSyntax(
                'Cannot extract original DN from deleted object',
            )

        try:
            existing = self.lo.authz_connection.get(original_dn, ['1.1'])
            if existing:
                raise univention.admin.uexceptions.objectExists(original_dn)
        except univention.admin.uexceptions.noObject:
            pass

        deleted_attrs = self.oldattr

        operational_attrs = {
            'entryUUID', 'entryCSN', 'modifyTimestamp', 'createTimestamp',
            'creatorsName', 'modifiersName', 'structuralObjectClass',
            'memberOf',
        }

        restore_attrs = []
        original_object_classes = None
        original_entryuuid = None
        original_object_identifier = None

        recyclebin_object_classes = {'extensibleObject', 'univentionRecycleBinObject'}

        for attr_name, attr_values in deleted_attrs.items():
            if attr_name == 'univentionRecycleBinOriginalObjectClass':
                original_object_classes = attr_values
                restore_attrs.append(('objectClass', attr_values))
            elif attr_name == 'univentionRecycleBinOriginalEntryUUID':
                original_entryuuid = attr_values
            elif attr_name == 'univentionRecycleBinOriginalUniventionObjectIdentifier':
                original_object_identifier = attr_values
            elif attr_name == 'objectClass':
                current_classes = {val.decode('utf-8') if isinstance(val, bytes) else val for val in attr_values}
                original_classes = current_classes - recyclebin_object_classes
                if original_classes and not original_object_classes:
                    original_object_classes = [cls.encode('utf-8') for cls in original_classes]
                    restore_attrs.append(('objectClass', original_object_classes))
            elif (not attr_name.startswith('univentionRecycleBin')
                  and attr_name not in operational_attrs
                  and attr_values
                  ):
                restore_attrs.append((attr_name, attr_values))

        if not restore_attrs:
            raise univention.admin.uexceptions.valueInvalidSyntax('No original attributes found to restore')

        if not original_object_classes:
            raise univention.admin.uexceptions.valueInvalidSyntax('No original objectClass found to restore')

        if original_entryuuid:
            restore_attrs.append(('entryUUID', original_entryuuid))

        if original_object_identifier:
            restore_attrs.append(('univentionObjectIdentifier', original_object_identifier))

        relax_rules_control = RelaxRulesControl(criticality=True)

        # First try with RelaxRules to preserve entryUUID
        if original_entryuuid:
            try:
                self.lo.authz_connection.add(original_dn, restore_attrs, serverctrls=[relax_rules_control])
                log.info("Restored object with original entryUUID: %s", original_dn)
            except (ldap.LDAPError, univention.admin.uexceptions.ldapError) as e:
                # If RelaxRules fails, try without entryUUID
                log.warning("Failed to restore with RelaxRules (%s), trying without entryUUID", e)
                restore_attrs_no_uuid = [(attr, vals) for attr, vals in restore_attrs if attr != 'entryUUID']
                self.lo.authz_connection.add(original_dn, restore_attrs_no_uuid)
                log.info("Restored object without original entryUUID: %s", original_dn)
        else:
            # No original entryUUID to restore
            restore_attrs_no_uuid = [(attr, vals) for attr, vals in restore_attrs if attr != 'entryUUID']
            self.lo.authz_connection.add(original_dn, restore_attrs_no_uuid)
            log.info("Restored object from recycle bin: %s", original_dn)

        self._restore_group_memberships(original_dn)
        self.remove()

        return original_dn

    def _restore_group_memberships(self, restored_dn):
        preserved_member_of = self.oldattr.get('seeAlso', [])

        if not preserved_member_of:
            log.debug("No preserved memberOf information found for %s", restored_dn)
            return

        log.info("Restoring group memberships for %s", restored_dn)

        for group_dn_bytes in preserved_member_of:
            group_dn = group_dn_bytes.decode('utf-8') if isinstance(group_dn_bytes, bytes) else group_dn_bytes

            group_attrs = self.lo.authz_connection.get(group_dn, ['objectClass', 'uniqueMember', 'memberUid'])
            if not group_attrs:
                log.warning("Group %s no longer exists, skipping membership restoration", group_dn)
                continue

            object_classes = [cls.decode('utf-8') if isinstance(cls, bytes) else cls for cls in group_attrs.get('objectClass', [])]

            modlist = []

            if 'groupOfUniqueNames' in object_classes or 'univentionGroup' in object_classes:
                current_unique_members = group_attrs.get('uniqueMember', [])
                restored_dn_bytes = restored_dn.encode('utf-8')

                if restored_dn_bytes not in current_unique_members:
                    modlist.append(('uniqueMember', ldap.MOD_ADD, [restored_dn_bytes]))
                    log.debug("Adding %s to uniqueMember of %s", restored_dn, group_dn)

            if 'posixGroup' in object_classes:
                current_member_uids = group_attrs.get('memberUid', [])
                try:
                    uid = ldap.dn.str2dn(restored_dn)[0][0][1]  # First RDN, first AVA, value
                    uid_bytes = uid.encode('utf-8')

                    if uid_bytes not in current_member_uids:
                        modlist.append(('memberUid', ldap.MOD_ADD, [uid_bytes]))
                        log.debug("Adding %s to memberUid of %s", uid, group_dn)
                except (IndexError, ldap.LDAPError) as e:
                    log.warning("Could not extract username from DN %s: %s", restored_dn, e)

            if modlist:
                self.lo.authz_connection.modify(group_dn, modlist)

    @classmethod
    def move_to_trashbin(cls, lo, position, original_dn, original_attrs, original_type, referenced_by=None):
        if referenced_by is None:
            referenced_by = []

        object_id = ldap.dn.dn2str(ldap.dn.str2dn(original_dn))

        # Filter out LDAP meta/operational attributes
        operational_attributes = {
            'entryUUID', 'entryCSN', 'entryDN',
            'createTimestamp', 'modifyTimestamp',
            'creatorsName', 'modifiersName',
            'structuralObjectClass', 'hasSubordinates', 'subschemaSubentry',
            'sambaPwdLastSet', 'sambaBadPasswordTime', 'sambaBadPasswordCount',
            'sambaAcctFlags',
            'memberOf',
        }

        escaped_object_id = ldap.dn.escape_dn_chars(object_id)
        deleted_dn = f'univentionRecycleBinOriginalDN={escaped_object_id},cn=recyclebin,cn=internal'

        ldap_attrs = [
            ('objectClass', [b'top', b'extensibleObject', b'univentionRecycleBinObject']),
            ('univentionRecycleBinOriginalDN', [original_dn.encode('utf-8')]),
            ('univentionRecycleBinOriginalType', [original_type.encode('utf-8')]),
            ('univentionRecycleBinDeleteAt', [cls._calculate_delete_at_timestamp(lo, original_type).encode('utf-8')]),
            ('univentionRecycleBinDeletedBy', [lo.binddn.encode('utf-8')]),
        ]

        if referenced_by:
            ldap_attrs.append(('univentionRecycleBinReferencedBy', [ref.encode('utf-8') for ref in referenced_by]))

        log.debug("Processing original attributes: %s", list(original_attrs.keys()))

        for attr_name, attr_values in original_attrs.items():
            if attr_name == 'entryUUID' and attr_values:
                ldap_attrs.append(('univentionRecycleBinOriginalEntryUUID', attr_values))
                log.debug("Storing original entryUUID: %s", attr_values)
            elif attr_name == 'univentionObjectIdentifier' and attr_values:
                ldap_attrs.append(('univentionRecycleBinOriginalUniventionObjectIdentifier', attr_values))
                log.debug("Storing original univentionObjectIdentifier: %s", attr_values)
            elif attr_name not in operational_attributes and attr_values:
                if attr_name == 'objectClass':
                    ldap_attrs.append(('univentionRecycleBinOriginalObjectClass', attr_values))
                else:
                    ldap_attrs.append((attr_name, attr_values))

        log.debug("Final LDAP attributes for deleted object: %s", [attr[0] for attr in ldap_attrs])

        try:
            lo.authz_connection.add(deleted_dn, ldap_attrs)
            log.debug("Created deleted object with extensibleObject: %s", deleted_dn)
        except (ldap.ALREADY_EXISTS, univention.admin.uexceptions.objectExists):
            log.debug("Trash entry already exists for %s, updating existing entry", original_dn)

            search_filter = f"(univentionRecycleBinOriginalDN={ldap.filter.escape_filter_chars(original_dn)})"
            existing_entries = lo.authz_connection.search(
                base='cn=recyclebin,cn=internal',
                scope='subtree',
                filter=search_filter,
                attr=[],
                unique=False,
                required=False,
            )

            if existing_entries:
                existing_dn = existing_entries[0][0]

                modlist = []
                for attr_name, attr_values in ldap_attrs:
                    if attr_name not in ['objectClass', 'univentionRecycleBinOriginalDN']:
                        modlist.append((ldap.MOD_REPLACE, attr_name, attr_values))

                if modlist:
                    lo.authz_connection.modify(existing_dn, modlist)
                    log.debug("Updated existing trash entry: %s", existing_dn)

                deleted_dn = existing_dn
            else:
                log.error("LDAP says entry exists but we can't find it for %s", original_dn)
                raise

        # Return a minimal object for compatibility
        deleted_obj = cls(None, lo, position, dn=deleted_dn)
        deleted_obj._exists = True
        return deleted_obj
