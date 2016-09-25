#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  Package functions
#
# Copyright 2016 Univention GmbH
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

from univention.lib.package_manager import PackageManager

from univention.appcenter.log import get_base_logger


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


def install_packages(pkgs):
	with get_package_manager().locked(reset_status=True, set_finished=True):
		return get_package_manager().commit(install=pkgs)


def update_packages():
	return get_package_manager().update()


def mark_packages_as_manually_installed(pkgs):
	return get_package_manager().mark_auto(False, *pkgs)
