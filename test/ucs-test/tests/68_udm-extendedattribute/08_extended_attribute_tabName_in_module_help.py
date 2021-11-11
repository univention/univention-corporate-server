#!/usr/share/ucs-test/runner pytest-3
## desc: Find settings/extended_attribute tabName in module help
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import subprocess
import univention.testing.strings as uts
import univention.testing.utils as utils
import pytest


class Test_UDMExtension(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_tabName_in_module_help(self, udm):
		"""Find settings/extended_attribute tabName in module help"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'tabName': uts.random_name()
		}

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		module_help_text = subprocess.Popen([udm.PATH_UDM_CLI_CLIENT, properties['module']], stdout=subprocess.PIPE).communicate()[0].decode('UTF-8')
		assert properties['tabName'] in module_help_text, 'Could not find tab name of created settings/extended_attribute in module help'
