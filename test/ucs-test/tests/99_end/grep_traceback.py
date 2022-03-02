#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2019-2022 Univention GmbH
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

RE_BROKEN = re.compile(r'^File "[^"]+", line \d+, in .*')
"""Match broken setup.log traceback:
Traceback (most recent call last):
File "<stdin>", line 8, in <module>
IOError: [Errno 2] No such file or directory: '/etc/machine.secret'
"""  # Bug #51834


class Tracebacks(set):

	def __init__(self, *args, **kwargs):
		super(Tracebacks, self).__init__(*args, **kwargs)
		self.occurred = 0
		self.filenames = set()


def main(filenames, ignore_exceptions={}):
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
					while line.startswith(' ') or RE_BROKEN.match(line):
						line = fd.readline()
						lines.append(line)
					d = Tracebacks()
					tb = tracebacks.setdefault(''.join(lines[:-1]), d)
					tb.add(lines[-1])
					tb.occurred += 1
					tb.filenames.add(filename)

	print('Found %d tracebacks:' % (len(tracebacks),))
	found = False
	for traceback, exceptions in tracebacks.items():
		ignore = False
		for ignore_exc, ignore_traceback in ignore_exceptions.items():
			ignore = any(ignore_exc.search(exc) for exc in exceptions) and (not ignore_traceback or any(tb_pattern.search(traceback) for tb_pattern in ignore_traceback))
			if ignore:
				print('\nIgnoring %s\n' % (ignore_exc.pattern,))
				break
		if ignore:
			continue
		found = True
		print('%d times in %s:' % (exceptions.occurred, ', '.join(exceptions.filenames)))
		print('Traceback (most recent call last):')
		print(traceback, end='')
		for exc in exceptions:
			print(exc.strip())
		print('')
	return not found


COMMON_EXCEPTIONS = dict((re.compile(x), [re.compile(z) if isinstance(z, str) else z for z in (y or [])]) for x, y in [
	# Errors from UCS 4.4-5 Jenkins runs:
	('^SERVER_DOWN: .*', None),
	(r'^(univention\.admin\.uexceptions\.)?objectExists: .*', [re.compile('_create.*self.lo.add', re.M | re.S)]),
	('^%s.*logo' % re.escape("IOError: [Errno 2] No such file or directory: u'/var/cache/univention-appcenter/"), [re.compile('%s.*shutil' % re.escape('<stdin>'), re.M | re.S)]),
	('^permissionDenied$', ['_create']),
	('^noObject:.*', ['__update_membership', 'sync_to_ucs', 'get_ucs_object']),
	('^ldapError: No such object', ['in _create']),
	('^ldap.NO_SUCH_OBJECT: .*', [r'quota\.py']),
	(r"^PAM.error: \('Authentication failure', 7\)", [re.escape('<string>')]),
	(r'^univention.lib.umc.Forbidden: 403 on .* \(command/join/scripts/query\):.*', [re.escape('<string>')]),
	('^ldapError: Invalid syntax: univentionLDAPACLActive: value #0 invalid per syntax', ['_create']),
	('^ldapError: Invalid syntax: univentionLDAPSchemaActive: value #0 invalid per syntax', ['_create']),
	(re.escape("IOError: [Errno 2] No such file or directory: '/etc/machine.secret'"), ['getMachineConnection', re.escape('<stdin>')]),  # Bug #51834
	(r'''^(cherrypy\._cperror\.)?NotFound: \(404, "The path '/(login|portal)/.*''', None),
	(r'(lockfile\.)?LockTimeout\: Timeout waiting to acquire lock for \/var\/run\/umc-server\.pid', None),
	("^FileExistsError:.*'/var/run/umc-server.pid'", None),
	(r'OSError\: \[Errno 3\].*', ['univention-management-console-server.*_terminate_daemon_process']),
	('univention.lib.umc.ServiceUnavailable: .*', ['univention-self-service-invitation']),

	# updater test cases:
	("^apt.cache.FetchFailedException: E:The repository 'http://localhost/univention-repository/.* Release' is not signed.", None),
	('ConfigurationError: Configuration error: host is unresolvable', None),
	('ConfigurationError: Configuration error: port is closed', None),
	('ConfigurationError: Configuration error: non-existing prefix "/DUMMY/.*', None),
	('ConfigurationError: Configuration error: timeout in network connection', None),
	('DownloadError: Error downloading http://localhost/DUMMY/: 403', None),
	('ProxyError: Proxy configuration error: credentials not accepted', None),
	# 10_ldap/listener_module_testpy
	('MyTestException: .*', None),
	# various test cases:
	('^(univention.management.console.modules.ucstest.)?NonThreadedError$', None),
	('^INVALID_SYNTAX: .*ABCDEFGHIJKLMNOPQRSTUVWXYZ.*', ['sync_from_ucs']),
	('^INVALID_SYNTAX: .*telephoneNumber.*', ['sync_from_ucs']),  # Bug #35391 52_s4connector/134sync_incomplete_attribute_ucs
	('^OTHER: .*[cC]annot rename.*', ['sync_from_ucs']),
	('univention.lib.umc.ConnectionError:.*machine.secret.*', None),
	('univention.lib.umc.ConnectionError:.*CERTIFICATE_VERIFY_FAILED.*', None),
	(r'^OSError: \[Errno 24\] Too many open files', None),
	(r'error: \[Errno 24\] Too many open files.*', None),
	('ImportError: cannot import name saxutils', [r'_cperror\.py']),
	(r'gaierror: \[Errno -5\] No address associated with hostname', None),
	('.*moduleCreationFailed: Target directory.*not below.*', None),
	# Tracebacks caused by specific bugs:
	(r'^OperationalError: \(psycopg2.OperationalError\) FATAL:.*admindiary.*', [r'admindiary_backend_wrapper\.py']),  # Bug #51671
	(r"OSError: \[Errno 2\] .*: '/var/lib/samba/sysvol/.*/Policies/'", [r'sysvol-cleanup\.py']),  # Bug #51670
	("AttributeError: 'NoneType' object has no attribute 'lower'", ['_remove_subtree_in_s4']),  # Bug #50282
	("AttributeError: 'NoneType' object has no attribute 'get'", ['primary_group_sync_from_ucs', 'group_members_sync_to_ucs']),  # Bug #49879
	('^ImportError: No module named __base', [r'app_attributes\.py', '_update_modules', 'univention-management-console-server.*in run']),  # Bug #50338
	('^ImportError: No module named s4', ['_update_modules']),  # Bug #50338
	(r"^TypeError\:\ \_\_init\_\_\(\)\ got\ an\ unexpected\ keyword\ argument\ \'help\_text\'", ['_update_modules']),  # Bug #50338
	('^ImportError: No module named directory', [r'app_attributes\.py']),  # Bug #50338
	('^ImportError: No module named admindiary.client', [r'faillog\.py', 'File.*uvmm', r'create_portal_entries\.py']),  # Bug #49866
	('^ImportError: No module named types', [r'import univention\.admin\.types']),  # Bug #50381
	('^ImportError: No module named docker_upgrade', ['univention-app']),  # Bug #50381
	('^ImportError: No module named docker_base', ['univention-app']),  # Bug #50381
	('^ImportError: No module named service', ['univention-app']),  # Bug #50381
	('^ImportError: No module named ldap_extension', ['get_action']),  # Bug #50381
	('^AttributeError: __exit__', ['with Server']),  # Bug #50583
	('^primaryGroupWithoutSamba: .*', ['primary_group_sync_to_ucs', 'sync_to_ucs']),  # Bug #49881
	(r"^(OS|IO)Error: \[Errno 2\] .*: '/usr/lib/pymodules/python2.7/univention/admin/syntax.d/.*", ['import_syntax_files']),  # package upgrade before dh-python
	('^insufficientInformation: No superordinate object given', ['sync_to_ucs']),  # Bug #49880
	("^AttributeError: type object 'object' has no attribute 'identify'", [r'faillog\.py']),
	('^IndexError: list index out of range', ['_read_from_ldap', 'get_user_groups']),  # Bug #46932, Bug #48943
	(r"AttributeError\: \'NoneType\' object has no attribute \'searchDn\'", ['get_user_groups']),  # Bug #48943
	("^subprocess.CalledProcessError: Command.*univention-directory-manager.*settings/portal_entry.*(create|remove).*univentionblog.*", [r'license_uuid\.py']),  # 45787
	("^KeyError: 'gidNumber'", ['_ldap_pre_remove']),  # Bug #51669
	(r'^IOError: \[Errno 32\] Broken pipe', ['process_output']),  # Bug #32532
	('^NOT_ALLOWED_ON_NONLEAF: .*subtree_delete:.*', ['s4_zone_delete']),  # Bug #43722 Bug #47343
	('^NoObject: No object found at DN .*', ['univention-portal-server.*in refresh']),
	(r"^OSError\: \[Errno 2\].*\/var\/run\/univention-management-console\/.*\.socket", None),
	(r'ldapError\:\ Type\ or\ value\ exists\:\ univentionPortalEntryLink\:\ value\ \#0\ provided\ more\ than\ once', None),  # Bug #51808
	(r"noLock\: The attribute \'sid\' could not get locked\.", ['getMachineSid', '__generate_group_sid']),  # Bug #44294
	(r'^ImportError\: No module named debhelper', [r'univention\/config_registry\/handler\.py']),  # Bug #51815
	(r'^NO\_SUCH\_OBJECT\:.*users.*', ['password_sync_s4_to_ucs']),  # Bug #50279
	(re.escape("Exception: Modifying blog entry failed: 1: E: Daemon died."), []),  # Bug #45787
	(r'pg.InternalError: FATAL:\s*PAM-Authentifizierung für Benutzer ».*$« fehlgeschlagen', ['univention-pkgdb-scan']),  # Bug #50937
	("TypeError: 'NoneType' object has no attribute '__getitem__'", ['add_primary_group_to_addlist']),  # Bug #47440
])


if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--ignore-exception', '-i', default='^$')
	parser.add_argument('filename', nargs='+')
	args = parser.parse_args()
	sys.exit(int(not main(args.filename, ignore_exceptions={re.compile(args.ignore_exception): None})))
