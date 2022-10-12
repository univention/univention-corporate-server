#!/usr/bin/python3
# -*- coding: utf-8 -*-

from subprocess import PIPE, STDOUT, Popen

from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Critical, ProblemFixed

_ = Translation('univention-management-console-module-diagnostic').translate

SCRIPT = '/usr/share/univention-directory-manager-tools/univention-migrate-users-to-ucs4.3'
title = _('User objects which are not migrated')
description = '\n'.join([
	_('With UCS 4.3 the LDAP format of user objects changed. After upgrading the Primary Directory Node all user objects are migrated into the new format.'),
	_('When a user object is created by a system which is not yet on UCS 4.3 it will have the old format. These user objects need to migrated again.'),
])
run_descr = ['Checks user objects exist which are not migrated by using %s --check' % (SCRIPT,)]


def run(_umc_instance):
	if ucr.get('server/role') != 'domaincontroller_master':
		return

	process = Popen([SCRIPT, '--check'], stderr=STDOUT, stdout=PIPE)
	stdout, stderr = process.communicate()
	stdout = stdout.decode('UTF-8', 'replace')
	if process.returncode:
		MODULE.error(description + stdout)
		raise Critical(description + stdout, buttons=[{
			'action': 'migrate_users',
			'label': _('Migrate user objects'),
		}])


def migrate_users(_umc_instance):
	process = Popen([SCRIPT], stderr=STDOUT, stdout=PIPE)
	stdout, stderr = process.communicate()
	stdout = stdout.decode('UTF-8', 'replace')
	if process.returncode:
		MODULE.error('Error running univention-migrate-users-to-ucs4.3:\n%s' % (stdout,))
		raise Critical(_('The migration failed: %s') % (stdout,))
	else:
		MODULE.process('Output of univention-migrate-users-to-ucs4.3:\n%s' % (stdout,))
	raise ProblemFixed(buttons=[])


actions = {
	'migrate_users': migrate_users,
}


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
