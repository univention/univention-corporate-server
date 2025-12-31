# SPDX-FileCopyrightText: 2014-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from .image import Image


class Vmdk(Image):
    SUFFIX = ".vmdk"
    FMT = "vmdk"
    OPTIONS = {
        "adapter_type": "lsilogic",
        "hwversion": "11",
    }
