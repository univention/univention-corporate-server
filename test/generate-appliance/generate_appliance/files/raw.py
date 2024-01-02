# SPDX-FileCopyrightText: 2014-2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

from pathlib import Path
from typing import IO, Any, Tuple

from . import BaseImage


class Raw(BaseImage):
    """represents a "RAW" disk image"""

    def __init__(self, inputfile: IO[bytes]) -> None:
        BaseImage.__init__(self)
        self._inputfile = inputfile
        self._path = Path(inputfile.name)

    @BaseImage.hashed
    def hash(self) -> Tuple[Any, ...]:
        return (Raw, self._inputfile)

    def _create(self, path: Path) -> None:
        pass

    def volume_size(self) -> int:
        return self.file_size()
