#!/usr/bin/python2.7
#
# Univention Portal
#
# Copyright 2019-2020 Univention GmbH
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

from six import with_metaclass
import requests

from univention.portal import Plugin
from univention.portal.log import get_logger

#ucr = ConfigRegistry()
#ucr.load()
#
#_umc_interface = ucr.get("umc/http/interface", "127.0.0.1")
#_umc_port = int(ucr.get("umc/http/port", 8090))
#UMC_SESSION_URL = "http://%s:%s/get/session-info" % (_umc_interface, _umc_port)

from univention.portal.user import User

class Authenticator(with_metaclass(Plugin)):
	def get_user(self, request):
		return None


class UMCAuthenticator(Authenticator):
	def __init__(self, umc_session_url, group_cache, portal_cookie_name="UMCSessionId", umc_cookie_name=None):
		self.umc_session_url = umc_session_url
		self.group_cache = group_cache
		self.portal_cookie_name = portal_cookie_name
		self.umc_cookie_name = umc_cookie_name or portal_cookie_name

	def refresh(self, force=False):
		return self.group_cache.refresh(force=force)

	def get_user(self, request):
		session = request.get_cookie(self.portal_cookie_name)
		username = request._get_username(session)
		groups = self.group_cache.get().get(username, [])
		return User(username, groups=groups)

	def _get_username(self, session):
		if session is None:
			get_logger("user").debug("no user given")
			return None
		get_logger("user").debug("searching user for %s" % session)
		username = self._ask_umc(session)
		if username is None:
			get_logger("user").debug("no user found")
		else:
			get_logger("user").debug("found %s" % username)
			return username.lower()

	def _ask_umc(self, session):
		try:
			response = requests.get(self.umc_session_url, cookies={self.umc_cookie_name: session})
			data = response.json()
			username = data["result"]["username"]
		except requests.ConnectionError as exc:
			get_logger("user").error("connection failed: %s" % exc)
		except ValueError:
			get_logger("user").error("malformed answer!")
		except KeyError:
			get_logger("user").warn("session unknown!")
		else:
			return username
