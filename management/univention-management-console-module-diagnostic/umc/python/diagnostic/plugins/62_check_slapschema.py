#!/usr/bin/python3
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Warning

_ = Translation('univention-management-console-module-diagnostic').translate

title = _('LDAP schema files are missing')
description = '\n'.join([
	_('The following LDAP schema definitions are missing:\n'),
])
att_missing = _('The schema definition for attribute {0} is missing.\n')


def reduce_errors(list_errors):
	error_info = []
	for error in list_errors:
		error_split = error.split()
		error_code = [word for word in error_split if word.isupper()]
		error_info.append(error_code)
	# print([[word for word in error.split() if word.isupper()] for error in list_errors])
	return error_info


def run(_umc_instance):
	process = Popen(['slapschema'], stdout=PIPE, stderr=PIPE,
	                env={'LANG': 'C'}, shell=True)
	stdout, stderr = process.communicate()
	stderr = stderr.decode('UTF-8', 'replace')

	# Check if there was an error
	if stderr:
		# Filter UNKNOWN error message
		error_list = stderr.splitlines()
		error_id = reduce_errors(error_list)
		# Raise Warning with all attribute missing a schema
		tmp_desc = description

		for error in error_id:
			tmp_desc = tmp_desc + "".join(att_missing.format(error[1]))

		raise Warning(tmp_desc)


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main

	main()
