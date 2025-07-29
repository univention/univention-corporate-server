#!/usr/bin/python3
#
# Univention Management Console
#  module: system halt/reboot
#
# SPDX-FileCopyrightText: 2014-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

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
