#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  Package functions
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
#

from logging import Handler
from contextlib import contextmanager

from univention.lib.package_manager import PackageManager, LockError  # LockError is actually imported from other files!

from univention.appcenter.log import get_base_logger
from univention.appcenter.utils import call_process


package_logger = get_base_logger().getChild('packages')


class _PackageManagerLogHandler(Handler):

	def emit(self, record):
		if record.name.startswith('packagemanager.dpkg'):
			if isinstance(record.msg, basestring):
				record.msg = record.msg.rstrip() + '\r'
			if record.name.startswith('packagemanager.dpkg.percentage'):
				record.levelname = 'DEBUG'
				record.levelno = 10


def get_package_manager():
	if get_package_manager._package_manager is None:
		package_manager = PackageManager(lock=False)
		package_manager.set_finished()  # currently not working. accepting new tasks
		package_manager.logger.parent = get_base_logger()
		log_filter = _PackageManagerLogHandler()
		package_manager.logger.addHandler(log_filter)
		get_package_manager._package_manager = package_manager
	return get_package_manager._package_manager
get_package_manager._package_manager = None


def reload_package_manager():
	if get_package_manager._package_manager is not None:
		get_package_manager().reopen_cache()


def packages_are_installed(pkgs, strict=True):
	package_manager = get_package_manager()
	if strict:
		return all(package_manager.is_installed(pkg) for pkg in pkgs)
	else:
		# app.is_installed(package_manager, strict=True) uses
		# apt_pkg.CURSTATE. Not desired when called during
		# installation of umc-module-appcenter together with
		# serveral other (app relevant) packages; for example
		# in postinst or joinscript (on master).
		# see Bug #33535 and Bug #31261
		for pkg_name in pkgs:
			try:
				pkg = package_manager.get_package(pkg_name, raise_key_error=True)
			except KeyError:
				return False
			else:
				if not pkg.is_installed:
					return False
		return True


@contextmanager
def package_lock(reset):
	try:
		with get_package_manager().locked(reset_status=reset, set_finished=reset):
			yield
	except LockError:
		package_logger.warn('Could not aquire lock!')
		raise


def install_packages_dry_run(pkgs, with_dist_upgrade):
	package_manager = get_package_manager()
	to_install = package_manager.get_packages(pkgs)
	if with_dist_upgrade:
		package_manager.cache.upgrade(dist_upgrade=True)
	package_changes = get_package_manager().mark(to_install, [], dry_run=True)
	return dict(zip(['install', 'remove', 'broken'], package_changes))


def install_packages(pkgs, with_dist_upgrade):
	with package_lock(reset=False):
		return get_package_manager().commit(install=pkgs, dist_upgrade=with_dist_upgrade)


def remove_packages_dry_run(pkgs, with_auto_remove):
	package_manager = get_package_manager()
	reload_package_manager()
	to_uninstall = package_manager.get_packages(pkgs)
	for package in to_uninstall:
		package.mark_delete()
	packages = [pkg.name for pkg in package_manager.packages() if pkg.marked_delete or (with_auto_remove and pkg.is_auto_removable)]
	reload_package_manager()
	return dict(zip(['install', 'remove', 'broken'], [[], packages, []]))


def remove_packages(pkgs, with_auto_remove):
	with package_lock(reset=False):
		success = get_package_manager().commit(remove=pkgs)
		if success and with_auto_remove:
			get_package_manager().autoremove()
		return success


def dist_upgrade(pkgs):
	with package_lock(reset=False):
		return get_package_manager().dist_upgrade()


def update_packages():
	call_process(['apt-get', 'update'], logger=package_logger)
	reload_package_manager()


def mark_packages_as_manually_installed(pkgs):
	return get_package_manager().mark_auto(False, *pkgs)
