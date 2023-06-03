# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

import sys
from logging import getLogger
from subprocess import check_call
from typing import Any, Tuple  # noqa: F401

from . import File
from .raw import Raw


log = getLogger(__name__)


class Vmdk(File):
    SUFFIX = ".vmdk"

    def __init__(self, raw, adapter_type="lsilogic", hwversion="11", subformat="streamOptimized"):
        # type: (Raw, str, str, str) -> None
        assert isinstance(raw, Raw)
        self._raw = raw
        self.options = {
            "adapter_type": adapter_type,
            "hwversion": hwversion,
            "subformat": subformat,
        }
        File.__init__(self)

    @File.hashed
    def hash(self):
        # type: () -> Tuple[Any, ...]
        return (Vmdk, self._raw.hash, self.options)

    def _create(self, path):
        # type: (str) -> None
        self._raw.path()
        log.info('Creating VMDK %s', path)
        cmd = ['qemu-img', 'convert', '-p', '-O', 'vmdk']
        for option in self.options.items():
            cmd += ["-o", "%s=%s" % option]
        cmd += [self._raw.path(), path]
        check_call(cmd, stdout=sys.stderr)
