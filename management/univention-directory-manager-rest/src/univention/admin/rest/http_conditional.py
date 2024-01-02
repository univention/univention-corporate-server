#!/usr/bin/python3
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2017-2024 Univention GmbH
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

import datetime
import hashlib
import re
import time
from email.utils import parsedate

from tornado.web import Finish, HTTPError

from univention.lib.i18n import Translation


_ = Translation('univention-directory-manager-rest').translate


def last_modified(date):
    return '%s, %02d %s %04d %02d:%02d:%02d GMT' % (
        ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')[date.tm_wday],
        date.tm_mday,
        ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')[date.tm_mon - 1],
        date.tm_year, date.tm_hour, date.tm_min, date.tm_sec,
    )


class ConditionalResource:

    def set_entity_tags(self, obj, check_conditionals=True, remove_after_check=False):
        self.set_header('Etag', self.get_etag(obj))
        modified = self.modified_from_timestamp(obj.oldattr['modifyTimestamp'][0].decode('utf-8', 'replace'))
        if modified:
            self.set_header('Last-Modified', last_modified(modified))
        if check_conditionals:
            self.check_conditional_requests()
        if remove_after_check:
            self._headers.pop("Etag", None)
            self._headers.pop("Last-Modified", None)

    def get_etag(self, obj):
        # generate as early as possible, to not cause side effects e.g. default values in obj.info. It must be the same value for GET and PUT
        if not obj._open:
            raise RuntimeError('Object was not opened!')
        etag = hashlib.sha1()
        etag.update(obj.dn.encode('utf-8', 'replace'))
        etag.update(obj.module.encode('utf-8', 'replace'))
        etag.update(b''.join(obj.oldattr.get('entryCSN', [])))
        etag.update((obj.entry_uuid or '').encode('utf-8'))
        #etag.update(json.dumps({k: [v.decode('ISO8859-1', 'replace') for v in val] for k, val in obj.oldattr.items()}, sort_keys=True).encode('utf-8'))
        #etag.update(json.dumps(obj.info, sort_keys=True).encode('utf-8'))
        return '"%s"' % etag.hexdigest()

    def modified_from_timestamp(self, timestamp):
        modified = time.strptime(timestamp, '%Y%m%d%H%M%SZ')
        # make sure Last-Modified is only send if it is not now
        if modified < time.gmtime(time.time() - 1):
            return modified

    def check_conditional_requests(self):
        etag = self._headers.get("Etag", "")
        if etag:
            self.check_conditional_request_etag(etag)

        last_modified = parsedate(self._headers.get('Last-Modified', ''))
        if last_modified is not None:
            last_modified = datetime.datetime(*last_modified[:6])
            self.check_conditional_request_modified_since(last_modified)
            self.check_conditional_request_unmodified_since(last_modified)

    def check_conditional_request_modified_since(self, last_modified):
        date = parsedate(self.request.headers.get('If-Modified-Since', ''))
        if date is not None:
            if_since = datetime.datetime(*date[:6])
            if if_since >= last_modified:
                self.set_status(304)
                raise Finish()

    def check_conditional_request_unmodified_since(self, last_modified):
        date = parsedate(self.request.headers.get('If-Unmodified-Since', ''))
        if date is not None:
            if_not_since = datetime.datetime(*date[:6])
            if last_modified > if_not_since:
                raise HTTPError(412, _('If-Unmodified-Since does not match Last-Modified.'))

    def check_conditional_request_etag(self, etag):
        safe_request = self.request.method in ('GET', 'HEAD', 'OPTIONS')

        def wheak(x):
            return x[2:] if x.startswith('W/') else x
        etag_matches = re.compile(r'\*|(?:W/)?"[^"]*"')

        def check_conditional_request_if_none_match():
            etags = etag_matches.findall(self.request.headers.get("If-None-Match", ""))
            if not etags:
                if self.request.headers.get("If-None-Match"):
                    raise HTTPError(400, 'Invalid "If-None-Match" syntax.')
                return

            if '*' in etags or wheak(etag) in map(wheak, etags):
                if safe_request:
                    self.set_status(304)  # Not modified
                    raise Finish()
                else:
                    message = _('The resource has meanwhile been changed. If-None-Match %s does not match entity tag %s.') % (', '.join(etags), etag)
                    raise HTTPError(412, message)  # Precondition Failed

        def check_conditional_request_if_match():
            etags = etag_matches.findall(self.request.headers.get("If-Match", ""))
            if not etags:
                if self.request.headers.get("If-Match"):
                    raise HTTPError(400, 'Invalid "If-Match" syntax.')
                return
            if '*' not in etags and wheak(etag) not in map(wheak, etags):
                message = _('The resource has meanwhile been changed. If-Match %s does not match entity tag %s.') % (', '.join(etags), etag)
                if not safe_request:
                    raise HTTPError(412, message)  # Precondition Failed
                elif self.request.headers.get('Range'):
                    raise HTTPError(416, message)  # Range Not Satisfiable

        check_conditional_request_if_none_match()
        check_conditional_request_if_match()
