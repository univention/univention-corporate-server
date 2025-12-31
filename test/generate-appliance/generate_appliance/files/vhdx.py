# SPDX-FileCopyrightText: 2014-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from .image import Image


class Vhdx(Image):
    SUFFIX = ".vhdx"
    FMT = "vhdx"
    OPTIONS = {
        "subformat": "dynamic",
    }
