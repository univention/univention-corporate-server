# Univention SAML
# Listener module to set up SAML IdP configuration
#
# Copyright 2018-2021 Univention GmbH
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

from typing import Dict, Optional  # noqa F401

import listener
import univention.debug as ud
from univention.config_registry.frontend import ConfigRegistry, ucr_update

name = 'univention-saml-idp-config'
description = 'Replication of identity provider settings'
filter = '(objectClass=univentionSAMLIdpConfig)'

LDAP_UCR_MAPPING = {
	'LdapGetAttributes': 'saml/idp/ldap/get_attributes',
}


def handler(dn, new, old):
	# type: (str, dict, dict) -> None
	ucr = ConfigRegistry()
	ucr.load()
	idp_config_objectdn = ucr.get('saml/idp/configobject', 'id=default-saml-idp,cn=univention,%(ldap/base)s' % ucr)

	if idp_config_objectdn == dn:
		changes = {}  # type: Dict[str, Optional[str]]
		for key, ucrv in LDAP_UCR_MAPPING.items():
			if key in new:
				changes[ucrv] = ", ".join("'%s'" % (x.decode('ASCII'),) for x in new[key])
			else:
				changes[ucrv] = None

		if changes:
			with listener.SetUID(0):
				ucr_update(ucr, changes)

	else:
		ud.debug(ud.LISTENER, ud.WARN, 'An IdP config object was modified, but it is not the object the listener is configured for (%s). Ignoring changes. DN of modified object: %r' % (idp_config_objectdn, dn))
