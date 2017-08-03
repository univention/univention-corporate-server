#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017 Univention GmbH
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

import os
import pwd
import grp
import stat
import glob

import univention.config_registry
from univention.management.console.modules.diagnostic import Warning

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check file permissions')
description = _('All files ok.')


class CheckError(Exception):
	def __init__(self, filename):
		self.filename = filename


class DoesNotExist(CheckError):
	def __str__(self):
		return _('File {path!r} does not exist.'.format(path=self.filename))


class OwnerMismatch(CheckError):
	def __init__(self, filename, expected_owner, actual_owner):
		super(OwnerMismatch, self).__init__(filename)
		self.expected_owner = expected_owner
		self.actual_owner = actual_owner

	def __str__(self):
		msg = _('File {path!r} has owner {actual!r} while {expected!r} was expected.')
		return msg.format(path=self.filename,
			expected=':'.join(self.expected_owner),
			actual=':'.join(self.actual_owner))


class PermissionMismatch(CheckError):
	def __init__(self, filename, actual_mode, expected_mode):
		super(PermissionMismatch, self).__init__(filename)
		self.actual_mode = actual_mode
		self.expected_mode = expected_mode

	def __str__(self):
		msg = _('File {path!r} has mode {actual:o}, {expected:o} was expected.')
		return msg.format(path=self.filename, actual=self.actual_mode,
			expected=self.expected_mode)


def get_actual_owner(uid, gid):
	try:
		name = pwd.getpwuid(uid).pw_name
	except KeyError:
		name = str(uid)
	try:
		group = grp.getgrgid(gid).gr_name
	except KeyError:
		group = str(gid)
	return (name, group)


def check_file(path, owner, group, mode, must_exist=False):
	try:
		file_stat = os.stat(path)
	except EnvironmentError:
		if must_exist:
			return DoesNotExist(path)
		return True

	expected_owner = (owner, group)
	actual_owner = get_actual_owner(file_stat.st_uid, file_stat.st_gid)
	if expected_owner != actual_owner:
		return OwnerMismatch(path, expected_owner, actual_owner)

	actual_mode = stat.S_IMODE(file_stat.st_mode)
	if actual_mode != mode:
		return PermissionMismatch(path, actual_mode, mode)

	return True


def file_and_permission_checks():
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	is_master = configRegistry.get('server/role') == 'domaincontroller_master'
	is_member = configRegistry.get('server/role') == 'memberserver'

	yield check_file('/etc/ldap.secret', 'root', 'DC Backup Hosts', 0640, must_exist=is_master)
	yield check_file('/etc/machine.secret', 'root', 'root', 0600, must_exist=True)
	yield check_file('/etc/pam_ldap.secret', 'root', 'root', 0600, must_exist=True)
	yield check_file('/etc/idp-ldap-user.secret', 'root', 'DC Backup Hosts', 0640, must_exist=is_master)
	yield check_file('/etc/libnss-ldap.conf', 'messagebus', 'root', 0440, must_exist=True)
	yield check_file('/var/run/slapd/ldapi', 'root', 'root', 0700)

	(host, domain) = (configRegistry.get('hostname'), configRegistry.get('domainname'))
	yield check_file('/etc/univention/ssl', 'root', 'root' if is_member else 'DC Backup Hosts', 0755, must_exist=True)
	yield check_file('/etc/univention/ssl/openssl.cnf', 'root', 'DC Backup Hosts', 0660, must_exist=is_master)
	yield check_file('/etc/univention/ssl/password', 'root', 'DC Backup Hosts', 0660, must_exist=is_master)
	yield check_file('/etc/univention/ssl/ucsCA', 'root', 'root' if is_member else 'DC Backup Hosts', 0775, must_exist=True)
	yield check_file('/etc/univention/ssl/ucs-sso.{}'.format(domain), 'root', 'DC Backup Hosts', 0750, must_exist=is_master)
	yield check_file('/etc/univention/ssl/{}.{}'.format(host, domain), '{}$'.format(host) if is_master else 'root', 'DC Backup Hosts', 0750, must_exist=True)

	yield check_file('/var/lib/univention-self-service-passwordreset-umc/memcached.socket', 'self-service-umc', 'nogroup', 0600)
	yield check_file('/var/run/univention-saml/memcached.socket', 'samlcgi', 'root', 0600)
	yield check_file('/var/run/uvmm.socket', 'root', 'root', 0755)
	for path in glob.iglob('/var/run/univention-management-console/*.socket'):
		yield check_file(path, 'root', 'root', 0700)

	known_mode_755 = set((
		'/var/cache/univention-appcenter',
		'/var/cache/univention-bind-proxy',
		'/var/cache/univention-config',
		'/var/cache/univention-directory-listener',
		'/var/cache/univention-directory-reports',
		'/var/cache/univention-management-console',
		'/var/cache/univention-management-console-module-diagnostic',
		'/var/cache/univention-samba4',
	))

	for path in glob.iglob('/var/cache/univention-*'):
		if path in known_mode_755:
			yield check_file(path, 'root', 'root', 0755)
		elif path == '/var/cache/univention-quota':
			yield check_file(path, 'root', 'root', 0750)
		else:
			yield check_file(path, 'root', 'root', 0700)

	yield check_file('/var/tmp/univention-management-console-frontend', 'root', 'root', 0755)

	for path in glob.iglob('/etc/univention/connector/*.sqlite'):
		yield check_file(path, 'root', 'root', 0644)

	saml_key = configRegistry.get('saml/idp/certificate/privatekey')
	if saml_key:
		yield check_file(saml_key, 'root', 'samlcgi', 0640, must_exist=True)


def run(_umc_instance):
	error_descriptions = [str(error) for error in file_and_permission_checks()
		if isinstance(error, CheckError)]
	if error_descriptions:
		raise Warning(description='\n'.join(error_descriptions))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
