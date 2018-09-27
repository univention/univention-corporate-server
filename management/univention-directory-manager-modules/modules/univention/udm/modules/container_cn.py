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
Module and object specific for "container/cn" UDM module.
"""

from __future__ import absolute_import, unicode_literals
from ..encoders import StringIntBooleanPropertyEncoder
from .generic import GenericUdm1Module, GenericUdm1Object, GenericUdm1ObjectProperties


class ContainerCnUdm1ObjectProperties(GenericUdm1ObjectProperties):
	"""container/cn UDM properties."""

	_encoders = {
		'computerPath': StringIntBooleanPropertyEncoder,
		'dhcpPath': StringIntBooleanPropertyEncoder,
		'dnsPath': StringIntBooleanPropertyEncoder,
		'groupPath': StringIntBooleanPropertyEncoder,
		'licensePath': StringIntBooleanPropertyEncoder,
		'mailPath': StringIntBooleanPropertyEncoder,
		'networkPath': StringIntBooleanPropertyEncoder,
		'policyPath': StringIntBooleanPropertyEncoder,
		'printerPath': StringIntBooleanPropertyEncoder,
		'sharePath': StringIntBooleanPropertyEncoder,
		'userPath': StringIntBooleanPropertyEncoder,
	}


class ContainerCnUdm1Object(GenericUdm1Object):
	"""Better representation of container/cn properties."""
	udm_prop_class = ContainerCnUdm1ObjectProperties


class ContainerCnUdm1Module(GenericUdm1Module):
	"""ContainerCnUdm1Object factory"""
	_udm_object_class = ContainerCnUdm1Object
	supported_api_versions = (1,)
