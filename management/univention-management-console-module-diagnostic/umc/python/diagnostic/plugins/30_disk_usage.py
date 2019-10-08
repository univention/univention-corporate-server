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

import univention.config_registry
from univention.management.console.modules.diagnostic import Warning, Critical, MODULE

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check free disk space')
description = _('Enough free disk space available.')

DISK_USAGE_THRESHOLD = 90
run_descr = ['Checks if enough free disk space is available']


def mount_points():
	for dp in psutil.disk_partitions():
		if dp.mountpoint != '/var/lib/docker/overlay':
			yield dp.mountpoint


def high_disk_usage():
	high = ((mp, psutil.disk_usage(mp).percent) for mp in mount_points())
	return {mp: pc for (mp, pc) in high if pc > DISK_USAGE_THRESHOLD}


def local_repository_exists():
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()
	return configRegistry.is_true('local/repository', False)


def is_varlog_own_partition():
	mp = set(mount_points())
	return '/var' in mp or '/var/log' in mp


def high_log_levels():
	def is_high(variable, default):
		return lambda ucr: int(ucr.get(variable, default)) > default

	def is_on(variable):
		return lambda ucr: ucr.is_true(variable, False)

	checks = (
		is_high('connector/debug/function', 0),
		is_high('connector/debug/level', 2),
		is_high('samba/debug/level', 33),
		is_high('directory/manager/cmd/debug/level', 0),
		is_high('dns/debug/level', 0),
		is_high('dns/dlz/debug/level', 0),
		is_high('ldap/debug/level', 0),
		is_high('listener/debug/level', 2),
		is_high('mail/postfix/ldaptable/debuglevel', 0),
		is_high('notifier/debug/level', 1),
		is_high('nscd/debug/level', 0),
		is_high('stunnel/debuglevel', 4),
		is_high('umc/module/debug/level', 2),
		is_high('umc/server/debug/level', 2),
		is_high('grub/loglevel', 0),
		is_high('mail/postfix/smtp/tls/loglevel', 0),
		is_high('mail/postfix/smtpd/tls/loglevel', 0),
		is_on('kerberos/defaults/debug'),
		is_on('mail/postfix/smtpd/debug'),
		is_on('samba4/sysvol/sync/debug'),
		is_on('aml/idp/ldap/debug'),
		is_on('saml/idp/log/debug/enabled'),
		is_on('pdate/check/boot/debug'),
		is_on('update/check/cron/debug'),
		lambda ucr: ucr.get('apache2/loglevel', 'warn') in ('notice', 'info', 'debug')
	)

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()
	return any(check(configRegistry) for check in checks)


def solutions():
	yield _('You may want to uninstall software via {appcenter:appcenter}.')
	if not is_varlog_own_partition():
		yield _('You may want to move /var/log to another disk or storage.')
	if local_repository_exists():
		yield _('You may want to move the local repository to another server.')


def run(_umc_instance):
	high = high_disk_usage()
	tmpl = _('- Disk for mountpoint %(mp)s is %(pc)s%% full.')
	disk_errors = [tmpl % {'mp': mp, 'pc': pc} for (mp, pc) in high.items()]

	problem_on_root = '/' in high
	problem_on_varlog = '/var/log' in high or '/var' in high or \
		(problem_on_root and not is_varlog_own_partition())

	if disk_errors:
		umc_modules = [{'module': 'appcenter', 'flavor': 'appcenter'}]
		error_descriptions = [_('Some disks are nearly full:')]
		error_descriptions.extend(disk_errors)

		if problem_on_root:
			error_descriptions.append('\n'.join(solutions()))

		if problem_on_varlog and high_log_levels():
			lvl_errors = (_('You have configured some high log levels.'), _('You may want to reset them via {ucr}.'))
			umc_modules.append({'module': 'ucr'})
			error_descriptions.append(' '.join(lvl_errors))

		if problem_on_root:
			MODULE.error('\n'.join(error_descriptions))
			raise Critical('\n'.join(error_descriptions), umc_modules=umc_modules)
		raise Warning('\n'.join(error_descriptions), umc_modules=umc_modules)


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
