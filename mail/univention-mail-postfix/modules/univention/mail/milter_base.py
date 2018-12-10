#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention mail Postfix
#  Milter base
#
# Copyright 2018 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

"""
Base class to quickly build milter applications.
You will have to overwrite and call super() for most milter methods. See
sender_check*.

Uses syslog, you have to run `syslog.openlog()` before using it!

Milter documentation:

	* http://www.postfix.org/MILTER_README.html
	* https://stuffivelearned.org/doku.php?id=programming:python:python-libmilter
"""

import os
import re
import syslog

import univention.uldap
from univention.config_registry import ConfigRegistry
import libmilter as lm

try:
	from typing import Dict, List, Optional, Set, Text, Union
except ImportError:
	pass


def log2syslog(msg, queue_id=None, level='INFO'):  # type: (str, Optional[str], Optional[str]) -> None
	if level == 'ERROR':
		level = 'ERR'
	try:
		syslog_level = getattr(syslog, 'LOG_{}'.format(level))
	except KeyError:
		syslog_level = syslog.LOG_INFO
	if queue_id:
		msg = '{}: {}'.format(queue_id, msg)
	syslog.syslog(syslog_level, msg)


class UCSMilterForkFactory(lm.ForkFactory):
	_ignore_interrupt = False

	def log(self, msg):  # type: (str) -> None
		if self._ignore_interrupt and 'Interrupted system call' in msg:
			# process received a signal, the blocking self.sock.accept() in
			# run() will create a socket.error. This is not a problem because
			# it is inside a "while True" loop.
			# -> Suppress logging it to not produce useless tickets.
			UCSMilterForkFactory._ignore_interrupt = False
			return
		log2syslog(msg)


class UCSMilterBase(lm.ForkMixin, lm.MilterProtocol, object):
	_ldap_secret_mtime = 0.0
	_lo = None
	_current_data = {}  # type: Dict[str, Set[str]]  # to prevent repeatedly logging same configuration
	_fork_factory = UCSMilterForkFactory
	_ucr = None
	headers_to_collect = ('date', 'subject', 'message-id')  # additionially to 'from' and 'to'
	regex_email_with_brackets = re.compile(r'.*<(.+@.+\..+)>$')
	regex_email_no_brackets = re.compile(r'(.+@.+\..+)$')
	mail_domains = []  # type: List[str]

	def __init__(self, opts=0, protos=0):  # type: (Optional[int], Optional[int]) -> None
		lm.MilterProtocol.__init__(self, opts, protos)
		lm.ForkMixin.__init__(self)

		self.sasl_login_name = ''
		self.envelope_from = ''
		self.header_data = {}  # type: Dict[str, str]
		self.queue_id = ''

		if not self.mail_domains:
			self.mail_domains.extend(self.get_mail_domains())
		if self._current_data.get('mail_domains') != set(self.mail_domains):
			self._current_data['mail_domains'] = set(self.mail_domains)
			self.log('Mail domains: {}'.format(', '.join(self.mail_domains or ['None'])))

	@classmethod
	def log(cls, msg, queue_id=None, level='INFO'):  # type: (str, Optional[str], Optional[str]) -> None
		log2syslog(msg, queue_id, level)

	@property
	def ucr(self):  # type: () -> ConfigRegistry
		if not self._ucr:
			self.get_ucr()
		return self._ucr

	@classmethod
	def get_ucr(cls):  # type: () -> ConfigRegistry
		if not cls._ucr:
			cls._ucr = ConfigRegistry()
			cls._ucr.load()
		return cls._ucr

	@classmethod
	def reload_ucr(cls):  # type: () -> ConfigRegistry
		if not cls._ucr:
			cls._ucr = cls.get_ucr()
		cls._ucr.load()
		return cls._ucr

	def clear_variables(self):  # type: () -> None
		self.header_data = {}
		self.sasl_login_name = self.envelope_from = self.queue_id = ''

	@classmethod
	def sig_handler_reload(cls, num, frame):
		"""
		Reload UCR and :py:attr`cls.mail_domains`.
		"""
		cls.log('Reloading.')
		cls.reload_ucr()
		cls.mail_domains = cls.get_mail_domains()
		cls._fork_factory._ignore_interrupt = True
		cls.log('Mail domains: {}'.format(', '.join(cls.mail_domains or ['None'])))

	@classmethod
	def get_lo(cls):  # type: () -> univention.uldap.access
		secret_mtime = os.stat('/etc/listfilter.secret').st_mtime
		if not cls._lo or cls._ldap_secret_mtime < secret_mtime:
			cls._lo = univention.uldap.getMachineConnection(
				ldap_master=False,
				secret_file='/etc/listfilter.secret'
			)
			cls._ldap_secret_mtime = os.stat('/etc/listfilter.secret').st_mtime
		return cls._lo

	@classmethod
	def get_mail_domains(cls):  # type: () -> List[str]
		lo = cls.get_lo()
		ldap_attr = ['cn']
		ldap_filter = 'objectClass=univentionMailDomainname'
		ldap_result = lo.search(filter=ldap_filter, attr=ldap_attr)
		return sorted(attr['cn'][0] for dn, attr in ldap_result)

	@lm.noReply
	def connect(self, hostname, family, ip, port, cmdDict):  # type: (str, str, str, int, Dict[str, str]) -> str
		self.clear_variables()
		return lm.CONTINUE

	def mailFrom(self, frAddr, cmdDict):  # type: (str, Dict[str, str]) -> None
		self.envelope_from = frAddr
		try:
			self.sasl_login_name = cmdDict['auth_authen']
		except KeyError:
			self.sasl_login_name = ''

	def header(self, key, val, cmdDict):  # type: (str, str, Dict[str, str]) -> None
		self.queue_id = cmdDict.get('i', '')  # is set, although doc says it is only set in DATA, EOH, EOM
		if key.lower() in ('from', 'to'):
			self.header_data[key.lower()] = self.get_only_email(val)
		elif key.lower() in self.headers_to_collect:
			self.header_data[key.lower()] = val

	def eoh(self, cmdDict):  # type: (Dict[str, str]) -> None
		self.queue_id = cmdDict.get('i', '')  # get again, in case it isn't set in header()

	def close(self):
		# don't log unnecessarily
		pass

	def get_only_email(self, text):  # type: (str) -> str
		m = self.regex_email_with_brackets.match(text)
		if not m:
			m = self.regex_email_no_brackets.match(text)
		if not m:
			return ''
		return m.groups()[0]

	@classmethod
	def my_translate(cls, s, del_chars):  # type: (Union[str, Text], Union[str, Text]) -> Union[str, Text]
		"""
		Remove characters in `del_chars` from string `s`.

		:param str s: string|unicode from which to remove characters in `del_chars`
		:param str del_chars: characters to remove from `s`
		:return: copy of `s` with characters in `del_chars` removed
		:rtype: str
		"""
		if isinstance(s, unicode):
			translate_table = dict((ord(x), None) for x in del_chars)  # type: Dict[int, None]
			return s.translate(translate_table)
		else:
			return s.translate(None, del_chars)
