# SPDX-FileCopyrightText: 2008-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""
Python native Univention debugging library.

See :py:mod:`univention.debug` for an alternative being a wrapper for the C
implementation.
"""

import logging
import sys
from functools import wraps
from itertools import chain
from warnings import warn


ERROR = 0
WARNING = WARN = 1
PROCESS = 2
INFO = 3
ALL = DEBUG = 4
TRACE = 5
DEFAULT = WARN

# The default levels provided are DEBUG(10), INFO(20), WARNING(30), ERROR(40) and CRITICAL(50).
# Mapping old levels to new ones
_map_lvl_old2new = {
    0: logging.ERROR,    # 40
    1: logging.WARNING,  # 30
    2: 25,               # 25
    3: logging.INFO,     # 20
    4: logging.DEBUG + 5,  # 15
    5: 5,                # 5
}

MAIN = 0x00
LDAP = 0x01
USERS = 0x02
NETWORK = 0x03
SSL = 0x04
SLAPD = 0x05
SEARCH = 0x06
TRANSFILE = 0x07
LISTENER = 0x08
POLICY = 0x09
ADMIN = 0x0A
CONFIG = 0x0B
LICENSE = 0x0C
KERBEROS = 0x0D
DHCP = 0x0E
PROTOCOL = 0x0F
MODULE = 0x10
ACL = 0x11
RESOURCES = 0x12
PARSER = 0x13
LOCALE = 0x14
AUTH = 0x15

NO_FLUSH = 0x00
FLUSH = 0x01

NO_FUNCTION = 0x00
FUNCTION = 0x01

_map_id_old2new = {
    MAIN: "MAIN",
    LDAP: "LDAP",
    USERS: "USERS",
    NETWORK: "NETWORK",
    SSL: "SSL",
    SLAPD: "SLAPD",
    SEARCH: "SEARCH",
    TRANSFILE: "TRANSFILE",
    LISTENER: "LISTENER",
    POLICY: "POLICY",
    ADMIN: "ADMIN",
    CONFIG: "CONFIG",
    LICENSE: "LICENSE",
    KERBEROS: "KERBEROS",
    DHCP: "DHCP",
    PROTOCOL: "PROTOCOL",
    MODULE: "MODULE",
    ACL: "ACL",
    RESOURCES: "RESOURCES",
    PARSER: "PARSER",
    LOCALE: "LOCALE",
    AUTH: "AUTH",
}


# 13.08.2008 13:13:57.123  LISTENER    ( ERROR   ) : listener: 1
# 13.08.2008 13:13:57.123  LISTENER    ( WARN    ) : received signal 2
# 13.08.2008 13:14:02.123  DEBUG_INIT
_outfmt = '%(asctime)s.%(msecs)03d %(name)-11s (%(levelname)-7s): %(message)s'
_outfmt_syslog = '%(name)-11s (%(levelname)-7s): %(message)s'
_datefmt = '%d.%m.%Y %H:%M:%S'


class _Formatter(logging.Formatter):
    def format(self, record):
        if record.name.startswith('ud2.'):
            record.name = record.name.split('.', 1)[-1]
        return super().format(record)


_logfilename = None
_handler_console = None
_handler_file = None
_handler_syslog = None
_do_flush = False
_enable_function = False
_enable_syslog = False
_logger_level = {key: DEFAULT for key in _map_id_old2new.values()}  # noqa: C420
_use_structured = True


def init(logfile, force_flush=0, enable_function=0, enable_syslog=0):
    """
    Initialize debugging library for logging to 'logfile'.

    :param str logfile:  name of the logfile, or 'stderr', or 'stdout'.
    :param bool force_flush: force flushing of messages (True).
    :param bool trace_function: enable (True) or disable (False) function tracing.
    :param bool enable_syslog: enable (True) or disable (False) logging to SysLog.
    :returns: output file or None.
    """
    global _logfilename, _handler_console, _handler_file, _do_flush, _enable_function, _enable_syslog  # _handler_syslog

    result = None
    _logfilename = logfile

    null_handler = logging.NullHandler()

    ud2_base_logger = logging.getLogger('ud2')
    ud2_base_logger.setLevel(_map_lvl_old2new[TRACE])
    ud2_base_logger.handlers = [null_handler]
    ud2_base_logger.propagate = False

    if _use_structured:
        from univention.logging import StructuredFormatter
        formatter = StructuredFormatter(with_date_prefix=True)
    else:
        formatter = _Formatter(_outfmt, _datefmt)
    exit()
    if logfile in ('stderr', '/dev/stderr', 'stdout', '/dev/stdout'):
        # add stderr or stdout handler
        _handler_console = logging.StreamHandler(sys.stdout if logfile in ('stdout', '/dev/stdout') else sys.stderr)
        _handler_console.setLevel(_map_lvl_old2new[TRACE])
        _handler_console.setFormatter(formatter)
        logging.getLogger('ud2').addHandler(_handler_console)
        logging.getLogger('ud2').removeHandler(null_handler)
        result = _handler_console.stream
    else:
        try:
            # add file handler
            _handler_file = logging.FileHandler(logfile, 'a+')
            _handler_file.setLevel(_map_lvl_old2new[TRACE])
            _handler_file.setFormatter(formatter)
            logging.getLogger('ud2').addHandler(_handler_file)
            logging.getLogger('ud2').removeHandler(null_handler)
            result = _handler_file.stream
        except OSError as ex:
            print('opening %s failed: %s' % (logfile, ex))

#     if enable_syslog:
#         try:
# add syslog handler
#             _handler_syslog = logging.handlers.SysLogHandler( ('localhost', 514), logging.handlers.SysLogHandler.LOG_ERR )
#             _handler_syslog.setLevel( _map_lvl_old2new[ERROR] )
#             _handler_syslog.setFormatter(formatter)
#             logging.getLogger('').addHandler(_handler_syslog)
#         except:
#             raise
#             print('opening syslog failed')

    logging.addLevelName(25, 'PROCESS')
    logging.addLevelName(15, 'DEBUG')
    logging.addLevelName(5, 'TRACE')
    logging.addLevelName(100, 'INIT')
    logging.addLevelName(99, 'EXIT')
    logging.addLevelName(98, 'REINIT')
    logging.addLevelName(97, 'BEGIN')
    logging.addLevelName(96, 'END')

    logging.getLogger('ud2').getChild('MAIN').log(100, '')

    _do_flush = force_flush
    _enable_function = enable_function
    _enable_syslog = enable_syslog

    return result


def exit():
    """Close debug logfile."""
    global _handler_console, _handler_file
    logging.getLogger('ud2').getChild('MAIN').log(99, 'EXIT')
    if _handler_console:
        logging.getLogger('').removeHandler(_handler_console)
        _handler_console = None

    if _handler_file:
        logging.getLogger('').removeHandler(_handler_file)
        _handler_file = None


def reopen():
    """Close and re-open the debug logfile."""
    logging.getLogger('ud2').getChild('MAIN').log(98, 'REINIT')
    init(_logfilename, _do_flush, _enable_function, _enable_syslog)


def set_level(category, level):
    """
    Set minimum required severity 'level' for facility 'category'.

    :param int category: ID of the category, e.g. MAIN, LDAP, USERS, ...
    :param int level: Level of logging, e.g. ERROR, WARN, PROCESS, INFO, ALL, TRACE
    """
    new_id = _map_id_old2new.get(category, 'MAIN')
    if level > TRACE:  # pragma: no cover
        level = TRACE
    elif level < ERROR:  # pragma: no cover
        level = ERROR
    _logger_level[new_id] = level


def get_level(category):
    """
    Get minimum required severity for facility 'category'.

    :param int category: ID of the category, e.g. MAIN, LDAP, USERS, ...
    :return: Return debug level of category.
    :rtype: int
    """
    new_id = _map_id_old2new.get(category, 'MAIN')
    return _logger_level[new_id]


def set_function(activate):
    """
    Enable or disable the logging of function begins and ends.

    :param bool activate: enable (True) or disable (False) function tracing.

    .. deprecated:: 4.4
        Use function decorator :py:func:`trace` instead.
    """
    global _enable_function
    _enable_function = activate


def debug(category, level, message, utf8=True):
    """
    Log message 'message' of severity 'level' to facility 'category'.

    :param int category: ID of the category, e.g. MAIN, LDAP, USERS, ...
    :param int level: Level of logging, e.g. ERROR, WARN, PROCESS, INFO, ALL, TRACE
    :param str message: The message to log.
    :param bool utf8: Assume the message is UTF-8 encoded.
    """
    new_id = _map_id_old2new.get(category, 'MAIN')
    if level <= _logger_level[new_id]:
        new_level = _map_lvl_old2new[level]
        logging.getLogger('ud2').getChild(new_id).log(new_level, message, extra={'logname': new_id})
        _flush()


class function:
    """
    Log function call begin and end.

    :param str fname: name of the function starting.
    :param bool utf8: Assume the message is UTF-8 encoded.

    .. deprecated:: 4.4
        Use function decorator :py:func:`trace` instead.

    >>> def my_func(agr1, agr2=None):
    ...    _d = function('my_func(...)')  # noqa: F841
    ...    return 'yes'
    >>> my_func(42)
    'yes'
    """

    def __init__(self, fname, utf8=True):
        warn('univention.debug2.function is deprecated and will be removed with UCS-5', PendingDeprecationWarning, stacklevel=2)
        self.fname = fname
        if _enable_function:
            logging.getLogger('ud2').getChild('MAIN').log(97, self.fname)
            _flush()

    def __del__(self):
        """Log the end of function."""
        if _enable_function:
            logging.getLogger('ud2').getChild('MAIN').log(96, self.fname)
            _flush()


def set_structured(use_structured=False):
    global _use_structured
    _use_structured = use_structured


def trace(with_args=True, with_return=False, repr=object.__repr__):
    """
    Log function call, optional with arguments and result.

    :param bool with_args: Log function arguments.
    :param bool with_return: Log function result.
    :param repr: Function accepting a single object and returing a string representation for the given object. Defaults to :py:func:`object.__repr__`, alternative :py:func:`repr`.

    >>> @trace(with_args=True, with_return=True)
    ... def my_func(arg1, arg2=None):
    ...     return 'yes'
    >>> my_func(42)
    'yes'
    >>> class MyClass(object):
    ...     @trace(with_args=True, with_return=True, repr=repr)
    ...     def my_meth(self, arg1, arg2=None):
    ...         return 'yes'
    >>> MyClass().my_meth(42)
    'yes'
    >>> @trace()
    ... def my_bug():
    ...     1 / 0
    >>> my_bug()
    Traceback (most recent call last):
        ...
    ZeroDivisionError: integer division or modulo by zero
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            fname = '%s.%s' % (f.__module__, f.__name__)
            _args = ', '.join(
                    chain(
                        (repr(arg) for arg in args),
                        ('%s=%s' % (k, repr(v)) for (k, v) in kwargs.items()),
                    ),
            ) if with_args else '...'

            logger = logging.getLogger('ud2').getChild('MAIN')
            logger.log(97, '%s(%s): ...', fname, _args)
            _flush()
            try:
                ret = f(*args, **kwargs)
            except BaseException:
                try:
                    (exctype, value) = sys.exc_info()[:2]
                    logger.log(96, '%s(...): %s(%s)', fname, exctype, value)
                finally:
                    exctype = value = None
                raise
            else:
                logger.log(96, '%s(...): %s', fname, repr(ret) if with_return else '...')
                return ret

        return wrapper

    return decorator


def _flush():
    """Flushing all messages."""
    if _do_flush:
        for handler in [_handler_console, _handler_file, _handler_syslog]:
            if handler:
                handler.flush()
