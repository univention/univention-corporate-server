#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017-2019 Univention GmbH
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
import shutil
import os.path
import datetime
import tempfile
import subprocess
import contextlib

import requests
import dateutil.tz
from OpenSSL import crypto
import univention.config_registry
from univention.management.console.modules.diagnostic import Critical, Warning, MODULE

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate
run_descr = ['This can be checked by running: ucr get server/role and ucr get ldap/master']
title = _('Check validity of SSL certificates')
description = _('All SSL certificates valid.')
links = [{
	'name': 'sdb',
	'href': _('http://sdb.univention.de/1183'),
	'label': _('Univention Support Database - Renewing the TLS/SSL certificates')
}]


WARNING_PERIOD = datetime.timedelta(days=50)


class CertificateWarning(Exception):
	def __init__(self, path):
		super(CertificateWarning, self).__init__(path)
		self.path = path


class CertificateWillExpire(CertificateWarning):
	def __init__(self, path, remaining):
		super(CertificateWillExpire, self).__init__(path)
		self.remaining = remaining

	def __str__(self):
		msg = _('Certificate {path!r} will expire in {days} days.')
		days = int(self.remaining.total_seconds() / 60 / 60 / 24)
		return msg.format(path=self.path, days=days)


class CertificateError(CertificateWarning):
	pass


class CertificateNotYetValid(CertificateError):
	def __str__(self):
		msg = _('Found not yet valid certificate {path!r}.')
		return msg.format(path=self.path)


class CertificateExpired(CertificateError):
	def __str__(self):
		msg = _('Found expired certificate {path!r}.')
		return msg.format(path=self.path)


class CertificateInvalid(CertificateError):
	def __init__(self, path, message):
		super(CertificateInvalid, self).__init__(path)
		self.message = message

	def __str__(self):
		if self.message:
			msg = _('Found invalid certificate {path!r}:\n{message}')
		else:
			msg = _('Found invalid certificate {path!r}.')
		return msg.format(path=self.path, message=self.message)


class CertificateMalformed(CertificateError):
	def __init__(self, path):
		super(CertificateMalformed, self).__init__(path)

	def __str__(self):
		msg = _('Found malformed certificate {path!r}.')
		return msg.format(path=self.path)


class CertificateVerifier(object):
	def __init__(self, root_cert_path, crl_path):
		self.root_cert_path = root_cert_path
		self.crl_path = crl_path

	@staticmethod
	def parse_generalized_time(generalized_time):
		# ASN.1 GeneralizedTime
		# Local time only. ``YYYYMMDDHH[MM[SS[.fff]]]''
		# Universal time (UTC time) only. ``YYYYMMDDHH[MM[SS[.fff]]]Z''.
		# Difference between local and UTC times. ``YYYYMMDDHH[MM[SS[.fff]]]+-HHMM''.

		sans_mircoseconds = re.sub('\.\d{3}', '', generalized_time)
		sans_difference = re.sub('[+-]\d{4}', '', sans_mircoseconds)
		date_format = {
			10: '%Y%m%d%H', 12: '%Y%m%d%H%M', 14: '%Y%m%d%H%M%S',
			11: '%Y%m%d%HZ', 13: '%Y%m%d%H%MZ', 15: '%Y%m%d%H%M%SZ',
		}.get(len(sans_difference))

		if date_format is None:
			raise ValueError('Unparsable generalized_time {!r}'.format(generalized_time))

		date = datetime.datetime.strptime(sans_mircoseconds, date_format)
		utc_difference = re.search('([+-])(\d{2})(\d{2})', sans_mircoseconds)

		if sans_mircoseconds.endswith('Z'):
			return date.replace(tzinfo=dateutil.tz.tzutc())
		elif utc_difference:
			(op, hours_str, minutes_str) = utc_difference.groups()
			try:
				(hours, minutes) = (int(hours_str), int(minutes_str))
			except ValueError:
				raise ValueError('Unparsable generalized_time {!r}'.format(generalized_time))

			if op == '+':
				offset = datetime.timedelta(hours=hours, minutes=minutes)
			else:
				offset = datetime.timedelta(hours=-hours, minutes=-minutes)
			with_offset = date.replace(tzinfo=dateutil.tz.tzoffset('unknown', offset))
			return with_offset.astimezone(dateutil.tz.tzutc())
		as_local = date.replace(tzinfo=dateutil.tz.tzlocal())
		return as_local.astimezone(dateutil.tz.tzutc())

	def _verify_timestamps(self, cert_path):
		now = datetime.datetime.now(dateutil.tz.tzutc())

		with open(cert_path) as fob:
			try:
				cert = crypto.load_certificate(crypto.FILETYPE_PEM, fob.read())
			except crypto.Error:
				yield CertificateMalformed(cert_path)
			else:
				valid_from = self.parse_generalized_time(cert.get_notBefore())

				if now < valid_from:
					yield CertificateNotYetValid(cert_path)

				valid_until = self.parse_generalized_time(cert.get_notAfter())
				expires_in = valid_until - now

				if expires_in < datetime.timedelta():
					yield CertificateExpired(cert_path)
				elif expires_in < WARNING_PERIOD:
					yield CertificateWillExpire(cert_path, expires_in)

	def _openssl_verify(self, path):
		# XXX It would be nice to do this in python. `python-openssl` has the
		# capability to check against CRL since version 16.1.0, but
		# unfortunately only version 0.14 is available in debian.
		cmd = ('openssl', 'verify', '-CAfile', self.root_cert_path, '-CRLfile', self.crl_path, '-crl_check', path)
		verify = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		(stdout, stderr) = verify.communicate()
		if verify.poll() != 0:
			# `openssl` can not cope with both `-CAfile` and `-CApath` at the
			# same time, so we need a second call. If omitted, `openssl` will
			# use `/etc/ssl/certs`.
			verify_sys = subprocess.Popen(('openssl', 'verify', path), stdout=subprocess.PIPE)
			verify_sys.communicate()
			if verify_sys.poll() != 0:
				yield CertificateInvalid(path, stdout)

	def verify_root(self):
		for error in self.verify(self.root_cert_path):
			yield error

	def verify(self, cert_path):
		for error in self._verify_timestamps(cert_path):
			yield error
		for error in self._openssl_verify(cert_path):
			yield error


def certificates(configRegistry):
	fqdn = '{}.{}'.format(configRegistry.get('hostname'), configRegistry.get('domainname'))
	default_certificate = '/etc/univention/ssl/{}/cert.pem'.format(fqdn)
	yield configRegistry.get('apache2/ssl/certificate', default_certificate)

	saml_certificate = configRegistry.get('saml/idp/certificate/certificate')
	if saml_certificate:
		yield saml_certificate

	postfix_certificate = configRegistry.get('mail/postfix/ssl/certificate')
	if postfix_certificate:
		yield postfix_certificate

	if os.path.exists('/etc/univention/ssl/ucsCA/index.txt'):
		with open('/etc/univention/ssl/ucsCA/index.txt') as fob:
			for line in fob.readlines():
				try:
					(status, _expiry, _revoked, serial, _path, _subject) = line.split('\t', 6)
				except ValueError:
					pass
				else:
					if status.strip() == 'V':
						yield '/etc/univention/ssl/ucsCA/certs/{}.pem'.format(serial)


@contextlib.contextmanager
def download_tempfile(url):
	with tempfile.NamedTemporaryFile() as fob:
		response = requests.get(url, stream=True)
		shutil.copyfileobj(response.raw, fob)
		fob.flush()
		yield fob.name


@contextlib.contextmanager
def convert_crl_to_pem(path):
	with tempfile.NamedTemporaryFile() as fob:
		convert = ('openssl', 'crl', '-inform', 'DER', '-in', path, '-outform', 'PEM', '-out', fob.name)
		subprocess.check_call(convert)
		yield fob.name


def verify_local(all_certificates):
	with convert_crl_to_pem('/etc/univention/ssl/ucsCA/crl/ucsCA.crl') as crl:
		verifier = CertificateVerifier('/etc/univention/ssl/ucsCA/CAcert.pem', crl)
		for error in verifier.verify_root():
			yield error
		for cert in all_certificates:
			for error in verifier.verify(cert):
				yield error


def verify_from_master(master, all_certificates):
	root_ca_uri = 'http://{}/ucs-root-ca.crt'.format(master)
	crl_uri = 'http://{}/ucsCA.crl'.format(master)
	with download_tempfile(root_ca_uri) as root_ca, download_tempfile(crl_uri) as crl:
		with convert_crl_to_pem(crl) as crl_pem:
			verifier = CertificateVerifier(root_ca, crl_pem)
			for error in verifier.verify_root():
				yield error
			for cert in all_certificates:
				for error in verifier.verify(cert):
					yield error


def run(_umc_instance):
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	all_certificates = certificates(configRegistry)
	is_local_check = configRegistry.get('server/role') in \
		('domaincontroller_master', 'domaincontroller_backup')

	if is_local_check:
		cert_verify = list(verify_local(all_certificates))
	else:
		cert_verify = list(verify_from_master(configRegistry.get('ldap/master'), all_certificates))

	error_descriptions = [str(error) for error in cert_verify if isinstance(error, CertificateWarning)]

	if error_descriptions:
		error_descriptions.append(_('Please see {sdb} on how to renew certificates.'))
		if any(isinstance(error, CertificateError) for error in cert_verify):
			raise Critical(description='\n'.join(error_descriptions))
		MODULE.error('\n'.join(error_descriptions))
		raise Warning(description='\n'.join(error_descriptions))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
