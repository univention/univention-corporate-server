#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2022 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
#

import sys
import os
import importlib


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
