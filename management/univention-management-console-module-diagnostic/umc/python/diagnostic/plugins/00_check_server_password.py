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


import ldap
import socket
import subprocess

import univention
import univention.uldap
import univention.lib.misc
import univention.admin.uldap
import univention.admin.modules as udm_modules
import univention.config_registry
from univention.config_registry import handler_set as ucr_set
from univention.config_registry import handler_unset as ucr_unset
from univention.management.console.modules.diagnostic import Critical, ProblemFixed, MODULE

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate
run_descr = ["Trying to authenticate with machine password against LDAP  Similar to running: univention-ldapsearch -LLLs base dn"]
title = _('Check machine password')
description = _('Authentication with machine password against LDAP successful.')
links = [{
	'name': 'sdb',
	'href': 'https://help.univention.com/t/manually-trigger-server-password-change/6376',
	'label': _('Univention Support Database - Manually trigger server password change')
}]


def fix_machine_password(umc_instance):
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	role = configRegistry.get('server/role')
	valid_roles = ('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
	if role in valid_roles:
		restore_machine_password(role, umc_instance.get_user_ldap_connection())

		if configRegistry.is_true('server/password/change', True):
			change_server_password(configRegistry)
		return run(umc_instance, retest=True)

	error_description = _('Unable to fix machine password on {}'.format(role))
	raise Critical(description=error_description)


def reset_password_change(umc_instance):
	MODULE.process('Resetting server/password/change')
	ucr_unset(['server/password/change'])
	return run(umc_instance, retest=True)


def reset_password_interval(umc_instance):
	MODULE.process('Resetting server/password/interval=21')
	ucr_set(['server/password/interval=21'])
	return run(umc_instance, retest=True)


actions = {
	'fix_machine_password': fix_machine_password,
	'reset_password_change': reset_password_change,
	'reset_password_interval': reset_password_interval
}


def check_machine_password(master=True):
	try:
		univention.uldap.getMachineConnection(ldap_master=master)
	except ldap.INVALID_CREDENTIALS:
		return False
	return True


def change_server_password(configRegistry):
	interval = configRegistry.get('server/password/interval', '21')
	ucr_set('server/password/interval=-1')
	try:
		cmd = ['/usr/lib/univention-server/server_password_change']
		output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
		MODULE.process('Output of server_password_change:\n%s' % (output,))
	except subprocess.CalledProcessError:
		MODULE.error('Error running server_password_change')
		MODULE.error('Output:\n%s' % (output,))
		error_descriptions = [
			_('Calling /usr/lib/univention-server/server_password_change failed.'),
			_('Please see {sdb} for more information.'),
		]
		MODULE.error(' '.join(error_descriptions))
		raise Critical(description=' '.join(error_descriptions))
	finally:
		ucr_set('server/password/interval={}'.format(interval))


def restore_machine_password(role, ldap_connection):
	with open('/etc/machine.secret') as fob:
		password = fob.read().rstrip('\n')

	if not password:
		password = univention.lib.misc.createMachinePassword()
		with open('/etc/machine.secret', 'w') as fob:
			fob.write(password)

	computers = udm_modules.get('computers/{}'.format(role))
	position = univention.admin.uldap.position(ldap_connection.base)
	udm_modules.init(ldap_connection, position, computers)
	filter_expr = ldap.filter.filter_format('(cn=%s)', (socket.gethostname(),))
	for computer in computers.lookup(None, ldap_connection, filter_expr):
		MODULE.process('Restoring password of UDM computer object')
		computer.open()
		computer['password'] = password
		computer.modify()


def run(_umc_instance, retest=False):
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	error_descriptions = list()
	buttons = [{
		'action': 'fix_machine_password',
		'label': _('Fix machine password'),
	}]

	is_master = configRegistry.get('server/role') == 'domaincontroller_master'
	if not is_master and not check_machine_password(master=False):
		error = _('Authentication against the local LDAP failed with the machine password.')
		error_descriptions.append(error)

	if not check_machine_password(master=True):
		error = _('Authentication against the master LDAP failed with the machine password.')
		error_descriptions.append(error)

	password_change = configRegistry.is_true('server/password/change', True)
	try:
		change_interval = int(configRegistry.get('server/password/interval', '21'))
	except TypeError:
		change_interval = 21

	error_change = _('Note that password rotation is disabled via the UCR variable server/password/change.')
	error_interval = _('Note that server/password/interval is set to {}.')

	if error_descriptions:
		note_sdb = _('See {sdb} for information on manual server password change.')
		error_descriptions.append(note_sdb)

		if not password_change:
			error_descriptions.append(error_change)
			buttons.append({
				'action': 'reset_password_change',
				'label': _('Set server/password/change=True'),
			})
		if change_interval < 1:
			error_descriptions.append(error_interval.format(change_interval))
			buttons.append({
				'action': 'reset_password_interval',
				'label': _('Set server/password/interval=21'),
			})

			MODULE.error('\n'.join(error_descriptions))
			raise Critical(description=' '.join(error_descriptions), buttons=buttons)
	if retest:
		raise ProblemFixed(buttons=[])


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
