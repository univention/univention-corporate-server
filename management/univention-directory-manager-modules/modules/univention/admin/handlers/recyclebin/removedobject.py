# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""UDM module for Recycle Bin deleted objects"""

import copy

import ldap
from ldap import modlist

import univention.admin.filter
import univention.admin.localization
import univention.admin.mapping as udm_mapping
import univention.admin.syntax as udm_syntax
import univention.admin.uexceptions
from univention.admin._ucr import configRegistry
from univention.admin.handlers import simpleLdap
from univention.admin.layout import Group, Tab
from univention.admin.log import log
from univention.admin.modules import _ldap_operational_attribute_names
from univention.admin.recyclebin import IGNORE_ATTRS, RECYCLEBIN_BASE, Reference, create_references
from univention.admindiary.events import DiaryEvent


translation = univention.admin.localization.translation('univention.admin.handlers.recyclebin')
_ = translation.translate


module = 'recyclebin/removedobject'
operations = ['read', 'remove', 'search', 'restore']
childs = False
short_description = _('Recycle Bin: Deleted Object')
object_name = _('Deleted Object')
object_name_plural = _('Deleted Objects')
long_description = _('Objects that have been moved to the Recycle Bin')

# during package upgrade. TODO: remove in UCS 5.3
udm_syntax.__dict__.setdefault('RecycleBinReference', udm_syntax.string)
udm_syntax.__dict__.setdefault('RecycleBinSupportedModules', udm_syntax.string)

# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'extensibleObject', 'univentionRecycleBinObject', 'dynamicObject'],
    ),
}

property_descriptions = {
    'originalDN': univention.admin.property(
        short_description=_('Original DN'),
        long_description=_('Distinguished name of the original object before deletion.'),
        syntax=udm_syntax.ldapDn,
        may_change=False,
        required=True,
        include_in_default_search=True,
        identifies=False,
    ),
    'originalUniventionObjectIdentifier': univention.admin.property(
        short_description=_('Original Object Identifier'),
        long_description=_('UniventionObjectIdentifier of the deleted object.'),
        syntax=udm_syntax.UUID,
        may_change=False,
        required=True,
        identifies=True,
    ),
    'originalObjectType': univention.admin.property(
        short_description=_('Original Object Type'),
        long_description=_('UDM module type of the original object.'),
        syntax=udm_syntax.RecycleBinSupportedModules,
        may_change=False,
        required=True,
    ),
    'originalObjectClasses': univention.admin.property(
        short_description=_('Original object classes'),
        long_description=_('Object classes of the deleted object.'),
        syntax=udm_syntax.string,
        may_change=False,
        required=False,
        multivalue=True,
        dontsearch=True,
    ),
    'originalEntryUUID': univention.admin.property(
        short_description=_('Original EntryUUID'),
        long_description=_('EntryUUID of the deleted object.'),
        syntax=udm_syntax.UUID,
        may_change=False,
        required=True,
    ),
    'originalName': univention.admin.property(
        short_description=_('Original Name'),
        long_description=_('Original name of the deleted object (uid for users, cn for groups).'),
        syntax=udm_syntax.string,
        may_change=False,
        include_in_default_search=True,
    ),
    'purgeAt': univention.admin.property(
        short_description=_('Delete At'),
        long_description=_('Timestamp when the object should be permanently deleted based on retention policy. Note: Actual deletion is handled by OpenLDAP DDS and may occur slightly later.'),
        syntax=udm_syntax.GeneralizedTimeUTC,
        may_change=False,
        required=True,
    ),
    'removalDate': univention.admin.property(
        short_description=_('Deletion Date'),
        long_description=_('Timestamp when the object was deleted.'),
        syntax=udm_syntax.GeneralizedTimeUTC,
        may_change=False,
        required=True,
    ),
    'referencedBy': univention.admin.property(
        short_description=_('Referenced By'),
        long_description=_('List of objects that referenced this object at deletion time.'),
        syntax=udm_syntax.RecycleBinReference,
        multivalue=True,
        may_change=False,
        dontsearch=True,
    ),
}

default_property_descriptions = copy.deepcopy(property_descriptions)  # for later reset of descriptions
default_options = copy.deepcopy(options)  # for later reset of descriptions

layout = [
    Tab(_('Deleted Object'), _('Basic information'), layout=[
        Group(_('Object information'), layout=[
            'originalObjectType',
            'originalName',
            'originalDN',
            'originalUniventionObjectIdentifier',
            'removalDate',
            'purgeAt',
        ]),
    ]),
    Tab(_('Referencing objects'), _('Objects referencing this deleted object'), layout=[
        'referencedBy',
    ]),
]


def map_reference(value):
    """
    Map a reference list to encoded LDAP attribute format.

    Input: List of lists (from complex syntax): [['groups', 'groups/group', 'users', 'dn', 'cn=...']]
    Output: Encoded string: b'groups:groups%2Fgroup:users:dn:cn%3D...'
    """
    if not value:
        return []

    result = []
    for ref in value:
        if len(ref) != 5:
            continue
        result.append(bytes(Reference(*ref)))
    return result


def unmap_reference(value):
    """
    Unmap encoded LDAP attribute to list of lists for complex syntax.

    Input: Encoded strings: ['groups:groups%2Fgroup:users:dn:cn%3D...']
    Output: List of lists: [['groups', 'groups/group', 'users', 'dn', 'cn=...']]
    """
    if not value:
        return []

    result = []
    for ref in value:
        parsed = Reference.parse(ref.decode('UTF-8'))
        if parsed:
            result.append(tuple(parsed))
    return result


mapping = udm_mapping.mapping()
mapping.register('originalObjectType', 'univentionRecycleBinOriginalType', None, udm_mapping.ListToString)
mapping.register('purgeAt', 'univentionRecycleBinDeleteAt', None, udm_mapping.ListToString)
mapping.register('removalDate', 'univentionRecycleBinDeletionDate', None, udm_mapping.ListToString)
mapping.register('referencedBy', 'univentionRecycleBinReference', map_reference, unmap_reference)
mapping.register('originalUniventionObjectIdentifier', 'univentionRecycleBinOriginalUniventionObjectIdentifier', None, udm_mapping.ListToString)
mapping.register('originalDN', 'univentionRecycleBinOriginalDN', None, udm_mapping.ListToString)
mapping.register('originalObjectClasses', 'univentionRecycleBinOriginalObjectClass')
mapping.register('originalEntryUUID', 'univentionRecycleBinOriginalEntryUUID', None, udm_mapping.ListToString)
# fmt: on


class object(simpleLdap):

    module = module
    ldap_base = RECYCLEBIN_BASE

    def __init__(self, *args, **kwargs) -> None:
        self.foreign_policies = []
        self.foreign_options = []
        super().__init__(*args, **kwargs)
        self.options.extend(self.foreign_options)
        self.policies.extend(self.foreign_policies)
        self.save()

    def open_guardian(self):
        pass  # lazy loading calls this for users/user

    def description(self) -> str:
        """Return the original name for display in UMC grid"""
        # return self['originalName']
        # return ldap.dn.explode_rdn(self.dn, True)[0]
        return self.oldattr.get('uid', self.oldattr.get('cn', [self.dn.encode('UTF-8')]))[0].decode('UTF-8')

    @property
    def descriptions(self):
        # caution! We are modifying the module (not object's!) property_descriptions here
        # descriptions = super().descriptions
        descriptions = copy.deepcopy(default_property_descriptions)
        if 'originalObjectType' not in self.info:
            return descriptions

        module = univention.admin.modules.get(self.info['originalObjectType'])
        if not module:
            log.error('Original object type %s not found', self.info['originalObjectType'])
            return descriptions

        # add original properties to description
        for pname, prop in module.property_descriptions.items():
            if pname not in descriptions and pname != 'objectFlag':
                # we need to do this for restore in UMC
                # otherwise UMC complains about required properties
                # of the original object that we don't have on the deleted object
                descriptions[pname] = copy.deepcopy(prop)  # don't change original description!
                descriptions[pname].may_change = False
                descriptions[pname].readonly = True
                descriptions[pname].identifies = False
                descriptions[pname].required = False
                descriptions[pname].prevent_umc_default_popup = True

        return descriptions

    def _post_unmap(self, info: dict, oldattr: dict) -> dict:
        """Add computed originalName property"""
        # we can't store operational attribute memberOf at the deleted object, so we store it as reference, which we can convert back to memberOf
        references = [Reference(*ref) for ref in info.get('referencedBy', [])]
        memberof_references = [ref for ref in references if ref.target_module == 'groups/group' and ref.target_property in ('users', 'hosts', 'nestedGroup') and ref.source_attr == 'dn']

        if memberof_references:
            member_of = [
                ref.resolve(self.lo)
                for ref in memberof_references
            ]
            oldattr['memberOf'] = [x.encode('UTF-8') for x in member_of if x]

        info = super()._post_unmap(info, oldattr)
        info['originalName'] = oldattr.get('uid', oldattr.get('cn', [self.dn.encode('UTF-8')]))[0].decode('UTF-8')
        self._unmap_original_properties(info, oldattr)
        return info

    def _unmap_original_properties(self, info, oldattr):
        global options, property_descriptions
        options = copy.deepcopy(default_options)
        property_descriptions = copy.deepcopy(default_property_descriptions)  # reset to original state for each object!

        if not self.dn or 'originalObjectType' not in info:
            return

        self.info['originalObjectType'] = info['originalObjectType']
        property_descriptions.update(self.descriptions)  # overwrite the module property descriptions!!

        module = univention.admin.modules.get(info['originalObjectType'])
        if not module:
            log.error('Original object type %s not found', info['originalObjectType'])
            return

        base = self.lo.base
        self.lo.lo.base = configRegistry['ldap/base']
        try:
            oldattr = oldattr.copy()
            oldattr['objectClass'] = oldattr['univentionRecycleBinOriginalObjectClass']
            obj = module.object(None, self.lo, None, info['originalDN'], attributes=oldattr)
            # some properties are only unmapped in open() e.g. users/user:primaryGroup, groups/group:users,...
            obj.open()
        # we are in hell.. there are potential errors here.
        # except univention.admin.uexceptions.primaryGroup: !?
        except univention.admin.uexceptions.wrongObjectType:
            # ignore?
            return
        finally:
            self.lo.lo.base = base
        props = obj.info

        for opt in module.options:
            if opt not in options and opt != 'defaut':
                options[opt] = copy.deepcopy(module.options[opt])
                options[opt].editable = False
        self.foreign_options = obj.options
        self.foreign_policies = obj.policies

        props['univentionObjectIdentifier'] = info['originalUniventionObjectIdentifier']
        info.update(props)

    def _ldap_pre_create(self) -> None:
        super()._ldap_pre_create()
        if not univention.dn.DN(self.dn).endswith(univention.dn.DN(self.ldap_base)):
            raise univention.admin.uexceptions.valueError(_('%s objects need to be created in %s: %s') % (module, self.ldap_base, self.dn))
        self._operational_attributes = _ldap_operational_attribute_names(self.lo)

    def _ldap_modlist(self):
        ml = super()._ldap_modlist()

        self.oldattr.setdefault('univentionRecycleBinReference', []).extend(
            bytes(ref) for ref in self.get_references()
        )

        # filter attributes, remove operational attributes and IGNORE_ATTRS
        orig_attr = {
            attr: value for attr, value in self.oldattr.items()
            if attr.lower() not in IGNORE_ATTRS | self._operational_attributes
        }
        ml += modlist.addModlist(orig_attr)
        return ml

    def get_references(self):
        return create_references(self.lo, self.info['originalObjectType'], self.info.get('originalDN'), self.oldattr)

    def restore_references(self) -> None:
        """Restore generic references from Recycle Bin object"""
        references = self['referencedBy']
        if not references:
            self.log.debug('No preserved references found')
            return

        self.log.info('Starting reference restoration', reference_count=len(references))

        for reference in references:
            ref = Reference(*reference)
            target_dn = ref.resolve(self.lo, verify_exists=True)
            if not target_dn:
                self.log.warning(
                    'Target object no longer exists, skipping reference restoration',
                    reference=reference,
                    reason='target_not_found',
                )
                continue

            source_attr_aliases = {'dn': 'originalDN'}
            source_attr_key = source_attr_aliases.get(ref.source_attr, ref.source_attr)
            source_value = self.info.get(source_attr_key)
            if not source_value:
                self.log.warning(
                    'Restored attribute not found or empty',
                    reference=reference,
                    source_attr=ref.source_attr,
                    reason='source_attr_not_found',
                )
                continue

            mod = univention.admin.modules.get(ref.target_module)  # e.g. groups/group
            target_obj = mod.object(None, self.lo.authz_connection, None, target_dn)
            target_obj.open()

            prop = ref.target_property  # e.g. users
            current_value = target_obj.get(prop)
            if target_obj.descriptions[prop].multivalue:
                if source_value in current_value or []:
                    continue
                target_obj[prop].append(source_value)
            else:
                if current_value == source_value:
                    continue
                target_obj[prop] = source_value

            try:
                target_obj.modify()
            except (univention.admin.uexceptions.base, ldap.LDAPError) as exc:
                self.log.warning(
                    'Failed to restore reference',
                    target_dn=target_dn,
                    target_module=ref.target_module,
                    target_property=prop,
                    error=str(exc),
                    reason='modify_failed',
                )
                # raise
            else:
                self.log.info(
                    'Successfully restored reference',
                    target_dn=target_dn,
                    target_module=ref.target_module,
                    target_property=prop,
                )

    def _get_admin_diary_event(self, event_name: str) -> DiaryEvent:
        name = self['originalObjectType'].replace('/', '_').upper()
        return DiaryEvent.get('UDM_%s_%s' % (name, event_name)) or DiaryEvent.get('UDM_GENERIC_%s' % event_name)

    @classmethod
    def rewrite_filter(cls, filter_expr, mapping) -> None:
        """Make originalName searchable by rewriting to uid/cn search"""
        super().rewrite_filter(filter_expr, mapping)
        if filter_expr.variable == 'originalName' and filter_expr.value:
            uid = copy.copy(filter_expr)
            uid.variable = 'uid'
            cn = copy.copy(filter_expr)
            cn.variable = 'cn'
            filter_s = '(|%s%s)' % (uid, cn)
            filter_expr.transform_to_conjunction(univention.admin.filter.parse(filter_s))


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
