# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

import os
from abc import ABCMeta
from functools import wraps
from hashlib import sha256
from logging import getLogger
from tempfile import gettempdir
from typing import Any, Callable, TypeVar, cast  # noqa: F401


F = TypeVar("F", bound=Callable[..., Any])


log = getLogger(__name__)


class Lazy(metaclass=ABCMeta):
    """base class for delayed file/image actions"""

    BASEDIR = gettempdir()
    SUFFIX = ""

    def __init__(self):
        # type: () -> None
        self._path = ""

    @staticmethod
    def lazy(fun):
        # type: (F) -> F

        @wraps(fun)
        def newfun(self, *args, **kwargs):
            # type: (Lazy, *Any, **Any) -> Any
            self._check()
            return fun(self, *args, **kwargs)

        return cast(F, newfun)

    def _check(self):
        # type: () -> None
        if self._path:
            return

        name = self.hash() + self.SUFFIX
        temp = os.path.join(self.BASEDIR, "." + name)
        try:
            self._create(temp)
            self._path = os.path.join(self.BASEDIR, self.hash() + self.SUFFIX)
            os.rename(temp, self._path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)

    def _create(self, path):
        # type: (str) -> None
        raise NotImplementedError()

    def hash(self):
        # type: () -> str
        raise NotImplementedError()


class File(Lazy, metaclass=ABCMeta):
    """base class for delayed file/image actions"""

    def __init__(self):
        # type: () -> None
        Lazy.__init__(self)

    @staticmethod
    def hashed(fun):
        # type: (Callable[..., Any]) -> Callable[..., str]
        def newfun(self, *args, **kwargs):
            # type: (File, *Any, **Any) -> str
            ret = fun(self, *args, **kwargs)
            return sha256(repr(ret).encode("UTF-8")).hexdigest()

        return newfun

    @Lazy.lazy
    def path(self):
        # type: () -> str
        return self._path

    @Lazy.lazy
    def file_size(self):
        # type: () -> int
        return os.stat(self._path).st_size

    @Lazy.lazy
    def used_size(self):
        # type: () -> int
        return os.stat(self._path).st_blocks * 512
