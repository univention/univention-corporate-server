#
# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

r"""
Module and object specific for all "mail/\*" UDM modules.

This module handles the problem that on a OX system, UDM modules are registered
for oxmail/ox$NAME, that opens LDAP objects with both
``univentionObjectType=oxmail/ox$NAME`` *and*
``univentionObjectType=mail/$NAME``.

:py:meth:`GenericModule._verify_univention_object_type()` raises a
:py:exc:`WrongObjectType` exception when loading it.

The overwritten method :py:meth:`_verify_univention_object_type()` allows both
`mail/\*` and `oxmail/\*` in `univentionObjectType`.
"""


import copy

import univention.admin.handlers  # noqa: F401

from ..encoders import ListOfListOflTextToDictPropertyEncoder, StringIntPropertyEncoder
from ..exceptions import WrongObjectType
from .generic import GenericModule, GenericObject, GenericObjectProperties


class MailAllObjectProperties(GenericObjectProperties):
    """mail/* UDM properties."""

    _encoders = {
        'mailQuota': StringIntPropertyEncoder,  # mail/folder
        'mailUserQuota': StringIntPropertyEncoder,  # oxmail/oxfolder
        'sharedFolderGroupACL': ListOfListOflTextToDictPropertyEncoder,
        'sharedFolderUserACL': ListOfListOflTextToDictPropertyEncoder,
    }


class MailAllObject(GenericObject):
    """Better representation of mail/* properties."""

    udm_prop_class = MailAllObjectProperties


class MailAllModule(GenericModule):
    """MailAllObject factory"""

    _udm_object_class = MailAllObject

    def _verify_univention_object_type(self, orig_udm_obj):
        # type: (univention.admin.handlers.simpleLdap) -> None
        r"""Allow both `mail/\*` and `oxmail/\*` in `univentionObjectType`."""
        uni_obj_type = copy.copy(getattr(orig_udm_obj, 'oldinfo', {}).get('univentionObjectType'))
        if uni_obj_type and uni_obj_type[0].startswith('mail/'):
            # oxmail/oxfolder -> .append(mail/folder)
            uni_obj_type.append('oxmail/ox{}'.format(uni_obj_type[0].split('/', 1)[1]))
        elif uni_obj_type and uni_obj_type[0].startswith('oxmail/'):
            # mail/folder -> .append(oxmail/oxfolder)
            uni_obj_type.append('mail/{}'.format(uni_obj_type[0].split('/', 1)[1][2:]))

        # and now the original test
        if uni_obj_type and self.name.split('/', 1)[0] not in [uot.split('/', 1)[0] for uot in uni_obj_type]:
            raise WrongObjectType(dn=orig_udm_obj.dn, module_name=self.name, univention_object_type=', '.join(uni_obj_type))

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['mail/*']
