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

import contextvars
import grp
import logging
import os

import univention.debug as ud
import univention.logging
from univention.logging import Structured
from univention.management.console.config import ucr


ALL_LOGGERS = ('MAIN', 'NETWORK', 'SSL', 'ADMIN', 'LDAP', 'MODULE', 'AUTH', 'PARSER', 'LOCALE', 'ACL', 'RESOURCES', 'PROTOCOL', 'tornado')

# TODO: still required with new logging?
# no exceptions from logging
# otherwise shutdown the server will raise an exception that the logging stream could not be closed
logging.raiseExceptions = False

_debug_loglevel = 2


class RequestFilter(logging.Filter):

    request_context = contextvars.ContextVar("request")

    def __init__(self, umcmodule):
        self.umcmodule = umcmodule
        super().__init__()

    def filter(self, record):
        record.umcmodule = self.umcmodule
        try:
            request_context = self.request_context.get()
        except LookupError:
            request_context = {}
        record.request_id = request_context.get('request_id', '-')
        if dn := request_context.get('requester_dn'):
            record.requester_dn = dn
        if ip := request_context.get('requester_ip'):
            record.requester_ip = ip
        if hostname := request_context.get('requester_hostname'):
            record.requester_hostname = hostname

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


def log_reopen():
    """Reopenes the logfile and reset the current loglevel"""
    CORE.reopen()
    _reset_debug_loglevel()
    log_set_level(_debug_loglevel)


def init_request_context_logging(umc_module):
    request_filter = RequestFilter(umc_module)
    add_filter(request_filter)


def add_filter(filter_, logger_names=ALL_LOGGERS):
    for name in logger_names:
        for handler in logging.getLogger(name).handlers:
            if filter_ not in handler.filters:
                handler.addFilter(filter_)


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
