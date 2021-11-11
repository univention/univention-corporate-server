#!/usr/share/ucs-test/runner pytest-3
## desc: settings/extended_attribute with attribute hidden in UMC
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools
##   - univention-management-console-module-udm
## bugs: [43373]

import univention.testing.strings as uts
from univention.testing.umc import Client
from univention.testing import utils
import pytest


def flatten(layout):
	result = set()

	def _parse(x):
		for y in x:
			if isinstance(y, list):
				_parse(y)
			elif isinstance(y, dict):
				_parse(y.get('layout', []))
			elif isinstance(y, str):
				result.add(y)
			else:
				raise TypeError(y)
	_parse(layout)
	return result


class Test_UDMExtension(object):
	@pytest.mark.skipif(not utils.package_installed('univention-management-console-module-udm'), reason='Missing software: univention-management-console-module-udm')
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('dangerous')
	def test_extended_attribute_hide_field(self, udm):
		"""settings/extended_attribute with attribute hidden in UMC"""
		# bugs: [43373]
		for property in ('username', 'password'):
			properties = {
				'name': uts.random_name(),
				'shortDescription': uts.random_string(),
				'CLIName': property,
				'module': 'users/user',
				'objectClass': 'person',
				'ldapMapping': 'uid',
				'disableUDMWeb': '1',
			}
			extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)
			client = Client.get_test_connection()
			layout = flatten(client.umc_command('udm/layout', [{"objectType": "users/user", "objectDN": None}], 'users/user').result)

			assert property not in layout, '%s is part of %r' % (property, layout,)
