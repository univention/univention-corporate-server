#!/usr/bin/python2.7 -u
# -*- coding: utf-8 -*-

import logging
import sys
import time
from functools import wraps
from string import Formatter
from typing import Any, Callable, Mapping, Sequence, Union  # noqa: F401


class VerboseFormatter(Formatter):
    def get_value(self, key, args, kwargs):  # type: (Union[int, str], Sequence[Any], Mapping[str, Any]) -> Any
        try:
            return super(VerboseFormatter, self).get_value(key, args, kwargs)
        except (IndexError, KeyError):
            return ""

    def check_unused_args(self, used_args, args, kwargs):  # type: (Any, Sequence[Any], Mapping[str, Any]) -> None
        pass


def verbose(msg, fmt="", formatter=VerboseFormatter()):  # type (str, str, Formatter) -> Callabble[[T], T]
    log = logging.getLogger(__name__)

    def decorator(f):  # type (Callable) -> Callable
        @wraps(f)
        def wrapper(*args, **kwargs):  # type (*Any, **Any) -> Any
            start = time.time()
            log.info("%s:BEGIN %s", msg, formatter.format(fmt, *args, **kwargs))
            sys.stdout.flush()
            try:
                return f(*args, **kwargs)
            finally:
                log.info("%s:END %.1f", msg, time.time() - start)
                sys.stdout.flush()

        return wrapper

    return decorator
