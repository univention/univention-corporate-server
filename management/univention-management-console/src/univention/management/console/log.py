# -*- coding: utf-8 -*-
#
# Univention Management Console
#  logging module for UMC
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2011-2024 Univention GmbH
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

"""
Logging
=======

This module provides a wrapper for univention.debug
"""

import functools
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

for _logger in (CORE, NETWORK, CRYPT, UDM, MODULE, AUTH, PARSER, LOCALE, ACL, RESOURCES, PROTOCOL):
    _logger.process = _logger.info
    _logger.info = _logger.debug
    _logger.debug = functools.partial(lambda _logger, msg, *args, **kwargs: _logger.log(1, msg, *args, **kwargs), _logger)

fallbackLoggingHandler = logging.StreamHandler()
fallbackLoggingHandler.setFormatter(logging.Formatter('%(asctime)s.%(msecs)03d ( %(levelname)-7s ) : %(message)s', '%d.%m.%y %H:%M:%S'))
CORE.root.setLevel(logging.DEBUG)
CORE.root.addHandler(fallbackLoggingHandler)
