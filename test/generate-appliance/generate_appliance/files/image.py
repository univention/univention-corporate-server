# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

import sys
from abc import ABCMeta
from json import loads
from logging import getLogger
from pathlib import Path
from subprocess import check_call, check_output
from typing import Any, Dict, Tuple  # noqa: F401

from . import BaseImage, Lazy
from .raw import Raw


log = getLogger(__name__)


class Image(BaseImage, metaclass=ABCMeta):
    FMT = ""
    OPTIONS: "Dict[str, str]" = {}

    def __init__(self, raw: Raw, **kwargs) -> None:
        assert isinstance(raw, Raw)
        self._raw = raw
        self.options = dict(self.OPTIONS, **kwargs)
        BaseImage.__init__(self)

    @BaseImage.hashed
    def hash(self) -> Tuple[Any, ...]:
        return (self.__class__, self._raw.hash, self.options)

    def _create(self, path: Path) -> None:
        self._raw.path()
        log.info('Creating %s %s', self.FMT.upper(), path)
        cmd = ['qemu-img', 'convert', '-p', '-O', self.FMT]
        for option in self.options.items():
            cmd += ["-o", "%s=%s" % option]
        cmd += [self._raw.path().as_posix(), path.as_posix()]
        check_call(cmd, stdout=sys.stderr)

    @Lazy.lazy
    def volume_size(self) -> int:
        cmd = [
            'qemu-img',
            'info',
            '-f',
            self.FMT,
            '--output',
            'json',
            self.path().as_posix(),
        ]
        output = check_output(cmd)
        data = loads(output.decode("utf-8"))
        return data["virtual-size"]
