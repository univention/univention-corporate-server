# -*- coding: utf-8 -*-
#
# Univention Application Reporting
#
# Copyright (C) 2015 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of the software contained in this package
# as well as the source package itself are made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this package provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use the software under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

__version__ = '1.0'

import urllib2
from socket import error as SocketError

from univention.appreport.api import UniventionServer
import univention.debug as ud


class ConnectionManager(object):

	user_agent = 'univention.appreport/%s' % (__version__,)
	timeout = 60

	def __init__(self):
		self.opener = self.build_opener()
		self.default_headers()

	def build_opener(self):
		handler = urllib2.BaseHandler()
		proxy_handler = urllib2.ProxyHandler()
		opener = urllib2.build_opener(handler, proxy_handler)
		return opener

	def default_headers(self):
		self.opener.addheaders = [('User-Agent', self.user_agent)]

	def request(self, request):
		try:
			response = self._request(request)
		except (SocketError,) as exc:
			ud.debug(ud.MAIN, ud.ERROR, 'Connection failed (%r): %s' % (request, self.http_error_string(exc)))
		except (urllib2.HTTPError, urllib2.URLError) as exc:
			ud.debug(ud.MAIN, ud.ERROR, 'Request failed (%r): %s' % (request, self.http_error_string(exc)))
		else:
			ud.debug(ud.MAIN, ud.INFO, 'Request successful: %s' % (response.getcode(),))

	def http_error_string(self, exc):
		return '%s: %s: errno=%r, reason=%r, strerror=%r' % (type(exc), exc, getattr(exc, 'errno', ''), getattr(exc, 'reason', ''), getattr(exc, 'strerror', ''))

	def _request(self, request):
		return self.opener.open(request.request, timeout=self.timeout)


class AppReporting(object):

	def __init__(self):
		self.connection = ConnectionManager()

	def main(self):
		self.log_init()
		self.make_requests()

	def log_init(self):
		ud.init('stderr', ud.FLUSH, ud.NO_FUNCTION)

	def make_requests(self):
		for service in self.services():
			ud.debug(ud.MAIN, ud.PROCESS, 'Processing requests for service %s' % (type(service).__name__,))
			for request in service.requests():
				ud.debug(ud.MAIN, ud.PROCESS, 'Requesting %s' % (request,))
				self.connection.request(request)

	def services(self):
		yield UniventionServer()


if __name__ == '__main__':
	AppReporting().main()
