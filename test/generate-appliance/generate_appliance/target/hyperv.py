# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

import os
from argparse import Namespace  # noqa: F401
from logging import getLogger

from ..files.pkzip import Pkzip
from ..files.raw import Raw  # noqa: F401
from ..files.vhdx import Vhdx
from . import Target


log = getLogger(__name__)


class HyperV(Target):
    """Hyper-V Image (zip)"""

    default = False

    def create(self, image, options):
        # type: (Raw, Namespace) -> None
        options = self.options
        image_name = "%s.vhdx" % (options.product,)
        if options.no_target_specific_filename:
            archive_name = options.filename
        else:
            archive_name = '%s-hyperv.zip' % (options.filename,)
        if os.path.exists(archive_name):
            raise IOError('Output file %r exists' % (archive_name,))

        vhdx = Vhdx(image)
        files = [
            (image_name, vhdx),
        ]
        pkzip = Pkzip(files)
        os.rename(pkzip.path(), archive_name)
        log.info('Generated "%s" appliance as\n  %s', self, archive_name)
