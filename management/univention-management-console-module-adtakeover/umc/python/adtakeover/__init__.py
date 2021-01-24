#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system halt/reboot
#
# Copyright 2014-2021 Univention GmbH
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

import traceback
from threading import Thread

from univention.config_registry import ConfigRegistry
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.protocol.definitions import SUCCESS, BAD_REQUEST, MODULE_ERR_COMMAND_FAILED
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import simple_response
# from univention.lib.package_manager import CMD_DISABLE_EXEC, CMD_ENABLE_EXEC

from univention.management.console.modules.adtakeover import takeover

ucr = ConfigRegistry()
ucr.load()
_ = umc.Translation('univention-management-console-module-adtakeover').translate


def background(func):
	def _foreground(self, request):
		def _background(self, request):
			self.progress.reset()
			MODULE.process('Running %s' % func.__name__)
			result = None
			message = None
			status = SUCCESS
			try:
				result = func(self, request)
			except takeover.TakeoverError as exc:
				status = BAD_REQUEST
				MODULE.warn('Error during %s: %s' % (func.__name__, exc))
				message = str(exc)
				self.progress.error(message)
			except Exception:
				status = MODULE_ERR_COMMAND_FAILED
				tb_text = traceback.format_exc()
				message = _("Execution of command '%(command)s' has failed:\n\n%(text)s") % {
					'command': func.__name__,
					'text': tb_text,
				}
				MODULE.process(message)
				self.progress.error(message)
			finally:
				self.finished(request.id, result, status=status, message=message)
				self.progress.finish()
		thread = Thread(target=_background, args=[self, request])
		thread.start()
	return _foreground


class Instance(umcm.Base):

	def __init__(self):
		super(Instance, self).__init__()
		self.progress = takeover.Progress()

	@simple_response
	def poll(self):
		return self.progress.poll()

	@simple_response
	def check_status(self):
		return takeover.check_status()

	@simple_response
	def set_status_done(self):
		takeover.set_status_done()

	@background
	def connect(self, request):
		username, password, ip = [request.options[var] for var in ['username', 'password', 'ip']]
		return takeover.count_domain_objects_on_server(ip, username, password, self.progress)

	@background
	def copy_domain_data(self, request):
		username, password, ip = [request.options[var] for var in ['username', 'password', 'ip']]
		takeover.join_to_domain_and_copy_domain_data(ip, username, password, self.progress)

	@simple_response
	def sysvol_info(self):
		return takeover.sysvol_info()

	@background
	def check_sysvol(self, request):
		takeover.check_sysvol(self.progress)

	@background
	def take_over_domain(self, request):
		takeover.take_over_domain(self.progress)
