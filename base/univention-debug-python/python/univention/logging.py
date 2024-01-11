#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2022-2024 Univention GmbH
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
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
A python-logging interface compatible wrapper for logging with :py:mod:`univention.debug`

>>> import univention.logging
>>> import logging
>>> logger = logging.getLogger('MAIN').getChild(__name__)
>>> univention.logging.basicConfig(level=logging.INFO)
>>> logger.info('test')
"""

from __future__ import absolute_import

import logging

import univention.debug as ud


__all__ = ['getLogger', 'basicConfig', 'Logger', 'DebugHandler', 'LevelDependentFormatter', 'extendLogger']
for name in logging.__all__:
    if name not in __all__:
        globals()[name] = getattr(logging, name)
__all__ += logging.__all__


_LEVEL_MAPPING = {
    logging.NOTSET: ud.ALL,  # 4
    logging.DEBUG: ud.INFO,  # 3
    logging.INFO: ud.PROCESS,  # 2
    logging.WARNING: ud.WARN,  # 1
    logging.ERROR: ud.ERROR,  # 0
    logging.CRITICAL: ud.ERROR,
}
_UD_LEVEL_MAPPING = {v: k for k, v in _LEVEL_MAPPING.items()}

_LEVEL_TO_FORMAT_MAPPING = {
    logging.NOTSET: "%(pid)s%(module)s.%(funcName)s:%(lineno)d: %(prefix)s%(message)s",
    logging.DEBUG: "%(pid)s%(prefix)s%(message)s",
    logging.INFO: "%(pid)s%(prefix)s%(message)s",
    logging.WARNING: "%(pid)s%(prefix)s%(message)s",
    logging.ERROR: "%(pid)s%(prefix)s%(message)s",
    logging.CRITICAL: "%(pid)s%(prefix)s%(message)s",
}

_UD_CATEGORIES = {
    cat: name
    for name, cat in ud.__dict__.items()
    if isinstance(cat, int) and name not in ('FLUSH', 'NO_FLUSH', 'FUNCTION', 'NO_FUNCTION', 'ALL', 'INFO', 'PROCESS', 'WARN', 'ERROR') and name.isupper()
}


def _map_level_to_ud(level):  # type: (int) -> int
    """
    Map logging level to univention-debug loglevel

    >>> _map_level_to_ud(logging.ERROR)
    0
    >>> _map_level_to_ud(logging.INFO)
    2
    >>> _map_level_to_ud(logging.DEBUG)
    3
    >>> _map_level_to_ud(logging.NOTSET)
    4
    >>> _map_level_to_ud(logging.INFO - 1)
    1
    >>> _map_level_to_ud(9)
    4
    >>> _map_level_to_ud(99)
    90
    """
    level = level if level in _LEVEL_MAPPING else (level // 10) * 10
    return _LEVEL_MAPPING.get(level, level)


def _map_ud_to_level(level):  # type: (int) -> int
    """
    Map univention-debug level to logging loglevel

    >>> _map_ud_to_level(0) == logging.ERROR
    True
    >>> _map_ud_to_level(1) == logging.WARNING
    True
    >>> _map_ud_to_level(2) == logging.INFO
    True
    >>> _map_ud_to_level(3) == logging.DEBUG
    True
    >>> _map_ud_to_level(4) == logging.NOTSET
    True
    >>> _map_ud_to_level(5)
    9
    >>> _map_ud_to_level(50)
    5
    >>> _map_ud_to_level(99)
    1
    """
    if level > 4:
        return max((10, (100 - level))) // 10
    return _UD_LEVEL_MAPPING.get(level)


def _map_category_name(category):  # type: (int) -> str
    """
    >>> _map_category_name(10)
    "ADMIN"
    """
    return _UD_CATEGORIES.get(category, "<unknown>")


def getLogger(name, **kwargs):  # type: (str) -> Logger
    """
    Return a logger with the specified name, creating it if necessary.

    .. param name:
        The name of a :py:mod:`univention.debug` category
        (if not existant `ud.MAIN` will be used)

    .. warning::
        If a logger with that name already exists and is not a :py:class:`univention.logging.Logger`
        no univention-debug logger is initialized and returned.

    .. param extend:
        Whether a non univention-debug logger should be extended to be one.

    .. param univention_debug_category:
        If the logger name should differ from the univention-debug category this param can be used
        as initialization call to create the logger once.

    >>> logger = getLogger('ADMIN').getChild(__name__)
    >>> logger.init('stdout', ud.FLUSH, ud.NO_FUNCTION)
    >>> logger.setLevel(logging.WARNING)
    >>> logger.info('some info')
    >>> logger.error('some error')
    """
    klass = logging.getLoggerClass()
    logging.setLoggerClass(Logger)
    try:
        logger = logging.getLogger(name)
    finally:
        logging.setLoggerClass(klass)

    if not isinstance(logging, Logger) and kwargs.pop('extend', False):
        extendLogger(name, **kwargs)
    return logger


def extendLogger(name, **kwargs):  # type: (str) -> None
    """
    Ensure that the logger with the specified name is a univention-debug logger otherwise transform it.

    .. param name:
        The name of the logger.

    .. param univention_debug_category:
        A :py:mod:`univention.debug` category (if not given :param:`name` will be used).
        If the logger name should differ from the univention-debug category this param can be used
        as initialization call to create the logger once.

    >>> import logging
    >>> logger = logging.getLogger('myservice')
    >>> extendLogger('myservice', univention_debug_category='MAIN')
    >>> logger.init('stdout', ud.FLUSH, ud.NO_FUNCTION)
    >>> logger.setLevel(logging.WARNING)
    >>> logger.warning('some warning')
    """
    logger = logging.getLogger(name)
    if isinstance(logger, Logger):
        return
    category = kwargs.get('univention_debug_category', name)
    ud_logger = logging.getLogger(category)
    if not isinstance(ud_logger, Logger):
        ud_logger = Logger(name, **kwargs)
    logger.__dict__.update(dict(ud_logger.__dict__, name=logger.name))
    logger.__class__ = Logger


def basicConfig(
    # *  # keywords-only!
    filename='stdout',
    level=None,
    univention_debug_level=None,
    log_pid=False,
    univention_debug_flush=ud.FLUSH,
    univention_debug_function=ud.NO_FUNCTION,
    univention_debug_categories=None,
    do_exit=True,
    delay_init=False,  # until first use
    **kwargs  # ,
):
    """
    Do basic configuration for the logging system.
    Especially initialize the :py:mod:`logging` module so that it uses :py:mod:`univention.debug`:

    >>> import logging
    >>> basicConfig(level=logging.DEBUG)
    >>> logger = logging.getLogger('ADMIN').getChild(__name__)
    >>> logger.info('some info')
    """
    categories = univention_debug_categories or list(_UD_CATEGORIES.values())

    if isinstance(univention_debug_flush, bool):
        univention_debug_flush = ud.FLUSH if univention_debug_flush else ud.NO_FLUSH
    if isinstance(univention_debug_function, bool):
        univention_debug_function = ud.FUNCTION if univention_debug_function else ud.NO_FUNCTION

    if not delay_init:
        logger = getLogger(categories[0])
        logger.univention_debug_handler.init(filename, univention_debug_flush, univention_debug_function)
    for category in categories:
        logger = getLogger(category)
        if level is not None:
            logger.setLevel(level)
        elif univention_debug_level is not None:
            logger.set_ud_level(univention_debug_level)
        logger.set_log_pid(log_pid)
        logger.univention_debug_handler.do_exit = do_exit
        if delay_init:
            logger.univention_debug_handler.auto_init = True
            logger.univention_debug_handler.delay_init = delay_init
            logger.univention_debug_handler._init_args = (filename, univention_debug_flush, univention_debug_function)


class Logger(logging.Logger):
    """
    A logger which automatically adds :py:mod:`univention.debug` as logging handler.

    Can be set as global default logger via `logging.setLoggerClass(univention.logging.Logger)`.
    """

    def __init__(self, name, level=logging.NOTSET, log_pid=False, **kwargs):
        super(Logger, self).__init__(name, level=level)
        self.propagate = False
        self.univention_debug_category = getattr(ud, kwargs.get('univention_debug_category', name))
        self.univention_debug_handler = handler = DebugHandler(self.univention_debug_category, **kwargs)
        self._formatter = LevelDependentFormatter(log_pid=log_pid)
        handler.setFormatter(self._formatter)
        handler.setLevel(self.level)
        self.addHandler(handler)

    def setLevel(self, level):
        super(Logger, self).setLevel(level)
        self.univention_debug_handler.setLevel(self.level)

    def set_log_pid(self, log_pid):
        self._formatter.log_pid = log_pid

    def set_ud_level(self, level):
        self.setLevel(_map_ud_to_level(level))

    def init(self, filename='stderr', flush=ud.NO_FLUSH, function=ud.NO_FUNCTION):
        """init :py:mod:`univention.debug`. must only be called once. returns the file descriptor on success"""
        return self.univention_debug_handler.init(filename, flush, function)

    def reopen(self):
        """reopen the :py:mod:`univention.debug` logfile. must be called e.g. after log rotation."""
        level = self.getEffectiveLevel()
        self.univention_debug_handler.reopen()
        self.univention_debug_handler.setLevel(level)

    def __repr__(self):
        msg = super(Logger, self).__repr__()
        return '<univention.logging.%s' % (msg[1:],)


class LevelDependentFormatter(logging.Formatter):
    """A formatter which logs different formats depending on the log level"""

    def __init__(self, datefmt=None, log_pid=False):
        self._style = None
        super(LevelDependentFormatter, self).__init__(None, datefmt=datefmt)
        self.log_pid = log_pid
        self._level_to_format_mapping = _LEVEL_TO_FORMAT_MAPPING.copy()

    def setFormat(self, level, fmt):
        self._level_to_format_mapping[level] = fmt

    def format(self, record):
        try:
            fmt = self._level_to_format_mapping[record.levelno]
        except KeyError:
            try:
                fmt = self._level_to_format_mapping[_map_ud_to_level(_map_level_to_ud(record.levelno))]
            except KeyError:
                fmt = self._level_to_format_mapping[logging.NOTSET]

        record.pid = ''
        if self.log_pid:
            record.pid = '%s: ' % (record.process,)

        if not hasattr(record, 'prefix'):
            record.prefix = ''

        self._fmt = fmt
        if self._style is not None:
            self._style._fmt = self._fmt
        return super(LevelDependentFormatter, self).format(record)


class DebugHandler(logging.Handler):
    """A logging handler which logs to :py:mod:`univention.debug`"""

    def __init__(self, category=ud.MAIN, level=logging.NOTSET, auto_init=False, delay_init=False, do_exit=True):
        self._category = category
        self.delay_init = delay_init
        self.auto_init = auto_init
        self.do_exit = do_exit
        self._init_args = ('stderr', ud.NO_FLUSH, ud.NO_FUNCTION)
        if auto_init and not delay_init:
            self.init(*self._init_args)
        super(DebugHandler, self).__init__(level)

    def emit(self, record):
        if self.auto_init and self.delay_init:
            self.init(*self._init_args)
            self.delay_init = False
        msg = self.format(record)
        level = _map_level_to_ud(record.levelno)

        name, _, prefix = record.name.partition('.')
        message = "%s: %s" % (prefix, msg) if prefix else msg
        try:
            ud.debug(self._category, level, message)
        except ValueError:  # embedded null character
            ud.debug(self._category, level, repr(message))

    def init(self, filename='stderr', flush=ud.NO_FLUSH, function=ud.NO_FUNCTION):
        """Initialize :py:mod:`univention.debug`. Must only be called once. returns the file descriptor on success"""
        return ud.init(filename, flush, function)

    def reopen(self):
        """reopen the :py:mod:`univention.debug` logfile. must be called e.g. after log rotation."""
        level = ud.get_level(self._category)
        # reopen() will reset all log levels of all categories
        # FIXME: reset level for every category and hope there is a handler for every category already
        ud.reopen()
        ud.set_level(self._category, level)

    def close(self):
        super(DebugHandler, self).close()
        if self.do_exit:
            ud.exit()

    def setLevel(self, level):
        super(DebugHandler, self).setLevel(level)
        ud.set_level(self._category, _map_level_to_ud(self.level))

    def __repr__(self):
        level = logging.getLevelName(self.level)
        return '<%s[%s](%s)>' % (self.__class__.__name__, _map_category_name(self._category), level)


# we need to set the logger for the univention.debug categories already here
# so that code can already use original pythons `logging.getLogger()` at import time
# and also even before importing this module
for _ in _UD_CATEGORIES.values():
    getLogger(_, extend=True)
