# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import time
from functools import wraps
from typing import Any, Callable, TypeVar, cast


DEFAULT_TIMEOUT = 90  # seconds

F = TypeVar('F', bound=Callable[..., None])


class WaitForNonzeroResultOrTimeout:

    def __init__(self, func: Callable[..., Any], timeout: int = DEFAULT_TIMEOUT) -> None:
        self.func = func
        self.timeout = timeout

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        for _i in range(self.timeout):
            result = self.func(*args, **kwargs)
            if result:
                break
            else:
                time.sleep(1)
        return result


class SetTimeout:

    def __init__(self, func: Callable[..., None], timeout: int = DEFAULT_TIMEOUT) -> None:
        self.func = func
        self.timeout = timeout

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        for i in range(self.timeout):
            try:
                print("** Entering", self.func.__name__)
                self.func(*args, **kwargs)
                print("** Exiting", self.func.__name__)
                break
            except Exception as ex:
                print("(%d)-- Exception cought: %s %s" % (i, type(ex), ex))
                time.sleep(1)
        else:
            self.func(*args, **kwargs)


def setTimeout(timeout: int = DEFAULT_TIMEOUT) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> None:
            for i in range(timeout):
                try:
                    print("** Entering", func.__name__)
                    func(*args, **kwargs)
                    print("** Exiting", func.__name__)
                    break
                except Exception as ex:
                    print("(%d)-- Exception cought: %s %s" % (i, type(ex), ex))
                    time.sleep(1)
            else:
                func(*args, **kwargs)
        return cast(F, wrapper)
    return decorator
