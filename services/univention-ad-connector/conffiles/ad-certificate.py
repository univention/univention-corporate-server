# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  this baseconfig script automatically generates the SSL certificate for the AD host
#
# Copyright 2004-2019 Univention GmbH
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

import os
import pipes

ad_var = 'connector/ad/ldap/host'
ssl_path = '/etc/univention/ssl'

cert_cmd = '/usr/sbin/univention-certificate'
cert_log = '/var/log/univention/ad-connector-certificate.log'


def handler(configRegistry, changes):
	new = configRegistry.get(ad_var, '')
	path = os.path.join(ssl_path, new)
	if new and not os.path.exists(path):
		os.system('%s new -name %s >> %s 2>&1' % (cert_cmd, pipes.quote(new), cert_log))
