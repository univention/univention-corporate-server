# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""UDM module for recyclebin deleted objects"""

import datetime
import uuid
from logging import getLogger

import ldap
import ldap.dn
from ldap.controls.simple import RelaxRulesControl

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.mapping as udm_mapping
import univention.admin.syntax as udm_syntax
import univention.admin.uexceptions
from univention.admin.handlers import simpleLdap
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.recyclebin')
_ = translation.translate

log = getLogger('ADMIN')

module = 'recyclebin/deletedobject'
operations = ['add', 'edit', 'remove', 'search', 'move']
childs = False
short_description = _('Recyclebin: Deleted Object')
object_name = _('Deleted Object')
object_name_plural = _('Deleted Objects')
long_description = _('Objects that have been moved to the recycle bin')

ldap_base = 'cn=recyclebin,cn=internal'

# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'extensibleObject', 'univentionRecycleBinObject'],
    ),
}

property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Object ID'),
        long_description=_('Unique identifier for the deleted object'),
        syntax=udm_syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
        may_change=False,
    ),
    'originalObjectType': univention.admin.property(
        short_description=_('Original Object Type'),
        long_description=_('UDM module type of the original object'),
        syntax=udm_syntax.string,
        may_change=False,
    ),
    'originalDN': univention.admin.property(
        short_description=_('Original DN'),
        long_description=_('Distinguished name of the original object before deletion'),
        syntax=udm_syntax.string,
        may_change=False,
    ),
    'deleteAt': univention.admin.property(
        short_description=_('Delete At'),
        long_description=_('Timestamp when the object should be permanently deleted based on retention policy'),
        syntax=udm_syntax.string,
        may_change=False,
    ),
    'deletedBy': univention.admin.property(
        short_description=_('Deleted By'),
        long_description=_('DN of the user who deleted the object'),
        syntax=udm_syntax.string,
        may_change=False,
    ),
    'referencedBy': univention.admin.property(
        short_description=_('Referenced By'),
        long_description=_('List of objects that referenced this object at deletion time'),
        syntax=udm_syntax.string,
        multivalue=True,
        may_change=False,
    ),
    'originalUniventionObjectIdentifier': univention.admin.property(
        short_description=_('Original Object Identifier'),
        long_description=_('Original univentionObjectIdentifier of the deleted object'),
        syntax=udm_syntax.string,
        may_change=False,
    ),
}

layout = [
    Tab(_('General'), _('Basic information'), layout=[
        Group(_('Object information'), layout=[
            'name',
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
]

mapping = udm_mapping.mapping()
mapping.register('name', 'cn', None, udm_mapping.ListToString)
mapping.register('originalObjectType', 'univentionRecycleBinOriginalType', None, udm_mapping.ListToString)
mapping.register('originalDN', 'univentionRecycleBinOriginalDN', None, udm_mapping.ListToString)
mapping.register('deleteAt', 'univentionRecycleBinDeleteAt', None, udm_mapping.ListToString)
mapping.register('deletedBy', 'univentionRecycleBinDeletedBy', None, udm_mapping.ListToString)
mapping.register('referencedBy', 'univentionRecycleBinReferencedBy')
mapping.register('originalUniventionObjectIdentifier', 'univentionRecycleBinOriginalUniventionObjectIdentifier', None, udm_mapping.ListToString)
# fmt: on


class object(simpleLdap):
    module = module

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
            if '|' in ref:
                parts = ref.split('|', 3)
                if len(parts) == 4:
                    parsed_refs.append({
                        'dn': parts[0],
                        'module': parts[1],
                        'property': parts[2],
                        'ldap_attribute': parts[3],
                    })
                else:
                    parsed_refs.append({
                        'dn': ref,
                        'module': 'unknown',
                        'property': 'unknown',
                        'ldap_attribute': 'unknown',
                    })
            else:
                parsed_refs.append({
                    'dn': ref,
                    'module': 'unknown',
                    'property': 'unknown',
                    'ldap_attribute': 'unknown',
                })

        return parsed_refs

    def restore(self):
        if not self.exists():
            raise univention.admin.uexceptions.noObject(self.dn)

        original_dn = self['originalDN']

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

        self.remove()

        return original_dn

    @classmethod
    def move_to_trashbin(cls, lo, position, original_dn, original_attrs, original_type, referenced_by=None):
        if referenced_by is None:
            referenced_by = []

        object_id = str(uuid.uuid4())

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

        ldap_attrs = [
            ('objectClass', [b'top', b'extensibleObject', b'univentionRecycleBinObject']),
            ('cn', [object_id.encode('utf-8')]),
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
                elif attr_name != 'cn':
                    ldap_attrs.append((attr_name, attr_values))

        log.debug("Final LDAP attributes for deleted object: %s", [attr[0] for attr in ldap_attrs])

        escaped_object_id = ldap.dn.escape_dn_chars(object_id)
        deleted_dn = f'cn={escaped_object_id},cn=recyclebin,cn=internal'

        lo.authz_connection.add(deleted_dn, ldap_attrs)
        log.debug("Created deleted object with extensibleObject: %s", deleted_dn)

        # Return a minimal object for compatibility
        deleted_obj = cls(None, lo, position, dn=deleted_dn)
        deleted_obj._exists = True
        return deleted_obj


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
