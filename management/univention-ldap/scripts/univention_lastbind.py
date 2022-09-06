#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention LDAP
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2022 Univention GmbH
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

from __future__ import print_function

import argparse
import ldap
import sys
from typing import List, Iterable, Optional, NoReturn

from univention.udm import UDM
import univention.udm.exceptions
from univention.config_registry import ConfigRegistry
import univention.admin.uldap


class ScriptError(Exception):
	pass


def error(msg):
	# type: (str) -> NoReturn
	raise ScriptError(msg)


def warning(msg):
	# type: (str) -> None
	print('Warning: %s' % (msg,), file=sys.stderr)


def get_ldap_connections():
	# type: () -> List[univention.admin.uldap.access]
	udm = UDM.machine().version(2)
	connections = []
	modules = ['computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave']
	for module in modules:
		for comp in udm.get(module).search():
			try:
				lo = univention.admin.uldap.access(host=comp.props.fqdn, base=udm.connection.base, binddn=udm.connection.binddn, bindpw=udm.connection.bindpw)
			except ldap.SERVER_DOWN:
				warning('Server "%s" is not reachable. The "authTimestamp" will not be read from it. Continuing.' % (comp.props.fqdn,))
			else:
				connections.append(lo)
	return connections


def get_users(binddn=None, bindpwdfile=None, only_this_user=None):
	# type: (Optional[str], Optional[str], Optional[str]) -> Iterable[univention.udm.modules.users_user.UsersUserObject]
	udm = get_writable_udm(binddn, bindpwdfile)
	if only_this_user:
		get_user = 'get' if '=' in only_this_user else 'get_by_id'
		get_user = getattr(udm.get('users/user'), get_user)
		try:
			users = [get_user(only_this_user)]
		except (univention.udm.exceptions.NoObject, univention.udm.exceptions.MultipleObjects) as err:
			error('The provided user "%s" could not be found: %s' % (only_this_user, err,))
	else:
		users = udm.get('users/user').search()
	return users


def get_youngest_timestamp(user, connections):
	# type: (univention.udm.modules.users_user.UsersUserObject, List[univention.admin.uldap.access]) -> Optional[str]
	timestamps = [timestamp.decode('ASCII') for lo in connections for timestamp in lo.getAttr(user.dn, 'authTimestamp')]
	timestamps = sorted(timestamps)
	return timestamps[-1] if len(timestamps) else None


def save_timestamp(user, timestamp=None):
	# type: (univention.udm.modules.users_user.UsersUserObject, Optional[str]) -> None
	if not timestamp:
		return
	if user.props.lastbind == timestamp:
		return
	user.props.lastbind = timestamp
	try:
		user.save()
	except univention.udm.exceptions.ModifyError as err:
		warning('Could not save new timestamp "%s" to "lastbind" extended attribute of user "%s". Continuing: %s' % (timestamp, user.dn, err,))


def update_users(binddn=None, bindpwdfile=None, only_this_user=None):
	# type: (Optional[str], Optional[str], Optional[str]) -> None
	connections = get_ldap_connections()
	for user in get_users(binddn, bindpwdfile, only_this_user):
		timestamp = get_youngest_timestamp(user, connections)
		save_timestamp(user, timestamp)


def get_writable_udm(binddn=None, bindpwdfile=None):
	# type: (Optional[str], Optional[str]) -> univention.udm.udm.UDM
	if binddn:
		if not bindpwdfile:
			error('"binddn" provided but not "bindpwdfile".')
		try:
			with open(bindpwdfile, 'r') as f:
				bindpwd = f.read().strip()
		except IOError as err:
			error('Could not open "bindpwdfile" "%s": %s' % (bindpwdfile, err,))
		ucr = ConfigRegistry()
		ucr.load()
		try:
			udm = UDM.credentials(binddn, bindpwd, ucr.get('ldap/base'), ucr.get('ldap/master'), ucr.get('ldap/master/port'))
		except univention.udm.exceptions.ConnectionError as err:
			error('Could not connect to server "%s" with provided "binddn" "%s" and "bindpwdfile" "%s": %s' % (ucr.get('ldap/master'), binddn, bindpwdfile, err,))
	else:
		try:
			udm = UDM.admin()
		except univention.udm.exceptions.ConnectionError as err:
			error('Could not create a writable connection to UDM on this server. Try to provide "binddn" and "bindpwdfile": %s' % (err,))
	udm.version(2)
	return udm


def main(args):
	# type: (argparse.Namespace) -> None
	if not args.user and not args.allusers:
		# --allusers is used as a safety net to prevent accidental execution for all users.
		raise ScriptError('Provide either --user USER or --allusers.')
	update_users(args.binddn, args.bindpwdfile, args.user)


def parse_args(args=None):
	# type: (Optional[List[str]]) -> argparse.Namespace
	parser = argparse.ArgumentParser(description='Save the youngest "authTimestamp" attribute of an user, from all reachable LDAP servers, into the "lastbind" extended attribute of the user. The "authTimestamp" attribute is set on a successful bind to an LDAP server when the "ldap/overlay/lastbind" UCR variable is set.')
	parser.add_argument("--user", help='Update the "lastbind" extended attribute of the given user. Can be either a DN or just the uid.')
	parser.add_argument("--allusers", action="store_true", help='Update the "lastbind" extended attribute of all users.')
	parser.add_argument("--binddn", help='The DN that is used to create a writable UDM connection.')
	parser.add_argument("--bindpwdfile", help='Path to the file that contains the password for --binddn.')
	return parser.parse_args(args)


if __name__ == '__main__':
	try:
		main(parse_args())
	except ScriptError as err:
		print('Error: %s' % (err,), file=sys.stderr)
