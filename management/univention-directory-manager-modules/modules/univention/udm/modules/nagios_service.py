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
Module and object specific for "nagios/service" UDM module.
"""

from __future__ import absolute_import, unicode_literals
from ..encoders import dn_list_property_encoder_for, DisabledPropertyEncoder, StringIntPropertyEncoder
from .generic import GenericModule, GenericObject, GenericObjectProperties


class NagiosServiceObjectProperties(GenericObjectProperties):
	"""nagios/service UDM properties."""

	_encoders = {
		'assignedHosts': dn_list_property_encoder_for('auto'),  # can be different types of computer/* objects
		'maxCheckAttempts': StringIntPropertyEncoder,
		'normalCheckInterval': StringIntPropertyEncoder,
		'notificationInterval': StringIntPropertyEncoder,
		'notificationOptionCritical': DisabledPropertyEncoder,
		'notificationOptionRecovered': DisabledPropertyEncoder,
		'notificationOptionUnreachable': DisabledPropertyEncoder,
		'notificationOptionWarning': DisabledPropertyEncoder,
		'retryCheckInterval': StringIntPropertyEncoder,
		'useNRPE': DisabledPropertyEncoder,
	}


class NagiosServiceObject(GenericObject):
	"""Better representation of nagios/service properties."""
	udm_prop_class = NagiosServiceObjectProperties


class NagiosServiceModule(GenericModule):
	"""NagiosServiceObject factory"""
	_udm_object_class = NagiosServiceObject

	class Meta:
		supported_api_versions = [1, 2]
		suitable_for = ['nagios/service']
