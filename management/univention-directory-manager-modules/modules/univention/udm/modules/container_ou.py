# -*- coding: utf-8 -*-
#
# Copyright 2018 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

"""
Module and object specific for "container/ou" UDM module.
"""

from __future__ import absolute_import, unicode_literals
from ..encoders import dn_property_encoder_for
from .container_cn import ContainerCnUdmModule, ContainerCnUdmObject, ContainerCnUdmObjectProperties


class ContainerOuUdmObjectProperties(ContainerCnUdmObjectProperties):
	"""container/ou UDM properties."""

	_encoders = ContainerCnUdmObjectProperties._encoders
	_encoders['ucsschoolClassShareFileServer'] = dn_property_encoder_for('auto')
	_encoders['ucsschoolHomeShareFileServer'] = dn_property_encoder_for('auto')


class ContainerOuUdmObject(ContainerCnUdmObject):
	"""Better representation of container/ou properties."""
	udm_prop_class = ContainerOuUdmObjectProperties


class ContainerOuUdmModule(ContainerCnUdmModule):
	"""ContainerOuUdmObject factory"""
	_udm_object_class = ContainerOuUdmObject

	class Meta:
		supported_api_versions = [1]
		suitable_for = ['containers/ou']
