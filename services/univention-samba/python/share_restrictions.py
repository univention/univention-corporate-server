#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Samba
#  this script creates samba configurations from ucr values
#
# Copyright 2004-2019 Univention GmbH
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

# This file is part of univention-lib and have to contain python2.4 valid code

from __future__ import print_function
from univention.config_registry import ConfigRegistry

from ConfigParser import ConfigParser
import os
import re
import shlex

# defaults
ucr = ConfigRegistry()

# global hashes
shares = {}
globals = {}
printers = {}

ucr.load()


class Restrictions(dict):
	INVALID_USERS = 'invalid users'
	VALID_USERS = 'valid users'
	HOSTS_DENY = 'hosts deny'
	HOSTS_ALLOW = 'hosts allow'

	def __init__(self, name):
		dict.__init__(self, {
			Restrictions.INVALID_USERS: None,
			Restrictions.VALID_USERS: None,
			Restrictions.HOSTS_DENY: None,
			Restrictions.HOSTS_ALLOW: None
		})
		self.name = name
		self.ucr = False

	def _add(self, key, value):
		if not isinstance(value, (tuple, list, set)):
			value = [value]
		value = map(lambda x: ' ' in x and '"%s"' % x or x, value)
		if self[key] is None:
			self[key] = set(value)
		else:
			self[key].update(value)

	@property
	def invalid_users(self):
		return self[Restrictions.INVALID_USERS]

	@invalid_users.setter
	def invalid_users(self, value):
		self._add(Restrictions.INVALID_USERS, value)

	@property
	def valid_users(self):
		return self[Restrictions.VALID_USERS]

	@valid_users.setter
	def valid_users(self, value):
		self._add(Restrictions.VALID_USERS, value)

	@property
	def hosts_deny(self):
		return self[Restrictions.HOSTS_DENY]

	@hosts_deny.setter
	def hosts_deny(self, value):
		self._add(Restrictions.HOSTS_DENY, value)

	@property
	def hosts_allow(self):
		return self[Restrictions.HOSTS_ALLOW]

	@hosts_allow.setter
	def hosts_allow(self, value):
		self._add(Restrictions.HOSTS_ALLOW, value)


class Share(Restrictions):
	pass


class Printer(Restrictions):

	def __init__(self, name):
		Restrictions.__init__(self, name)
		self['smbname'] = None

	@property
	def smbname(self):
		return self['smbname']

	@smbname.setter
	def smbname(self, name):
		self['smbname'] = name


class ShareConfiguration(object):
	SHARES_DIR = '/etc/samba/local.config.d'
	SHARES_UDM_DIR = '/etc/samba/shares.conf.d'
	PRINTERS_UDM_DIR = '/etc/samba/printers.conf.d'
	POSTFIX = '.local.config.conf'
	PREFIX = 'printer.'
	INCLUDE_CONF = '/etc/samba/local.config.conf'
	GLOBAL_CONF = '/etc/samba/local.config.d/global.local.config.conf'
	CUPS_CONF = '/etc/cups/printers.conf'

	def __init__(self):
		self._shares = {}
		self._globals = {}
		self._printers = {}

	def delete(self):
		"""delete all conf's in SHARES_DIR and INCLUDE_CONF"""

		if not os.path.isdir(ShareConfiguration.SHARES_DIR):
			os.makedirs(ShareConfiguration.SHARES_DIR)
		if os.path.isfile(ShareConfiguration.INCLUDE_CONF):
			os.remove(ShareConfiguration.INCLUDE_CONF)
		if os.path.isfile(ShareConfiguration.GLOBAL_CONF):
			os.remove(ShareConfiguration.GLOBAL_CONF)

		for item in os.listdir(ShareConfiguration.SHARES_DIR):
			file = os.path.join(ShareConfiguration.SHARES_DIR, item)
			if os.path.isfile(file) and file.endswith(ShareConfiguration.POSTFIX):
				os.remove(file)

	def read_shares(self):
		"""get invalid user from samba share conf"""

		if not os.path.isdir(ShareConfiguration.SHARES_UDM_DIR):
			return

		for file in os.listdir(ShareConfiguration.SHARES_UDM_DIR):
			filename = os.path.join(ShareConfiguration.SHARES_UDM_DIR, file)
			cfg = ConfigParser()
			cfg.read(filename)
			try:
				share = Share(cfg.sections()[0])
			except IndexError:
				continue

			if cfg.has_option(share.name, Restrictions.INVALID_USERS):
				share.invalid_users = shlex.split(cfg.get(share.name, Restrictions.INVALID_USERS))
			if cfg.has_option(share.name, Restrictions.HOSTS_DENY):
				share.hosts_deny = shlex.split(cfg.get(share.name, Restrictions.HOSTS_DENY))

			self._shares[share.name] = share

	def read_printers(self):
		"""get invalid/valid users from cups and samba config"""

		# read CUPS configuration
		if os.path.isfile(ShareConfiguration.CUPS_CONF):
			reg_cups = re.compile('\s*<Printer\s+([^>]+)>')

			fd = open("/etc/cups/printers.conf")
			try:
				for line in fd.readlines():
					m_cups = reg_cups.match(line)

					if m_cups:
						prt = Printer(m_cups.group(1).strip())
						self._printers[prt.name] = prt
			finally:
				fd.close()

		# samba
		if not os.path.exists(ShareConfiguration.PRINTERS_UDM_DIR):
			return

		for filename in os.listdir(ShareConfiguration.PRINTERS_UDM_DIR):
			cfg = ConfigParser()
			cfg.read(os.path.join(ShareConfiguration.PRINTERS_UDM_DIR, filename))
			try:
				prt_name = cfg.sections()[0]
			except IndexError:
				continue

			prt = None
			if prt_name in self._printers:
				prt = self._printers[prt_name]
			else:
				if cfg.has_option(prt_name, 'printer name'):
					cups_name = cfg.get(prt_name, 'printer name')
					if cups_name in self._printers:
						prt = self._printers[cups_name]
						prt.smbname = prt_name

			if prt is None:
				continue

			if cfg.has_option(prt_name, Restrictions.INVALID_USERS):
				prt.invalid_users = shlex.split(cfg.get(prt_name, Restrictions.INVALID_USERS))
			if cfg.has_option(prt_name, Restrictions.VALID_USERS):
				prt.valid_users = shlex.split(cfg.get(prt_name, Restrictions.VALID_USERS))
			if cfg.has_option(prt_name, Restrictions.HOSTS_DENY):
				prt.hosts_deny = shlex.split(cfg.get(prt_name, Restrictions.HOSTS_DENY))

	def _set_invalids(self, value, share, group):
		if share and group and value.lower() in ('true', 'yes', '1'):
			if share not in self._shares:
				self._shares[share] = Share(share)

			self._shares[share].ucr = True
			self._shares[share].invalid_users = '@' + group

	def _set_denied_hosts(self, value, share):
		if share not in self._shares:
			self._shares[share] = Share(share)

		self._shares[share].ucr = True
		self._shares[share].hosts_deny = shlex.split(value)

	def _set_printmode_group(self, mode, group):
		if mode not in ('none', 'all'):
			return

		group = "@" + group
		for prt in self._printers.values():
			prt.ucr = True
			if mode == 'none':
				prt.invalid_users = group
			else:
				prt.valid_users = group

	def _set_printmode_hosts(self, hosts, mode):
		if mode not in ('none', 'all'):
			return

		hosts = hosts.split(' ')
		for prt in self._printers.values():
			prt.ucr = True
			if mode == "none":
				prt.hosts_deny = hosts
			else:
				prt.hosts_allow = hosts

	def _set_othershares(self, value, group):
		"""append group to invalid users for all shares, except shares
		group (the groupname) and marktplatz"""
		if not group or not value.lower() in ('true', 'yes', '1'):
			return

		for share in self._shares.values():
			if share.name in (group, 'marktplatz', 'homes'):
				continue

			share.invalid_users = '@' + group
			share.ucr = True

	def _set_othershares_hosts(self, value):
		if not value:
			return

		for share in self._shares.values():
			if share.name in ('marktplatz', 'homes'):
				continue
			share.hosts_deny = shlex.split(value)
			share.ucr = True

	# set global options to -> globals
	def _set_globals(self, value, option):
		if option and value:
			self._globals[option] = value

	# set share options to -> shares
	def _set_options(self, value, share, option):
		if share and option and value:
			if share not in self._shares:
				return
			if option not in self._shares[share]:
				self._shares[share][option] = set()
			self._shares[share].ucr = True
			self._shares[share][option].add(value)

	# parse ucr
	def read_ucr(self):
		_map = dict(
			options=(re.compile('samba/share/([^\/]+)/options/(.*)'), self._set_options),
			globals=(re.compile('samba/global/options/(.*)'), self._set_globals),
			hosts=(re.compile('samba/share/([^\/]+)/hosts/deny'), self._set_denied_hosts),
			users=(re.compile('samba/share/([^\/]+)/usergroup/([^\/]+)/invalid'), self._set_invalids),
			printmode_groups=(re.compile('samba/printmode/usergroup/(.*)'), self._set_printmode_group),
			printmode_hosts=(re.compile('samba/printmode/hosts/(.*)'), self._set_printmode_hosts),
			othershares=(re.compile('samba/othershares/usergroup/([^\/]+)/invalid'), self._set_othershares),
			othershares_hosts=(re.compile('samba/othershares/hosts/deny'), self._set_othershares_hosts)
		)

		for key in ucr.keys():
			for regex, func in _map.values():
				match = regex.match(key)
				if match:
					func(ucr[key], *match.groups())

	def read(self):
		# get available cups samba printers and valid/invalid users
		self.read_printers()

		# get invalid users for shares from samba config
		self.read_shares()

		# get ucr options
		self.read_ucr()

	def write(self):
		includes = set()

		self.delete()

		# write conf file with global options
		if len(self.globals):
			fd = open(ShareConfiguration.GLOBAL_CONF, 'w')
			try:
				fd.write("[global]\n")
				fd.write(''.join(map(lambda item: '%s = %s\n' % item, self.globals.items())))
			finally:
				fd.close()

			includes.add('include = %s' % ShareConfiguration.GLOBAL_CONF)

		# write share configs files with options and invalid users
		for share in self._shares.values():
			# write share conf only if we have ucr settings
			if not share.ucr:
				continue

			share_filename = os.path.join(ShareConfiguration.SHARES_DIR, share.name + ShareConfiguration.POSTFIX)
			fd = open(share_filename, "w")
			try:
				fd.write("[" + share.name + "]\n")
				for option in share:
					if share[option] is None:
						continue
					fd.write('%s = ' % option)
					fd.write(' '.join(share[option]))
					fd.write('\n')
			finally:
				fd.close()
			includes.add('include = %s' % share_filename)

		# write print share configs
		for prt in self._printers.values():
			# write prin share conf only if we have a proper ucr setting
			if not prt.ucr:
				continue

			filename = os.path.join(ShareConfiguration.SHARES_DIR, ShareConfiguration.PREFIX + prt.name + ShareConfiguration.POSTFIX)
			includes.add('include = %s' % filename)

			fd = open(filename, 'w')
			try:
				if not prt.smbname:
					fd.write('[%s]\n' % prt.name)
				else:
					fd.write('[%s]\n' % prt.smbname)
					fd.write('printer name = %s\n' % prt.name)
					fd.write('path = /tmp\n')
					fd.write('guest ok = yes\n')
					fd.write('printable = yes\n')

				for option in (Restrictions.VALID_USERS, Restrictions.INVALID_USERS, Restrictions.HOSTS_DENY, Restrictions.HOSTS_ALLOW):
					if option in prt and prt[option] is not None:
						fd.write('%s = ' % option)
						fd.write(' '.join(prt[option]))
						fd.write('\n')
			finally:
				fd.close()

		# all include statements go to this file (create file een if there is no include
		f = open(ShareConfiguration.INCLUDE_CONF, 'w')
		try:
			f.write('\n'.join(includes) + '\n')
		finally:
			f.close()

	@property
	def globals(self):
		return self._globals

	@property
	def shares(self):
		return self._shares

	@property
	def printers(self):
		return self._printers


if __name__ == '__main__':
	cfg = ShareConfiguration()
	cfg.read()
	print(cfg.globals)
	print(cfg.shares)
	print(cfg.printers)
	cfg.write()
