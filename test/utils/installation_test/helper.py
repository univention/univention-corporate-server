# -*- coding: utf-8 -*-


import linecache
import logging
import sys
import time
from functools import wraps
from os.path import samefile
from string import Formatter
from types import FrameType
from typing import Any, Callable, Mapping, Optional, Sequence, Union


COLORS = {
    "RESET": "\033[0m",
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "MAGENTA": "\033[35m",
    "CYAN": "\033[36m",
    "WHITE": "\033[37m",
}


class VerboseFormatter(Formatter):
    def get_value(self, key: Union[int, str], args: Sequence[Any], kwargs: Mapping[str, Any]) -> Any:
        try:
            return super().get_value(key, args, kwargs)
        except (IndexError, KeyError):
            return ""

    def check_unused_args(self, used_args: Any, args: Sequence[Any], kwargs: Mapping[str, Any]) -> None:
        pass


def verbose(msg, fmt="", formatter=VerboseFormatter()):  # type (str, str, Formatter) -> Callabble[[T], T]
    log = logging.getLogger(__name__)

    def decorator(f):  # type (Callable) -> Callable
        @wraps(f)
        def wrapper(*args, **kwargs):  # type (*Any, **Any) -> Any
            start = time.time()
            log.info(
                "%(MAGENTA)s%(msg)s%(CYAN)s:%(GREEN)sBEGIN%(RESET)s %(args)s",
                dict(
                    COLORS,
                    msg=msg,
                    args=formatter.format(fmt, *args, **kwargs),
                ),
            )
            sys.stdout.flush()
            try:
                return f(*args, **kwargs)
            finally:
                log.info(
                    "%(MAGENTA)s%(msg)s%(CYAN)s:%(GREEN)sEND%(RESET)s %(duration).1f",
                    dict(
                        COLORS,
                        msg=msg,
                        duration=time.time() - start,
                    ),
                )
                sys.stdout.flush()

        return wrapper

    return decorator


def trace_calls(frame: FrameType, event: str, arg: Any) -> Optional[Callable]:
    log = logging.getLogger(__name__)

    co = frame.f_code
    try:
        is_main = samefile(co.co_filename, sys.modules["__main__"].__file__ or __file__)
    except OSError:
        is_main = False

    if event == "line":
        if is_main:
            log.debug(
                "%(MAGENTA)s%(fname)s%(CYAN)s:%(GREEN)s%(lno)d%(RESET)s %(code)s",
                dict(
                    COLORS,
                    fname=co.co_filename,
                    lno=frame.f_lineno, code=linecache.getline(co.co_filename, frame.f_lineno).rstrip("\n"),
                ),
            )
    elif event == "call":
        caller = frame.f_back
        if False:
            log.info(
                "%(MAGENTA)s%(sname)s%(CYAN)s:%(GREEN)s%(sno)d%(RESET)s -> %(MAGENTA)s%(dname)s%(CYAN)s:%(GREEN)s%(dno)d%(RESET)s %(func)s",
                dict(
                    COLORS,
                    sname=caller.f_code.co_filename if caller else "?",
                    sno=caller.f_lineno if caller else 0,
                    dname=co.co_filename,
                    dno=frame.f_lineno,
                    func=co.co_name,
                ),
            )

    return trace_calls
