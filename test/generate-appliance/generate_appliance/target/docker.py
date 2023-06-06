# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

import os
import sys
from argparse import Namespace
from logging import getLogger
from subprocess import check_call

from ..files.raw import Raw
from . import Target

log = getLogger(__name__)


class Docker(Target):
    """Docker Image (tgz)"""

    default = False

    def create(self, image: Raw, options: Namespace) -> None:
        archive_name = os.path.join(os.getcwd(), '%s-docker.tar' % (options.filename,))
        if os.path.exists(archive_name):
            raise IOError('Output file %r exists' % (archive_name,))

        image_path = image.path()
        log.info('Guestfishing')
        cmd = [
            'guestfish',
            'add-ro', image_path, ':',
            'run', ':',
            'mount', '/dev/vg_ucs/root', '/', ':',
            'mount', '/dev/sda1', '/boot', ':',
            'tar-out', '/', archive_name,
        ]
        check_call(cmd, stdout=sys.stderr)
        log.info('Generated "%s" appliance as\n  %s', self, archive_name)
