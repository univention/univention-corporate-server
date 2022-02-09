# -*- coding: utf-8 -*-
#
# Copyright 2022 Univention GmbH
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

from univention.udm import UDM, NoObject


def handler(configRegistry, changes):
	if configRegistry.get('server/role') != "domaincontroller_master":
		print('self-service-links module can only run on role Primary Directory Node')
		return

	udm = UDM.machine().version(3)
	for key, (old, new) in changes.items():
		activated = configRegistry.is_true(None, value=new)
		name = {
			'umc/self-service/profiledata/enabled': 'self-service-my-profile',
			'umc/self-service/protect-account/backend/enabled': 'self-service-protect-account',
			'umc/self-service/passwordreset/backend/enabled': 'self-service-password-forgotten',
			'umc/self-service/account-registration/backend/enabled': 'self-service-create-account',
			'umc/self-service/account-verification/backend/enabled': 'self-service-verify-account',
			'umc/self-service/service-specific-passwords/backend/enabled': 'self-service-service-specific-passwords',
		}.get(key)
		if not name:
			continue
		try:
			obj = udm.get('portals/entry').get_by_id(name)
		except NoObject:
			continue
		obj.props.activated = activated
		obj.save()
		print(obj.dn, 'active state set to', activated)
