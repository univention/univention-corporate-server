# -*- coding: utf-8 -*-
#
# Copyright 2018-2019 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

"""
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

from __future__ import absolute_import, unicode_literals
import copy
from ..encoders import ListOfListOflTextToDictPropertyEncoder, StringIntPropertyEncoder
from .generic import GenericModule, GenericObject, GenericObjectProperties
from ..exceptions import WrongObjectType


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
		"""
		Allow both `mail/\*` and `oxmail/\*` in `univentionObjectType`.
		"""
		uni_obj_type = copy.copy(getattr(orig_udm_obj, 'oldattr', {}).get('univentionObjectType'))
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
		supported_api_versions = [1, 2]
		suitable_for = ['mail/*']
