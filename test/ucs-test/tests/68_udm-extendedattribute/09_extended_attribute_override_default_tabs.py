#!/usr/share/ucs-test/runner pytest-3
## desc: Override default tab with settings/extended_attribute
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


from __future__ import print_function
import subprocess
import univention.testing.strings as uts
import univention.testing.utils as utils
import pytest


class Test_UDMExtension(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_override_default_tabs(self, udm):
		"""Override default tab with settings/extended_attribute"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'tabName': 'Certificate',
			'overwriteTab': '1'
		}

		udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		module_help_text = subprocess.Popen([udm.PATH_UDM_CLI_CLIENT, properties['module']], stdout=subprocess.PIPE).communicate()[0].decode('UTF-8').splitlines()

		for i in range(0, len(module_help_text)):
			if module_help_text[i] == '  %s:' % properties['tabName']:
				assert properties['CLIName'] in module_help_text[i + 1], 'Could not find attribute CLI name under tab'
				try:
					assert module_help_text[i + 2].endswith(':'), ' '.join(['-->', module_help_text[i + 2], '\nTab not overriden'])
				except IndexError:
					# no more help, tab is overwritten
					pass
				return
		pytest.fail('Tab not found')
