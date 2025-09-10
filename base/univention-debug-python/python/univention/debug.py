#!/usr/bin/python3
#
# Univention Debug
#  debug.py
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""
Univention debugging and logging library.

example:
>>> f = init('stdout', NO_FLUSH, FUNCTION) #doctest: +ELLIPSIS
... ...  DEBUG_INIT
>>> set_level(LISTENER, ERROR)
"""


import sys
from functools import wraps
from itertools import chain
from warnings import warn

from univention import _debug
from univention._debug import (
    ACL, ADMIN, ALL, AUTH, CONFIG, DEBUG, DHCP, ERROR, FLUSH, FUNCTION, INFO, KERBEROS, LDAP, LICENSE, LISTENER, LOCALE,
    MAIN, MODULE, NETWORK, NO_FLUSH, NO_FUNCTION, PARSER, POLICY, PROCESS, PROTOCOL, RESOURCES, SEARCH, SLAPD, SSL,
    TRACE, TRANSFILE, USERS, WARN, begin, end, exit, get_level, init, reopen, set_function, set_level, set_structured,
)


__all__ = ('ACL', 'ADMIN', 'ALL', 'AUTH', 'CONFIG', 'DEBUG', 'DHCP', 'ERROR', 'FLUSH', 'FUNCTION', 'INFO', 'KERBEROS', 'LDAP', 'LICENSE', 'LISTENER', 'LOCALE', 'MAIN', 'MODULE', 'NETWORK', 'NO_FLUSH', 'NO_FUNCTION', 'PARSER', 'POLICY', 'PROCESS', 'PROTOCOL', 'RESOURCES', 'SEARCH', 'SLAPD', 'SSL', 'TRACE', 'TRANSFILE', 'USERS', 'WARN', 'begin', 'debug', 'debug', 'end', 'exit', 'function', 'get_level', 'init', 'reopen', 'set_function', 'set_level', 'set_structured', 'trace')


def debug(category, level, message, utf8=True):
    """
    Log message 'message' of severity 'level' to facility 'category'.

    :param int category: ID of the category, e.g. MAIN, LDAP, USERS, ...
    :param int level: Level of logging, e.g. ERROR, WARN, PROCESS, INFO, ALL
    :param str message: The message to log.
    :param bool utf8: Assume the message is UTF-8 encoded.

    >>> debug(LISTENER, ERROR, 'Fatal error: var=%s' % 42) #doctest: +ELLIPSIS
    ... ...  LISTENER    ( ERROR   ) : Fatal error: var=42
    """
    _debug.debug(category, level, message)


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
        warn('univention.debug.function is deprecated and will be removed with UCS-5', PendingDeprecationWarning, stacklevel=2)
        self.fname = fname
        _debug.begin(self.fname)

    def __del__(self):
        """Log the end of function."""
        _debug.end(self.fname)


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

            _debug.begin('%s(%s): ...' % (fname, _args))
            try:
                ret = f(*args, **kwargs)
            except BaseException:
                try:
                    (exctype, value) = sys.exc_info()[:2]
                    _debug.end('%s(...): %s(%s)' % (fname, exctype, value))
                finally:
                    exctype = value = None
                raise
            else:
                _debug.end('%s(...): %s' % (fname, repr(ret) if with_return else '...'))
                return ret

        return wrapper

    return decorator


if __name__ == '__main__':  # pragma: no cover
    import doctest
    doctest.testmod()
