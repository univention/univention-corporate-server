# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright 2010-2019 Univention GmbH
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
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from univention.admin.uexceptions import base as udm_error
import univention.admin.modules
import univention.admin.handlers.uvmm.profile as uvmm_profile

from univention.lib.i18n import Translation

from univention.management.console.log import MODULE
from univention.management.console.ldap import machine_connection
from univention.management.console.error import UMC_Error
from univention.management.console.modules.decorators import simple_response

from urlparse import urlsplit

univention.admin.modules.update()

_ = Translation('univention-management-console-modules-uvmm').translate


class Profiles(object):
	"""
	UVMM profiles.
	"""

	PROFILE_RDN = 'cn=Profiles,cn=Virtual Machine Manager'
	VIRTTECH_MAPPING = {
		'kvm-hvm': _('Full virtualization (KVM)'),
	}

	@staticmethod
	def _udm2json(data):
		"""
		Convert to UDM dictionary to Python dictionary
		"""
		for key, value in data.iteritems():
			if key in ('vnc', 'pvcdrom', 'pvinterface', 'pvdisk', 'advkernelconf'):
				yield (key, value in ('1', 'TRUE'))
			elif key in ('cpus',):
				yield (key, int(value))
			else:
				yield (key, value)

	@machine_connection(write=False)
	def read_profiles(self, ldap_connection=None, ldap_position=None):
		"""
		Read all profiles from LDAP.
		"""
		base = "%s,%s" % (Profiles.PROFILE_RDN, ldap_position.getDn())
		res = ()
		if ldap_connection is not None:
			try:
				res = uvmm_profile.lookup(
					None,
					ldap_connection,
					'',
					base=base,
					scope='sub',
					required=False,
					unique=False
				)
			except udm_error as exc:
				MODULE.error("Failed to read profiles: %s" % (exc,))
		self.profiles = dict(
			(obj.dn, dict(self._udm2json(obj.info)))
			for obj in res
		)
		MODULE.info("read %d profiles from LDAP" % (len(self.profiles),))

	@simple_response
	def profile_query(self, nodeURI):
		"""
		Returns a list of profiles matching the given host.
		"""
		uri = urlsplit(nodeURI)
		tech = 'kvm' if uri.scheme == 'qemu' else uri.scheme
		MODULE.info("profile/query.tech=%s" % (tech,))

		return [
			{'id': dn, 'label': profile['name'], 'data': profile}
			for (dn, profile) in self.profiles.iteritems()
			if profile['virttech'].startswith(tech)
		]

	@simple_response
	def profile_get(self, profileDN):
		"""
		Returns one profile.
		"""
		try:
			return self.profiles[profileDN]
		except LookupError:
			raise UMC_Error(_('Unknown profile %s') % (profileDN,))
