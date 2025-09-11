# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""UDM module for recyclebin deleted objects"""

import json
from logging import getLogger

import ldap
from ldap import LDAPError, modlist
from ldap.controls.simple import RelaxRulesControl

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.mapping as udm_mapping
import univention.admin.syntax as udm_syntax
import univention.admin.uexceptions
from univention.admin.handlers import simpleLdap
from univention.admin.layout import Group, Tab
from univention.admin.recyclebin import RECYCLEBIN_BASE


translation = univention.admin.localization.translation('univention.admin.handlers.recyclebin')
_ = translation.translate

log = getLogger('ADMIN')

module = 'recyclebin/deletedobject'
operations = ['edit', 'remove', 'search', 'restore']
childs = False
short_description = _('Recyclebin: Deleted Object')
object_name = _('Deleted Object')
object_name_plural = _('Deleted Objects')
long_description = _('Objects that have been moved to the recycle bin')


options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'extensibleObject', 'univentionRecycleBinObject'],
    ),
}

property_descriptions = {
    'originalObjectType': univention.admin.property(
        short_description=_('Original Object Type'),
        long_description=_('UDM module type of the original object.'),
        syntax=udm_syntax.supportedUdmModulesRecyclebin,
        may_change=False,
        required=True,
    ),
    'originalDN': univention.admin.property(
        short_description=_('Original DN'),
        long_description=_('Distinguished name of the original object before deletion.'),
        syntax=udm_syntax.ldapDn,
        may_change=False,
        required=True,
        include_in_default_search=True,
        identifies=True,
    ),
    'deleteAt': univention.admin.property(
        short_description=_('Delete At'),
        long_description=_('Timestamp when the object should be permanently deleted based on retention policy.'),
        syntax=udm_syntax.GeneralizedTimeUTC,
        may_change=False,
        required=True,
    ),
    'deletedBy': univention.admin.property(
        short_description=_('Deleted By'),
        long_description=_('DN of the user who deleted the object.'),
        syntax=udm_syntax.ldapDn,
        may_change=False,
        required=True,
    ),
    'referencedBy': univention.admin.property(
        short_description=_('Referenced By'),
        long_description=_('List of objects that referenced this object at deletion time.'),
        syntax=udm_syntax.string,
        multivalue=True,
        may_change=False,
    ),
    'originalUniventionObjectIdentifier': univention.admin.property(
        short_description=_('Original Object Identifier'),
        long_description=_('UniventionObjectIdentifier of the deleted object.'),
        syntax=udm_syntax.UUID,
        may_change=False,
        required=True,
    ),
    'originalData': univention.admin.property(
        short_description=_('Original properties'),
        long_description=_('Properties of the deleted object.'),
        syntax=udm_syntax.TwoTextArea,
        may_change=False,
        required=False,
    ),
    'originalObjectClasses': univention.admin.property(
        short_description=_('Original object classes'),
        long_description=_('Object classes of the deleted object.'),
        syntax=udm_syntax.string,
        may_change=False,
        required=False,
        multivalue=True,
    ),
    'originalEntryUUID': univention.admin.property(
        short_description=_('Original EntryUUID'),
        long_description=_('EntryUUID of the deleted object.'),
        syntax=udm_syntax.UUID,
        may_change=False,
        required=True,
    ),
}


layout = [
    Tab(_('General'), _('Basic information'), layout=[
        Group(_('Object information'), layout=[
            'originalObjectType',
            'originalDN',
            'originalUniventionObjectIdentifier',
            'deleteAt',
            'deletedBy',
        ]),
        Group(_('References'), layout=[
            'referencedBy',
        ]),
    ]),
    Tab(_('Original properties'), _('Original properties'), layout=[
        'originalData',
    ]),
]

mapping = udm_mapping.mapping()
mapping.register('originalObjectType', 'univentionRecycleBinOriginalType', None, udm_mapping.ListToString)
mapping.register('deleteAt', 'univentionRecycleBinDeleteAt', None, udm_mapping.ListToString)
mapping.register('deletedBy', 'univentionRecycleBinDeletedBy', None, udm_mapping.ListToString)
mapping.register('referencedBy', 'univentionRecycleBinReferencedBy')
mapping.register('originalUniventionObjectIdentifier', 'univentionRecycleBinOriginalUniventionObjectIdentifier', None, udm_mapping.ListToString)
mapping.register('originalDN', 'univentionRecycleBinOriginalDN', None, udm_mapping.ListToString)
mapping.register('originalObjectClasses', 'univentionRecycleBinOriginalObjectClass')
mapping.register('originalEntryUUID', 'univentionRecycleBinOriginalEntryUUID', None, udm_mapping.ListToString)


class object(simpleLdap):
    module = module
    ldap_base = RECYCLEBIN_BASE
    ignore_attr_from_deleted_object = [
        'objectClass',
        'univentionObjectType',
        'entryUUID',
        'entryCSN',
        'modifyTimestamp',
        'univentionObjectIdentifier',
    ]

    def get_original_dn(self):
        rdn = ldap.dn.str2dn(self.dn)[0][0]
        if rdn[0] == 'univentionRecycleBinOriginalDN':
            return rdn[1]
        original_dn_attr = self.oldattr.get('univentionRecycleBinOriginalDN')
        if original_dn_attr:
            return original_dn_attr[0].decode('utf-8') if isinstance(original_dn_attr[0], bytes) else original_dn_attr[0]
        return None

    def __init__(self, *args, **kwargs):
        # we cant write memberOf, so we store the values in the member attribute instead
        if 'attributes' in kwargs:
            if 'member' in kwargs['attributes']:
                kwargs['attributes']['memberOf'] = kwargs['attributes']['member']
                del kwargs['attributes']['member']
        super().__init__(*args, **kwargs)
        if self.dn and 'originalObjectType' in self.info:
            try:
                mod = univention.admin.modules.get(self.info['originalObjectType']).object(None, args[1], None)
                info = mod.mapping.unmapValues(self.oldattr)
                info = mod._post_unmap(info, self.oldattr)
                info['univentionObjectIdentifier'] = self.info['originalUniventionObjectIdentifier']
                if 'password' in info:
                    info['password'] = '***'
                self['originalData'] = json.dumps(info, indent=4)
            except AttributeError:
                log.error('Original object type for deleted object not found')

    def _ldap_pre_create(self) -> None:
        super()._ldap_pre_create()
        if not self.dn.endswith(self.ldap_base):
            raise univention.admin.uexceptions.valueError(f'{module} objects need to be created in {self.ldap_base}: {self.dn}')

    def _ldap_modlist(self):
        ml = super()._ldap_modlist()
        for attr in self.ignore_attr_from_deleted_object:
            if attr in self.oldattr:
                del self.oldattr[attr]
        # we can't write memberOf and there is no ctrl to allow it
        if 'memberOf' in self.oldattr:
            self.oldattr['member'] = self.oldattr['memberOf']
            del self.oldattr['memberOf']
        ml += modlist.addModlist(self.oldattr)
        return ml

    def _restore_group_memberships(self, restored_dn):
        try:
            preserved_memberships = self.oldattr.get('seeAlso', [])
            if not preserved_memberships:
                log.debug("No preserved group memberships found for %s", restored_dn)
                return

            log.info("Restoring group memberships for %s", restored_dn)

            for group_bytes in preserved_memberships:
                group_dn = group_bytes.decode('utf-8') if isinstance(group_bytes, bytes) else group_bytes

                try:
                    group_attrs = self.lo.authz_connection.get(group_dn)
                    if not group_attrs:
                        log.warning("Group %s no longer exists, skipping membership restoration", group_dn)
                        continue

                    object_classes = group_attrs.get('objectClass', [])
                    object_classes = [oc.decode('utf-8') if isinstance(oc, bytes) else oc for oc in object_classes]

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
                            uid = ldap.dn.str2dn(restored_dn)[0][0][1]  # Extract uid from DN
                            uid_bytes = uid.encode('utf-8')
                            if uid_bytes not in current_member_uids:
                                modlist.append(('memberUid', ldap.MOD_ADD, [uid_bytes]))
                                log.debug("Adding %s to memberUid of %s", uid, group_dn)
                        except (IndexError, ldap.LDAPError) as e:
                            log.warning("Could not extract username from DN %s: %s", restored_dn, e)

                    if modlist:
                        self.lo.authz_connection.modify(group_dn, modlist)
                        log.info("Successfully restored membership of %s in group %s", restored_dn, group_dn)
                    else:
                        log.debug("No membership changes needed for group %s", group_dn)

                except ldap.LDAPError as e:
                    log.warning("Failed to restore membership in group %s: %s", group_dn, e)
                except Exception as e:
                    log.error("Unexpected error restoring membership in group %s: %s", group_dn, e)

        except Exception as e:
            log.error("Error in _restore_group_memberships for %s: %s", restored_dn, e)

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

        if original_entryuuid:
            try:
                self.lo.authz_connection.add(original_dn, restore_attrs, serverctrls=[relax_rules_control])
                log.info("Restored object with original entryUUID: %s", original_dn)
            except (LDAPError, univention.admin.uexceptions.ldapError) as e:
                log.warning("Failed to restore with RelaxRules (%s), trying without entryUUID", e)
                restore_attrs_no_uuid = [(attr, vals) for attr, vals in restore_attrs if attr != 'entryUUID']
                self.lo.authz_connection.add(original_dn, restore_attrs_no_uuid)
                log.info("Restored object without original entryUUID: %s", original_dn)
        else:
            restore_attrs_no_uuid = [(attr, vals) for attr, vals in restore_attrs if attr != 'entryUUID']
            self.lo.authz_connection.add(original_dn, restore_attrs_no_uuid)
            log.info("Restored object from recycle bin: %s", original_dn)

        self._restore_group_memberships(original_dn)

        self.remove()

        return original_dn


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
