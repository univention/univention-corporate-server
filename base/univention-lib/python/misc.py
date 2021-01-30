#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Univention Common Python Library
"""
# Copyright 2012-2021 Univention GmbH
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

import subprocess
from typing import Optional  # noqa F401

from univention.config_registry import ConfigRegistry


def createMachinePassword():
	# type: () -> str
	"""
	Returns a $(pwgen) generated password according to the
	requirements in |UCR| variables
	`machine/password/length` and `machine/password/complexity`.

	:returns: A password.
	:rtype: str
	"""
	ucr = ConfigRegistry()
	ucr.load()
	length = ucr.get('machine/password/length', '20')
	compl = ucr.get('machine/password/complexity', 'scn')
	p = subprocess.Popen(["pwgen", "-1", "-" + compl, length], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdout, stderr) = p.communicate()
	if not isinstance(stdout, str):  # Python 3
		return stdout.decode('ASCII', 'replace').strip()
	return stdout.strip()


def getLDAPURIs(ucr=None):
	# type: (Optional[ConfigRegistry]) -> str
	"""
	Returns a space separated list of all configured |LDAP| servers, according to |UCR| variables
	`ldap/server/name` and `ldap/server/addition`.

	:param ConfigRegistry ucr: An optional |UCR| instance.
	:returns: A space separated list of |LDAP| |URI|.
	:rtype: str
	"""
	if ucr is None:
		ucr = ConfigRegistry()
		ucr.load()

	uri_string = ''
	ldaphosts = []
	port = ucr.get('ldap/server/port', '7389')
	ldap_server_name = ucr.get('ldap/server/name')
	ldap_server_addition = ucr.get('ldap/server/addition')

	if ldap_server_name:
		ldaphosts.append(ldap_server_name)
	if ldap_server_addition:
		ldaphosts.extend(ldap_server_addition.split())
	if ldaphosts:
		urilist = ["ldap://%s:%s" % (host, port) for host in ldaphosts]
		uri_string = ' '.join(urilist)

	return uri_string


def getLDAPServersCommaList(ucr=None):
	# type: (Optional[ConfigRegistry]) -> str
	"""
	Returns a comma-separated string with all configured |LDAP| servers,
	`ldap/server/name` and `ldap/server/addition`.

	:param ConfigRegistry ucr: An optional |UCR| instance.
	:returns: A space separated list of |LDAP| host names.
	:rtype: str
	"""
	if ucr is None:
		ucr = ConfigRegistry()
		ucr.load()

	ldap_servers = ''
	ldaphosts = []
	ldap_server_name = ucr.get('ldap/server/name')
	ldap_server_addition = ucr.get('ldap/server/addition')

	if ldap_server_name:
		ldaphosts.append(ldap_server_name)
	if ldap_server_addition:
		ldaphosts.extend(ldap_server_addition.split())
	if ldaphosts:
		ldap_servers = ','.join(ldaphosts)

	return ldap_servers


def custom_username(name, ucr=None):
	# type: (str, Optional[ConfigRegistry]) -> str
	"""
	Returns the customized user name configured via |UCR| `users/default/*`.

	:param str name: A user name.
	:param ConfigRegistry ucr: An optional |UCR| instance.
	:returns: The translated user name.
	:rtype: str
	:raises ValueError: if no name is given.
	"""
	if not name:
		raise ValueError()

	if ucr is None:
		ucr = ConfigRegistry()
		ucr.load()

	return ucr.get("users/default/" + name.lower().replace(" ", ""), name)


def custom_groupname(name, ucr=None):
	# type: (str, Optional[ConfigRegistry]) -> str
	"""
	Returns the customized group name configured via |UCR| `groups/default/*`.

	:param str name: A group name.
	:param ConfigRegistry ucr: An optional |UCR| instance.
	:returns: The translated group name.
	:rtype: str
	:raises ValueError: if no name is given.
	"""
	if not name:
		raise ValueError()

	if ucr is None:
		ucr = ConfigRegistry()
		ucr.load()

	return ucr.get("groups/default/" + name.lower().replace(" ", ""), name)
