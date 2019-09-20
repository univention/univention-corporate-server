# -*- coding: utf-8 -*-
#
# Univention RADIUS
#  NTLM-Authentication program
#
# Copyright (C) 2012-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

import os
import logging

from ldap.filter import filter_format
import univention.uldap
from ldap import SERVER_DOWN
import univention.config_registry

SAMBA_ACCOUNT_FLAG_DISABLED = 'D'
SAMBA_ACCOUNT_FLAG_LOCKED = 'L'
DISALLOWED_SAMBA_ACCOUNT_FLAGS = frozenset((SAMBA_ACCOUNT_FLAG_DISABLED, SAMBA_ACCOUNT_FLAG_LOCKED, ))


def convert_network_access_attr(attributes):
	access = attributes.get('univentionNetworkAccess')
	if access == ['1']:
		return True
	return False


def convert_ucs_debuglevel(ucs_debuglevel):
	logging_debuglevel = [logging.ERROR, logging.WARN, logging.INFO, logging.INFO, logging.DEBUG][max(0, min(4, ucs_debuglevel))]
	return logging_debuglevel


def decode_stationId(stationId):
	if not stationId:
		return None
	stationId = stationId.lower()
	# remove all non-hex characters, so different formats may be decoded
	# e.g. 11:22:33:44:55:66 or 1122.3344.5566 or 11-22-33-44-55-66 or ...
	stationId = ''.join(c for c in stationId if c in '0123456789abcdef')
	stationId = stationId.decode('hex')
	return ':'.join([byte.encode('hex') for byte in stationId])


def parse_username(username):
	'''convert username from host/-format to $-format if required'''
	if not username.startswith('host/'):
		return username
	username = username.split('/', 1)[1]  # remove host/
	username = username.split('.', 1)[0]  # remove right of '.'
	return username + '$'


def get_ldapConnection():
	try:
		# try ldap/server/name, then each of ldap/server/addition
		ldapConnection = univention.uldap.getMachineConnection(ldap_master=False, reconnect=False)
	except SERVER_DOWN:
		# then master dc
		ldapConnection = univention.uldap.getMachineConnection()
	return ldapConnection


class NetworkAccessError(Exception):
	def __init__(self, msg):
		self.msg = msg


class UserNotAllowedError(NetworkAccessError):
	pass


class MacNotAllowedError(NetworkAccessError):
	pass


class NoHashError(NetworkAccessError):
	pass


class UserDeactivatedError(NetworkAccessError):
	pass


class NetworkAccess(object):

	def __init__(self, username, stationId, loglevel=None, logfile=None):  # type: (str, str, Optional[int], Optional[str]) -> None
		self.username = parse_username(username)
		self.mac_address = decode_stationId(stationId)
		self.ldapConnection = get_ldapConnection()
		self.configRegistry = univention.config_registry.ConfigRegistry()
		self.configRegistry.load()
		self.whitelisting = self.configRegistry.is_true('radius/mac/whitelisting')
		self._setup_logger(loglevel, logfile)
		self.logger.debug('Given username: "{}"'.format(username))
		self.logger.debug('Given stationId: "{}"'.format(stationId))

	def _setup_logger(self, loglevel, logfile):  # type: (Optional[int], Optional[str]) -> None
		self.configRegistry = univention.config_registry.ConfigRegistry()
		self.configRegistry.load()
		if loglevel is not None:
			ucs_debuglevel = loglevel
		else:
			try:
				ucs_debuglevel = int(self.configRegistry.get('freeradius/auth/helper/ntlm/debug', '2'))
			except ValueError:
				ucs_debuglevel = 2
		debuglevel = convert_ucs_debuglevel(ucs_debuglevel)
		self.logger = logging.getLogger('radius-ntlm')
		self.logger.setLevel(debuglevel)
		if logfile is not None:
			log_handler = logging.FileHandler(logfile)
			log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)10s: [pid={}; user={}; mac={}] %(message)s'.format(os.getpid(), self.username, self.mac_address))
		else:
			log_handler = logging.StreamHandler()
			log_formatter = logging.Formatter('%(levelname)10s: [user={}; mac={}] %(message)s'.format(self.username, self.mac_address))
		log_handler.setFormatter(log_formatter)
		self.logger.addHandler(log_handler)
		# self.logger.info("Loglevel set to: {}".format(ucs_debuglevel))

	def build_access_dict(self, ldap_result):
		access_dict = dict()
		for (dn, attributes) in ldap_result:
			access_dict[dn] = convert_network_access_attr(attributes)
		return access_dict

	def get_user_network_access(self, uid):
		users = self.ldapConnection.search(filter=filter_format('(uid=%s)', (uid, )), attr=['univentionNetworkAccess'])
		return self.build_access_dict(users)

	def get_station_network_access(self, mac_address):
		stations = self.ldapConnection.search(filter=filter_format('(macAddress=%s)', (mac_address, )), attr=['univentionNetworkAccess'])
		return self.build_access_dict(stations)

	def get_groups_network_access(self, dn):
		groups = self.ldapConnection.search(filter=filter_format('(uniqueMember=%s)', (dn, )), attr=['univentionNetworkAccess'])
		return self.build_access_dict(groups)

	def evaluate_ldap_network_access(self, access, level=''):

		def format_network_access_msg(dn, policy):
			if policy:
				return level + 'ALLOW %r' % (dn, )
			return level + 'DENY %r' % (dn, )

		short_circuit = not self.logger.isEnabledFor(logging.DEBUG)
		policy = any(access.values())
		if short_circuit and policy:
			return policy
		for dn in access.keys():
			self.logger.debug(format_network_access_msg(dn, access[dn]))
			parents_access = self.get_groups_network_access(dn)
			if self.evaluate_ldap_network_access(parents_access, level=level + '-> '):
				policy = True
				if short_circuit:
					break
		return policy

	def check_proxy_filter_policy(self):
		'''Dummy function for UCS@school'''
		self.logger.debug('UCS@school RADIUS support is not installed')
		return False

	def check_network_access(self):
		result = self.get_user_network_access(self.username)
		if not result:
			self.logger.info('Login attempt with unknown username')
			return False
		self.logger.debug('Checking LDAP settings for user')
		policy = self.evaluate_ldap_network_access(result)
		if policy:
			self.logger.info('Login attempt permitted by LDAP settings')
		else:
			self.logger.info('Login attempt denied by LDAP settings')
		return policy

	def check_station_whitelist(self):
		if not self.whitelisting:
			self.logger.debug('MAC filtering is disabled by radius/mac/whitelisting.')
			return True
		self.logger.debug('Checking LDAP settings for stationId')
		if not self.mac_address:
			self.logger.info('Login attempt without MAC address, but MAC filtering is enabled.')
			return False
		result = self.get_station_network_access(self.mac_address)
		if not result:
			self.logger.info('Login attempt with unknown MAC address')
			return False
		policy = self.evaluate_ldap_network_access(result)
		if policy:
			self.logger.info('Login attempt permitted by LDAP settings')
		else:
			self.logger.info('Login attempt denied by LDAP settings')
		return policy

	def getNTPasswordHash(self):
		'stationId may be None if it was not supplied to the program'
		if not (self.check_proxy_filter_policy() or self.check_network_access()):
			raise UserNotAllowedError('User is not allowed to authenticate via RADIUS')
		if not self.check_station_whitelist():
			raise MacNotAllowedError('stationId is denied, because it is not whitelisted')
		# user is authorized to authenticate via RADIUS, retrieve NT-password-hash from LDAP and return it
		self.logger.info('User is allowed to use RADIUS')
		result = self.ldapConnection.search(filter=filter_format('(uid=%s)', (self.username, )), attr=['sambaNTPassword', 'sambaAcctFlags'])
		try:
			nt_password_hash = result[0][1]['sambaNTPassword'][0].decode('hex')
		except (IndexError, KeyError, TypeError):
			raise NoHashError('No valid NT-password-hash found. Check the "sambaNTPassword" attribute of the user.')
		sambaAccountFlags = frozenset(result[0][1]['sambaAcctFlags'][0])
		if sambaAccountFlags & DISALLOWED_SAMBA_ACCOUNT_FLAGS:
			raise UserDeactivatedError('Account is deactivated')
		return nt_password_hash
