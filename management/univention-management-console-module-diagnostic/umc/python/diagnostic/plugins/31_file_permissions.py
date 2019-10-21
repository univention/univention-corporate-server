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

import os
import pwd
import grp
import stat
import glob
from collections import namedtuple
from univention.management.console.log import MODULE

import univention.config_registry
from univention.management.console.modules.diagnostic import Warning

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check file permissions')
description = _('All files ok.')
run_descr = ['Checks file permissions']


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
		return msg.format(path=self.filename, expected=':'.join(self.expected_owner), actual=':'.join(self.actual_owner))


class PermissionMismatch(CheckError):
	def __init__(self, filename, actual_mode, expected_mode):
		super(PermissionMismatch, self).__init__(filename)
		self.actual_mode = actual_mode
		self.expected_mode = expected_mode

	def __str__(self):
		msg = _('File {path!r} has mode {actual:o}, {expected:o} was expected.')
		return msg.format(path=self.filename, actual=self.actual_mode, expected=self.expected_mode)


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
			MODULE.error("%s must exist, but does not" % (path))
			return DoesNotExist(path)
		return True

	expected_owner = (owner, group)
	actual_owner = get_actual_owner(file_stat.st_uid, file_stat.st_gid)
	if expected_owner != actual_owner:
		MODULE.error("Owner mismatch: %s should be owned by %s, is actually owned by %s" % (path, expected_owner, actual_owner))
		return OwnerMismatch(path, expected_owner, actual_owner)

	actual_mode = stat.S_IMODE(file_stat.st_mode)
	if actual_mode != mode:
		MODULE.error("Permission mismatch: %s should have the permission mode %s but has the mode %s" % (path, mode, actual_mode))
		return PermissionMismatch(path, actual_mode, mode)

	return True


def file_and_permission_checks():
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	is_primary = configRegistry.get('server/role') in ('domaincontroller_master', 'domaincontroller_backup')
	is_dc = configRegistry.get('server/role').startswith('domaincontroller_')
	(host, domain) = (configRegistry.get('hostname'), configRegistry.get('domainname'))

	cf_type = namedtuple('check_file_kwargs', ('path', 'owner', 'group', 'mode', 'must_exist'))

	check_file_args = [
		cf_type('/etc/ldap.secret', 'root', 'DC Backup Hosts', 0o640, must_exist=is_primary),
		cf_type('/etc/machine.secret', 'root', 'root', 0o600, must_exist=True),
		cf_type('/etc/pam_ldap.secret', 'root', 'root', 0o600, must_exist=True),
		cf_type('/etc/idp-ldap-user.secret', 'root', 'DC Backup Hosts', 0o640, must_exist=is_primary),
		cf_type('/etc/libnss-ldap.conf', 'messagebus', 'root', 0o440, must_exist=True),
		cf_type('/var/run/slapd/ldapi', 'root', 'root', 0o700, False),
		cf_type('/etc/univention/ssl', 'root', 'DC Backup Hosts' if is_dc else 'root', 0o755, must_exist=True),
		cf_type('/etc/univention/ssl/openssl.cnf', 'root', 'DC Backup Hosts', 0o660, must_exist=is_primary),
		cf_type('/etc/univention/ssl/password', 'root', 'DC Backup Hosts', 0o660, must_exist=is_primary),
		cf_type('/etc/univention/ssl/ucsCA', 'root', 'DC Backup Hosts' if is_dc else 'root', 0o775 if is_dc else 0o755, must_exist=True),
		cf_type('/etc/univention/ssl/ucs-sso.{}'.format(domain), 'root', 'DC Backup Hosts', 0o750, must_exist=is_primary),
		cf_type('/etc/univention/ssl/{}.{}'.format(host, domain), '{}$'.format(host) if is_primary else 'root', 'DC Backup Hosts' if is_dc else 'root', 0o750, must_exist=True),
		cf_type('/var/lib/univention-self-service-passwordreset-umc/memcached.socket', 'self-service-umc', 'nogroup', 0o600, False),
		cf_type('/var/run/univention-saml/memcached.socket', 'samlcgi', 'nogroup', 0o700, False),
		cf_type('/var/run/uvmm.socket', 'root', 'root', 0o755, False),
		cf_type('/var/cache/univention-ad-connector', 'root', 'root', 0o755, False),
		cf_type('/var/cache/univention-appcenter', 'root', 'root', 0o755, False),
		cf_type('/var/cache/univention-bind-proxy', 'root', 'root', 0o755, False),
		cf_type('/var/cache/univention-config', 'root', 'root', 0o755, False),
		cf_type('/var/cache/univention-system-setup', 'root', 'root', 0o711, False),
		cf_type('/var/cache/univention-directory-listener', 'root', 'root', 0o755, False),
		cf_type('/var/cache/univention-directory-reports', 'root', 'root', 0o755, False),
		cf_type('/var/cache/univention-management-console', 'root', 'root', 0o755, False),
		cf_type('/var/cache/univention-management-console-module-diagnostic', 'root', 'root', 0o755, False),
		cf_type('/var/cache/univention-printserver', 'root', 'root', 0o755, False),
		cf_type('/var/cache/univention-samba4', 'root', 'root', 0o755, False),
		cf_type('/var/cache/univention-quota', 'root', 'root', 0o750, False),
		cf_type('/var/cache/univention-ox', 'listener', 'root', 0o770, False),
		cf_type('/var/mail', 'root', 'mail', 0o2775, True),
		cf_type('/var/mail/systemmail', 'systemmail', 'mail', 0o600, False),
		cf_type('/var/tmp/univention-management-console-frontend', 'root', 'root', 0o755, False),
	]

	iglob_paths = [
		('/var/run/univention-management-console/*.socket', ('root', 'root', 0o700, False)),
		('/var/cache/univention-*', ('root', 'root', 0o700, False)),
		('/var/tmp/univention-management-console-frontend/*', ('root', 'root', 0o600, False)),
		('/etc/univention/connector/*.sqlite', ('root', 'root', 0o644, False)),
	]

	for glob_path, args in iglob_paths:
		existing_paths = [cfa.path for cfa in check_file_args]
		for path in glob.iglob(glob_path):
			if path not in existing_paths:
				check_file_args.append(cf_type(path, *args))

	saml_key = configRegistry.get('saml/idp/certificate/privatekey')
	if saml_key:
		check_file_args.append(cf_type(saml_key, 'root', 'samlcgi', 0o640, must_exist=True))

	for kwarg in check_file_args:
		yield check_file(*kwarg)


def run(_umc_instance):
	error_descriptions = [str(error) for error in file_and_permission_checks() if isinstance(error, CheckError)]
	if error_descriptions:
		raise Warning(description='\n'.join(error_descriptions))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
