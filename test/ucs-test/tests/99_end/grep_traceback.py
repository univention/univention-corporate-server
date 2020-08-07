#!/usr/bin/python2.7
#
# Copyright 2019-2020 Univention GmbH
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
"""Grep python tracebacks in logfiles"""

from __future__ import print_function

import re
import gzip
import sys


class Set(set):
	pass


def main(filenames, ignore_exceptions=(), ignore_tracebacks=()):
	tracebacks = {}
	for filename in filenames:
		opener = gzip.open if filename.endswith('.gz') else open
		with opener(filename) as fd:
			line = True
			while line:
				line = fd.readline()
				if line.endswith('Traceback (most recent call last):\n'):
					lines = []
					line = ' '
					while line.startswith(' '):
						line = fd.readline()
						lines.append(line)
					d = Set()
					d.occurred = 1
					d.filenames = set()
					tb = tracebacks.setdefault(''.join(lines[:-1]), d)
					tb.add(lines[-1])
					tb.occurred += 1
					d.filenames.add(filename)

	print(len(tracebacks))
	found = False
	for traceback, exceptions in tracebacks.items():
		ignored_exc = (ignore for exc in exceptions for ignore in ignore_exceptions if ignore.search(exc))
		ignored_tracebacks = (ignore for exc in exceptions for ignore in ignore_tracebacks if ignore.search(exc))
		try:
			print('\nIgnoring %s\n' % ((next(ignored_exc) or next(ignored_tracebacks)).pattern,))
			continue
		except StopIteration:
			pass
		found = True
		print('%d times in %s:' % (exceptions.occurred, ', '.join(d.filenames)))
		print('Traceback (most recent call last):')
		print(traceback, end='')
		for exc in exceptions:
			print(exc, end=' ')
		print()
	return not found


COMMON_EXCEPTIONS = [re.compile(x) for x in [
	# Errors from UCS 4.4-5 Jenkins runs:
	'^SERVER_DOWN: .*',
	'^INVALID_SYNTAX: .*ABCDEFGHIJKLMNOPQRSTUVWXYZ.*',
	'^OTHER: .*cannot rename.*',
	'^NOT_ALLOWED_ON_NONLEAF: .*subtree_delete:.*',
	'^ldapError: No such object',
	'^objectExists: .*',
	'^%s.*logo' % re.escape("IOError: [Errno 2] No such file or directory: u'/var/cache/univention-appcenter/"),
	'^permissionDenied$',
	'^noObject:.*',
	'^NoObject: No object found at DN .*',
	r'^OSError: \[Errno 24\] Too many open files',
	r'error: \[Errno 24\] Too many open files.*',
	r'gaierror: \[Errno -5\] No address associated with hostname',
	r'''^NotFound: \(404, "The path '/(login|portal)/.*''',
	'^IndexError: list index out of range',
	"^KeyError: 'gidNumber'",
	'^ldap.NO_SUCH_OBJECT: .*',
	r"^PAM.error: \('Authentication failure', 7\)",
	r'^univention.lib.umc.Forbidden: 403 on .* \(command/join/scripts/query\):.*',
	r'^IOError: \[Errno 32\] Broken pipe',
	"^apt.cache.FetchFailedException: E:The repository 'http://localhost/univention-repository/.* Release' is not signed.",
	'^ldapError: Invalid syntax: univentionLDAPACLActive: value #0 invalid per syntax',
	'^ldapError: Invalid syntax: univentionLDAPSchemaActive: value #0 invalid per syntax',
	'^univention.admin.uexceptions.objectExists: .*',
	'^NonThreadedError$',
	re.escape("IOError: [Errno 2] No such file or directory: '/etc/machine.secret'"),
	'.*moduleCreationFailed: Target directory.*not below.*',
	"^subprocess.CalledProcessError: Command.*univention-directory-manager.*settings/portal_entry.*(create|remove).*univentionblog.*",
	'^cherrypy._cperror.NotFound:.*',
	re.escape('lockfile.LockTimeout: Timeout waiting to acquire lock for /var/run/umc-server.pid'),
	"^FileExistsError:.*'/var/run/umc-server.pid'"
	'ConfigurationError: Configuration error: host is unresolvable',
	'ConfigurationError: Configuration error: port is closed',
	'ConfigurationError: Configuration error: non-existing prefix "/DUMMY/.*',
	'ConfigurationError: Configuration error: timeout in network connection',
	'DownloadError: Error downloading http://localhost/DUMMY/: 403',
	'ProxyError: Proxy configuration error: credentials not accepted',
	'MyTestException: .*',
	'univention.lib.umc.ConnectionError:.*machine.secret.*',
	'univention.lib.umc.ConnectionError:.*CERTIFICATE_VERIFY_FAILED.*',
	r'^OperationalError: \(psycopg2.OperationalError\) FATAL:.*admindiary.*',  # Bug #51671
	r"OSError: \[Errno 2\] No such file or directory: '/var/lib/samba/sysvol/.*/Policies/'",  # Bug #51670
	"AttributeError: 'NoneType' object has no attribute 'lower'",  # Bug #50282
	"AttributeError: 'NoneType' object has no attribute 'get'",  # Bug #49879
	'^ImportError: No module named __base',  # Bug #50338
	'^ImportError: No module named admindiary.client',  # Bug #49866
	'^ImportError: No module named types',  # Bug #50381
	'^ImportError: No module named directory',  # Bug #50338
	'^primaryGroupWithoutSamba: .*',  # Bug #49881

	# '^ldap.NO_SUCH_OBJECT: .*',
]]


if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--ignore-exception', '-i', default='^$')
	parser.add_argument('filename', nargs='+')
	args = parser.parse_args()
	sys.exit(int(not main(args.filename, ignore_exceptions=[re.compile(args.ignore_exception)])))
