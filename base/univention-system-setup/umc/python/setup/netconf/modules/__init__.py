"""
Univention Setup: network configuration abstract base classes
"""
# Copyright 2004-2019 Univention GmbH
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
import sys
import os
import logging
import imp
from univention.management.console.modules.setup.netconf import Phase, SkipPhase


class RunPhases(object):

	"""
	Handle modules for network configuration.
	<http://lkubuntu.wordpress.com/2012/10/02/writing-a-python-plugin-api/>
	"""

	def __init__(self):
		self.classes = []
		self.phases = []
		self.logger = logging.getLogger("uss.network.plug")

	def find(self):
		for module_dir in sys.modules[__name__].__path__:
			for dirpath, dirnames, filenames in os.walk(module_dir):
				self.logger.debug("Processing '%s'...", dirpath)
				for filename in filenames:
					name, ext = os.path.splitext(filename)
					if ext not in (".py",):
						self.logger.debug("Skipping '%s'", filename)
						continue
					try:
						info = imp.find_module(name, [dirpath])
					except ImportError:
						self.logger.warn("Failed to open '%s'", filename)
					yield name, info

	def load(self):
		for name, (pfile, filename, desc) in self.find():
			try:
				module = imp.load_module(name, pfile, filename, desc)
			except SyntaxError as ex:
				self.logger.warn("Failed to import '%s': %s", name, ex)
			finally:
				if pfile:
					pfile.close()
			for key, value in vars(module).items():
				if not key.startswith('_'):
					self.add(key, value)
		self.logger.info("Finished loading %d modules", len(self.classes))

	def add(self, name, obj):
		try:
			Phase._check_valid(obj)
			self.logger.info("Adding phase %s", name)
			self.classes.append(obj)
		except SkipPhase as ex:
			self.logger.debug("Phase '%s' is invalid: %s", name, ex)

	def setup(self, changeset):
		for clazz in self.classes:
			self.logger.info("Configuring phase %s...", clazz.__name__)
			try:
				phase = clazz(changeset)
				self.logger.debug("Calling %s.check()...", phase)
				phase.check()
				self.logger.info("Adding phase %s as %02d", phase, phase.priority)
				self.phases.append(phase)
			except SkipPhase as ex:
				self.logger.warn("Phase skipped: %s", ex)

	def pre(self):
		for phase in sorted(self.phases):
			self.logger.info("Calling %s.pre() at %02d...", phase, phase.priority)
			try:
				phase.pre()
			except Exception as ex:
				self.logger.warn("Failed %s.pre(): %s", phase, ex, exc_info=True)

	def post(self):
		for phase in sorted(self.phases, reverse=True):
			self.logger.info("Calling %s.post() at %02d...", phase, phase.priority)
			try:
				phase.post()
			except Exception as ex:
				self.logger.warn("Failed %s.post(): %s", phase, ex, exc_info=True)
