# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  license check
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

import getopt
import datetime
import traceback

import univention.admin.license
import univention.admin.uexceptions as uexceptions
import univention.admin.uldap
import univention.config_registry
import univention.license

License = univention.admin.license.License
_license = univention.admin.license._license


class UsageError(Exception):
	pass


def usage(msg=None):
	out = []
	script_name = 'univention-license-check'
	if msg:
		out.append('E: %s' % msg)
	out.append('usage: %s [options]' % script_name)
	out.append('options:')
	out.append('  --%-30s %s' % ('binddn', 'bind DN'))
	out.append('  --%-30s %s' % ('bindpw', 'bind password'))
	out.append('  --%-30s %s' % ('list-dns', 'list DNs of found objects'))
	out.append('OPERATION FAILED')
	return out


def parse_options(argv):
	options = {}
	long_opts = ['binddn=', 'bindpw=', 'list-dns']
	try:
		opts, args = getopt.getopt(argv, '', long_opts)
	except getopt.error as msg:
		raise UsageError(str(msg))
	if args:
		raise UsageError('options "%s" not recognized' % ' '.join(args))
	for opt, val in opts:
		options[opt[2:]] = val
	return options


def default_pw():
		secret = open('/etc/ldap.secret', 'r')
		passwd = secret.readline().strip()
		secret.close()
		return passwd


def format(label, num, max, expired, cmp, ignored=False):
	args = [(label + ':').ljust(20), str(num).rjust(9), str(max).rjust(9), 'OK']
	if expired:
		args[-1] = 'EXPIRED'
	elif cmp(num, max) > 0:
		args[-1] = 'FAILED'
	if ignored and args[-1] in ['FAILED', 'EXPIRED']:
		args[-1] = 'IGNORED'
	return '%s %s of %s... %s' % tuple(args)


def find_licenses(lo, baseDN, module='*'):
	def find_wrap(dir):
		try:
			return lo.searchDn(base=dir, filter='(univentionLicenseObject=*)')
		except uexceptions.noObject:
			return []
	filter = 'univentionLicenseModule=%s' % module
	dirs = ['cn=directory,cn=univention,%s' % baseDN, 'cn=default containers,cn=univention,%s' % baseDN]
	objects = [o for d in dirs for o in find_wrap(d)]
	containers = [c for o in objects for c in lo.get(o)['univentionLicenseObject']]
	licenses = [l for c in containers for l in lo.searchDn(base=c, filter=filter)]
	return licenses


def choose_license(lo, dns):
	for dn in dns:
		retval = univention.license.check(dn)
		if retval == -1:
			continue
		return dn, retval
	return None, -1


def check_license(lo, dn, list_dns, expired):
	if expired == -1:
		return ['No valid license object found', 'OPERATION FAILED']
	out = []

	def check_code(code):
		for label, value in [('searchpath', 8), ('basedn', 4), ('enddate', 2), ('signature', 1)]:
			if code >= value:
				code -= value
				ok = 'FAILED'
			else:
				ok = 'OK'
			out.append('Checking %s... %s' % ((label.ljust(10)), ok))

	def check_type():
		def mylen(xs):
			if xs is None:
				return 0
			return len(xs)
		v = _license.version
		types = _license.licenses[v]
		if dn is None:
			max = [_license.licenses[v][type] for type in types]
		else:
			max = [lo.get(dn)[_license.keys[v][type]][0] for type in types]
		objs = [lo.searchDn(filter=_license.filters[v][type]) for type in types]
		num = [mylen(obj) for obj in objs]
		_license.checkObjectCounts(max, num)
		for i in range(len(types)):
			m = max[i]
			n = num[i]
			odn = objs[i]
			if i == License.USERS or i == License.ACCOUNT:
				n -= _license.sysAccountsFound
				if n < 0:
					n = 0
			ln = _license.names[v][i]
			if m:
				if list_dns:
					out.append("")

				ignored = False
				if v == '2' and i == License.SERVERS:
					# Ignore the server count
					ignored = True
				out.append(format(ln, n, m, 0, _license.compare, ignored))
				if list_dns and not max == 'unlimited':
					for dnout in odn:
						out.extend(["  %s" % dnout, ])
				if list_dns and (i == License.USERS or i == License.ACCOUNT):
					out.append("  %s Systemaccounts are ignored." % _license.sysAccountsFound)

	def check_time():
		now = datetime.date.today()
		then = lo.get(dn)['univentionLicenseEndDate'][0]
		if not then == 'unlimited':
			(day, month, year) = then.split('.')
			then = datetime.date(int(year), int(month), int(day))
			if now > then:
				out.append('Has expired on: %s                  -- EXPIRED' % then)
			else:
				out.append('Will expire on: %s' % then)
	if dn is not None and list_dns:
		out.append('License found at: %s' % dn)
	check_code(expired)
	check_type()
	if dn is not None:
		check_time()
	return out


def main(argv):
	options = parse_options(argv)
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()
	baseDN = configRegistry['ldap/base']
	master = configRegistry['ldap/master']
	port = int(configRegistry.get('ldap/master/port', '7389'))
	binddn = options.get('binddn', 'cn=admin,%s' % baseDN)
	bindpw = options.get('bindpw', None)
	if bindpw is None:
		try:
			bindpw = default_pw()
		except IOError:
			raise UsageError("Permission denied, try `--binddn' and `--bindpwd'")
	try:
		lo = univention.admin.uldap.access(host=master, port=port, base=baseDN, binddn=binddn, bindpw=bindpw)
	except uexceptions.authFail:
		raise UsageError("Authentication failed, try `--bindpwd'")

	out = ['Base DN: %s' % baseDN]
	try:
		_license.init_select(lo, 'admin')
		out.extend(check_license(lo, None, 'list-dns' in options, 0))
	except uexceptions.base:
		dns = find_licenses(lo, baseDN, 'admin')
		dn, expired = choose_license(lo, dns)
		out.extend(check_license(lo, dn, 'list-dns' in options, expired))
	except Exception:
		# output any other tracebacks
		trace_out = traceback.format_exc().splitlines()
		out.extend(trace_out)
	finally:
		return out


def doit(argv):
	try:
		out = main(argv[1:])
		return out
	except UsageError as msg:
		return usage(str(msg))
