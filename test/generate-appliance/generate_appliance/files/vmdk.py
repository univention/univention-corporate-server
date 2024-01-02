# SPDX-FileCopyrightText: 2014-2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

from .image import Image


class Vmdk(Image):
    SUFFIX = ".vmdk"
    FMT = "vmdk"
    OPTIONS = {
        "adapter_type": "lsilogic",
        "hwversion": "11",
        "subformat": "streamOptimized",
    }
