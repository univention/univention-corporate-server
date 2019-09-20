#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2016-2019 Univention GmbH
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

import socket
import urlparse
import univention.config_registry
from univention.management.console.modules.diagnostic import Warning, MODULE

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check resolving repository servers')
description = _('No problems were found while resolving update repositories.')
links = [{
	'name': 'sdb',
	'href': _('http://sdb.univention.de/1298'),
	'label': _('Univention Support Database - DNS Server on DC does not resolve external names')
}]
run_descr = ['Checks resolving repository servers']


def repositories():
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	if configRegistry.is_true('repository/online', True):
		yield configRegistry.get('repository/online/server', 'updates.software-univention.de/')
		yield configRegistry.get('repository/app_center/server', 'appcenter.software-univention.de')


def test_resolve(url):
	parsed = urlparse.urlsplit(url if '//' in url else '//' + url)
	MODULE.process("Trying to resolve address of repository server %s" % (parsed.hostname))
	MODULE.process("Similar to running: host %s" % (parsed.hostname))

	try:
		socket.getaddrinfo(parsed.hostname, parsed.scheme)
	except socket.gaierror:
		return False
	return True


def unresolvable_repositories():
	for repository in repositories():
		if not test_resolve(repository):
			yield repository


def run(_umc_instance):
	error_descriptions = [_('The following FQDNs were not resolvable:')]
	unresolvable = list(unresolvable_repositories())
	if unresolvable:
		error_descriptions.extend(unresolvable)
		error_descriptions.append(_('Please see {sdb} for troubleshooting DNS problems.'))
		MODULE.error('\n'.join(error_descriptions))
		raise Warning(description='\n'.join(error_descriptions))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
