#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2019-2021 Univention GmbH
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

import os
import re
import gzip
import sys

RE_BROKEN = re.compile(r'^File "[^"]+", line \d+, in .*')
"""Match broken setup.log traceback:
Traceback (most recent call last):
File "<stdin>", line 8, in <module>
File "xyz", line 8, in bar
foo = bar
IOError: [Errno 2] No such file or directory: '/etc/machine.secret'
"""  # Bug #51834

RE_APPCENTER = re.compile(r'^(\s+\d+ .*[\d \-:]+ \[(    INFO| WARNING|   DEBUG|   ERROR)\]:)')
"""Match appcenter.log
 17954 packages                         21-02-14 04:25:09 [ WARNING]: Traceback (most recent call last):
 17954 packages                         21-02-14 04:25:09 [ WARNING]:   File "/usr/sbin/univention-pkgdb-scan", line 37, in <module>
 17954 packages                         21-02-14 04:25:09 [ WARNING]:     univention.pkgdb.main()
 17954 packages                         21-02-14 04:25:09 [ WARNING]:   File "/usr/lib/python2.7/dist-packages/pgdb.py", line 1619, in connect
 17954 packages                         21-02-14 04:25:09 [ WARNING]:     cnx = _connect(dbname, dbhost, dbport, dbopt, dbuser, dbpasswd)
 17954 packages                         21-02-14 04:25:09 [ WARNING]: Exception: foo
"""  # noqa: E101


class Tracebacks(set):

	def __init__(self, *args, **kwargs):
		super(Tracebacks, self).__init__(*args, **kwargs)
		self.occurred = 0
		self.filenames = set()


def main(filenames, ignore_exceptions={}):
	tracebacks = {}
	for filename in filenames:
		opener = gzip.open if filename.endswith('.gz') else open
		with opener(filename, 'rt') as fd:
			line = True
			while line:
				line = fd.readline()
				if line.endswith('Traceback (most recent call last):\n'):
					lines = []
					line = '  '
					while line.startswith('  ') or RE_BROKEN.match(line) or (RE_APPCENTER.match(line) and 'appcenter' in filename):
						line = fd.readline()
						if 'appcenter' in filename and RE_APPCENTER.match(line):
							line = RE_APPCENTER.sub('', line)
							lines.append(line[1:])
							if RE_BROKEN.match(line.strip()):
								lines.append(RE_APPCENTER.sub('', fd.readline())[1:])
						elif RE_BROKEN.match(line):
							lines.append('  ' + line)
							if 'File "<stdin>"' not in line:
								lines.append('    ' + fd.readline())
						else:
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
				print('\nIgnoring %s\n ' % (ignore_exc.pattern,))
				break
		if ignore:
			continue
		found = True
		print('%d times in %s:' % (exceptions.occurred, ', '.join(exceptions.filenames)))
		if os.environ.get('JENKINS_WS'):
			for fn in exceptions.filenames:
				print('%sws/test/%s' % (os.environ['JENKINS_WS'], os.path.basename(fn)))
		print('Traceback (most recent call last):')
		print(traceback, end='')
		for exc in exceptions:
			print(exc.strip())
		print('\n ')
	return not found


COMMON_EXCEPTIONS = dict((re.compile(x), [re.compile(z) if isinstance(z, str) else z for z in (y or [])]) for x, y in [
	# Errors from UCS Jenkins runs:
	(r'^(ldap\.)?SERVER_DOWN: .*', None),
	(r'^(ldap\.)?NO_SUCH_OBJECT: .*', None),
	(r'^(univention\.admin\.uexceptions\.)?objectExists: .*', [re.compile('_create.*self.lo.add', re.M | re.S)]),
	('^%s.*logo' % re.escape("IOError: [Errno 2] No such file or directory: u'/var/cache/univention-appcenter/"), [re.compile('%s.*shutil' % re.escape('<stdin>'), re.M | re.S)]),
	("INSUFFICIENT_ACCESS: {'desc': 'Insufficient access'}$", ['uldap.py.* in modify']),  # Bug #53721, ...
	("INSUFFICIENT_ACCESS: {'desc': 'Insufficient access', 'info': 'no write access to parent'}", ['uldap.py.* in add', 'uldap.py.* in delete']),  # Bug #53721, ...
	('permissionDenied$', ['_create', 'in sync_to_ucs', 'locking.py.*in lock']),
	('univention.admin.uexceptions.permissionDenied: Can not modify lock time of .*', ['in sync_to_ucs']),
	(r'^(univention\.admin\.uexceptions\.)?noObject:.*', ['__update_membership', 'sync_to_ucs', 'get_ucs_object']),
	('^ldapError: No such object', ['in _create']),
	(r"^PAM.error: \('Authentication failure', 7\)", [re.escape('<string>')]),
	(r'^univention.lib.umc.Forbidden: 403 on .* \(command/join/scripts/query\):.*', [re.escape('<string>')]),
	('^ldapError: Invalid syntax: univentionLDAPACLActive: value #0 invalid per syntax', ['_create']),
	('^ldapError: Invalid syntax: univentionLDAPSchemaActive: value #0 invalid per syntax', ['_create']),
	(r"^(FileNotFoundError|IOError): \[Errno 2\] No such file or directory: '/etc/machine.secret'", ['getMachineConnection', re.escape('<stdin>')]),  # Bug #51834
	(r'''^(cherrypy\._cperror\.)?NotFound: \(404, "The path '/(login|portal)/.*''', None),
	(r'(lockfile\.)?LockTimeout\: Timeout waiting to acquire lock for \/var\/run\/umc-server\.pid', None),
	("^FileExistsError:.*'/var/run/umc-server.pid'", None),
	(r'OSError\: \[Errno 3\].*', ['univention-management-console-server.*_terminate_daemon_process']),
	('univention.lib.umc.ServiceUnavailable: .*', ['univention-self-service-invitation']),
	(re.escape('NoSuperordinate: No superordinate was supplied, but one of type settings/cn is required to create/save a settings/portal object.'), ['univention-portal-server']),  # 4.4-8 before upgrade to 5.0-0
	(r"ldap.NO_SUCH_OBJECT: .*matched\'\: \'dc\=.*", ['^  File "/usr/lib/python3/dist-packages/univention/admin/uldap.py", line .*, in add']),
	(r"ldap.NO_SUCH_OBJECT: .*matched\'\: \'cn\=users,dc\=.*", ['^  File "/usr/lib/python3/dist-packages/univention/admin/uldap.py", line .*, in search']),  # s4c
	(r'^univention.admin.uexceptions.noObject: No such object$', ['^  File "/usr/lib/python3/dist-packages/univention/admin/objects.py", line .*, in get']),  # s4c
	# only happens if tests fails, we need this as overview of all failed pytests: ('^AssertionError.*', None),  # Already caught by tests itself

	# during upgrade to UCS 5.0-0
	("^apt.cache.FetchFailedException: E:The repository 'http://localhost/univention-repository.* Release' is not signed.", None),
	('ImportError: No module named client', ['univention-directory-listener/system/faillog.py', 'univention-directory-listener/system/udm_extension.py', 'univention-directory-listener/system/portal_groups.py', 'univention-directory-listener/system/app_attributes.py']),  # Bug #53290 Bug #53862
	("AttributeError: 'ConfigRegistry' object has no attribute '_walk'", ['univention-directory-listener/system/nfs-shares.py']),  # Bug #53291 Bug #53862
	("AttributeError: 'module' object has no attribute 'localization'", ['univention-directory-listener/system/app_attributes.py']),  # Bug #53862
	("univention.lib.umc.ConnectionError: .*Could not send request.*Connection refused", ['univention-self-service-invitation']),  # Bug #53670

	# updater test cases:
	('urllib.error.URLError: .*', ['updater/tools.py.*in access']),
	('urllib.error.HTTPError: .*', ['updater/tools.py.*in access']),
	('ConfigurationError: Configuration error: host is unresolvable', None),
	('ConfigurationError: Configuration error: port is closed', None),
	('ConfigurationError: Configuration error: non-existing prefix "/DUMMY/.*', None),
	('ConfigurationError: Configuration error: timeout in network connection', None),
	('(univention.updater.errors.)?DownloadError: Error downloading http://localhost/DUMMY/.*: 403', None),
	('ProxyError: Proxy configuration error: credentials not accepted', None),
	('socket.timeout: timed out', None),
	(r'socket.gaierror: \[Errno \-2\] Name or service not known', None),
	('ConfigurationError: Configuration error: Temporary failure in name resolution', ['in access']),
	(r'socket.gaierror: \[Errno \-3\] Temporary failure in name resolution', ['urllib/request.py']),
	# 10_ldap/listener_module_testpy
	('MyTestException: .*', None),
	('univention.management.console.modules.ucstest.ThreadedError', None),  # 60_umc/17_traceback_handling.py
	# various test cases:
	('AssertionError: .*contain.*traceback', ['01_var_log_tracebacks']),
	('^(univention.management.console.modules.ucstest.)?NonThreadedError$', None),
	(r'^(ldap\.)?INVALID_SYNTAX: .*ABCDEFGHIJKLMNOPQRSTUVWXYZ.*', ['sync_from_ucs']),
	(r'^(ldap\.)?INVALID_SYNTAX: .*telephoneNumber.*', ['sync_from_ucs']),  # Bug #35391 52_s4connector/134sync_incomplete_attribute_ucs
	('^ldap.OTHER: .*[cC]annot rename.*parent does not exist', ['sync_from_ucs']),  # Bug #53748, ...
	('univention.lib.umc.ConnectionError:.*machine.secret.*', None),
	('univention.lib.umc.ConnectionError:.*CERTIFICATE_VERIFY_FAILED.*', None),
	(r'^OSError: \[Errno 24\] Too many open files', None),
	(r'error: \[Errno 24\] Too many open files.*', None),
	('ImportError: cannot import name saxutils', [r'_cperror\.py']),
	(r'gaierror: \[Errno -5\] No address associated with hostname', None),
	('.*moduleCreationFailed: Target directory.*not below.*', None),
	("univention.udm.exceptions.NoObject: No object found at DN 'cn=internal-name-for-a-tile", ['in refresh']),  # 86_selenium/185_portal_administration_inline_creation  # Bug #53333
	("univention.admin.uexceptions.noObject: cn=internal-name-for-a-tile,cn=entry,cn=portals", None),  # 86_selenium/185_portal_administration_inline_creation  # Bug #53333
	("ldap.NO_SUCH_OBJECT:.*'matched': 'cn=entry,cn=portals,cn=univention,", None),  # 86_selenium/185_portal_administration_inline_creation  # Bug #53333
	('univention.testing.utils.LDAPObjectNotFound: DN:', ['test_container_cn_rename_uppercase_rollback_with_special_characters']),  # Bug #53776
	('dns.resolver.NoAnswer: The DNS response does not contain an answer to the question:', ['test__dns_reverse_zone_check_resolve', 'test_dns_reverse_zone_check_resolve']),  # Bug #53775
	('^KeyError$', ['in find_rrset']),  # Bug #53775
	# UCS@school test cases:
	# ("ucsschool.importer.exceptions.InitialisationError: Value of 'scheme:description' must be a string.", ['in prepare_import']),  # Bug #53564
	("ucsschool.importer.exceptions.ConfigurationError: Columns configured in csv:mapping missing:", ['in read_input']),  # Bug #53564
	("ValueError: time data '.*' does not match format '%Y-%m-%d'", ['import_user.py.* in validate']),  # Bug #53564
	("ucsschool.importer.exceptions.InitialisationError: Recursion detected when resolving formatting dependencies for 'email'.", ['user_import.py.* in read_input']),  # Bug #53564
	("ucsschool.importer.exceptions.InvalidBirthday: Birthday has invalid format: '.*' error: time data '.*' does not match format '%Y-%m-%d'.", ['user_import.py.* in create_and_modify_users']),  # Bug #53564
	("ucsschool.importer.exceptions.UcsSchoolImportSkipImportRecord: Skipping user '.*' with firstname starting with \".\"", ['user_import.py.* in create_and_modify_users']),  # Bug #53564
	("ucsschool.importer.exceptions.TooManyErrors: More than 0 errors.", ['cmdline.py.* in main', 'in import_users']),  # Bug #53564
	(r"ucsschool.importer.exceptions.InitialisationError: Configuration value of username:max_length:default is .*, but must not be higher than UCR variable ucsschool/username/max_length \(20\).", ['in prepare_import']),  # Bug #53564
	("ucsschool.importer.exceptions.InitialisationError: The 'user_deletion' configuration key is deprecated. Please set 'deletion_grace_period'.", ['in prepare_import']),  # Bug #53564
	("ucsschool.importer.exceptions.InitialisationError: Thou shalt not import birthdays!", ['in prepare_import']),  # Bug #53564
	("ucsschool.importer.exceptions.InitialisationError: Deprecated configuration key 'scheme:username:allow_rename'.", ['in prepare_import']),  # Bug #53564
	("ucsschool.importer.exceptions.InitialisationError: Value of 'scheme:.*' must be a string.", ['in prepare_import']),  # Bug #53564
	("ucsschool.importer.exceptions.MoveError: Error moving.*from school 'NoSchool' to", ['in create_and_modify_users']),  # Bug #53564
	("ucsschool.importer.exceptions.UniqueIdError: Username '.*' is already in use by .*", ['in create_and_modify_users']),  # Bug #53564
	('ucsschool.importer.exceptions.UserValidationError: <unprintable UserValidationError object>', ['in create_and_modify_users']),  # Bug #53564
	("ucsschool.importer.exceptions.UnknownSchoolName: School '.*' does not exist.", ['in create_and_modify_users']),  # Bug #53564
	(".*WARNING/ForkPoolWorker.* in create_and_modify_users", []),  # Bug #53564
	(r"ucsschool.lib.models.attributes.ValidationError: .*is missing in the users 'school\(s\)' attributes", ['in create_and_modify_users']),  # Bug #53564
	("Exception: Empty user.input_data.", ['test228_input_data_pyhook.py']),  # Bug #53564
	("ConnectionForced:.*broker forced connection closure with reason .*shutdown", ['celery']),  # Bug #53564
	(r"error: \[Errno 104\] Connection reset by peer", ['celery']),  # Bug #53671 Bug #53564
	(r"ConnectionResetError: \[Errno 104\] Connection reset by peer", ['celery']),  # Bug #53671 Bug #53564
	("gunicorn.errors.HaltServer:.*Worker failed to boot", ['gunicorn']),  # Bug #53564
	("univention.admin.uexceptions.noLock: The attribute 'uid' could not get locked.", ['users/user.py.*in _ldap_pre_ready']),  # Bug #53749
	("univention.admin.uexceptions.uidAlreadyUsed: .*", ['in sync_to_ucs']),  # Bug #53749
	(r"IOError: \[Errno 2\] No such file or directory: u'/etc/ucsschool-import/(postgres|django_key).secret'", ['gunicorn']),  # Bug #53750
	("ImportError: Error accessing LDAP via machine account: {'desc': 'Invalid credentials'}", ['univention-directory-listener/system/ucsschool-s4-branch-site.py']),
	# Tracebacks caused by specific bugs:
	(r'^ldap\.NO_SUCH_OBJECT: .*', [r'quota\.py']),  # Bug #52765
	(r'.*OperationalError.*FATAL:.*admindiary.*', [r'admindiary_backend_wrapper\.py', '_wrap_pool_connect']),  # Bug #51671
	(r"(OSError|FileNotFoundError): \[Errno 2\] .*: '/var/lib/samba/sysvol/.*/Policies/'", [r'sysvol-cleanup\.py']),  # Bug #51670
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
	(r'^(univention\.admin\.uexceptions\.)?primaryGroupWithoutSamba: .*', ['primary_group_sync_to_ucs', 'sync_to_ucs']),  # Bug #49881
	(r"^(OS|IO)Error: \[Errno 2\] .*: '/usr/lib/pymodules/python2.7/univention/admin/syntax.d/.*", ['import_syntax_files']),  # package upgrade before dh-python  # Bug #52958
	(r"^(OS|IO)Error: \[Errno 2\] .*: '/usr/lib/pymodules/python2.7/univention/admin/hooks.d/.*", ['import_hook_files']),  # package upgrade before dh-python  # Bug #52958
	(r'^(univention\.admin\.uexceptions\.)?(insufficientInformation|noSuperordinate): No superordinate object given', ['sync_to_ucs']),  # Bug #49880
	("^AttributeError: type object 'object' has no attribute 'identify'", [r'faillog\.py']),
	(r"FileNotFoundError: \[Errno 2\] No such file or directory: '/var/cache/univention-appcenter/.*\.logo'", ['File "<stdin>"']),  # 55_app_modproxy
	('^IndexError: list index out of range', ['_read_from_ldap', 'get_user_groups']),  # Bug #46932, Bug #48943
	(r"AttributeError\: \'NoneType\' object has no attribute \'searchDn\'", ['get_user_groups']),  # Bug #48943
	("^subprocess.CalledProcessError: Command.*univention-directory-manager.*settings/portal_entry.*(create|remove).*univentionblog.*", [r'license_uuid\.py']),  # 45787
	("^KeyError: 'gidNumber'", ['_ldap_pre_remove']),  # Bug #51669
	(r'^(BrokenPipeError|IOError): \[Errno 32\] Broken pipe', ['process_output']),  # Bug #32532
	(r'^(ldap\.)?NOT_ALLOWED_ON_NONLEAF: .*subtree_delete:.*', ['s4_zone_delete']),  # Bug #43722 Bug #47343
	('^NoObject: No object found at DN .*', ['univention-portal-server.*in refresh']),
	(r"^OSError\: \[Errno 2\].*\/var\/run\/univention-management-console\/.*\.socket", None),
	(r'ldapError\:\ Type\ or\ value\ exists\:\ univentionPortalEntryLink\:\ value\ \#0\ provided\ more\ than\ once', None),  # Bug #51808
	(r"noLock\: The attribute \'sid\' could not get locked\.", ['getMachineSid', '__generate_group_sid']),  # Bug #44294
	(r'^ImportError\: No module named debhelper', [r'univention\/config_registry\/handler\.py']),  # Bug #51815
	(r'^NO\_SUCH\_OBJECT\:.*users.*', ['password_sync_s4_to_ucs']),  # Bug #50279
	(re.escape("Exception: Modifying blog entry failed: 1: E: Daemon died."), []),  # Bug #45787
	(r'pg.InternalError: FATAL:\s*PAM-Authentifizierung für Benutzer ».*$« fehlgeschlagen', ['univention-pkgdb-scan']),  # Bug #50937
	('pg.InternalError: FATAL:.*kein pg_hba.conf-Eintrag für Host', ['univention-pkgdb-scan']),  # 52790
	('pg.InternalError: FATAL:.*Datenbank .*pkgdb.* existiert nicht', ['univention-pkgdb-scan']),  # 52791
	('pg.InternalError: could not connect to server: No such file or directory', ['univention-pkgdb-scan']),  # 52795
	("TypeError: 'NoneType' object has no attribute '__getitem__'", ['add_primary_group_to_addlist']),  # Bug #47440
	("TypeError: argument of type 'NoneType' is not iterable", ['disable_user_from_ucs', 'primary_group_sync_from_ucs']),  # Bug #52788, Bug #51809
	(r"FileNotFoundError\: \[Errno 2\] No such file or directory\: \'\/etc\/machine\.secret\'", [r'bind\.py.*_ldap_auth_string']),  # Bug #52789
	('dbm.error: db type could not be determined', ['univention-management-console-web-server']),  # Bug #52764
	('at least one delete handler failed', ['_add_all_shares_below_this_container_to_dn_list', 'cleanup_python_moduledir']),  # Bug #43171, ...
	('ldap.NO_SUCH_OBJECT', ['_add_all_shares_below_this_container_to_dn_list']),  # Bug #43171
	(re.escape('LISTENER    ( PROCESS ) : updating') + '.*command a', ['cleanup_python_moduledir']),  # ...
	('ldap.ALREADY_EXISTS.*as it is still the primaryGroupID', ['in sync_from_ucs']),  # Bug #53278
	('ldap.ALREADY_EXISTS.*already set via primaryGroupID', ['in sync_from_ucs']),  # Bug #53278
	('ldap.NOT_ALLOWED_ON_NONLEAF:.*Unable to delete a non-leaf node .*it has .* child', ['in delete_in_s4']),  # Bug #53278
	('univention.admin.uexceptions.valueError: The domain part of the primary mail address is not in list of configured mail domains:', ['in sync_to_ucs']),  # Bug #53277
	(r"subprocess.CalledProcessError: Command '\('rndc', 'reconfig'\)' returned non-zero exit status 1", ['univention-fix-ucr-dns']),  # Bug #53332
	(r"ldap.NO_SUCH_OBJECT: .*objectclass: Cannot add cn=(user|machine),cn=\{[0-9a-f-]+\},cn=policies,cn=system,DC=.*parent does not exist", ['in sync_from_ucs']),  # Bug #53334
	("TypeError: 'NoneType' object is not subscriptable", ['primary_group_sync_to_ucs', 'add_primary_group_to_addlist']),  # Bug #53276
	("CONSTRAINT_VIOLATION: .*Failed to re-index objectSid in .*unique index violation on objectSid", ['sync_from_ucs']),  # Bug #53720 Bug #53752
	('ldap.REFERRAL:.*', ['uldap.py']),  # Bug #53721
	('INSUFFICIENT_ACCESS:.*', ['in password_sync_s4_to_ucs']),  # Bug #53721
	("ModuleNotFoundError: No module named 'univention.config_registry'", ['/usr/sbin/univention-config-registry']),  # Bug #53765
	("AttributeError: module 'univention.admin.syntax' has no attribute 'UMCMessageCatalogFilename_and_GNUMessageCatalog'", ['_unregister_app', 'import_hook_files', 'pupilgroups.py']),  # Bug #53754
	('univention.admin.uexceptions.noObject: uid=.*', ['connector/ad/.*set_userPrincipalName_from_ucr']),  # Bug #53769
	('ldap.TYPE_OR_VALUE_EXISTS:.*SINGLE-VALUE attribute description.*specified more than once', ['sync_from_ucs']),  # Bug #52801
])


if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--ignore-exception', '-i', default='^$')
	parser.add_argument('-d', '--default-exceptions', action='store_true')
	parser.add_argument('filename', nargs='+')
	args = parser.parse_args()
	ignore_exceptions = COMMON_EXCEPTIONS if args.default_exceptions else {re.compile(args.ignore_exception): None}
	sys.exit(int(not main(args.filename, ignore_exceptions=ignore_exceptions)))
