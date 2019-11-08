# Univention SAML
# Listener module to set up SAML IdP configuration
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
import listener

import univention.debug as ud
from univention.config_registry import ConfigRegistry, handler_set, handler_unset

name = 'univention-saml-idp-config'
description = 'Replication of identity provider settings'
filter = '(objectClass=univentionSAMLIdpConfig)'

LDAP_UCR_MAPPING = {
	'LdapGetAttributes': 'saml/idp/ldap/get_attributes',
}


def handler(dn, new, old):
	ucr = ConfigRegistry()
	ucr.load()
	idp_config_objectdn = ucr.get('saml/idp/configobject', 'id=default-saml-idp,cn=univention,%s' % ucr.get('ldap/base'))
	listener.setuid(0)
	try:
		if idp_config_objectdn == new['entryDN'][0]:
			for key in LDAP_UCR_MAPPING.keys():
				if key in new:
					ucr_value = ""
					if key == 'LdapGetAttributes':
						ucr_value = "'" + "', '".join(new[key]) + "'"

					handler_set(['%s=%s' % (LDAP_UCR_MAPPING[key], ucr_value)])
				else:
					handler_unset(['%s' % LDAP_UCR_MAPPING[key]])
		else:
			ud.debug(ud.LISTENER, ud.WARN, 'An IdP config object was modified, but it is not the object the listener is configured for (%s). Ignoring changes. DN of modified object: %s' % (idp_config_objectdn, new['entryDN']))

	finally:
		listener.unsetuid()
