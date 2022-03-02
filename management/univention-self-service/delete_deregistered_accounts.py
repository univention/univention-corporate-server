#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2020-2022 Univention GmbH
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
import datetime
import logging
from ldap.filter import filter_format

from univention.udm import UDM
import univention.udm.exceptions
from univention.config_registry import ConfigRegistry
from univention.management.console.modules.passwordreset import DEREGISTRATION_TIMESTAMP_FORMATTING


class ScriptError(Exception):
	pass


def error(msg):
	# type: (str) -> NoReturn
	raise ScriptError(msg)


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


def get_users(deregistration_timestamp_threshold, binddn=None, bindpwdfile=None):
	# type: (Optional[str], Optional[str], Optional[str]) -> Iterable[univention.udm.modules.users_user.UsersUserObject]
	udm = get_writable_udm(binddn, bindpwdfile)
	return udm.get('users/user').search(filter_s=filter_format('(&(univentionDeregisteredThroughSelfService=TRUE)(univentionDeregistrationTimestamp<=%s))', (deregistration_timestamp_threshold,)))


def setup_logging(filename=None):
	# type: (Optional[str]) -> None
	logging.basicConfig(filename=filename, level=logging.INFO, format='%(levelname)s: %(message)s')


def main(args):
	# type: (argparse.Namespace) -> None
	setup_logging(args.logfile)
	now = datetime.datetime.utcnow()
	dt = datetime.timedelta(
		days=args.timedelta_days,
		hours=args.timedelta_hours,
		minutes=args.timedelta_minutes,
		seconds=args.timedelta_seconds
	)
	deregistration_timestamp_threshold = datetime.datetime.strftime(now - dt, DEREGISTRATION_TIMESTAMP_FORMATTING)
	logging.info('Deleting users with univentionDeregisteredThroughSelfService=TRUE whose univentionDeregistrationTimestamp is older than {}'.format(dt))
	users_found = False
	for user in get_users(deregistration_timestamp_threshold, args.binddn, args.bindpwdfile):
		users_found = True
		if args.dry_run:
			logging.info('dry-run: Deleting {}'.format(user))
		else:
			logging.info('Deleting {}'.format(user))
			user.delete()
	if not users_found:
		logging.info('No users need to be deleted')


def parse_args(args=None):
	# type: (Optional[List[str]]) -> argparse.Namespace
	parser = argparse.ArgumentParser(description='Delete users/user objects with univentionDeregisteredThroughSelfService=TRUE whose univentionDeregistrationTimestamp is older than specified timedelta')
	parser.add_argument("--dry-run", action="store_true", help='Only log the users that would be deleted')
	parser.add_argument("--logfile", help='Path to a logfile')
	parser.add_argument("--timedelta-days", type=int, default=0, help='Delete the user if univentionDeregistrationTimestamp is older than TIMEDELTA_DAYS days.')
	parser.add_argument("--timedelta-hours", type=int, default=0, help='Delete the user if univentionDeregistrationTimestamp is older than TIMEDELTA_HOURS hours.')
	parser.add_argument("--timedelta-minutes", type=int, default=0, help='Delete the user if univentionDeregistrationTimestamp is older than TIMEDELTA_MINUTES minutes.')
	parser.add_argument("--timedelta-seconds", type=int, default=0, help='Delete the user if univentionDeregistrationTimestamp is older than TIMEDELTA_SECONDS seconds.')
	parser.add_argument("--binddn", help='The DN that is used to create a writable UDM connection.')
	parser.add_argument("--bindpwdfile", help='Path to the file that contains the password for --binddn.')
	return parser.parse_args(args)


if __name__ == '__main__':
	try:
		main(parse_args())
	except ScriptError as err:
		logging.error(err)
