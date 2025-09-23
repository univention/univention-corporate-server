#!/usr/bin/python3
# SPDX-FileCopyrightText: 2022-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""
A python-logging interface compatible wrapper for logging with :py:mod:`univention.debug`

>>> import univention.logging
>>> import logging
>>> logger = logging.getLogger('MAIN').getChild(__name__)
>>> univention.logging.basicConfig(level=logging.INFO)
>>> logger.info('test')
"""

import contextlib
import copy
import datetime
import logging
import time
import traceback
from typing import Any

from logfmter import Logfmter

import univention.debug as ud


__all__ = ['DebugHandler', 'Logger', 'StructuredFormatter', 'basicConfig', 'extendLogger', 'getLogger']
for name in logging.__all__:
    if name not in __all__:
        globals()[name] = getattr(logging, name)
__all__ += logging.__all__

RESERVED = ('args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename', 'funcName', 'levelname', 'levelno', 'lineno', 'message', 'module', 'msecs', 'msg', 'name', 'pathname', 'process', 'processName', 'relativeCreated', 'stack_info', 'taskName', 'thread', 'threadName')

logging.PROCESS = 25
logging.TRACE = logging.DEBUG - 5
logging.addLevelName(logging.PROCESS, 'PROCESS')
logging.addLevelName(logging.TRACE, 'TRACE')
_LEVEL_MAPPING = {
    logging.NOTSET: 100,
    logging.TRACE: 5,  # 5 -> 5
    logging.DEBUG - 1: ud.ALL,  # 9 -> 4
    logging.DEBUG: ud.ALL,  # 10 -> 4
    logging.INFO: ud.INFO,  # 20 -> 3
    logging.PROCESS: ud.PROCESS,  # 25 -> 2
    logging.WARNING: ud.WARN,  # 30 -> 1
    logging.ERROR: ud.ERROR,  # 40 -> 0
    # logging.CRITICAL: ud.ERROR,  50 -> 0
}
_UD_LEVEL_MAPPING = {v: k for k, v in _LEVEL_MAPPING.items()}

_UD_CATEGORIES = {
    cat: name
    for name, cat in ud.__dict__.items()
    if isinstance(cat, int) and name not in ('FLUSH', 'NO_FLUSH', 'FUNCTION', 'NO_FUNCTION', 'ALL', 'INFO', 'PROCESS', 'WARN', 'ERROR', 'DEBUG', 'WARNING') and name.isupper()
}


def _map_level_to_ud(level: int) -> int:
    """
    Map logging level to univention-debug loglevel

    >>> _map_level_to_ud(logging.ERROR)
    0
    >>> _map_level_to_ud(logging.PROCESS)
    2
    >>> _map_level_to_ud(logging.INFO)
    3
    >>> _map_level_to_ud(logging.DEBUG)
    4
    >>> _map_level_to_ud(logging.TRACE)
    5
    >>> _map_level_to_ud(logging.NOTSET)
    100
    >>> _map_level_to_ud(logging.INFO - 1)
    4
    >>> _map_level_to_ud(logging.DEBUG - 1)
    5
    >>> _map_level_to_ud(logging.DEBUG - 9)
    79
    >>> _map_level_to_ud(4)
    19
    >>> _map_level_to_ud(9)
    5
    >>> _map_level_to_ud(99)
    0
    """
    if level <= 0:
        return 100
    if level >= logging.ERROR:
        return 0
    if 0 < level < logging.TRACE:
        return 100 - ((level) * 20) - 1
    if logging.TRACE <= level < logging.DEBUG:
        return ud.TRACE
    if logging.PROCESS <= level < logging.WARNING:
        return ud.PROCESS
    level = level if level in _LEVEL_MAPPING else (level // 10) * 10
    return _LEVEL_MAPPING.get(level, level)


def _map_ud_to_level(level: int) -> int:
    """
    Map univention-debug level to logging loglevel

    >>> _map_ud_to_level(0) == logging.ERROR
    True
    >>> _map_ud_to_level(1) == logging.WARNING
    True
    >>> _map_ud_to_level(2) == logging.PROCESS
    True
    >>> _map_ud_to_level(3) == logging.INFO
    True
    >>> _map_ud_to_level(4) == logging.DEBUG
    True
    >>> _map_ud_to_level(5) == logging.TRACE
    True
    >>> _map_ud_to_level(6)
    4
    >>> _map_ud_to_level(50)
    2
    >>> _map_ud_to_level(99)
    0
    """
    if level >= 100:
        return 0
    if level > ud.TRACE:
        return (99 - level) // 20
        base = 100 if level <= 10 else 110
        return max((10, (base - level))) // 20
    return _UD_LEVEL_MAPPING.get(level)


def _map_category_name(category: int) -> str:
    """
    >>> _map_category_name(10)
    'ADMIN'
    """
    return _UD_CATEGORIES.get(category, '<unknown>')


def getLogger(name: str, **kwargs: Any) -> 'Logger':
    """
    Return a logger with the specified name, creating it if necessary.

    :param name:
        The name of a :py:mod:`univention.debug` category
        (if not existant `ud.MAIN` will be used)
    :param extend:
        Whether a non univention-debug logger should be extended to be one.
    :param univention_debug_category:
        If the logger name should differ from the univention-debug category this param can be used
        as initialization call to create the logger once.

    .. warning::
        If a logger with that name already exists and is not a :py:class:`univention.logging.Logger`
        no univention-debug logger is initialized and returned.

    >>> logger = getLogger('ADMIN')  # .getChild(__name__)
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


def extendLogger(name: str, **kwargs: Any) -> None:
    """
    Ensure that the logger with the specified name is a univention-debug logger otherwise transform it.

    :param name: The name of the logger.
    :param univention_debug_category:
        A :py:mod:`univention.debug` category (if not given `name` will be used).
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
    filename='stdout',
    level=None,
    *,
    univention_debug_level=None,
    univention_debug_flush=ud.FLUSH,
    univention_debug_function=ud.NO_FUNCTION,
    univention_debug_categories=None,
    do_exit=True,
    delay_init=False,  # until first use
    use_structured_logging=True,
    **kwargs,
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
        logger.univention_debug_handler.do_exit = do_exit
        if delay_init:
            logger.univention_debug_handler.auto_init = True
            logger.univention_debug_handler.delay_init = delay_init
            logger.univention_debug_handler._init_args = (filename, univention_debug_flush, univention_debug_function)


class SyslogPrefix(logging.Filter):
    """Convert Python log level to Syslog priority."""

    def __init__(self, key='syslog_priority'):
        super().__init__()
        self.key = key

    def filter(self, record):
        setattr(record, self.key, f'<{self.get_syslog_prefix(record.levelno)}>')
        return True

    def get_syslog_prefix(self, level):
        """
        Syslog priorities:

            <0>: Emergency
            <1>: Alert
            <2>: Critical
            <3>: Error
            <4>: Warning
            <5>: Notice
            <6>: Info
            <7>: Debug
        """
        if level >= logging.CRITICAL:
            return 2
        elif level >= logging.ERROR:
            return 3
        elif level >= logging.WARNING:
            return 4
        elif level >= logging.PROCESS:
            return 5
        elif level >= logging.INFO:
            return 6
        elif level >= logging.DEBUG:
            return 7
        else:
            return 7


class StructuredFormatter(logging.Formatter):
    r"""
    A formatter combining prefixed content and structured data from logfmt.

    Producing log lines like:

        2025-01-01T00:00:00.000000+00:00 INFO    [         -] module.function:1 the message\t| pid=12345 logname=ADMIN
    """

    def __init__(
        self,
        fmt=None,
        *,
        defaults=None,
        data_fields=None,
        data_mapping=None,
        data_defaults=None,
        data_ignored_keys=None,
        add_full_tracebacks=True,
        with_date_prefix=False,
        key='logfmt',
    ):
        # fmt = fmt or '[{request_id:>10.10}] {module}.{funcName}:{lineno} {message}\t| {logfmt}'
        fmt = fmt or '[{request_id:>10.10}] {message}\t| {logfmt}'
        if with_date_prefix:
            fmt = f'{{syslog_priority}}{{asctime}} {{levelname:>8.8}} {fmt}'
        style = '{'
        self.key = key
        self.add_full_tracebacks = add_full_tracebacks
        _datefmt = '%Y-%m-%dT%H:%M:%S.%f+%z'  # broken, see self.formatTime
        self.logfmter = Logfmter(
            keys=data_fields or ['pid', 'umcmodule', 'logname', 'func'],
            mapping=data_mapping or {'at': 'levelname', 'pid': 'process', 'time': 'asctime', 'logname': 'name'},
            defaults={'func': '{module}.{funcName}:{lineno}'} | (data_defaults or {}),
            ignored_keys=data_ignored_keys or ['msg', 'request_id', 'syslog_priority'],  # 'stack_info', 'exc_info'
            datefmt=_datefmt,
        )
        super().__init__(fmt=fmt, datefmt=_datefmt, defaults={'request_id': '-', key: '', 'syslog_priority': ''} | (defaults or {}), style=style)

    def formatMessage(self, record):
        setattr(record, self.key, self.logfmter.format(copy.copy(record)))
        return super().formatMessage(record)

    def format(self, record):
        msg = record.msg
        if hasattr(record, 'traceback'):
            record.exc_text = record.traceback
            del record.traceback

        if isinstance(record.msg, dict):
            record.msg = msg.get('msg')
            for key, val in msg.items():
                if key != 'msg':
                    setattr(record, key, val)
        try:
            record.message = record.getMessage().replace('\t|', '\t\\|')
            if record.message.strip('\t !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'):
                record.message = self.logfmter.format_string(record.message)
            if self.usesTime():
                record.asctime = self.formatTime(record, self.datefmt)
            s = self.formatMessage(record).rstrip('\n')
        finally:
            record.msg = msg

        if not self.add_full_tracebacks:
            return s
        if record.exc_info and not record.exc_text:
            record.exc_text = ''.join(traceback.format_exception(*record.exc_info)).rstrip('\n')
        if record.exc_text:
            s = f'{s}\n{record.exc_text}'
        if record.stack_info:
            s = f'{s}\n{self.formatStack(record.stack_info)}'
        return s

    def formatTime(self, record, datefmt=None):
        dt = datetime.datetime.fromtimestamp(record.created, tz=datetime.UTC)
        local_dt = dt.astimezone()
        return local_dt.isoformat(timespec='microseconds')


class Logger(logging.Logger):
    """
    A logger which automatically adds :py:mod:`univention.debug` as logging handler.

    Can be set as global default logger via ``logging.setLoggerClass(univention.logging.Logger)``.
    """

    def __init__(self, name, level=logging.NOTSET, **kwargs):
        kwargs.pop('log_pid', None)
        self.univention_debug_category = getattr(ud, kwargs.get('univention_debug_category', name.split('.', 1)[0]))
        self.univention_debug_handler = handler = DebugHandler(self.univention_debug_category, **kwargs)
        if level == logging.NOTSET:
            level = handler.getLevel()
        super().__init__(name, level=level)
        self.propagate = False
        self._formatter = StructuredFormatter()
        handler.setFormatter(self._formatter)
        handler.setLevel(self.level)
        self.addHandler(handler)

    def setLevel(self, level):
        super().setLevel(level)
        self.univention_debug_handler.setLevel(self.level)

    def isEnabledFor(self, level):
        # we need to overwrite the method because something might have
        # called `ud.set_level()` without using this logging interface.
        # prevent the cache from giving wrong results
        return level >= self.getEffectiveLevel()

    def getEffectiveLevel(self):
        return self.univention_debug_handler.getLevel()

    def set_ud_level(self, level):
        self.setLevel(_map_ud_to_level(level))

    def init(self, filename='stderr', flush=ud.NO_FLUSH, function=ud.NO_FUNCTION, structured=False):
        """init :py:mod:`univention.debug`. must only be called once. returns the file descriptor on success"""
        return self.univention_debug_handler.init(filename, flush, function, structured)

    def exit(self):
        return self.univention_debug_handler.close()

    def reopen(self):
        """reopen the :py:mod:`univention.debug` logfile. must be called e.g. after log rotation."""
        level = self.getEffectiveLevel()
        self.univention_debug_handler.reopen()
        self.univention_debug_handler.setLevel(level)

    def set_structured(self, /, use_structured_logging):  # pragma: no cover
        from warnings import warn
        warn('set_structured is obsolete', PendingDeprecationWarning, stacklevel=2)

    def __repr__(self):
        msg = super().__repr__()
        return '<univention.logging.%s' % (msg[1:],)

    def destroy(self):
        self.manager.loggerDict.pop(self.name)
        for key in list(self.manager.loggerDict.keys()):
            if key.startswith(f'{self.name}.'):
                self.manager.loggerDict.pop(key)


class Structured:
    """Wrapper for standard logging to simplify specifying structured data."""

    __slots__ = ('__bound_extra', '__log')

    def __init__(self, log, bound_extra=None):
        assert isinstance(log, logging.Logger)
        self.__log = log
        self.__bound_extra = bound_extra or {}

    def getChild(self, name):
        return Structured(self.__log.getChild(name), self.__bound_extra)

    def bind(self, **extra):
        merged = {**self.__bound_extra, **extra}
        return Structured(self.__log, merged)

    def trace(_self, _message, *_args, stacklevel=1, **_kwargs):
        _self.log(logging.TRACE, _message, *_args, stacklevel=stacklevel + 1, **_kwargs)

    def debug(_self, _message, *_args, **_kwargs):
        _self._log(_self.__log.debug, _message, *_args, **_kwargs)

    def info(_self, _message, *_args, **_kwargs):
        _self._log(_self.__log.info, _message, *_args, **_kwargs)

    def process(_self, _message, *_args, stacklevel=1, **_kwargs):
        _self.log(logging.PROCESS, _message, *_args, stacklevel=stacklevel + 1, **_kwargs)

    def warning(_self, _message, *_args, **_kwargs):
        _self._log(_self.__log.warning, _message, *_args, **_kwargs)

    def error(_self, _message, *_args, **_kwargs):
        _self._log(_self.__log.error, _message, *_args, **_kwargs)

    def critical(_self, _message, *_args, **_kwargs):
        _self._log(_self.__log.critical, _message, *_args, **_kwargs)

    def exception(_self, _message, *_args, **_kwargs):
        _kwargs.setdefault('exc_info', True)
        _self._log(_self.__log.exception, _message, *_args, **_kwargs)

    @contextlib.contextmanager
    def timing(_self, _message, *_args, level=logging.TRACE, stacklevel=1, **_kwargs):
        start = time.perf_counter()
        try:
            yield
        finally:
            end = time.perf_counter()
            _self.log(level, _message, *_args, stacklevel=stacklevel + 2, duration=f"{end - start:.6f}", **_kwargs)

    def _log(_self, _func, _msg, *args, exc_info=None, stack_info=False, stacklevel=1, **extra):
        return _func(
            _msg,
            *args,
            exc_info=exc_info,
            extra=_self._merge_extras(extra),
            stack_info=stack_info,
            stacklevel=stacklevel + 2,
        )

    def log(_self, _level, _msg, *args, exc_info=None, stack_info=False, stacklevel=1, **extra):
        return _self.__log.log(
            _level,
            _msg,
            *args,
            exc_info=exc_info,
            extra=_self._merge_extras(extra),
            stack_info=stack_info,
            stacklevel=stacklevel + 1,
        )

    def _merge_extras(self, extra):
        merged = {**self.__bound_extra, **extra}
        return {(f'x_{key}' if key in RESERVED else key): value for key, value in merged.items()}

    def __reduce__(self):
        return (
            self.__class__._reconstruct,
            (self.__log.name, self.__bound_extra),
        )

    @classmethod
    def _reconstruct(cls, name, extra):
        return cls(logging.getLogger(name), extra)

    def __getattr__(self, name):
        if name == '_Structured__log':
            raise AttributeError(name)  # pragma: no cover
        return getattr(self.__log, name)

    def __setattr__(self, name, value):
        if name.removeprefix('_Structured') in self.__slots__:
            return super().__setattr__(name, value)
        setattr(self.__log, name, value)  # pragma: no cover


class DebugHandler(logging.Handler):
    """A logging handler which logs to :py:mod:`univention.debug`"""

    def __init__(self, category=ud.MAIN, level=logging.NOTSET, auto_init=False, delay_init=False, do_exit=True, filename='stderr'):
        self._category = category
        self.delay_init = delay_init
        self.auto_init = auto_init
        self.do_exit = do_exit
        self._init_args = (filename, ud.NO_FLUSH, ud.NO_FUNCTION, False)
        if auto_init and not delay_init:
            self.init(*self._init_args)
        super().__init__(level)

    def emit(self, record):
        if self.auto_init and self.delay_init:
            self.init(*self._init_args)
            self.setLevel(self.level)
            self.delay_init = False
        message = self.format(record)
        level = _map_level_to_ud(record.levelno)

        try:
            ud.debug(self._category, level, message)
        except ValueError:  # embedded null character
            ud.debug(self._category, level, message.replace('\x00', repr('\x00')))

    def init(self, filename='stderr', flush=ud.NO_FLUSH, function=ud.NO_FUNCTION, structured=False):
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
        super().close()
        if self.do_exit:
            ud.exit()

    def get_ud_level(self):
        return ud.get_level(self._category)

    def getLevel(self):
        if self.delay_init:
            # if we haven't yet initialized UD, the UD level is not set.
            # so the level set in the logger is the correct one
            return self.level
        return _map_ud_to_level(self.get_ud_level())

    def setLevel(self, level):
        super().setLevel(level)
        ud.set_level(self._category, _map_level_to_ud(self.level))

    def __repr__(self):
        level = logging.getLevelName(self.level)
        return '<%s[%s](%s)>' % (self.__class__.__name__, _map_category_name(self._category), level)


# we need to set the logger for the univention.debug categories already here
# so that code can already use original pythons `logging.getLogger()` at import time
# and also even before importing this module
for _ in _UD_CATEGORIES.values():
    getLogger(_, extend=True)
