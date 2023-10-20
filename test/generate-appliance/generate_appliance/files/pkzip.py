# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

from logging import getLogger
from pathlib import Path
from zipfile import ZipFile

from . import File
from .archive import Archive


log = getLogger(__name__)


class Pkzip(Archive):
    SUFFIX = ".zip"

    def _create(self, path: Path) -> None:
        _ = [source_file.path() for _, source_file in self._file_list if isinstance(source_file, File)]
        log.info('Creating PKZIP %s', path)
        with ZipFile(path.as_posix(), mode="w", allowZip64=True) as archive:
            for name, source_file in self._file_list:
                if isinstance(source_file, bytes):
                    archive.writestr(name, source_file)
                else:
                    archive.write(source_file.path().as_posix(), name)
