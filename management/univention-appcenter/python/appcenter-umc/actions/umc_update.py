#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for updating the list of available apps
#  (UMC version)
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import os
import os.path
import shutil
import stat
from glob import glob


try:
    # try to derive from docker's update
    from univention.appcenter.actions.docker_update import Update
except ImportError:
    # otherwise take the normal one
    from univention.appcenter.actions.update import Update

from univention.appcenter.app_cache import AllApps, Apps
from univention.appcenter.extended_attributes import create_option_icon


FRONTEND_ICONS_DIR = '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/scalable'


class Update(Update):

    def _update_local_files(self):
        super()._update_local_files()

        self.debug('Updating app icon files in UMC directory...')

        # clear existing SVG logo files and re-copy them again
        for isvg in glob(os.path.join(FRONTEND_ICONS_DIR, 'apps-*.svg')):
            os.unlink(isvg)

        for app in AllApps().get_all_apps():
            create_option_icon(app)
            for _app in Apps().get_all_apps_with_id(app.id):
                self._update_svg_file(_app.logo_name, _app.get_cache_file('logo'))
                self._update_svg_file(_app.logo_detail_page_name, _app.get_cache_file('logodetailpage'))

    def _get_conffiles(self):
        conffiles = super()._get_conffiles()
        return [*conffiles, '/usr/share/univention-management-console/modules/apps.xml', '/usr/share/univention-management-console/i18n/de/apps.mo']

    def _update_svg_file(self, _dest_file, src_file):
        if not _dest_file:
            return
        dest_file = os.path.join(FRONTEND_ICONS_DIR, _dest_file)
        if os.path.exists(src_file):
            shutil.copy2(src_file, dest_file)
            # self.debug('copying %s -> %s' % (src_file, dest_file))

            # images are created with UMC umask: -rw-------
            # change the mode to UCS umask:      -rw-r--r--
            os.chmod(dest_file, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IROTH)
