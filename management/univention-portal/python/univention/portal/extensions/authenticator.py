#!/usr/bin/python3
#
# Univention Portal
#
# Copyright 2019-2021 Univention GmbH
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

import requests
from six import with_metaclass
from univention.portal import Plugin
from univention.portal.log import get_logger
from univention.portal.user import User


class Session(object):
	def __init__(self, nonce):
		self.nonce = nonce
		self.user = None

	def is_valid(self):
		return True


class Authenticator(with_metaclass(Plugin)):
	"""
	Our base class for authentication
	May hold all the sessions, set cookies, etc.

	The idea is that this class handles the following
	methods from the Portal:
	`login_request`: A user GETs to the login action
	`login_user`: Credentials are POSTed to this action
	`get_user`: While gathering the portal data, the caller wants

	This base class does nothing...
	"""

	def get_auth_mode(self, request):  # pragma: no cover
		return "ucs"

	async def login_request(self, request):  # pragma: no cover
		pass

	async def login_user(self, request):  # pragma: no cover
		pass

	async def logout_user(self, request):  # pragma: no cover
		pass

	async def get_user(self, request):  # pragma: no cover
		return User(username=None, display_name=None, groups=[], headers={})

	def refresh(self, reason=None):  # pragma: no cover
		pass


class UMCAuthenticator(Authenticator):
	"""
	Specialized Authenticator that relies on a UMC that actually holds any session.
	Asks UMC for every request if this session is known.

	auth_mode:
		The preferred mode for auth. The portal hands it over to the frontend.
	umc_session_url:
		The URL where to go to with the cookie. Expects a json answer with the username.
	group_cache:
		As UMC does not return groups, we need a cache object that gets us the groups for the username.
	"""

	def __init__(self, auth_mode, umc_session_url, group_cache):
		self.auth_mode = auth_mode
		self.umc_session_url = umc_session_url
		self.group_cache = group_cache

	def get_auth_mode(self, request):
		return self.auth_mode

	def refresh(self, reason=None):
		return self.group_cache.refresh(reason=reason)

	async def get_user(self, request):
		cookies = dict((key, morsel.value) for key, morsel in request.cookies.items())
		username, display_name = await self._get_username(cookies)
		groups = self.group_cache.get().get(username, [])
		return User(username, display_name=display_name, groups=groups, headers=dict(request.request.headers))

	async def _get_username(self, cookies):
		for cookie in cookies:
			if cookie.startswith("UMCSessionId"):
				# UMCSessionId-1234 -> Host: localhost:1234
				host_port = cookie[13:]
				if host_port:
					host_port = ":{}".format(host_port)
				break
		else:
			get_logger("user").debug("no user given")
			return None, None
		headers = {"Host": "localhost" + host_port}
		get_logger("user").debug("searching user for cookies=%r" % cookies)
		username = await self._ask_umc(cookies, headers)
		if username is None:
			get_logger("user").debug("no user found")
			return None, None
		else:
			get_logger("user").debug("found %s" % (username,))
			return username.lower(), username

	async def _ask_umc(self, cookies, headers):
		try:
			response = requests.get(self.umc_session_url, cookies=cookies, headers=headers)
			data = response.json()
			username = data["result"]["username"]
		except requests.RequestException as e:
			get_logger("user").error("connection failed: %s" % e)
		except ValueError:
			get_logger("user").error("malformed answer!")
		except KeyError:
			get_logger("user").warning("session unknown!")
		else:
			return username
