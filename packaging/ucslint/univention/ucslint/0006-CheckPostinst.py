# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2008-2023 Univention GmbH
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

from __future__ import annotations

from os import listdir
from os.path import join, normpath
from typing import Any

import univention.ucslint.base as uub


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

    def getMsgIds(self) -> uub.MsgIds:
        return {
            '0006-1': (uub.RESULT_WARN, 'postinst script does not contain string "#DEBHELPER#"'),
            '0006-2': (uub.RESULT_ERROR, 'script contains univention-directory-manager or univention-admin at beginning of a line - please use a join script'),
            '0006-3': (uub.RESULT_WARN, 'script contains univention-directory-manager or univention-admin - please use a join script'),
            '0006-4': (uub.RESULT_WARN, 'script contains "sh -e" in hashbang'),
            '0006-5': (uub.RESULT_WARN, 'script contains "set -e"'),
            '0006-6': (uub.RESULT_ERROR, 'script contains no "exit 0" at end of file'),
            '0006-7': (uub.RESULT_WARN, 'script uses broken remove_ucr_template'),
            '0006-8': (uub.RESULT_WARN, 'script uses broken remove_ucr_info_file'),
        }

    def check(self, path: str) -> None:
        super().check(path)

        fnlist_scripts: dict[str, dict[str, Any]] = {}

        #
        # search debian scripts
        #
        for f in listdir(normpath(join(path, 'debian'))):
            fn = normpath(join(path, 'debian', f))
            if f.rsplit('.', 1)[-1] in ['preinst', 'postinst', 'prerm', 'postrm']:
                fnlist_scripts[fn] = {
                    'debhelper': False,
                    'udm_calls': 0,
                    'udm_in_line': 0,
                    'set-e-hashbang': False,
                    'set-e-body': 0,
                    'endswith-exit-0': False,
                    'uses-remove_ucr_template': False,
                    'uses-remove_ucr_info_file': False,
                }
                self.debug(f'found {fn}')

        #
        # check scripts
        #
        for fn, checks in fnlist_scripts.items():
            try:
                with open(fn) as fd:
                    content = fd.read()
            except OSError:
                content = ''

            if not content:
                continue

            lines = content.splitlines()

            if '#DEBHELPER#' in lines:
                checks['debhelper'] = True

            # look for "set -e" in hashbang
            hashbang = lines[0]
            if '/bin/sh -e' in hashbang or '/bin/bash -e' in hashbang:
                checks['set-e-hashbang'] += 1

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                self.debug(f'line: {line}')
                for cmd in ['univention-directory-manager ', '/usr/sbin/univention-directory-manager ', 'univention-admin ', '/usr/sbin/univention-admin ']:
                    if line.startswith(cmd):
                        checks['udm_calls'] += 1
                    elif cmd in line:
                        checks['udm_in_line'] += 1

                # search for "set -e" in line
                if line.startswith('set -e'):
                    checks['set-e-body'] = True
                elif 'set -e' in line:
                    checks['set-e-body'] = True

                checks['endswith-exit-0'] = line.endswith('exit 0')

                checks['uses-remove_ucr_template'] |= 'remove_ucr_template ' in line
                checks['uses-remove_ucr_info_file'] |= 'remove_ucr_info_file ' in line

        #
        # create result
        #
        for fn, checks in fnlist_scripts.items():
            if not checks['debhelper']:
                self.addmsg('0006-1', 'script does not contain #DEBHELPER#', fn)

            if checks['set-e-hashbang']:
                self.addmsg('0006-4', 'script contains "sh -e" in hashbang', fn)

            if checks['set-e-body']:
                self.addmsg('0006-5', 'script contains "set -e"', fn)

            if checks['udm_calls']:
                self.addmsg('0006-2', f'script contains {checks["udm_calls"]} calls of univention-directory-manager or univention-admin - use a join script', fn)
            if checks['udm_in_line']:
                self.addmsg('0006-3', f'script may contain {checks["udm_in_line"]} calls of univention-directory-manager or univention-admin - please check and use a join script', fn)

            if not checks['endswith-exit-0']:
                self.addmsg('0006-6', 'script contains no "exit 0" at end of file', fn)

            if checks['uses-remove_ucr_template']:
                self.addmsg('0006-7', 'script uses broken remove_ucr_template; should use dpkg-maintscript-helper rm_conffile', fn)

            if checks['uses-remove_ucr_info_file']:
                self.addmsg('0006-8', 'script uses broken remove_ucr_info_file; should use dpkg-maintscript-helper rm_conffile', fn)
