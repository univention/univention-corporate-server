#!/usr/bin/python3
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

import argparse
import collections
import contextlib
import gzip
import io
import os
import re
import sys

RE_BROKEN = re.compile(r'^File "[^"]+", line \d+, in .*')  # Bug #51834
RE_APPCENTER = re.compile(r'^(\s+\d+ .*[\d \-:]+ \[(    INFO| WARNING|   DEBUG|   ERROR)\]:)')


class Tracebacks(set):

	def __init__(self, *args, **kwargs):
		super(Tracebacks, self).__init__(*args, **kwargs)
		self.occurred = 0
		self.filenames = set()


@contextlib.contextmanager
def getfile(filename, mode):
	if isinstance(filename, str):
		fd = gzip.open(filename, mode) if filename.endswith('.gz') else open(filename, mode)
		with fd as fd:
			yield fd, filename
	else:
		name = getattr(filename, 'name', repr(filename))
		if isinstance(name, int):
			name = repr(filename)
		if name.endswith('.gz'):
			with gzip.open(name, mode) as fd:
				yield fd, name
		else:
			yield filename, name


def main(files, ignore_exceptions=[], out=sys.stdout):
	tracebacks = {}
	for file_ in files:
		with getfile(file_, 'rt') as (fd, filename):
			line = True
			while line:
				line = fd.readline()
				if line.endswith('Traceback (most recent call last):\n'):
					# TODO: refactor: can probably be done easily by just fetching 2 lines until first line doesn't start with '.*File "' and strip the start
					# please note that tracebacks may leave out the source code of lines in some certain situations
					num_spaces = None
					lines = []
					line = '  '
					while line.startswith('  ') or RE_BROKEN.match(line) or (RE_APPCENTER.match(line) and 'appcenter' in filename):
						line = fd.readline()
						if num_spaces is None and line.strip().startswith('File '):
							num_spaces = len(line.split('File ', 1)[0]) - 2
						if num_spaces and num_spaces > 0 and line[:num_spaces].startswith('  '):
							line = line[num_spaces:]
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

	print('Found %d tracebacks:' % (len(tracebacks),), file=out)
	found = False
	for traceback, exceptions in tracebacks.items():
		ignore = False
		for e in ignore_exceptions:
			ignore = any(e.ignore_exception.search(exc) for exc in exceptions) and (not e.ignore_traceback or any(tb_pattern.search(traceback) for tb_pattern in e.ignore_traceback))
			if ignore:
				print('', file=out)
				for bug in e.bugs:
					print('https://forge.univention.org/bugzilla/show_bug.cgi?id=%d' % (bug,), file=out)
				print('Ignoring %s ' % (e.ignore_exception.pattern,), file=out)
				break
		if ignore:
			continue
		found = True
		print('', file=out)
		print('%d times in %s:' % (exceptions.occurred, ', '.join(exceptions.filenames)), file=out)
		if os.environ.get('JENKINS_WS'):
			for fn in exceptions.filenames:
				print('%sws/test/%s' % (os.environ['JENKINS_WS'], os.path.basename(fn)), file=out)
		print('Traceback (most recent call last):', file=out)
		print(traceback, end='', file=out)
		for exc in exceptions:
			print(exc.strip(), file=out)
		print('', file=out)
	return not found


class E(collections.namedtuple('Exception', ['re_exception', 're_traceback', 'bugs_'], defaults=(None, (),))):

	@property
	def bugs(self):
		if isinstance(self.bugs_, tuple):
			return self.bugs_
		return (self.bugs_,)

	@property
	def ignore_exception(self):
		if isinstance(self.re_exception, str):
			return re.compile(self.re_exception)
		return self.re_exception

	@property
	def ignore_traceback(self):
		if isinstance(self.re_traceback, str):
			return [re.compile(self.re_traceback)]
		return [re.compile(t) if isinstance(t, str) else t for t in self.re_traceback or []]


COMMON_EXCEPTIONS = (
	# Errors from UCS Jenkins runs:
	E(r'^(ldap\.)?SERVER_DOWN: .*'),
	E(r'^(ldap\.)?NO_SUCH_OBJECT: .*'),
	E(r'^(univention\.admin\.uexceptions\.)?objectExists: .*', [re.compile('_create.*self.lo.add', re.M | re.S)]),
	E('^%s.*logo' % re.escape("IOError: [Errno 2] No such file or directory: u'/var/cache/univention-appcenter/"), [re.compile('%s.*shutil' % re.escape('<stdin>'), re.M | re.S)]),
	E("INSUFFICIENT_ACCESS: {'desc': 'Insufficient access'}$", ['uldap.py.* in modify'], 53721),
	E("INSUFFICIENT_ACCESS: {'desc': 'Insufficient access', 'info': 'no write access to parent'}", ['uldap.py.* in add', 'uldap.py.* in delete'], 53721),
	E('permissionDenied$', ['_create', 'in sync_to_ucs', 'locking.py.*in lock', 'in __primary_group']),
	E('univention.admin.uexceptions.permissionDenied: Can not modify lock time of .*', ['in sync_to_ucs']),
	E(r'^(univention\.admin\.uexceptions\.)?noObject:.*', ['__update_membership', 'sync_to_ucs', 'get_ucs_object']),
	E('^ldapError: No such object', ['in _create']),
	E(r"^PAM.error: \('Authentication failure', 7\)", [re.escape('<string>')]),
	E(r'^univention.lib.umc.Forbidden: 403 on .* \(command/join/scripts/query\):.*', [re.escape('<string>')]),
	E('^ldapError: Invalid syntax: univentionLDAPACLActive: value #0 invalid per syntax', ['_create']),
	E('^ldapError: Invalid syntax: univentionLDAPSchemaActive: value #0 invalid per syntax', ['_create']),
	E(r"^(FileNotFoundError|IOError): \[Errno 2\] No such file or directory: '/etc/machine.secret'", ['getMachineConnection', re.escape('<stdin>')], 51834),
	E(r'''^(cherrypy\._cperror\.)?NotFound: \(404, "The path '/(login|portal)/.*'''),
	E(r'(lockfile\.)?LockTimeout\: Timeout waiting to acquire lock for \/var\/run\/umc-server\.pid'),
	E("^FileExistsError:.*'/var/run/umc-server.pid'"),
	E(r'OSError\: \[Errno 3\].*', ['univention-management-console-server.*_terminate_daemon_process']),
	E('univention.lib.umc.ServiceUnavailable: .*', ['univention-self-service-invitation']),
	E(re.escape('NoSuperordinate: No superordinate was supplied, but one of type settings/cn is required to create/save a settings/portal object.'), ['univention-portal-server']),  # 4.4-8 before upgrade to 5.0-0
	E(r"ldap.NO_SUCH_OBJECT: .*matched\'\: \'dc\=.*", ['^  File "/usr/lib/python3/dist-packages/univention/admin/uldap.py", line .*, in add']),
	E(r"ldap.NO_SUCH_OBJECT: .*matched\'\: \'cn\=users,dc\=.*", ['^  File "/usr/lib/python3/dist-packages/univention/admin/uldap.py", line .*, in search']),  # s4c
	E(r'^univention.admin.uexceptions.noObject: No such object$', ['^  File "/usr/lib/python3/dist-packages/univention/admin/objects.py", line .*, in get']),  # s4c
	# during upgrade to UCS 5.0-0
	E("^(apt.cache.FetchFailedException|apt_pkg.Error): E:The repository 'http://localhost/univention-repository.* Release' is not signed."),
	E('ImportError: No module named client', [
		'univention-directory-listener/system/faillog.py',
		'univention-directory-listener/system/udm_extension.py',
		'univention-directory-listener/system/portal_groups.py',
		'univention-directory-listener/system/app_attributes.py'
	], (53290, 53862)),
	E("AttributeError: 'ConfigRegistry' object has no attribute '_walk'", ['univention-directory-listener/system/nfs-shares.py'], (53291, 53862)),
	E("AttributeError: 'module' object has no attribute 'localization'", ['univention-directory-listener/system/app_attributes.py', 'system/portal_groups.py'], 53862),
	E("ImportError: cannot import name localization", ['univention-directory-listener/system/app_attributes.py'], 53862),
	E("ConnectionRefusedError: \\[Errno 111\\] Connection refused", ['univention-self-service-invitation'], 53670),
	E("ConnectionRefusedError: \\[Errno 111\\] Connection refused", ['univention/lib/umc.py.*in send'], 53670),
	E("univention.lib.umc.ConnectionError: .*Could not send request.*Connection refused", ['univention-self-service-invitation'], 53670),
	E("ssl.SSLCertVerificationError.*self signed certificate in certificate chain", ['univention/lib/umc.py.*in send'], 53670),
	E("univention.lib.umc.ConnectionError: .*Could not send request.*SSLCertVerificationError", ['univention-self-service-invitation'], 53670),
	E("FileNotFoundError: \\[Errno 2\\] No such file or directory: '/etc/machine.secret'", ['univention/lib/umc.py.*in authenticate_with_machine_account'], 53670),
	E("TypeError: modify() got an unexpected keyword argument 'rename_callback'", ['_register_app'], 54578),
	# during UCS 5.0-0-errata updates
	E("TypeError: __init__() got an unexpected keyword argument 'cli_enabled'", ['_register_app'], 54584),

	# updater test cases:
	E('urllib.error.URLError: .*', ['updater/tools.py.*in access']),
	E('urllib.error.HTTPError: .*', ['updater/tools.py.*in access']),
	E('ConfigurationError: Configuration error: host is unresolvable'),
	E('ConfigurationError: Configuration error: port is closed'),
	E('ConfigurationError: Configuration error: non-existing prefix "/DUMMY/.*'),
	E('ConfigurationError: Configuration error: timeout in network connection'),
	E('(univention.updater.errors.)?DownloadError: Error downloading http://localhost/DUMMY/.*: 403'),
	E('ProxyError: Proxy configuration error: credentials not accepted'),
	E('socket.timeout: timed out'),
	E(r'socket.gaierror: \[Errno \-2\] Name or service not known'),
	E('ConfigurationError: Configuration error: Temporary failure in name resolution', ['in access']),
	E(r'socket.gaierror: \[Errno \-3\] Temporary failure in name resolution', ['urllib/request.py']),
	# 10_ldap/listener_module_testpy
	E('MyTestException: .*'),
	E('univention.management.console.modules.ucstest.ThreadedError'),  # 60_umc/17_traceback_handling.py
	# various test cases:
	E('AssertionError: .*contain.*traceback', ['01_var_log_tracebacks']),
	E('^(univention.management.console.modules.ucstest.)?NonThreadedError$'),
	E(r'^(ldap\.)?INVALID_SYNTAX: .*ABCDEFGHIJKLMNOPQRSTUVWXYZ.*', ['sync_from_ucs']),
	E(r'^(ldap\.)?INVALID_SYNTAX: .*telephoneNumber.*', ['sync_from_ucs'], 35391),  # 52_s4connector/134sync_incomplete_attribute_ucs
	E('^ldap.OTHER: .*[cC]annot rename.*parent does not exist', ['sync_from_ucs'], 53748),
	E('univention.lib.umc.ConnectionError:.*machine.secret.*'),
	E('univention.lib.umc.ConnectionError:.*CERTIFICATE_VERIFY_FAILED.*'),
	E(r'^OSError: \[Errno 24\] Too many open files'),
	E(r'error: \[Errno 24\] Too many open files.*'),
	E('ImportError: cannot import name saxutils', [r'_cperror\.py']),
	E(r'gaierror: \[Errno -5\] No address associated with hostname'),
	E('.*moduleCreationFailed: Target directory.*not below.*'),
	E("univention.udm.exceptions.NoObject: No object found at DN 'cn=internal-name-for-a-tile", ['in refresh']),  # 86_selenium/185_portal_administration_inline_creation  # Bug #53333
	E("univention.admin.uexceptions.noObject: cn=internal-name-for-a-tile,cn=entry,cn=portals"),  # 86_selenium/185_portal_administration_inline_creation  # Bug #53333
	E("ldap.NO_SUCH_OBJECT:.*'matched': 'cn=entry,cn=portals,cn=univention,"),  # 86_selenium/185_portal_administration_inline_creation  # Bug #53333
	E('univention.testing.utils.LDAPObjectNotFound: DN:', ['test_container_cn_rename_uppercase_rollback_with_special_characters'], 53776),
	E('dns.resolver.NoAnswer: The DNS response does not contain an answer to the question:', ['test__dns_reverse_zone_check_resolve', 'test_dns_reverse_zone_check_resolve'], 53775),
	E('^KeyError$', ['in find_rrset'], 53775),
	# UCS@school test cases:
	# ("ucsschool.importer.exceptions.InitialisationError: Value of 'scheme:description' must be a string.", ['in prepare_import'], 53564),
	E("ucsschool.importer.exceptions.ConfigurationError: Columns configured in csv:mapping missing:", ['in read_input'], 53564),
	E("ValueError: time data '.*' does not match format '%Y-%m-%d'", ['import_user.py.* in validate'], 53564),
	E("ucsschool.importer.exceptions.InitialisationError: Recursion detected when resolving formatting dependencies for 'email'.", ['user_import.py.* in read_input'], 53564),
	E("ucsschool.importer.exceptions.InvalidBirthday: Birthday has invalid format: '.*' error: time data '.*' does not match format '%Y-%m-%d'.", ['user_import.py.* in create_and_modify_users'], 53564),
	E("ucsschool.importer.exceptions.UcsSchoolImportSkipImportRecord: Skipping user '.*' with firstname starting with \".\"", ['user_import.py.* in create_and_modify_users'], 53564),
	E("ucsschool.importer.exceptions.TooManyErrors: More than 0 errors.", ['cmdline.py.* in main', 'in import_users'], 53564),
	E(
		r"ucsschool.importer.exceptions.InitialisationError: Configuration value of username:max_length:default is .*, "
		r"but must not be higher than UCR variable ucsschool/username/max_length \(20\).", ['in prepare_import'], 53564),
	E("ucsschool.importer.exceptions.InitialisationError: The 'user_deletion' configuration key is deprecated. Please set 'deletion_grace_period'.", ['in prepare_import'], 53564),
	E("ucsschool.importer.exceptions.InitialisationError: Thou shalt not import birthdays!", ['in prepare_import'], 53564),
	E("ucsschool.importer.exceptions.InitialisationError: Deprecated configuration key 'scheme:username:allow_rename'.", ['in prepare_import'], 53564),
	E("ucsschool.importer.exceptions.InitialisationError: Value of 'scheme:.*' must be a string.", ['in prepare_import'], 53564),
	E("ucsschool.importer.exceptions.MoveError: Error moving.*from school 'NoSchool' to", ['in create_and_modify_users'], 53564),
	E("ucsschool.importer.exceptions.UniqueIdError: Username '.*' is already in use by .*", ['in create_and_modify_users'], 53564),
	E('ucsschool.importer.exceptions.UserValidationError: <unprintable UserValidationError object>', ['in create_and_modify_users'], 53564),
	E("ucsschool.importer.exceptions.UnknownSchoolName: School '.*' does not exist.", ['in create_and_modify_users'], 53564),
	E(".*WARNING/ForkPoolWorker.* in create_and_modify_users", [], 53564),
	E(r"ucsschool.lib.models.attributes.ValidationError: .*is missing in the users 'school\(s\)' attributes", ['in create_and_modify_users'], 53564),
	E("Exception: Empty user.input_data.", ['test228_input_data_pyhook.py'], 53564),
	E("ConnectionForced:.*broker forced connection closure with reason .*shutdown", ['celery'], 53564),
	E(r"error: \[Errno 104\] Connection reset by peer", ['celery'], (53671, 53564)),
	E(r"ConnectionResetError: \[Errno 104\] Connection reset by peer", ['celery'], (53671, 53564)),
	E("gunicorn.errors.HaltServer:.*Worker failed to boot", ['gunicorn'], 53564),
	E("univention.admin.uexceptions.noLock: The attribute 'uid' could not get locked.", ['users/user.py.*in _ldap_pre_ready'], 53749),
	E("univention.admin.uexceptions.uidAlreadyUsed: .*", ['in sync_to_ucs'], 53749),
	E(r"IOError: \[Errno 2\] No such file or directory: u'/etc/ucsschool-import/(postgres|django_key).secret'", ['gunicorn'], 53750),
	E("ImportError: Error accessing LDAP via machine account: {'desc': 'Invalid credentials'}", ['univention-directory-listener/system/ucsschool-s4-branch-site.py']),
	E("ldap.CONSTRAINT_VIOLATION: .*unique index violation on objectSid", ['in sync_from_ucs'], 43775),  # a test creates a user with the default Administrators SID, which creates a SID-Conflict
	# Tracebacks caused by specific UCS bugs:
	E(r'^ldap\.NO_SUCH_OBJECT: .*', [r'quota\.py'], 52765),
	E(r'.*OperationalError.*FATAL:.*admindiary.*', [r'admindiary_backend_wrapper\.py', '_wrap_pool_connect'], 51671),
	E(r"(OSError|FileNotFoundError): \[Errno 2\] .*: '/var/lib/samba/sysvol/.*/Policies/'", [r'sysvol-cleanup\.py'], 51670),
	E("AttributeError: 'NoneType' object has no attribute 'lower'", ['_remove_subtree_in_s4'], 50282),
	E("AttributeError: 'NoneType' object has no attribute 'get'", ['primary_group_sync_from_ucs', 'group_members_sync_to_ucs'], 49879),
	E('^ImportError: No module named __base', [r'app_attributes\.py', '_update_modules', 'univention-management-console-server.*in run'], 50338),
	E('^ImportError: No module named s4', ['_update_modules'], 50338),
	E(r"^TypeError\:\ \_\_init\_\_\(\)\ got\ an\ unexpected\ keyword\ argument\ \'help\_text\'", ['_update_modules'], 50338),
	E('^ImportError: No module named directory', [r'app_attributes\.py'], 50338),
	E('^ImportError: No module named admindiary.client', [r'faillog\.py', 'File.*uvmm', r'create_portal_entries\.py'], 49866),
	E('^ImportError: No module named types', [r'import univention\.admin\.types'], 50381),
	E('^ImportError: No module named docker_upgrade', ['univention-app'], 50381),
	E('^ImportError: No module named docker_base', ['univention-app'], 50381),
	E('^ImportError: No module named service', ['univention-app'], 50381),
	E('^ImportError: No module named ldap_extension', ['get_action'], 50381),
	E('^AttributeError: __exit__', ['with Server'], 50583),
	E(r'^(univention\.admin\.uexceptions\.)?primaryGroupWithoutSamba: .*', ['primary_group_sync_to_ucs', 'sync_to_ucs'], 49881),
	E(r"^(OS|IO)Error: \[Errno 2\] .*: '/usr/lib/pymodules/python2.7/univention/admin/syntax.d/.*", ['import_syntax_files']),  # package upgrade before dh-python  # Bug #52958
	E(r"^(OS|IO)Error: \[Errno 2\] .*: '/usr/lib/pymodules/python2.7/univention/admin/hooks.d/.*", ['import_hook_files']),  # package upgrade before dh-python  # Bug #52958
	E(r'^(univention\.admin\.uexceptions\.)?(insufficientInformation|noSuperordinate): No superordinate object given', ['sync_to_ucs'], 49880),
	E("^AttributeError: type object 'object' has no attribute 'identify'", [r'faillog\.py']),
	E(r"FileNotFoundError: \[Errno 2\] No such file or directory: '/var/cache/univention-appcenter/.*\.logo'", ['File "<stdin>"']),  # 55_app_modproxy
	E('^IndexError: list index out of range', ['_read_from_ldap', 'get_user_groups'], (46932, 48943)),
	E(r"AttributeError\: \'NoneType\' object has no attribute \'searchDn\'", ['get_user_groups'], 48943),
	E("^subprocess.CalledProcessError: Command.*univention-directory-manager.*settings/portal_entry.*(create|remove).*univentionblog.*", [r'license_uuid\.py'], 45787),
	E("^KeyError: 'gidNumber'", ['_ldap_pre_remove'], 51669),
	E(r'^(BrokenPipeError|IOError): \[Errno 32\] Broken pipe', ['process_output'], 32532),
	E(r'^(ldap\.)?NOT_ALLOWED_ON_NONLEAF: .*subtree_delete:.*', ['s4_zone_delete'], (43722, 47343)),
	E('^NoObject: No object found at DN .*', ['univention-portal-server.*in refresh']),
	E(r"^OSError\: \[Errno 2\].*\/var\/run\/univention-management-console\/.*\.socket"),
	E(r'ldapError\:\ Type\ or\ value\ exists\:\ univentionPortalEntryLink\:\ value\ \#0\ provided\ more\ than\ once', None, 51808),
	E(r"noLock\: The attribute \'sid\' could not get locked\.", ['getMachineSid', '__generate_group_sid'], 44294),
	E(r'^ImportError\: No module named debhelper', [r'univention\/config_registry\/handler\.py'], 51815),
	E(r'^NO\_SUCH\_OBJECT\:.*users.*', ['password_sync_s4_to_ucs'], 50279),
	E(re.escape("Exception: Modifying blog entry failed: 1: E: Daemon died."), [], 45787),
	E(r'pg.InternalError: FATAL:\s*PAM-Authentifizierung für Benutzer ».*$« fehlgeschlagen', ['univention-pkgdb-scan'], 50937),
	E('pg.InternalError: FATAL:.*kein pg_hba.conf-Eintrag für Host', ['univention-pkgdb-scan'], 52790),
	E('pg.InternalError: FATAL:.*Datenbank .*pkgdb.* existiert nicht', ['univention-pkgdb-scan'], 52791),
	E('pg.InternalError: could not connect to server: No such file or directory', ['univention-pkgdb-scan'], 52795),
	E("TypeError: 'NoneType' object has no attribute '__getitem__'", ['add_primary_group_to_addlist'], 47440),
	E("TypeError: argument of type 'NoneType' is not iterable", ['disable_user_from_ucs', 'primary_group_sync_from_ucs'], (52788, 51809)),
	E(r"FileNotFoundError\: \[Errno 2\] No such file or directory\: \'\/etc\/machine\.secret\'", [r'bind\.py.*_ldap_auth_string'], 52789),
	E('dbm.error: db type could not be determined', ['univention-management-console-web-server'], 52764),
	E('at least one delete handler failed', ['_add_all_shares_below_this_container_to_dn_list', 'cleanup_python_moduledir'], 43171),
	E('ldap.NO_SUCH_OBJECT', ['_add_all_shares_below_this_container_to_dn_list'], 43171),
	E(re.escape('LISTENER    ( PROCESS ) : updating') + '.*command a', ['cleanup_python_moduledir']),  # ...
	E('ldap.ALREADY_EXISTS.*as it is still the primaryGroupID', ['in sync_from_ucs'], 53278),
	E('ldap.ALREADY_EXISTS.*already set via primaryGroupID', ['in sync_from_ucs'], 53278),
	E('ldap.NOT_ALLOWED_ON_NONLEAF:.*Unable to delete a non-leaf node .*it has .* child', ['in delete_in_s4'], 53278),
	E('univention.admin.uexceptions.valueError: The domain part of the primary mail address is not in list of configured mail domains:', ['in sync_to_ucs'], 53277),
	E(r"subprocess.CalledProcessError: Command '\('rndc', 'reconfig'\)' returned non-zero exit status 1", ['univention-fix-ucr-dns'], 53332),
	E(r"ldap.NO_SUCH_OBJECT: .*objectclass: Cannot add cn=(user|machine),cn=\{[0-9a-f-]+\},cn=policies,cn=system,DC=.*parent does not exist", ['in sync_from_ucs'], 53334),
	E("TypeError: 'NoneType' object is not subscriptable", ['primary_group_sync_to_ucs', 'add_primary_group_to_addlist'], 53276),
	E("CONSTRAINT_VIOLATION: .*Failed to re-index objectSid in .*unique index violation on objectSid", ['sync_from_ucs'], (53720, 53752)),
	E('ldap.REFERRAL:.*', ['uldap.py'], 53721),
	E('INSUFFICIENT_ACCESS:.*', ['in password_sync_s4_to_ucs'], 53721),
	E("ModuleNotFoundError: No module named 'univention.config_registry'", ['/usr/sbin/univention-config-registry'], 53765),
	E("AttributeError: module 'univention.admin.syntax' has no attribute 'UMCMessageCatalogFilename_and_GNUMessageCatalog'", ['_unregister_app', 'import_hook_files', 'pupilgroups.py'], 53754),
	E('univention.admin.uexceptions.noObject: uid=.*', ['connector/ad/.*set_userPrincipalName_from_ucr'], 53769),
	E('ldap.TYPE_OR_VALUE_EXISTS:.*SINGLE-VALUE attribute description.*specified more than once', ['sync_from_ucs'], 52801),
	E('univention.admin.uexceptions.wrongObjectType: relativeDomainName=.* is not recognized as dns/txt_record.', ['ucs_txt_record_create'], 53425),
	# Tracebacks caused by specific UCS@school bugs:
	E(r"_ldb.LdbError: \(1, 'LDAP client internal error: NT_STATUS_INVALID_PARAMETER'\)", ['univention-samba4-site-tool.py'], 54592),
)


def test_appcenter():
	fd = io.StringIO("""Match appcenter.log
 17954 packages                         21-02-14 04:25:09 [ WARNING]: Traceback (most recent call last):
 17954 packages                         21-02-14 04:25:09 [ WARNING]:   File "/usr/sbin/univention-pkgdb-scan", line 37, in <module>
 17954 packages                         21-02-14 04:25:09 [ WARNING]:     univention.pkgdb.main()
 17954 packages                         21-02-14 04:25:09 [ WARNING]:   File "/usr/lib/python2.7/dist-packages/pgdb.py", line 1619, in connect
 17954 packages                         21-02-14 04:25:09 [ WARNING]:     cnx = _connect(dbname, dbhost, dbport, dbopt, dbuser, dbpasswd)
 17954 packages                         21-02-14 04:25:09 [ WARNING]: Exception: foo
""")  # noqa: E101
	fd.name = '/var/log/univention/appcenter.log'
	out = io.StringIO('w')
	assert not main([fd], out=out)
	assert '''Traceback (most recent call last):
  File "/usr/sbin/univention-pkgdb-scan", line 37, in <module>
    univention.pkgdb.main()
  File "/usr/lib/python2.7/dist-packages/pgdb.py", line 1619, in connect
    cnx = _connect(dbname, dbhost, dbport, dbopt, dbuser, dbpasswd)
Exception: foo''' in out.getvalue(), out.getvalue()  # noqa: E101


def test_broken_setup():
	fd = io.StringIO("""Match broken setup.log traceback:
Traceback (most recent call last):
File "<stdin>", line 8, in <module>
File "xyz", line 8, in bar
foo = bar
Exception: foo
bar""")
	out = io.StringIO('w')
	assert not main([fd], out=out)
	assert """Traceback (most recent call last):
  File "<stdin>", line 8, in <module>
  File "xyz", line 8, in bar
    foo = bar
Exception: foo""" in out.getvalue(), out.getvalue()  # noqa: E101


def test_journald_indented():
	fd = io.StringIO("""Match indented journald format
    Traceback (most recent call last):
      File "<stdin>", line 8, in <module>
      File "xyz", line 8, in bar
        foo = bar
    Exception: foo
bar""")  # noqa: E101
	out = io.StringIO('w')
	assert not main([fd], out=out)
	assert """Traceback (most recent call last):
  File "<stdin>", line 8, in <module>
  File "xyz", line 8, in bar
    foo = bar
Exception: foo""" in out.getvalue(), out.getvalue()  # noqa: E101


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--ignore-exception', '-i', action='append', type=E, default=[E('^$')])
	parser.add_argument('-d', '--default-exceptions', action='store_true')
	parser.add_argument('files', type=argparse.FileType('r'), nargs='+')
	args = parser.parse_args()
	ignore_exceptions = COMMON_EXCEPTIONS if args.default_exceptions else args.ignore_exception
	sys.exit(int(not main(args.files, ignore_exceptions=ignore_exceptions)))
