#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
Milter that rejects mails with forged addresses in both
	* the envelope (MAIL FROM protocol stage)
	* the "From" header (DATA protocol stage)

Legitimate email addresses are found as 'mailPrimaryAddress' and
'mailAlternativeAddress' in LDAP.

Copyright (c) 2018 Daniel Tröder, daniel@admin-box.com
Licensed under the MIT License (MIT)
SPDX short identifier: MIT
License text: https://opensource.org/licenses/MIT

python-libmilter is licensed under the GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
import re
import sys
import signal
import syslog
import traceback

from ldap.filter import filter_format
import libmilter as lm
import univention.uldap
from univention.config_registry import ConfigRegistry


class NoForgedFromMilter(lm.ForkMixin, lm.MilterProtocol):
	_lo = None
	_ldap_secret_mtime = 0.0
	regex_email_with_brakets = re.compile(r'.*<(.+@.+\..+)>$')
	regex_email_no_brakets = re.compile(r'(.+@.+\..+)$')
	mail_domains = []

	def __init__(self, opts=0, protos=0):
		lm.MilterProtocol.__init__(self, opts, protos)
		lm.ForkMixin.__init__(self)
		self.sasl_login_name = ''
		self.legitimate_addresses = []
		self.envelope_from = ''
		self.header_from = ''
		self.recipients = []
		self.__class__.mail_domains = self.get_mail_domains()
		self.log('Mail domains: {}'.format(', '.join(self.mail_domains)))

	@classmethod
	def log(cls, msg, level='INFO'):
		if level == 'ERROR':
			level = 'ERR'
		try:
			syslog_level = getattr(syslog, 'LOG_{}'.format(level))
		except KeyError:
			syslog_level = syslog.LOG_INFO
		syslog.syslog(syslog_level, msg)

	def clear_variables(self):
		self.sasl_login_name = ''
		self.legitimate_addresses = []
		self.envelope_from = ''
		self.header_from = ''
		self.recipients = []

	@classmethod
	def get_lo(cls):
		secret_mtime = os.stat('/etc/listfilter.secret').st_mtime
		if not cls._lo or cls._ldap_secret_mtime < secret_mtime:
			cls._lo = univention.uldap.getMachineConnection(
				ldap_master=False,
				secret_file='/etc/listfilter.secret'
			)
			cls._ldap_secret_mtime = os.stat('/etc/listfilter.secret').st_mtime
		return cls._lo

	@classmethod
	def get_legitimate_addresses_for_username(cls, sasl_login_name):
		lo = cls.get_lo()
		ldap_attr = ['mailPrimaryAddress', 'mailAlternativeAddress']
		ldap_filter = filter_format('(&(uid=%s)(objectclass=univentionMail))', (sasl_login_name,))
		ldap_result = lo.search(filter=ldap_filter, attr=ldap_attr)
		try:
			return ldap_result[0][1]['mailPrimaryAddress'] + ldap_result[0][1].get('mailAlternativeAddress', [])
		except IndexError:
			cls.log('Found no email address for sasl_login_name={!r}.'.format(sasl_login_name), 'ERROR')
			return ''

	@classmethod
	def get_mail_domains(cls):
		lo = cls.get_lo()
		ldap_attr = ['cn']
		ldap_filter = 'objectClass=univentionMailDomainname'
		ldap_result = lo.search(filter=ldap_filter, attr=ldap_attr)
		return [attr['cn'][0] for dn, attr in ldap_result]

	@classmethod
	def reload_sig_handler(cls, num, frame):
		cls.mail_domains = cls.get_mail_domains()
		cls.log('Reloaded. Mail domains: {}'.format(', '.join(cls.mail_domains)))

	@lm.noReply
	def connect(self, hostname, family, ip, port, cmdDict):
		self.clear_variables()
		return lm.CONTINUE

	def mailFrom(self, frAddr, cmdDict):
		self.envelope_from = frAddr
		try:
			self.sasl_login_name = cmdDict['auth_authen']
		except KeyError:
			# not authenticated session
			local_part, at, domain = self.envelope_from.rpartition('@')
			if domain and domain in self.mail_domains:
				self.log('REJECT: envelope_from ({}) of not authenticated user with hosted domain ({}).'.format(
					self.envelope_from, domain))
				return lm.REJECT
		else:
			# authenticated session
			if not self.legitimate_addresses:
				self.legitimate_addresses = self.get_legitimate_addresses_for_username(self.sasl_login_name)
			if self.envelope_from not in self.legitimate_addresses:
				self.log('REJECT: envelope_from ({}) not in legitimate addresses ({}).'.format(
					self.envelope_from, ', '.join(self.legitimate_addresses)))
				return lm.REJECT
		return lm.CONTINUE

	def header(self, key, val, cmdDict):
		if key.lower() == 'from':
			m = self.regex_email_with_brakets.match(val)
			if not m:
				m = self.regex_email_no_brakets.match(val)
			if not m:
				self.log('Invalid email address: {!r}: {!r}.'.format(key, val), 'ERROR')
				return lm.REJECT
			self.header_from = m.groups()[0]
			if self.sasl_login_name:
				# authenticated session
				if not self.legitimate_addresses:
					self.legitimate_addresses = self.get_legitimate_addresses_for_username(self.sasl_login_name)
				if self.header_from in self.legitimate_addresses:
					return lm.CONTINUE
				else:
					self.log('REJECT: header_from ({}) not in legitimate addresses ({!s}).'.format(
						self.header_from, val, ', '.join(self.legitimate_addresses)))
					return lm.REJECT
			else:
				# not authenticated session
				local_part, at, domain = self.header_from.rpartition('@')
				if domain and domain in self.mail_domains:
					self.log('REJECT: header_from ({}) of not authenticated user with hosted domain ({}).'.format(
						self.header_from, domain))
					return lm.REJECT
		return lm.CONTINUE

	def eob(self, cmdDict):
		# don't log unnecessarily
		return lm.CONTINUE

	def close(self):
		# don't log unnecessarily
		pass


def run_milter():
	ucr = ConfigRegistry()
	ucr.load()
	syslog.openlog(ident="no_forged_from", logoption=syslog.LOG_PID, facility=syslog.LOG_MAIL)
	port = ucr.get('mail/postfix/no-forged-from-milter-port', 5656)
	NoForgedFromMilter.log('Starting NoForgedFromMilter on port {}.'.format(port))
	# test LDAP connection
	NoForgedFromMilter.get_lo()

	opts = lm.SMFIP_NOHELO | lm.SMFIP_NORCPT | lm.SMFIP_NOBODY | lm.SMFIP_NOEOH | lm.SMFIP_NODATA
	milter_factory = lm.ForkFactory('inet:127.0.0.1:{}'.format(port), NoForgedFromMilter, opts)

	def sig_handler(num, frame):
		NoForgedFromMilter.log('Stopping NoForgedFromMilter.')
		milter_factory.close()
		sys.exit(0)
	signal.signal(signal.SIGINT, sig_handler)
	signal.signal(signal.SIGTERM, sig_handler)
	signal.signal(signal.SIGHUP, NoForgedFromMilter.reload_sig_handler)

	try:
		milter_factory.run()
	except Exception as exc:
		milter_factory.close()
		# print to journald/syslog and log to mail.log
		print('EXCEPTION OCCURRED: {}'.format(exc))
		traceback.print_tb(sys.exc_traceback)
		NoForgedFromMilter.log('Exception in NoForgedFromMilter run: {}'.format(exc), 'ERROR')
		sys.exit(3)


if __name__ == '__main__':
	run_milter()
