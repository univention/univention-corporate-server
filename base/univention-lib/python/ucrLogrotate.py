#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
#
# Copyright 2010-2012 Univention GmbH
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

def _getBoolDefault(varGlobal, varLocal, settings, configRegistry):

	configName = varGlobal.split("/")[-1]
	if configRegistry.is_true(varGlobal, True):
		settings[configName] = configName
	if configRegistry.is_false(varLocal):
		if settings.get(configName): del settings[configName]
	if configRegistry.is_true(varLocal, False):
		settings[configName] = configName

def getLogrotateConfig(name, configRegistry):

	settings = {}

	for var in ["logrotate/", "logrotate/" + name + "/"]:

		if configRegistry.get(var + "rotate"): 
			settings["rotate"] = configRegistry[var + "rotate"] 
		if configRegistry.get(var + "rotate/count"): 
			settings["rotate/count"] = "rotate " + configRegistry[var + "rotate/count"] 
		if configRegistry.get(var + "size"): 
			settings["size"] = "size " + configRegistry[var + "size"] 
		if configRegistry.get(var + "create"): 
			settings["create"] = "create " + configRegistry[var + "create"] 

	_getBoolDefault("logrotate/missingok", "logrotate/" + name + "/missingok", settings, configRegistry)
	_getBoolDefault("logrotate/compress", "logrotate/" + name + "/compress", settings, configRegistry)
	_getBoolDefault("logrotate/notifempty", "logrotate/" + name + "/notifempty", settings, configRegistry)

	return settings
