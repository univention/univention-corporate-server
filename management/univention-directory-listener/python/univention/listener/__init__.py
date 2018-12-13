# -*- coding: utf-8 -*-
#
# Copyright 2017-2019 Univention GmbH
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
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.


"""
Listener module API

To create a listener module (LM) with this API, create a Python file in
/usr/lib/univention-directory-listener/system/ which includes:

1. a subclass of ListenerModuleHandler
2. with an inner class "Configuration" that has at least the class attributes
   "name", "description" and "ldap_filter"

See /usr/share/doc/univention-directory-listener/examples/ for examples.
"""

from __future__ import absolute_import
from univention.listener.api_adapter import ListenerModuleAdapter
from univention.listener.handler_configuration import ListenerModuleConfiguration
from univention.listener.handler import ListenerModuleHandler
from univention.listener.exceptions import ListenerModuleConfigurationError, ListenerModuleRuntimeError

__all__ = [
	'ListenerModuleAdapter', 'ListenerModuleConfigurationError', 'ListenerModuleRuntimeError',
	'ListenerModuleConfiguration', 'ListenerModuleHandler'
]
