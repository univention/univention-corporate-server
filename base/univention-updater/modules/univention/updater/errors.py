#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages updates
#
# Copyright 2008-2014 Univention GmbH
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

class UpdaterException(Exception):
	"""The root of all updater excptions."""
	pass


class RequiredComponentError(UpdaterException):
	"""Signal required component not available."""
	def __init__(self, version, components):
		self.version = version
		self.components = components

	def __str__(self):
		if len(self.components) == 1:
			return "The update to UCS %s is blocked because the component '%s' is marked as required." % (
				self.version, self.component[0])
		return "The update to UCS %s is blocked because the components %s are marked as required." % (
			self.version, ', '.join("'%s'" for _ in self.component))

class PreconditionError(UpdaterException):
    """Signal abort by release or component pre-/post-update script.
    args=(phase=preup|postup, order=pre|main|post, component, script-filename)."""
    def __init__(self, phase, order, component, script):
        Exception.__init__(self, phase, order, component, script)

class DownloadError(UpdaterException):
	"""Signal temporary error in network communication."""
	def __str__(self):
		return "Error downloading %s: %d" % self.args

class ConfigurationError(UpdaterException):
	"""Signal permanent error in configuration."""
	def __str__(self):
		return "Configuration error: %s" % self.args[1]

class VerificationError(ConfigurationError):
	"""Signal permanent error in script verification."""
	def __str__(self):
		return "Verification error: %s" % self.args[1]

class CannotResolveComponentServerError(ConfigurationError):
	"""Signal permanent error in component configuration."""
	def __init__(self, component, for_mirror_list):
		self.component = component
		self.for_mirror_list = for_mirror_list
	def __str__(self):
		return "Cannot resolve component server for disabled component '%s' (mirror_list=%s)." % (self.component, self.for_mirror_list)

class ProxyError(ConfigurationError):
	"""Signal permanent error in proxy configuration."""
	def __str__(self):
		return "Proxy configuration error: %s" % self.args[1]

class LockingError(UpdaterException):
	"""Signal other updater process running."""
	def __str__(self):
		return "Another updater process is currently running - abort\n%s" % self.args[0]
