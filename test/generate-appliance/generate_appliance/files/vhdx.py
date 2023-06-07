# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

import sys
from logging import getLogger
from pathlib import Path
from subprocess import check_call
from typing import Any, Tuple

from . import File
from .raw import Raw


log = getLogger(__name__)


class Vhdx(File):
    SUFFIX = ".vhdx"

    def __init__(self, raw: Raw) -> None:
        assert isinstance(raw, Raw)
        self._raw = raw
        File.__init__(self)

    @File.hashed
    def hash(self) -> Tuple[Any, ...]:
        return (Vhdx, self._raw.hash)

    def _create(self, path: Path) -> None:
        self._raw.path()
        log.info('Creating VHDX %s', path)
        cmd = [
            'qemu-img',
            'convert',
            '-p',
            '-O',
            'vhdx',
            '-o',
            'subformat=dynamic',
            self._raw.path().as_posix(),
            path.as_posix(),
        ]
        check_call(cmd, stdout=sys.stderr)
