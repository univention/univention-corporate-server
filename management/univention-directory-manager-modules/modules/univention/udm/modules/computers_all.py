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
Module and object for all `computers/\*` UDM modules.
"""

from __future__ import absolute_import, unicode_literals
from ..encoders import (
	CnameListPropertyEncoder, DnsEntryZoneAliasListPropertyEncoder, DnsEntryZoneForwardListMultiplePropertyEncoder,
	DnsEntryZoneReverseListMultiplePropertyEncoder,
	dn_list_property_encoder_for, dn_property_encoder_for, StringIntBooleanPropertyEncoder, StringIntPropertyEncoder
)
from .generic import GenericModule, GenericObject, GenericObjectProperties


class ComputersAllObjectProperties(GenericObjectProperties):
	"""`computers/\*` UDM properties."""

	_encoders = {
		'dnsAlias': CnameListPropertyEncoder,  # What is this? Isn't this data in dnsEntryZoneAlias already?
		'dnsEntryZoneAlias': DnsEntryZoneAliasListPropertyEncoder,
		'dnsEntryZoneForward': DnsEntryZoneForwardListMultiplePropertyEncoder,
		'dnsEntryZoneReverse': DnsEntryZoneReverseListMultiplePropertyEncoder,
		'groups': dn_list_property_encoder_for('groups/group'),
		'nagiosParents': dn_list_property_encoder_for('auto'),  # can be different types of computer/* objects
		'nagiosServices': dn_list_property_encoder_for('nagios/service'),
		'network': dn_property_encoder_for('networks/network'),
		'portal': dn_property_encoder_for('settings/portal'),
		'primaryGroup': dn_property_encoder_for('groups/group'),
		'reinstall': StringIntBooleanPropertyEncoder,
		'sambaRID': StringIntPropertyEncoder,
	}


class ComputersAllObject(GenericObject):
	"""Better representation of `computers/\*` properties."""
	udm_prop_class = ComputersAllObjectProperties


class ComputersAllModule(GenericModule):
	"""ComputersAllObject factory"""
	_udm_object_class = ComputersAllObject

	class Meta:
		supported_api_versions = [1, 2]
		default_positions_property = 'computers'
		suitable_for = ['computers/*']


class ComputersDCModule(ComputersAllModule):
	"""ComputersAllObject factory with an adjusted default position"""

	class Meta:
		supported_api_versions = [1, 2]
		default_positions_property = 'domaincontroller'
		suitable_for = ['computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave']


class ComputersMemberModule(ComputersAllModule):
	"""ComputersAllObject factory with an adjusted default position"""

	def _get_default_object_positions(self):
		ret = super(ComputersMemberModule, self)._get_default_object_positions()
		if len(ret) == 4 and \
			'cn=computers,{}'.format(self.connection.base) in ret and \
			'cn=memberserver,cn=computers,{}'.format(self.connection.base) in ret and \
			'cn=dc,cn=computers,{}'.format(self.connection.base) in ret and \
			self.connection.base in ret:
				ret.remove('cn=memberserver,cn=computers,{}'.format(self.connection.base))
				ret.insert(0, 'cn=memberserver,cn=computers,{}'.format(self.connection.base))
		return ret

	class Meta:
		supported_api_versions = [1, 2]
		default_positions_property = 'computers'
		suitable_for = ['computers/memberserver']
