#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import importlib
import os
import sys


def import_module(name, local_src_path, python_module_name, use_installed):
    if use_installed:
        module_name = python_module_name
    else:
        if local_src_path not in sys.path:
            sys.path.insert(1, local_src_path)
        module_name = name
    module = importlib.import_module(module_name)
    sys.modules[python_module_name] = module
    return module


def skipifbuildingpackage(func):
    import pytest
    return pytest.mark.skipif(bool(os.environ.get('DEBBUILDOPTS')), reason='Skipping in build environment. You need to check this test manually')(func)
