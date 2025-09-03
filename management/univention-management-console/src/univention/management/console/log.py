#
# Univention Management Console
#  logging module for UMC
#
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Logging
=======

This module provides a wrapper for univention.debug
"""

import grp
import logging
import os

import univention.debug as ud
import univention.logging
from univention.management.console.config import ucr


# no exceptions from logging
# otherwise shutdown the server will raise an exception that the logging stream could not be closed
logging.raiseExceptions = False

_debug_ready = False
_debug_loglevel = 2


def _reset_debug_loglevel():
    global _debug_loglevel
    ucr.load()
    _debug_loglevel = max(ucr.get_int('umc/server/debug/level', 2), ucr.get_int('umc/module/debug/level', 2))


_reset_debug_loglevel()


def log_init(filename, log_level=2, log_pid=None):
    """
    Initializes Univention debug.

    :param str filename: The filename just needs to be a relative name. The directory /var/log/univention/ is prepended and the suffix '.log' is appended.
    :param int log_level: log level to use (1-4)
    :param bool log_pid: Prefix log message with process ID
    """
    if not os.path.isabs(filename) and filename not in {'stdout', 'stderr'}:
        filename = '/var/log/univention/%s.log' % filename

    # basic config is not able to return the fd, so we do it here
    fd = CORE.init(filename, ud.FLUSH, ud.NO_FUNCTION)
    univention.logging.basicConfig(
        filename=filename,
        log_pid=log_pid,
        univention_debug_level=log_level,
        univention_debug_flush=True,
        univention_debug_function=False,
        univention_debug_categories=('MAIN', 'LDAP', 'NETWORK', 'SSL', 'ADMIN', 'MODULE', 'AUTH', 'PARSER', 'LOCALE', 'ACL', 'RESOURCES', 'PROTOCOL'),
    )
    if filename not in ('stdout', 'stderr', '/dev/stdout', '/dev/stderr'):
        adm = grp.getgrnam('adm')
        os.fchown(fd.fileno(), 0, adm.gr_gid)
        os.fchmod(fd.fileno(), 0o640)
    CORE.root.removeHandler(fallbackLoggingHandler)

    return fd


def log_set_level(level=0):
    """
    Sets the log level for all components.

    :param int level: log level to set
    """
    for _component in (CORE, NETWORK, CRYPT, UDM, MODULE, AUTH, PARSER, LOCALE, ACL, RESOURCES, PROTOCOL):
        CORE.set_ud_level(level)


def log_reopen():
    """Reopenes the logfile and reset the current loglevel"""
    CORE.reopen()
    _reset_debug_loglevel()
    log_set_level(_debug_loglevel)


CORE = logging.getLogger('MAIN')
NETWORK = logging.getLogger('NETWORK')
CRYPT = logging.getLogger('SSL')
UDM = logging.getLogger('ADMIN')
MODULE = logging.getLogger('MODULE')
AUTH = logging.getLogger('AUTH')
PARSER = logging.getLogger('PARSER')
LOCALE = logging.getLogger('LOCALE')
ACL = logging.getLogger('ACL')
RESOURCES = logging.getLogger('RESOURCES')
PROTOCOL = logging.getLogger('PROTOCOL')

fallbackLoggingHandler = logging.StreamHandler()
fallbackLoggingHandler.setFormatter(logging.Formatter('%(asctime)s.%(msecs)03d ( %(levelname)-7s ) : %(message)s', '%d.%m.%y %H:%M:%S'))
CORE.root.setLevel(logging.DEBUG)
CORE.root.addHandler(fallbackLoggingHandler)
