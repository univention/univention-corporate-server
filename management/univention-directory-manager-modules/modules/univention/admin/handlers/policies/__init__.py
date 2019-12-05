#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  import all policy modules
#
# Copyright 2004-2020 Univention GmbH
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

__path__ = __import__('pkgutil').extend_path(__path__, __name__)  # type: ignore

import os
import os.path
import sys
if sys.version_info >= (3,):
	import importlib


policies = []


def import_py3():
	base_name = ".".join(__name__.split(".")[:-1])
	path = os.path.abspath(os.path.dirname(__file__))
	for w_root, w_dirs, w_files in os.walk(path):
		for file_ in w_files:
			if not file_.endswith('.py') or file_.startswith('__') or file_ in ('policy.py', 'base.py'):
				continue
			file_path = os.path.join(w_root, file_)
			module_name = base_name + "." + file_[: -3]
			spec = importlib.util.spec_from_file_location(module_name, file_path)
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)
			policies.append(module)


def import_py2():
	path = os.path.abspath(os.path.dirname(__file__))
	for w_root, w_dirs, w_files in os.walk(path):
		for file_ in w_files:
			if not file_.endswith('.py') or file_.startswith('__') or file_ in ('policy.py', 'base.py'):
				continue
			policies.append(__import__(file_[: -3], globals(), locals(), ['']))


if sys.version_info >= (3,):
	import_py3()
else:
	import_py2()
