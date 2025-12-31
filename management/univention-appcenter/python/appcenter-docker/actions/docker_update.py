#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for updating the list of available apps
#  (Docker version)
#
# SPDX-FileCopyrightText: 2017-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from univention.appcenter.actions.update import Update


class Update(Update):
    def _get_conffiles(self):
        conffiles = super()._get_conffiles()
        return [*conffiles, '/etc/apache2/sites-available/000-default.conf', '/etc/apache2/sites-available/default-ssl.conf']
