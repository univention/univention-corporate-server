# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

from logging import getLogger

from ..files.pkzip import Pkzip
from ..files.raw import Raw
from ..files.vhdx import Vhdx
from . import TargetFile


log = getLogger(__name__)


class HyperV(TargetFile):
    """Hyper-V Image (zip)"""

    SUFFIX = "hyperv.zip"
    default = False

    def create(self, image: Raw) -> None:
        options = self.options
        image_name = f"{options.product}.vhdx"
        archive_name = self.archive_name()

        vhdx = Vhdx(image)
        files = [
            (image_name, vhdx),
        ]
        pkzip = Pkzip(files)
        pkzip.path().rename(archive_name)
        log.info('Generated "%s" appliance as\n  %s', self, archive_name)
