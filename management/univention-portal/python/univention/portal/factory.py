#!/usr/bin/python3
#
# Univention Portal
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


import univention.portal.config as config
from univention.portal import get_dynamic_classes


def make_arg(arg_definition):
	arg_type = arg_definition["type"]
	if arg_type == "static":
		return arg_definition["value"]
	elif arg_type == "config":
		return config.fetch(arg_definition["key"])
	elif arg_type == "class":
		Klass = get_dynamic_classes(arg_definition["class"])
		args = []
		kwargs = {}
		for _arg_definition in arg_definition.get("args", []):
			args.append(make_arg(_arg_definition))
		for name, _arg_definition in arg_definition.get("kwargs", {}).items():
			kwargs[name] = make_arg(_arg_definition)
		return Klass(*args, **kwargs)
	raise TypeError("Unknown arg_definition: {!r}".format(arg_definition))


def make_portal(portal_definition):
	return make_arg(portal_definition)
