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

import re
import subprocess

import univention.ucslint.base as uub
from univention.ucslint.common import RE_HASHBANG_SHELL


RE_BASHISM = re.compile(r'^.*?\s+line\s+(\d+)\s+[(](.*?)[)][:]\n([^\n]+)$')
RE_LOCAL = re.compile(
    r'''
    \blocal\b
    \s+
    \w+
    =
    (?:\$(?![?$!#\s'"]
        |\{[?$!#]\}
        |$)
    |`
    )
    ''',
    re.VERBOSE,
)


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

    def getMsgIds(self) -> uub.MsgIds:
        return {
            '0013-1': (uub.RESULT_WARN, 'failed to open file'),
            '0013-2': (uub.RESULT_ERROR, 'possible bashism found'),
            '0013-3': (uub.RESULT_WARN, 'cannot parse output of "checkbashism"'),
            '0013-4': (uub.RESULT_WARN, 'unquoted local variable'),
        }

    def check(self, path: str) -> None:
        super().check(path)

        for fn in uub.FilteredDirWalkGenerator(
                path,
                ignore_suffixes=['.po'],
                reHashBang=RE_HASHBANG_SHELL,
        ):
            self.debug(f'Testing file {fn}')
            try:
                self.check_bashism(fn)
                self.check_unquoted_local(fn)
            except (OSError, UnicodeDecodeError):
                self.addmsg('0013-1', 'failed to open file', fn)

    def check_bashism(self, fn: str) -> None:
        p = subprocess.Popen(['checkbashisms', fn], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        # 2 = file is no shell script or file is already bash script
        # 1 = bashism found
        # 0 = everything is posix compliant
        if p.returncode == 1:
            for item in stderr.decode('utf-8', 'replace').split('possible bashism in '):
                item = item.strip()
                if not item:
                    continue

                match = RE_BASHISM.search(item)
                if not match:
                    escaped = item.replace('\n', '\\n').replace('\r', '\\r')
                    self.addmsg('0013-3', f'cannot parse checkbashism output:\n"{escaped}"', fn)
                    continue

                row = int(match.group(1))
                msg = match.group(2)
                code = match.group(3)

                self.addmsg('0013-2', f'possible bashism ({msg}):\n{code}', fn, row)

    def check_unquoted_local(self, fn: str) -> None:
        with open(fn) as fd:
            for row, line in enumerate(fd, start=1):
                line = line.strip()
                match = RE_LOCAL.search(line)
                if not match:
                    continue

                self.addmsg('0013-4', f'unquoted local variable: {line}', fn, row)
