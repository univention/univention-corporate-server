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
from univention.admin.handlers import _Attributes, simpleLdap
from univention.admin.layout import Group, Tab
from univention.admin.recyclebin import RECYCLEBIN_BASE


translation = univention.admin.localization.translation('univention.admin.handlers.recyclebin')
_ = translation.translate

log = getLogger('ADMIN')

module = 'recyclebin/deletedobject'
operations = ['edit', 'remove', 'search', 'move']
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
        syntax=udm_syntax.string,  # Fixed from supportedUdmModulesRecyclebin
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
        identifies=True,
    ),
    'originalData': univention.admin.property(
        short_description=_('Original properties'),
        long_description=_('Properties of the deleted object.'),
        syntax=udm_syntax.TextArea,  # Fixed from TwoTextArea
        may_change=False,
        required=False,
    ),
    'originalObjectClasses': univention.admin.property(  # Christian's addition
        short_description=_('Original object classes'),
        long_description=_('Object classes of the deleted object.'),
        syntax=udm_syntax.string,
        may_change=False,
        required=False,
        multivalue=True,
    ),
    'originalEntryUUID': univention.admin.property(  # Christian's addition
        short_description=_('Original EntryUUID'),
        long_description=_('EntryUUID of the deleted object.'),
        syntax=udm_syntax.UUID,
        may_change=False,
        required=True,
    ),
    'cn': univention.admin.property(  # Our addition for search
        short_description=_('Common Name'),
        long_description=_('Common name from the original object'),
        syntax=udm_syntax.string,
        may_change=False,
        required=False,
        include_in_default_search=True,
    ),
    'uid': univention.admin.property(  # Our addition for search
        short_description=_('User ID'),
        long_description=_('User ID from the original object'),
        syntax=udm_syntax.uid,
        may_change=False,
        required=False,
        include_in_default_search=True,
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
            'originalObjectClasses',  # Christian's addition
            'originalEntryUUID',  # Christian's addition
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
mapping.register('originalObjectClasses', 'univentionRecycleBinOriginalObjectClass')  # Christian's addition
mapping.register('originalEntryUUID', 'univentionRecycleBinOriginalEntryUUID', None, udm_mapping.ListToString)  # Christian's addition
mapping.register('cn', 'cn')  # Our addition
mapping.register('uid', 'uid')  # Our addition


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

    @classmethod
    def identify(cls, dn: str, attr: _Attributes, canonical: bool = False) -> bool:
        """
        Identify if an LDAP object should be handled by this recyclebin module.

        :param dn: The DN of the LDAP object
        :param attr: The attributes of the LDAP object
        :param canonical: Whether to use canonical mode (unused)
        :return: True if this module should handle the object
        """
        ocs = {x.decode('utf-8') if isinstance(x, bytes) else str(x) for x in attr.get('objectClass', [])}
        required_ocs = {'univentionRecycleBinObject', 'extensibleObject', 'top'}
        return required_ocs.issubset(ocs)


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
