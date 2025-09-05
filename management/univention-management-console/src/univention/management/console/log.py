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

import tornado

import univention.debug as ud
import univention.logging
from univention.logging import Structured
from univention.management.console.config import ucr


# no exceptions from logging
# otherwise shutdown the server will raise an exception that the logging stream could not be closed
logging.raiseExceptions = False

_debug_ready = False
_debug_loglevel = 2


class UMCModuleFilter(logging.Filter):

    def __init__(self, umcmodule):
        self.umcmodule = umcmodule
        super().__init__()

    def filter(self, record):
        record.umcmodule = self.umcmodule
        return True


def _reset_debug_loglevel():
    global _debug_loglevel
    ucr.load()
    _debug_loglevel = max(ucr.get_int('umc/server/debug/level', 2), ucr.get_int('umc/module/debug/level', 2))


_reset_debug_loglevel()


def log_init(filename, log_level=2, log_pid=None, **kwargs):
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
        **kwargs,
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


def prepare_handler(handler: logging.Handler, structured_logging=False):
    if structured_logging:
        handler.setFormatter(univention.logging.StructuredFormatter())
    else:
        handler.setFormatter(tornado.log.LogFormatter(fmt='%(color)s%(asctime)s  %(levelname)10s      (%(process)9d) :%(end_color)s %(message)s', datefmt='%d.%m.%y %H:%M:%S'))


def log_reopen():
    """Reopenes the logfile and reset the current loglevel"""
    CORE.reopen()
    _reset_debug_loglevel()
    log_set_level(_debug_loglevel)


CORE = Structured(logging.getLogger('MAIN'))
NETWORK = Structured(logging.getLogger('NETWORK'))
CRYPT = Structured(logging.getLogger('SSL'))
UDM = Structured(logging.getLogger('ADMIN'))
MODULE = Structured(logging.getLogger('MODULE'))
AUTH = Structured(logging.getLogger('AUTH'))
PARSER = Structured(logging.getLogger('PARSER'))
LOCALE = Structured(logging.getLogger('LOCALE'))
ACL = Structured(logging.getLogger('ACL'))
RESOURCES = Structured(logging.getLogger('RESOURCES'))
PROTOCOL = Structured(logging.getLogger('PROTOCOL'))

fallbackLoggingHandler = logging.StreamHandler()
fallbackLoggingHandler.setFormatter(univention.logging.StructuredFormatter(with_date_prefix=True))
CORE.root.setLevel(logging.DEBUG)
CORE.root.addHandler(fallbackLoggingHandler)
