# -*- coding: utf-8 -*-
#
# UCS test
"""
Networking helper that may establish connection redirection for testing
network connections/configuration of different programs (e.g. postfix).

WARNING:
The networking helper will install special iptables rules that may completely
break routing from/to the test system. Especially if the test script does
not clean up in error cases!
"""
from __future__ import print_function
#
# Copyright 2014-2019 Univention GmbH
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

import re
import copy
import subprocess
import univention.config_registry


class UCSTestNetwork(Exception):
	pass


class UCSTestNetworkCannotDetermineExternalAddress(UCSTestNetwork):
	pass


class UCSTestNetworkCmdFailed(UCSTestNetwork):
	pass


class UCSTestNetworkUnknownLoop(UCSTestNetwork):
	pass


class UCSTestNetworkUnknownRedirection(UCSTestNetwork):
	pass


class UCSTestNetworkNoWithStatement(UCSTestNetwork):
	message = 'NetworkRedirector has to be used via with statement!'


class UCSTestNetworkOnlyOneLoopSupported(UCSTestNetwork):
	message = 'NetworkRedirector does support only ONE loop at a time!'


class NetworkRedirector(object):

	"""
	The NetworkRedirector is able to establish port/connection redirections via
	iptables. It has to be used via the with-statement.

	>>> with NetworkRedirector() as nethelper:
	>>> nethelper.add_loop('1.2.3.4', '4.3.2.1')
	>>> nethelper.add_redirection('1.1.1.1', 25, 60025)
	>>> ...
	>>> # the following lines are optional! NetworkRedirector does automatic cleanup!
	>>> nethelper.remove_loop('1.2.3.4', '4.3.2.1')
	>>> nethelper.remove_redirection('1.1.1.1', 25, 60025)

	It is also possible to redirect all traffic to a specific port.
	The trailing "/0" is important, otherwise the redirection won't work!

	>>> nethelper.add_redirection('0.0.0.0/0', 25, 60025)
	"""

	BIN_IPTABLES = '/sbin/iptables'
	CMD_LIST_LOOP = [
		# localhost--><addr1> ==> <addr2>-->localhost
		[BIN_IPTABLES, '-t', 'mangle', '%(action)s', 'OUTPUT', '-d', '%(addr1)s', '-j', 'TOS', '--set-tos', '0x04'],
		[BIN_IPTABLES, '-t', 'nat', '%(action)s', 'OUTPUT', '-d', '%(addr1)s', '-j', 'DNAT', '--to-destination', '%(local_external_addr)s'],
		[BIN_IPTABLES, '-t', 'nat', '%(action)s', 'POSTROUTING', '-m', 'tos', '--tos', '0x04', '-j', 'SNAT', '--to-source', '%(addr2)s'],

		# localhost--><addr2> ==> <addr1>-->localhost
		[BIN_IPTABLES, '-t', 'mangle', '%(action)s', 'OUTPUT', '-d', '%(addr2)s', '-j', 'TOS', '--set-tos', '0x08'],
		[BIN_IPTABLES, '-t', 'nat', '%(action)s', 'OUTPUT', '-d', '%(addr2)s', '-j', 'DNAT', '--to-destination', '%(local_external_addr)s'],
		[BIN_IPTABLES, '-t', 'nat', '%(action)s', 'POSTROUTING', '-m', 'tos', '--tos', '0x08', '-j', 'SNAT', '--to-source', '%(addr1)s'],
	]

	CMD_LIST_REDIRECTION = [
		# redirect localhost-->%(remote_addr)s:%(remote_port)s ==> localhost:%(local_port)s
		[BIN_IPTABLES, '-t', 'nat', '%(action)s', 'OUTPUT', '-p', 'tcp', '-d', '%(remote_addr)s', '--dport', '%(remote_port)s', '-j', 'DNAT', '--to-destination', '127.0.0.1:%(local_port)s'],
	]

	def __init__(self):
		self.ucr = univention.config_registry.ConfigRegistry()
		self.ucr.load()
		self._external_address = None
		reUCRaddr = re.compile('^interfaces/[^/]+/address$')
		for key in self.ucr.keys():
			if reUCRaddr.match(key):
				self._external_address = self.ucr.get(key)
				break
		if not self._external_address:
			raise UCSTestNetworkCannotDetermineExternalAddress
		self.used_by_with_statement = False
		self.cleanup_rules = []  # [ ('loop', 'addr1', 'addr2'), ('redirection', 'remoteaddr', remoteport, localport), ... ]

	def __enter__(self):
		print('*** Entering with-statement of NetworkRedirector()')
		self.used_by_with_statement = True
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		print('*** Leaving with-statement of NetworkRedirector()')
		self.revert_network_settings()

	def revert_network_settings(self):
		print('*** NetworkRedirector.revert_network_settings()')
		for entry in copy.deepcopy(self.cleanup_rules):
			if entry[0] == 'loop':
				self.remove_loop(entry[1], entry[2], ignore_errors=True)
			elif entry[0] == 'redirection':
				self.remove_redirection(entry[1], entry[2], entry[3], ignore_errors=True)

	def run_commands(self, cmdlist, argdict, ignore_errors=False):
		"""
		Start all commands in cmdlist and replace formatstrings with arguments in argdict.

		>>> run_commands([['/bin/echo', '%(msg)s'], ['/bin/echo', 'World']], {'msg': 'Hello'})
		"""
		for cmd in cmdlist:
			cmd = copy.deepcopy(cmd)
			for i, val in enumerate(cmd):
				cmd[i] = val % argdict
			print('*** %r' % cmd)
			result = subprocess.call(cmd)
			if result and not ignore_errors:
				print('*** Exitcode: %r' % result)
				raise UCSTestNetworkCmdFailed('Command returned with non-zero exitcode: %r' % cmd)

	def add_loop(self, addr1, addr2):
		"""
		Add connection loop for addr1 and addr2.
		Outgoing connections to addr1 will be redirected back to localhost. The redirected
		connection will appear as it comes from addr2. All outgoing traffic to addr2 will
		be also redirected back to localhost and will appear as it comes from addr1.

		HINT: only one loop may be established at a time!
		"""
		if not self.used_by_with_statement:
			raise UCSTestNetworkNoWithStatement
		for i in self.cleanup_rules:
			if i[0] == 'loop':
				raise UCSTestNetworkOnlyOneLoopSupported

		self.cleanup_rules.append(('loop', addr1, addr2))
		args = {
			'addr1': addr1,
			'addr2': addr2,
			'local_external_addr': self._external_address,
			'action': '-A',
		}
		print('*** Adding network loop (%s <--> %s)' % (addr1, addr2))
		self.run_commands(self.CMD_LIST_LOOP, args)

	def remove_loop(self, addr1, addr2, ignore_errors=False):
		"""
		Remove previously defined connection loop.
		"""
		entry = ('loop', addr1, addr2)
		if entry not in self.cleanup_rules:
			raise UCSTestNetworkUnknownLoop('The given loop has not been established and cannot be removed.')

		self.cleanup_rules.remove(entry)
		args = {
			'addr1': addr1,
			'addr2': addr2,
			'local_external_addr': self._external_address,
			'action': '-D',
		}
		print('*** Removing network loop (%s <--> %s)' % (addr1, addr2))
		self.run_commands(self.CMD_LIST_LOOP, args, ignore_errors)

	def add_redirection(self, remote_addr, remote_port, local_port):
		"""
		Add new connection redirection.

		Outgoing connections to <remote_addr>:<remote_port> will be redirected back to localhost:<local_port>.
		"""
		if not self.used_by_with_statement:
			raise UCSTestNetworkNoWithStatement

		entry = ('redirection', remote_addr, remote_port, local_port)
		if entry not in self.cleanup_rules:
			self.cleanup_rules.append(entry)
			args = {
				'remote_addr': remote_addr,
				'remote_port': remote_port,
				'local_port': local_port,
				'action': '-A',
			}
			print('*** Adding network redirection (%s:%s --> 127.0.0.1:%s)' % (remote_addr, remote_port, local_port))
			self.run_commands(self.CMD_LIST_REDIRECTION, args)

	def remove_redirection(self, remote_addr, remote_port, local_port, ignore_errors=False):
		"""
		Remove previously defined connection redirection.
		"""
		entry = ('redirection', remote_addr, remote_port, local_port)
		if entry not in self.cleanup_rules:
			raise UCSTestNetworkUnknownRedirection('The given redirection has not been established and cannot be removed.')

		self.cleanup_rules.remove(entry)
		args = {
			'remote_addr': remote_addr,
			'remote_port': remote_port,
			'local_port': local_port,
			'action': '-D',
		}
		print('*** Removing network redirection (%s:%s <--> 127.0.0.1:%s)' % (remote_addr, remote_port, local_port))
		self.run_commands(self.CMD_LIST_REDIRECTION, args, ignore_errors)
