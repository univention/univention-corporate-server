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

import univention.config_registry
from univention.management.console.modules.diagnostic import Warning, MODULE
from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate
run_descr = ["Checks if the output of /usr/share/univention-directory-listener/get_notifier_id.py and the value in /var/lib/univention-directory-listener/notifier_id are the same"]
title = _('Check for problems with UDN replication')
description = _('No problems found with UDN replication.')

links = [{
	'name': 'sdb',
	'href': 'https://help.univention.com/t/troubleshooting-listener-notifier/6430',
	'label': _('Univention Support Database - Troubleshooting: Listener-/Notifier')
}]


def get_id(master, cmd='GET_ID'):
	sock = socket.create_connection((master, 6669), 60.0)

	sock.send('Version: 3\nCapabilities: \n\n')
	sock.recv(100)

	sock.send('MSGID: 1\n{cmd}\n\n'.format(cmd=cmd))
	notifier_result = sock.recv(100).strip()

	(msg_id, notifier_id) = notifier_result.split('\n', 1)
	return notifier_id


def run(_umc_instance):
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	try:
		notifier_id = get_id(configRegistry.get('ldap/master'))
	except socket.error:
		MODULE.error('Error retrieving notifier ID from the UDN.')
		raise Warning(_('Error retrieving notifier ID from the UDN.'))
	else:
		with open('/var/lib/univention-directory-listener/notifier_id') as fob:
			id_from_file = fob.read().strip()

		if notifier_id != id_from_file:
			ed = [
				_('Univention Directory Notifier ID and the locally stored version differ.'),
				_('This might indicate an error or still processing transactions.')
			]
			MODULE.error('\n'.join(ed))
			raise Warning('\n'.join(ed))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
