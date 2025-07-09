#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""import all computer modules"""

import importlib
import os
import os.path


__path__ = __import__('pkgutil').extend_path(__path__, __name__)  # type: ignore


computers = [
    importlib.import_module('%s.%s' % (__name__, fn[:-3]))
    for fn in os.listdir(os.path.dirname(__file__))
    if fn.endswith('.py') and not fn.startswith('__') and fn not in ('computer.py',)
]
