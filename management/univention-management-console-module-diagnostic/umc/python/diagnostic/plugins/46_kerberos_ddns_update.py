#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017 Univention GmbH
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

import ldap
import socket
import subprocess
import contextlib

import univention.lib.admember
import univention.config_registry
from univention.management.console.modules.diagnostic import Critical

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check kerberos authenticated DNS updates')
description = _('No errors occured.')


class UpdateError(Exception):
	pass


class KinitError(UpdateError):
	def __init__(self, principal, keytab, password_file):
		super(KinitError, self).__init__(principal, keytab, password_file)
		self.principal = principal
		self.keytab = keytab
		self.password_file = password_file

	def __str__(self):
		if self.keytab:
			msg = _('`kinit` for principal {princ} with keytab {tab} failed.')
		else:
			msg = _('`kinit` for principal {princ} with password file {file} failed.')
		return msg.format(princ=self.principal, tab=self.keytab, file=self.password_file)


class NSUpdateError(UpdateError):
	def __init__(self, hostname, domainname):
		super(NSUpdateError, self).__init__(hostname, domainname)
		self.hostname = hostname
		self.domainname = domainname

	def __str__(self):
		msg = _('`nsupdate` check for domain {domain} failed.')
		return msg.format(domain=self.domainname)


@contextlib.contextmanager
def kinit(principal, keytab=None, password_file=None):
	auth = '--keytab={tab}' if keytab else '--password-file={file}'
	cmd = ('kinit', auth.format(tab=keytab, file=password_file), principal)
	try:
		subprocess.check_call(cmd)
	except subprocess.CalledProcessError:
		raise KinitError(principal, keytab, password_file)
	else:
		yield
		subprocess.call(('kdestroy',))


def nsupdate(server, domainname):
	process = subprocess.Popen(('nsupdate', '-g' , '-t', '15'), stdin=subprocess.PIPE,
		stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	cmd = 'server {server}\nprereq yxdomain {domain}\nsend\n'
	_ = process.communicate(cmd.format(server=server, domain=domainname))
	if process.poll() != 0:
		raise NSUpdateError(server, domainname)


def get_server(config_registry):
	server = '{}.{}'.format(config_registry.get('hostname'), config_registry.get('domainname'))
	if config_registry.is_true('ad/member'):
		ad_domain_info = univention.lib.admember.lookup_adds_dc()
		return ad_domain_info.get('DC IP', server)
	return server


def check_dns_machine_principal(server, hostname, domainname):
	with kinit('{}$'.format(hostname), password_file='/etc/machine.secret'):
		nsupdate(server, domainname)


def check_dns_server_principal(hostname, domainname):
	with kinit('dns-{}'.format(hostname), keytab='/var/lib/samba/private/dns.keytab'):
		nsupdate(hostname, domainname)


def check_nsupdate(config_registry):
	server = get_server(config_registry)
	hostname = config_registry.get('hostname')
	domainname = config_registry.get('domainname')
	is_dc = config_registry.get('samba4/role') == 'DC'

	try:
		check_dns_machine_principal(server, hostname, domainname)
	except UpdateError as error:
		yield error

	if is_dc:
		try:
			check_dns_server_principal(hostname, domainname)
		except UpdateError as error:
			yield error


def is_service_active(service):
	lo = univention.uldap.getMachineConnection()
	raw_filter = '(&(univentionService=%s)(cn=%s))'
	filter_expr = ldap.filter.filter_format(raw_filter, (service, socket.gethostname()))
	for (dn, _attr) in lo.search(filter_expr, attr=['cn']):
		if dn is not None:
			return True
	return False


def run(_umc_instance):
	if is_service_active('Samba 3'):
		return  # ddns updates are not possible

	config_registry = univention.config_registry.ConfigRegistry()
	config_registry.load()

	problems = list(check_nsupdate(config_registry))
	if problems:
		ed = [_('Errors occured while running `kinit` or `nsupdate`.')]
		ed.extend(str(error) for error in problems)
		raise Critical(description='\n'.join(ed))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
