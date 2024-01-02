#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system halt/reboot
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2014-2024 Univention GmbH
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
from functools import wraps

import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.error import BadRequest
# from univention.lib.package_manager import CMD_DISABLE_EXEC, CMD_ENABLE_EXEC
from univention.management.console.log import MODULE
from univention.management.console.modules.adtakeover import takeover
from univention.management.console.modules.decorators import simple_response, threaded


_ = umc.Translation('univention-management-console-module-adtakeover').translate


def reset_progress(func):
    @wraps(func)
    def _foreground(self, request):
        self.progress.reset()
        MODULE.process('Running %s' % func.__name__)
        try:
            return func(self, request)
        except takeover.TakeoverError as exc:
            MODULE.warn('Error during %s: %s' % (func.__name__, exc))
            message = str(exc)
            self.progress.error(message)
            raise BadRequest(message)
        except Exception:
            tb_text = traceback.format_exc()
            message = _("Execution of command '%(command)s' has failed:\n\n%(text)s") % {
                'command': func.__name__,
                'text': tb_text,
            }
            MODULE.process(message)
            self.progress.error(message)
            raise
        finally:
            self.progress.finish()
    return _foreground


class Instance(umcm.Base):

    def init(self):
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

    @threaded
    @reset_progress
    def connect(self, request):
        username, password, ip = (request.options[var] for var in ['username', 'password', 'ip'])
        return takeover.count_domain_objects_on_server(ip, username, password, self.progress)

    @threaded
    @reset_progress
    def copy_domain_data(self, request):
        username, password, ip = (request.options[var] for var in ['username', 'password', 'ip'])
        takeover.join_to_domain_and_copy_domain_data(ip, username, password, self.progress)

    @simple_response
    def sysvol_info(self):
        return takeover.sysvol_info()

    @threaded
    @reset_progress
    def check_sysvol(self, request):
        takeover.check_sysvol(self.progress)

    @threaded
    @reset_progress
    def take_over_domain(self, request):
        takeover.take_over_domain(self.progress)
