# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""UDM module for recyclebin deleted objects"""

import json
from logging import getLogger

from ldap import modlist

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
operations = ['add', 'edit', 'remove', 'search', 'move']
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
        long_description=_('UDM module type of the original object'),
        syntax=udm_syntax.supportedUdmModulesRecyclebin,
        may_change=False,
        required=True,
    ),
    'originalDN': univention.admin.property(
        short_description=_('Original DN'),
        long_description=_('Distinguished name of the original object before deletion'),
        syntax=udm_syntax.ldapDn,
        may_change=False,
        required=True,
        include_in_default_search=True,
    ),
    'deleteAt': univention.admin.property(
        short_description=_('Delete At'),
        long_description=_('Timestamp when the object should be permanently deleted based on retention policy'),
        syntax=udm_syntax.GeneralizedTimeUTC,
        may_change=False,
        required=True,
    ),
    'deletedBy': univention.admin.property(
        short_description=_('Deleted By'),
        long_description=_('DN of the user who deleted the object'),
        syntax=udm_syntax.ldapDn,
        may_change=False,
        required=True,
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
        syntax=udm_syntax.UUID,
        may_change=False,
        required=True,
        identifies=True,
    ),
    'originalData': univention.admin.property(
        short_description=_('Original data'),
        long_description=_('Original data of the deleted object.'),
        syntax=udm_syntax.TwoTextArea,
        may_change=False,
        required=False,
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
    Tab(_('Original data'), _('Original data'), layout=[
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


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
