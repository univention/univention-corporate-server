# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

import sys
from logging import getLogger
from subprocess import check_call

from ..files.raw import Raw
from . import TargetFile


log = getLogger(__name__)


class Docker(TargetFile):
    """Docker Image (tgz)"""

    SUFFIX = "docker.tar"
    default = False

    def create(self, image: Raw,) -> None:
        archive_name = self.archive_name()

        image_path = image.path()
        log.info('Guestfishing')
        cmd = [
            'guestfish',
            'add-ro', image_path.as_posix(), ':',
            'run', ':',
            'mount', '/dev/vg_ucs/root', '/', ':',
            'mount', '/dev/sda1', '/boot', ':',
            'tar-out', '/', archive_name.as_posix(),
        ]
        check_call(cmd, stdout=sys.stderr,)
        log.info('Generated "%s" appliance as\n  %s', self, archive_name,)
