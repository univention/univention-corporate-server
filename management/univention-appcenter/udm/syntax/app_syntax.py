# -*- coding: utf-8 -*-
#
# Univention Directory Manager Modules
#  direcory manager syntax for Apps
#
# Copyright 2019 Univention GmbH
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

from univention.admin.syntax import boolean, TrueFalseUp, OkOrNot

# For UCS systems < UCS 4.4 in the domain we define these syntax classes and distribute them

try:
	from univention.admin.syntax import AppActivatedBoolean as appcenterFoo
	del appcenterFoo
except ImportError:
	class AppActivatedBoolean(boolean):
		pass

try:
	from univention.admin.syntax import AppActivatedTrue as appcenterFoo
	del appcenterFoo
except ImportError:
	class AppActivatedTrue(TrueFalseUp):
		pass

try:
	from univention.admin.syntax import AppActivatedOK as appcenterFoo
	del appcenterFoo
except ImportError:
	class AppActivatedOK(OkOrNot):
		pass
