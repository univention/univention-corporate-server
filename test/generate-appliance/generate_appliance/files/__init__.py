# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

from __future__ import annotations
from abc import ABCMeta
from functools import wraps
from hashlib import sha256
from logging import getLogger
from pathlib import Path
from tempfile import gettempdir
from typing import Any, Callable, Optional, TypeVar, cast  # noqa: F401


F = TypeVar("F", bound=Callable[..., Any])


log = getLogger(__name__)


class Lazy(metaclass=ABCMeta):
    """base class for delayed file/image actions"""

    BASEDIR = Path(gettempdir())
    SUFFIX = ""

    def __init__(self) -> None:
        self._path: Path | None = None

    @staticmethod
    def lazy(fun: F) -> F:

        @wraps(fun)
        def newfun(self: Lazy, *args: Any, **kwargs: Any) -> Any:
            self._check()
            return fun(self, *args, **kwargs)

        return cast(F, newfun)

    def _check(self) -> None:
        if self._path is not None:
            return

        name = self.hash() + self.SUFFIX
        temp = self.BASEDIR / ("." + name)
        try:
            self._create(temp)
            self._path = self.BASEDIR / (self.hash() + self.SUFFIX)
            temp.rename(self._path)
        finally:
            if temp.exists():
                temp.unlink()

    def _create(self, path: Path) -> None:
        raise NotImplementedError()

    def hash(self) -> str:
        raise NotImplementedError()


class File(Lazy, metaclass=ABCMeta):
    """base class for delayed file/image actions"""

    def __init__(self) -> None:
        Lazy.__init__(self)

    @staticmethod
    def hashed(fun: Callable[..., Any]) -> Callable[..., str]:
        def newfun(self: File, *args: Any, **kwargs: Any) -> str:
            ret = fun(self, *args, **kwargs)
            return sha256(repr(ret).encode("UTF-8")).hexdigest()

        return newfun

    @Lazy.lazy
    def path(self) -> Path:
        assert self._path is not None
        return self._path

    @Lazy.lazy
    def file_size(self) -> int:
        return self.path().stat().st_size


class BaseImage(File, metaclass=ABCMeta):

    def volume_size(self) -> int:
        raise NotImplementedError()
