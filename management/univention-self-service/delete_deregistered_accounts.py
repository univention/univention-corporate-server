#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import argparse
import datetime
import logging
from typing import TYPE_CHECKING, NoReturn

from ldap.filter import filter_format

import univention.udm.exceptions
from univention.config_registry import ConfigRegistry
from univention.management.console.modules.passwordreset import DEREGISTRATION_TIMESTAMP_FORMATTING
from univention.udm import UDM


if TYPE_CHECKING:
    from collections.abc import Iterable


logger = logging.getLogger(__name__)


class ScriptError(Exception):
    pass


def error(msg: str) -> NoReturn:
    raise ScriptError(msg)


def get_writable_udm(binddn: str | None = None, bindpwdfile: str | None = None) -> univention.udm.udm.UDM:
    if binddn:
        if not bindpwdfile:
            error('"binddn" provided but not "bindpwdfile".')
        try:
            with open(bindpwdfile) as f:
                bindpwd = f.read().strip()
        except OSError as err:
            error('Could not open "bindpwdfile" "%s": %s' % (bindpwdfile, err))
        ucr = ConfigRegistry()
        ucr.load()
        try:
            udm = UDM.credentials(binddn, bindpwd, ucr.get('ldap/base'), ucr.get('ldap/master'), ucr.get('ldap/master/port'))
        except univention.udm.exceptions.ConnectionError as err:
            error('Could not connect to server "%s" with provided "binddn" "%s" and "bindpwdfile" "%s": %s' % (ucr.get('ldap/master'), binddn, bindpwdfile, err))
    else:
        try:
            udm = UDM.admin()
        except univention.udm.exceptions.ConnectionError as err:
            error('Could not create a writable connection to UDM on this server. Try to provide "binddn" and "bindpwdfile": %s' % (err,))
    udm.version(2)
    return udm


def get_users(deregistration_timestamp_threshold: str | None, binddn: str | None = None, bindpwdfile: str | None = None) -> Iterable[univention.udm.modules.users_user.UsersUserObject]:
    udm = get_writable_udm(binddn, bindpwdfile)
    return udm.get('users/user').search(filter_s=filter_format('(&(univentionDeregisteredThroughSelfService=TRUE)(univentionDeregistrationTimestamp<=%s))', (deregistration_timestamp_threshold,)))


def setup_logging(filename: str | None = None) -> None:
    logging.basicConfig(filename=filename, level=logging.INFO, format='%(levelname)s: %(message)s')


def main(args: argparse.Namespace) -> None:
    setup_logging(args.logfile)
    now = datetime.datetime.utcnow()
    dt = datetime.timedelta(
        days=args.timedelta_days,
        hours=args.timedelta_hours,
        minutes=args.timedelta_minutes,
        seconds=args.timedelta_seconds,
    )
    deregistration_timestamp_threshold = datetime.datetime.strftime(now - dt, DEREGISTRATION_TIMESTAMP_FORMATTING)
    logger.info('Deleting users with univentionDeregisteredThroughSelfService=TRUE whose univentionDeregistrationTimestamp is older than %s', dt)
    users_found = False
    for user in get_users(deregistration_timestamp_threshold, args.binddn, args.bindpwdfile):
        users_found = True
        if args.dry_run:
            logger.info('dry-run: Deleting %s', user)
        else:
            logger.info('Deleting %s', user)
            user.delete()
    if not users_found:
        logger.info('No users need to be deleted')


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
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
        logger.error(err)
