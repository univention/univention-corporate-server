#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017-2019 Univention GmbH
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

import psutil

import univention.uldap

import univention.config_registry
from univention.management.console.modules.diagnostic import Critical, MODULE
from univention.management.console.modules.diagnostic import util

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check Heimdal KDC on Samba 4 DC')
description = _('Samba 4 KDC running.')
umc_modules = [{'module': 'services'}]
run_descr = ['This can be checked by running: samba-tool processes']


def samba_kdc_running():
	try:
		import samba.messaging
	except ImportError:
		return False
	msg = samba.messaging.Messaging()
	try:
		ids = msg.irpc_servers_byname('kdc_server')
	except KeyError:
		return False
	return bool(ids)


def is_heimdal_kdc_running():
	kdc_paths = ('/usr/lib/heimdal-servers/kdc', '/usr/lib/heimdal-servers/kpasswdd')
	process_paths = (p.exe() for p in psutil.process_iter())
	return any(path in kdc_paths for path in process_paths)


def is_kerberos_autostart_disabled():
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()
	return configRegistry.is_false('kerberos/autostart')


def run(_umc_instance):
	error = _('This is a Samba 4 DC, but `samba-tool processes` reports no `kdc_server`.')
	heimdal_error = _('This may be, because Heimdal KDC seems to be running.')
	autostart_error = _('This may be, because `kerberos/autostart` is not disabled.')
	solution = _('You may want to stop Heimdal KDC and restart Samba via {services}')

	if util.is_service_active('Samba 4') and not samba_kdc_running():
		error_descriptions = [error]
		if is_heimdal_kdc_running():
			error_descriptions.append(heimdal_error)
			if not is_kerberos_autostart_disabled():
				error_descriptions.append(autostart_error)
			error_descriptions.append(solution)
		MODULE.error('n'.join(error_descriptions))
		raise Critical('\n'.join(error_descriptions))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
