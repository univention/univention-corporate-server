# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import re


def expand_path(xpath: str) -> str:
    # replaces instances of [@containsClass="className"]
    # with
    # [contains(concat(" ", normalize-space(@class), " "), " className ")]
    pattern = r'(?<=\[)@containsClass=([\"\'])(.*?)\1(?=\])'
    replacement = r'contains(concat(\1 \1, normalize-space(@class), \1 \1), \1 \2 \1)'
    return re.sub(pattern, replacement, xpath)
