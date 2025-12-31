#!/usr/bin/python3
#
# Univention Management Console
#  module: software management
#
# SPDX-FileCopyrightText: 2013-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import locale

import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.appcenter.actions import get_action
from univention.appcenter.app_cache import Apps
from univention.appcenter.log import log_to_logfile
from univention.management.console.modules.appcenter.sanitizers import error_handling
from univention.management.console.modules.decorators import simple_response


_ = umc.Translation('univention-management-console-module-apps').translate


class Instance(umcm.Base):

    def init(self):
        locale.setlocale(locale.LC_ALL, str(self.locale))
        try:
            log_to_logfile()
        except OSError:
            pass

    @simple_response
    def get(self, application):
        app = Apps().find(application)
        domain = get_action('domain')
        if app is None:
            return None
        return domain.to_dict([app])[0]

    def error_handling(self, etype, exc, etraceback):
        error_handling(etype, exc, etraceback)
        return super().error_handling(exc, etype, etraceback)
