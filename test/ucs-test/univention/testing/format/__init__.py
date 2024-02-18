# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Import all UCS Test formatters."""
from univention.testing.format.html import HTML as format_html  # noqa: F401
from univention.testing.format.jenkins import Jenkins as format_jenkins  # noqa: F401
from univention.testing.format.junit import Junit as format_junit  # noqa: F401
from univention.testing.format.tap import TAP as format_tap  # noqa: F401
from univention.testing.format.text import Raw as format_raw, Text as format_text  # noqa: F401


FORMATS = [f[7:] for f in dir() if f.startswith('format_')]
