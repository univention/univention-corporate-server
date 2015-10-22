#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  App Center sanitizers
#
# Copyright 2011-2015 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

from univention.management.console.modules.sanitizers import Sanitizer, StringSanitizer, DictSanitizer, BooleanSanitizer
import univention.config_registry
import univention.management.console as umc
from univention.appcenter.app import AppManager


_ = umc.Translation('univention-management-console-module-appcenter').translate


class AppSanitizer(Sanitizer):
	def _sanitize(self, value, name, further_args):
		return AppManager.find(value)


# TODO: remove this, unused!
class AnySanitizer(Sanitizer):
	def _sanitize(self, value, name, further_args):
		any_given = any([value] + further_args.values())
		if not any_given:
			self.raise_formatted_validation_error(_('Any of %r must be given') % ([name] + further_args.keys()), name, value)
		return any_given


class NoDoubleNameSanitizer(StringSanitizer):
	def _sanitize(self, value, name, further_arguments):
		from constants import COMPONENT_BASE
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
		if '%s/%s' % (COMPONENT_BASE, value) in ucr:
			self.raise_validation_error(_("There already is a component with this name"))
		return value


basic_components_sanitizer = DictSanitizer({
		'server': StringSanitizer(required=True, minimum=1),
		'prefix': StringSanitizer(required=True),
		'unmaintained': BooleanSanitizer(required=True),
	},
	allow_other_keys=False,
)


advanced_components_sanitizer = DictSanitizer({
		'server': StringSanitizer(),
		'prefix': StringSanitizer(),
		'unmaintained': BooleanSanitizer(),
		'enabled': BooleanSanitizer(required=True),
		'name': StringSanitizer(required=True, regex_pattern='^[A-Za-z0-9\-\_\.]+$'),
		'description': StringSanitizer(),
		'username': StringSanitizer(),
		'password': StringSanitizer(),
		'version': StringSanitizer(regex_pattern='^((([0-9]+\\.[0-9]+|current),)*([0-9]+\\.[0-9]+|current))?$')
	}
)


add_components_sanitizer = advanced_components_sanitizer + DictSanitizer({
		'name': NoDoubleNameSanitizer(required=True, regex_pattern='^[A-Za-z0-9\-\_\.]+$'),
	}
)
