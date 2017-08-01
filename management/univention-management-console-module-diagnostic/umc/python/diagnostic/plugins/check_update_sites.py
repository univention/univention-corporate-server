#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2016-2017 Univention GmbH
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
# <http://www.gnu.org/licenses/>.

import requests
import univention.config_registry

from univention.management.console.modules.diagnostic import Warning

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check for errors with update sites')
description = _('No new problems were found while connecting to updates sites')


def run():
	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()
	description_items = []
	sites = ucr.get("repository/credentials/Univention Software Repository/uris").split(" ")
	for site in sites:
		uri = "https://%s" % (site)
		code = requests.get(uri).status_code
		if not code == 200:
			description_items.append("Errorcode %s during connecting to %s" % (code, uri))
	if len(description_items) > 0:
		description = "\n".join(description_items)
		raise Warning(description)


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
