# -*- coding: utf-8 -*-
#
# Univention SAML
# Listener module to set up SAML configuration
#
# Copyright 2015-2021 Univention GmbH
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

from __future__ import absolute_import

from os.path import exists
from subprocess import call
from typing import Dict, Optional  # noqa F401

import listener
from univention.config_registry.frontend import ConfigRegistry, ucr_update

name = 'univention-saml-servers'
description = 'Manage ucs/server/saml-idp-server/* variables'
filter = '(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))'
attributes = ['univentionService']


def handler(dn, new, old):
	# type: (str, dict, dict) -> None
	ucr = ConfigRegistry()
	ucr.load()

	try:
		fqhn = '%s.%s' % (new['cn'][0].decode('UTF-8'), new['associatedDomain'][0].decode('ASCII'))
	except LookupError:
		return

	ucrv = 'ucs/server/saml-idp-server/%s' % (fqhn,)

	changes = {}  # type: Dict[str, Optional[str]]
	if b'univention-saml' in new.get('univentionService', []):
		changes[ucrv] = fqhn
	elif b'univention-saml' in old.get('univentionService', []):
		changes[ucrv] = None

	if changes:
		with listener.SetUID(0):
			ucr_update(ucr, changes)

			path_to_cert = ucr.get('saml/idp/certificate/certificate')
			path_to_key = ucr.get('saml/idp/certificate/privatekey')
			if path_to_cert and exists(path_to_cert) and path_to_key and exists(path_to_key):
				call(['systemctl', 'restart', 'univention-saml'])
