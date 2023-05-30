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


IMAGE_DESCRIPTOR = '''# Description file created by VMDK stream converter
version=1
# Believe this is random
CID=7e5b80a7
# Indicates no parent
parentCID=ffffffff
createType="streamOptimized"
# Extent description
RDONLY #SECTORS# SPARSE "call-me-stream.vmdk"
# The Disk Data Base
#DDB
ddb.adapterType = "lsilogic"
# #SECTORS# / 63 / 255 rounded up
ddb.geometry.cylinders = "#CYLINDERS#"
ddb.geometry.heads = "255"
ddb.geometry.sectors = "63"
# Believe this is random
ddb.longContentID = "8f15b3d0009d9a3f456ff7b28d324d2a"
ddb.virtualHWVersion = "11"'''


class Vmdk(File):
    SUFFIX = ".vmdk"

    def __init__(self, raw, image_descriptor="", streamOptimized=False):
        # type: (Raw, str, bool) -> None
        assert isinstance(raw, Raw)
        self._raw = raw
        self.image_descriptor = image_descriptor or IMAGE_DESCRIPTOR
        self._streamOptimized = streamOptimized
        File.__init__(self)

    @File.hashed
    def hash(self):
        # type: () -> Tuple[Any, ...]
        return (Vmdk, self.image_descriptor, self._raw.hash, self._streamOptimized)

    def _create(self, path):
        # type: (str) -> None
        self._raw.path()
        fmt = "streamOptimized" if self._streamOptimized else "monolithicSparse"
        log.info('Creating VMDK %s (%s)', path, fmt)
        cmd = ('qemu-img', 'convert', '-p', '-O', 'vmdk', '-o', 'subformat=%s' % (fmt,), self._raw.path(), path)
        check_call(cmd, stdout=sys.stderr)
