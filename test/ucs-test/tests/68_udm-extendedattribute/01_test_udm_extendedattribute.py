#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Create settings/extended_attribute
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

from __future__ import print_function

import subprocess
import os

import pytest

from univention.config_registry import ConfigRegistry
from univention.testing import utils as testing_utils
from univention.testing.umc import Client
import univention.testing.strings as uts
import univention.testing.utils as utils
import univention.testing.udm as udm_test
import univention.testing.ucr as ucr_test


@pytest.fixture
def properties():
	return {
		'name': uts.random_name(),
		'shortDescription': uts.random_string(),
		'CLIName': uts.random_name(),
		'module': 'users/user',
		'objectClass': 'univentionFreeAttributes',
		'ldapMapping': 'univentionFreeAttribute15'
	}


@pytest.fixture
def hook_name():
	return uts.random_name()


@pytest.fixture
def cleanup(hook_name):
	yield
	os.remove('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name)
	os.remove('/tmp/%s_executed' % hook_name)


@pytest.fixture
def acc(fn_hook):
	exit_cmd = ['/bin/rm', '-f', fn_hook]
	with utils.AutoCallCommand(exit_cmd=exit_cmd) as acc_:
		yield acc_


@pytest.fixture
def fn_hook():
	return '/usr/lib/python3/dist-packages/univention/admin/hooks.d/{}.py'.format(hook_name)


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
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_creation(self, udm, properties):
		"""Create settings/extended_attribute"""

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		utils.verify_ldap_object(extended_attribute, {
			'univentionUDMPropertyShortDescription': [properties['shortDescription']],
			'univentionUDMPropertyModule': [properties['module']],
			'univentionUDMPropertyLdapMapping': [properties['ldapMapping']],
			'univentionUDMPropertyCLIName': [properties['CLIName']],
			'univentionUDMPropertyObjectClass': [properties['objectClass']]
		})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_removal(self, udm, properties):
		"""Remove settings/extended_attribute"""

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		udm.remove_object('settings/extended_attribute', dn=extended_attribute)
		utils.verify_ldap_object(extended_attribute, should_exist=False)

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_singlevalue_set_during_object_creation(self, udm, properties):
		"""Set settings/extended_attribute value during object creation"""

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		# create user object with extended attribute set
		extended_attribute_value = uts.random_string()
		user = udm.create_user(**{properties['CLIName']: extended_attribute_value})[0]
		utils.verify_ldap_object(user, {properties['ldapMapping']: [extended_attribute_value]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_singlevalue_set_during_object_creation_after_removal(self, udm, properties):
		"""After an singlevalue settings/extended_attribute has been removed, try to still set value for it during object creation"""

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)
		udm.remove_object('settings/extended_attribute', dn=extended_attribute)

		# create user object and set extended attribute
		extended_attribute_value = uts.random_string()
		user = udm.create_user({properties['CLIName']: extended_attribute_value})[0]
		utils.verify_ldap_object(user, {properties['ldapMapping']: []})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_multivalue_append_during_object_creation(self, udm):
		"""Append multivalue settings/extended_attribute values to object"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'multivalue': '1'
		}

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		# create user object and set extended attribute
		extended_attribute_values = [uts.random_string(), uts.random_string()]
		user = udm.create_user(append={properties['CLIName']: extended_attribute_values})[0]
		utils.verify_ldap_object(user, {properties['ldapMapping']: extended_attribute_values})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_multivalue_append_during_object_creation_after_removal(self, udm):
		"""After an multivalue settings/extended_attribute has been removed, try to still append values for it to object"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'multivalue': '1'
		}

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)
		udm.remove_object('settings/extended_attribute', dn=extended_attribute)

		# create user object and set extended attribute
		extended_attribute_values = [uts.random_string(), uts.random_string()]
		user = udm.create_user(append={properties['CLIName']: extended_attribute_values})[0]
		utils.verify_ldap_object(user, {properties['ldapMapping']: []})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_creation_with_all_attributes(self, udm):
		"""Create settings/extended_attribute with all attributes set"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'longDescription': uts.random_string(),
			'translationShortDescription': 'de_DE %s' % uts.random_string(),
			'translationLongDescription': 'de_DE %s' % uts.random_string(),
			'translationTabName': 'de_DE %s' % uts.random_string(),
			'syntax': 'string',
			'hook': uts.random_string(),
			'multivalue': '1',
			'default': uts.random_string(),
			'disableUDMWeb': '1',
			'tabName': uts.random_string(),
			'tabPosition': '1',
			'groupName': uts.random_string(),
			'groupPosition': '1',
			'tabAdvanced': '1',
			'overwriteTab': '1',
			'fullWidth': '1',
			'mayChange': '1',
			'notEditable': '1',
			'valueRequired': '1',
			'deleteObjectClass': '1',
			'version': uts.random_string(),
			'doNotSearch': '1',
			'set': {'options': uts.random_string()}  # "options" property of settings/extended_attribute collides with already existing keyword argument "options"
		}

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		utils.verify_ldap_object(extended_attribute, {
			'univentionUDMPropertyShortDescription': [properties['shortDescription']],
			'univentionUDMPropertyModule': [properties['module']],
			'univentionUDMPropertyLdapMapping': [properties['ldapMapping']],
			'univentionUDMPropertyCLIName': [properties['CLIName']],
			'univentionUDMPropertyObjectClass': [properties['objectClass']],
			'univentionUDMPropertyLongDescription': [properties['longDescription']],
			'univentionUDMPropertySyntax': [properties['syntax']],
			'univentionUDMPropertyHook': [properties['hook']],
			'univentionUDMPropertyMultivalue': [properties['multivalue']],
			'univentionUDMPropertyDefault': [properties['default']],
			'univentionUDMPropertyLayoutDisable': [properties['disableUDMWeb']],
			'univentionUDMPropertyLayoutTabName': [properties['tabName']],
			'univentionUDMPropertyLayoutPosition': [properties['tabPosition']],
			'univentionUDMPropertyLayoutGroupName': [properties['groupName']],
			'univentionUDMPropertyLayoutGroupPosition': [properties['groupPosition']],
			'univentionUDMPropertyLayoutTabAdvanced': [properties['tabAdvanced']],
			'univentionUDMPropertyLayoutOverwriteTab': [properties['overwriteTab']],
			'univentionUDMPropertyLayoutFullWidth': [properties['fullWidth']],
			'univentionUDMPropertyValueMayChange': [properties['mayChange']],
			'univentionUDMPropertyValueNotEditable': [properties['notEditable']],
			'univentionUDMPropertyDeleteObjectClass': [properties['deleteObjectClass']],
			'univentionUDMPropertyVersion': [properties['version']],
			'univentionUDMPropertyOptions': [properties['set']['options']],
			'univentionUDMPropertyDoNotSearch': [properties['doNotSearch']]
		})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extented_attribute_set_during_object_modification(self, udm, properties):
		"""Set settings/extended_attribute value during object creation"""

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		user = udm.create_user()[0]
		extended_attribute_value = uts.random_string()
		udm.modify_object('users/user', dn=user, **{properties['CLIName']: extended_attribute_value})
		utils.verify_ldap_object(user, {properties['ldapMapping']: [extended_attribute_value]})

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

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_attribute_positioning_in_custom_tab(self, udm):
		"""Positioning in custom tabs"""
		tab = uts.random_name()
		extended_attributes = {}

		for i in range(4, 0, -1):
			properties = {
				'name': uts.random_name(),
				'shortDescription': uts.random_string(),
				'CLIName': uts.random_name(),
				'module': 'users/user',
				'objectClass': 'univentionFreeAttributes',
				'ldapMapping': 'univentionFreeAttribute%s' % i,
				'tabPosition': str(i),
				'tabName': tab
			}
			udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)
			extended_attributes[properties['CLIName']] = i

		module_help_text = subprocess.Popen([udm.PATH_UDM_CLI_CLIENT, properties['module']], stdout=subprocess.PIPE).communicate()[0].decode('UTF-8').splitlines()
		tab_position = 1
		for line in module_help_text:
			try:
				cli_name = line.strip().split()[0]
			except Exception:
				continue

			if cli_name in extended_attributes:
				assert extended_attributes[cli_name] == tab_position, 'Detected mistake in appearance order of attribute CLI names under tab'
				tab_position += 1

		assert tab_position >= 4, 'Not all created attributes found in module'

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_default_apply_singlevalue(self, udm):
		"""Default value gets applied for single value settings/extended_attribute when a value is not explicitly given"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'default': uts.random_string()
		}

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		user = udm.create_user()[0]
		utils.verify_ldap_object(user, {properties['ldapMapping']: [properties['default']]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_default_apply_multivalue(self, udm):
		"""Default value gets applied for multi value settings/extended_attribute when a value is not explicitly given"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'multivalue': '1',
			'default': uts.random_string()
		}

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		user = udm.create_user()[0]
		utils.verify_ldap_object(user, {properties['ldapMapping']: [properties['default']]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_default_override_singlevalue(self, udm):
		"""Default value of single value settings/extended_attribute is overridden by explicitly given value"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'default': uts.random_string()
		}

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		extended_attribute_value = uts.random_string()
		user = udm.create_user(**{properties['CLIName']: extended_attribute_value})[0]
		utils.verify_ldap_object(user, {properties['ldapMapping']: [extended_attribute_value]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_default_override_multivalue(self, udm):
		"""Default value of multi value settings/extended_attribute is overridden by explicitly given values"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'multivalue': '1',
			'default': uts.random_string()
		}

		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		extended_attribute_value = uts.random_string()
		user = udm.create_user(**{properties['CLIName']: extended_attribute_value})[0]
		utils.verify_ldap_object(user, {properties['ldapMapping']: [extended_attribute_value]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_mayChange_enforcement(self, udm):
		"""Check that mayChange=0 is enforced for settings/extended_attribute"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'mayChange': '0'
		}

		udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		user = udm.create_user(**{properties['CLIName']: uts.random_string()})[0]
		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed, message='UDM did not report an error while trying to modify a settings/extended_attribute value which may not change'):
			udm.modify_object('users/user', dn=user, **{properties['CLIName']: uts.random_string()})

	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_remove_required_singlevalue_1(self, udm):
		"""Check that required=True is enforced for singlevalue extended attributes"""
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_string(),
			shortDescription='Test short description',
			CLIName='univentionUCSTestAttribute',
			module='groups/group',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			valueRequired='1'
		)

		# try creating an udm object without the just created extended attribute given (expected to fail)
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed, message='UDM did not report an error while trying to create an object a required single value extended attribute was not given'):
			udm.create_group()

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_remove_required_singlevalue_2(self, udm):
		"""Remove required settings/extended_attribute single value"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'groups/group',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'valueRequired': '1'
		}

		udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		extended_attribute_value = uts.random_string()
		group = udm.create_group(**{properties['CLIName']: extended_attribute_value})[0]

		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed, message='UDM did not report an error while trying to remove a required settings/extended_attribute single value from object'):
			udm.modify_object('groups/group', dn=group, remove={properties['CLIName']: [extended_attribute_value]})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_remove_required_multivalue(self, udm):
		"""Remove required settings/extended_attribute multi value"""
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'groups/group',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'valueRequired': '1',
			'multivalue': '1'
		}

		udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		extended_attribute_values = [uts.random_string(), uts.random_string()]
		group = udm.create_group(append={properties['CLIName']: extended_attribute_values})[0]

		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):  # UDM did not report an error while trying to remove a required settings/extended_attribute multi value from object
			udm.modify_object('groups/group', dn=group, remove={properties['CLIName']: extended_attribute_values})

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extented_attribute_required_enforcement_singlevalue(self, udm):
		"""Check that required=True is enforced for singlevalue extended attributes"""
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_string(),
			shortDescription='Test short description',
			CLIName='univentionUCSTestAttribute',
			module='groups/group',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			valueRequired='1'
		)

		# try creating an udm object without the just created extended attribute given (expected to fail)
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed, message='UDM did not report an error while trying to create an object even though a required single value extended attribute was not given'):
			udm.create_group()

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.xfail(reason='wrong version')
	def test_extended_attribute_required_enforcement_multivalue(self, udm):
		"""Check that required=True is enforced for multivalue extended attributes"""
		# bugs: [31302]
		# versions:
		#  3.1-1: skip
		#  3.2-0: fixed
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_string(),
			shortDescription='Test short description',
			CLIName='univentionUCSTestAttribute',
			module='groups/group',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			valueRequired='1',
			multivalue='1'
		)

		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed, message='UDM did not report an error while trying to create an object even though a required multivalue extended attribute was not given'):
			udm.create_group()

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.xfail(reason='wrong version')
	def test_extented_attribute_creation_with_default_value_not_allowed_by_syntax(self, udm):
		"""Create settings/extented_attribute with a value for it's default which is not valid for it's syntax value"""
		# versions:
		#   3.2-0: skip
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_object(
				'settings/extended_attribute',
				position=udm.UNIVENTION_CONTAINER,
				name=uts.random_name(),
				shortDescription=uts.random_string(),
				CLIName=uts.random_string(),
				module='users/user',
				objectClass='univentionFreeAttributes',
				ldapMapping='univentionFreeAttribute15',
				syntax='integer',
				default='notaninteger'
			)

	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extented_attribute_ldap_addlist_hook(self, udm, hook_name, cleanup):
		"""settings/extented_attribute LDAP addlist hook"""
		with open('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name, 'w') as hook_module:
			hook_module.write("""
import univention.admin
import univention.admin.modules
import univention.admin.hook
import univention.admin.handlers.users.user

class %s(univention.admin.hook.simpleHook):
	def hook_ldap_addlist(self, obj, al=[]):
		with open('/tmp/%s_executed', 'w') as fp:
			if not isinstance(obj, univention.admin.handlers.users.user.object):
				fp.write('LDAP addlist hook called with wrong object parameter (Type: %%s)' %% type(obj))
		return al + [('description', b'%s')]
""" % (hook_name, hook_name, hook_name))

		udm.stop_cli_server()
		cli_name = uts.random_string()
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_name(),
			shortDescription=uts.random_string(),
			CLIName=cli_name,
			module='users/user',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			hook=hook_name
		)

		user = udm.create_user(**{cli_name: uts.random_string()})[0]
		utils.verify_ldap_object(user, {'description': [hook_name]})

		with open('/tmp/%s_executed' % hook_name) as fp:
			fails = fp.read()
			assert not fails, fails

	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extented_attribute_ldap_pre_create_hook(self, udm, ucr, hook_name, cleanup):
		"""settings/extented_attribute LDAP pre create hook"""
		with open('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name, 'w') as hook_module:
			hook_module.write("""
import univention.admin
import univention.admin.modules
import univention.admin.hook
import univention.admin.handlers.users.user
import univention.testing.utils

class %s(univention.admin.hook.simpleHook):
	def hook_ldap_pre_create(self, module):
		with open('/tmp/%s_executed', 'w') as fp:
			if not isinstance(module, univention.admin.handlers.users.user.object):
				fp.write('LDAP pre create Hook called with wrong object parameter (Type: %%s)' %% type(module))

			univention.testing.utils.wait_for_replication()
			try:
				univention.testing.utils.verify_ldap_object('uid=%s,cn=users,%s', should_exist = False)
			except univention.testing.utils.LDAPUnexpectedObjectFound:
				fp.write('\\nObject had already been created when LDAP pre create hook was called')
""" % (hook_name, hook_name, hook_name, ucr['ldap/base']))

		udm.stop_cli_server()
		cli_name = uts.random_string()
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_name(),
			shortDescription=uts.random_string(),
			CLIName=cli_name,
			module='users/user',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			hook=hook_name
		)

		udm.create_user(**{cli_name: uts.random_string(), 'username': hook_name})[0]

		with open('/tmp/%s_executed' % hook_name) as fp:
			fails = fp.read()
			assert not fails, fails

	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extented_attribute_open_hook(self, udm, hook_name, cleanup):
		"""settings/extented_attribute open hook"""
		with open('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name, 'w') as hook_module:
			hook_module.write("""
import univention.admin
import univention.admin.modules
import univention.admin.hook
import univention.admin.handlers.users.user

class %s(univention.admin.hook.simpleHook):
	def hook_open(self, obj):
		with open('/tmp/%s_executed', 'a+') as fp:
			if not isinstance(obj, univention.admin.handlers.users.user.object):
				fp.write('Hook called with wrong object parameter (Type: %%s)' %% type(module))
""" % (hook_name, hook_name))

		udm.stop_cli_server()
		cli_name = uts.random_string()
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_name(),
			shortDescription=uts.random_string(),
			CLIName=cli_name,
			module='users/user',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			hook=hook_name
		)

		user = udm.create_user(**{cli_name: uts.random_string()})[0]
		udm.modify_object('users/user', dn=user, displayName=uts.random_name())

		with open('/tmp/%s_executed' % hook_name) as fp:
			fails = fp.read()
			assert not fails, fails

	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extented_attribute_ldap_post_create_hook(self, udm, ucr, hook_name, cleanup):
		"""settings/extented_attribute LDAP post create hook"""
		with open('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name, 'w') as hook_module:
			hook_module.write("""
import univention.admin
import univention.admin.modules
import univention.admin.hook
import univention.admin.handlers.users.user
import univention.testing.utils

class %s(univention.admin.hook.simpleHook):
	def hook_ldap_post_create(self, module):
		with open('/tmp/%s_executed', 'w') as fp:
			if not isinstance(module, univention.admin.handlers.users.user.object):
				fp.write('Hook called with wrong object parameter (Type: %%s)' %% type(module))

			univention.testing.utils.wait_for_replication()
			try:
				univention.testing.utils.verify_ldap_object('uid=%s,cn=users,%s')
			except univention.testing.utils.LDAPObjectNotFound:
				fp.write('\\nObject had not yet been created when LDAP post create hook was called')
""" % (hook_name, hook_name, hook_name, ucr['ldap/base']))

		udm.stop_cli_server()
		cli_name = uts.random_string()
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_name(),
			shortDescription=uts.random_string(),
			CLIName=cli_name,
			module='users/user',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			hook=hook_name
		)

		udm.create_user(**{cli_name: uts.random_string(), 'username': hook_name})[0]

		with open('/tmp/%s_executed' % hook_name) as fp:
			fails = fp.read()
			assert not fails, fails

	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extented_attribute_ldap_post_modify_hook(self, udm, ucr, hook_name, cleanup):
		"""settings/extented_attribute LDAP post modify hook"""
		with open('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name, 'w') as hook_module:
			hook_module.write("""
import univention.admin
import univention.admin.modules
import univention.admin.hook
import univention.admin.handlers.users.user
import univention.testing.utils

class %s(univention.admin.hook.simpleHook):
	def hook_ldap_post_modify(self, module):
		with open('/tmp/%s_executed', 'w') as fp:
			if not isinstance(module, univention.admin.handlers.users.user.object):
				fp.write('LDAP post modify hook called with wrong object parameter (Type: %%s)' %% type(module))

			univention.testing.utils.wait_for_replication()
			try:
				univention.testing.utils.verify_ldap_object('uid=%s,cn=users,%s', {'description': [b'%s']}, retry_count=0)
			except univention.testing.utils.LDAPObjectValueMissing:
				fp.write('\\nObject was not yet modified when LDAP post modify hook was called')
""" % (hook_name, hook_name, hook_name, ucr['ldap/base'], hook_name))

		udm.stop_cli_server()
		cli_name = uts.random_string()
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_name(),
			shortDescription=uts.random_string(),
			CLIName=cli_name,
			module='users/user',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			hook=hook_name
		)

		user = udm.create_user(**{cli_name: uts.random_string(), 'username': hook_name})[0]
		udm.modify_object('users/user', dn=user, description=hook_name)

		with open('/tmp/%s_executed' % hook_name) as fp:
			fails = fp.read()
			assert not fails, fails

	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extented_attribute_ldap_modlist_hook(self, udm, hook_name, cleanup):
		"""settings/extented_attribute LDAP modlist hook"""
		with open('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name, 'w') as hook_module:
			hook_module.write("""
import univention.admin
import univention.admin.modules
import univention.admin.hook
import univention.admin.handlers.users.user
import univention.testing.utils

class %s(univention.admin.hook.simpleHook):
	def hook_ldap_modlist(self, module, ml=[]):
		with open('/tmp/%s_executed', 'w') as fp:
			if not isinstance(module, univention.admin.handlers.users.user.object):
				fp.write('LDAP modlist hook called with wrong object parameter (Type: %%s)' %% type(module))
		return ml + [('description', module.get('description', b''), b'%s')]
""" % (hook_name, hook_name, hook_name))

		udm.stop_cli_server()
		cli_name = uts.random_string()

		user = udm.create_user(**{cli_name: uts.random_string()})[0]
		utils.verify_ldap_object(user, {'description': []})

		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_name(),
			shortDescription=uts.random_string(),
			CLIName=cli_name,
			module='users/user',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			hook=hook_name
		)

		udm.modify_object('users/user', dn=user, displayName=uts.random_name())
		utils.verify_ldap_object(user, {'description': [hook_name]})

		with open('/tmp/%s_executed' % hook_name) as fp:
			fails = fp.read()
			assert not fails, fails

	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extented_attribute_ldap_pre_modify_hook(self, udm, ucr, hook_name, cleanup):
		"""settings/extented_attribute LDAP pre modify hook"""
		with open('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name, 'w') as hook_module:
			hook_module.write("""
import univention.admin
import univention.admin.modules
import univention.admin.hook
import univention.admin.handlers.users.user
import univention.testing.utils

class %s(univention.admin.hook.simpleHook):
	def hook_ldap_pre_modify(self, module):
		with open('/tmp/%s_executed', 'w') as fp:
			if not isinstance(module, univention.admin.handlers.users.user.object):
				fp.write('LDAP pre modify hook called with wrong object parameter (Type: %%s)' %% type(module))

			univention.testing.utils.wait_for_replication()
			try:
				univention.testing.utils.verify_ldap_object('uid=%s,cn=users,%s', {'description': []}, retry_count=0)
			except univention.testing.utils.LDAPObjectUnexpectedValue:
				fp.write('\\nObject had already been modified when LDAP pre modify hook was called')
""" % (hook_name, hook_name, hook_name, ucr['ldap/base']))

		udm.stop_cli_server()
		cli_name = uts.random_string()
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_name(),
			shortDescription=uts.random_string(),
			CLIName=cli_name,
			module='users/user',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			hook=hook_name
		)

		user = udm.create_user(**{cli_name: uts.random_string(), 'username': hook_name})[0]
		udm.modify_object('users/user', dn=user, description=uts.random_name())

		with open('/tmp/%s_executed' % hook_name) as fp:
			fails = fp.read()
			assert not fails, fails

	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extented_attribute_ldap_pre_remove_hook(self, udm, ucr, hook_name, cleanup):
		"""settings/extented_attribute LDAP pre remove hook"""
		with open('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name, 'w') as hook_module:
			hook_module.write("""
import univention.admin
import univention.admin.modules
import univention.admin.hook
import univention.admin.handlers.users.user
import univention.testing.utils

class %s(univention.admin.hook.simpleHook):
	def hook_ldap_pre_remove(self, module):
		with open('/tmp/%s_executed', 'w') as fp:
			if not isinstance(module, univention.admin.handlers.users.user.object):
				fp.write('LDAP pre remove hook called with wrong object parameter (Type: %%s)' %% type(module))

			univention.testing.utils.wait_for_replication()
			try:
				univention.testing.utils.verify_ldap_object('uid=%s,cn=users,%s')
			except univention.testing.utils.LDAPObjectNotFound:
				fp.write('\\nObject had already been removed when LDAP pre remove hook was called')
""" % (hook_name, hook_name, hook_name, ucr['ldap/base']))

		udm.stop_cli_server()
		cli_name = uts.random_string()
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_name(),
			shortDescription=uts.random_string(),
			CLIName=cli_name,
			module='users/user',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			hook=hook_name
		)

		user = udm.create_user(**{cli_name: uts.random_string(), 'username': hook_name})[0]
		udm.remove_object('users/user', dn=user)

		with open('/tmp/%s_executed' % hook_name) as fp:
			fails = fp.read()
			assert not fails, fails

	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extented_attribute_ldap_post_remove_hook(self, udm, ucr, hook_name, cleanup):
		"""settings/extented_attribute LDAP post remove hook"""
		with open('/usr/lib/python3/dist-packages/univention/admin/hooks.d/%s.py' % hook_name, 'w') as hook_module:
			hook_module.write("""
import univention.admin
import univention.admin.modules
import univention.admin.hook
import univention.admin.handlers.users.user
import univention.testing.utils

class %s(univention.admin.hook.simpleHook):
	def hook_ldap_post_remove(self, module):
		with open('/tmp/%s_executed', 'w') as fp:
			if not isinstance(module, univention.admin.handlers.users.user.object):
				fp.write('LDAP post remove hook call with wrong object parameter (Type: %%s)' %% type(module))

			univention.testing.utils.wait_for_replication()
			try:
				univention.testing.utils.verify_ldap_object('uid=%s,cn=users,%s', should_exist=False)
			except univention.testing.utils.LDAPUnexpectedObjectFound:
				fp.write('\\nObject had not yet been removed when LDAP post remove hook was called')
""" % (hook_name, hook_name, hook_name, ucr['ldap/base']))

		udm.stop_cli_server()
		cli_name = uts.random_string()
		udm.create_object(
			'settings/extended_attribute',
			position=udm.UNIVENTION_CONTAINER,
			name=uts.random_name(),
			shortDescription=uts.random_string(),
			CLIName=cli_name,
			module='users/user',
			objectClass='univentionFreeAttributes',
			ldapMapping='univentionFreeAttribute15',
			hook=hook_name
		)

		user = udm.create_user(**{cli_name: uts.random_string(), 'username': hook_name})[0]
		udm.remove_object('users/user', dn=user)

		with open('/tmp/%s_executed' % hook_name) as fp:
			fails = fp.read()
			assert not fails, fails

	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_set_user_required_field_without_default(self, udm, ucr):
		"""settings/extented_attribute"""
		kwargs = dict(name='test', ldapMapping='foo', objectClass='bar', shortDescription='test', valueRequired='1', CLIName='test', module=['users/user'])
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_object('settings/extended_attribute', position='cn=custom attributes, cn=univention, %s' % ucr['ldap/base'], **kwargs)
		kwargs['default'] = 'foo'
		udm.create_object('settings/extended_attribute', position='cn=custom attributes, cn=univention, %s' % ucr['ldap/base'], **kwargs)

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_removal_oc(self, udm):
		"""Test settings/extended_attribute with deleteObjectClass=1"""
		# bugs: [41207]
		ea_name = uts.random_name()
		ea_properties = {
			'name': ea_name,
			'shortDescription': ea_name,
			'CLIName': ea_name,
			'module': 'groups/group',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15',
			'deleteObjectClass': '1',
			'mayChange': '1',
		}
		ea = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **ea_properties)
		udm.stop_cli_server()

		ea_value = uts.random_string()
		group_dn, group_name = udm.create_group(**{ea_name: ea_value})
		utils.verify_ldap_object(group_dn, expected_attr={'objectClass': ['univentionFreeAttributes']}, strict=False)

		udm.modify_object('groups/group', dn=group_dn, set={ea_name: ''})
		with pytest.raises(utils.LDAPObjectValueMissing, message='objectClass was not removed from group %r @ %r' % (group_name, group_dn)):
			utils.verify_ldap_object(group_dn, expected_attr={'objectClass': ['univentionFreeAttributes']}, strict=False)

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_options_removal(self, udm):
		"""Test settings/extended_options removal"""
		# bugs: [25240,21608,41580]
		utils.stop_s4connector()
		eo_name = uts.random_name()
		eo_properties = {
			'name': eo_name,
			'shortDescription': eo_name,
			'module': 'groups/group',
			'objectClass': 'univentionFreeAttributes',
			'editable': '1',
		}
		eo = udm.create_object('settings/extended_options', position=udm.UNIVENTION_CONTAINER, **eo_properties)

		group_dn, group_name = udm.create_group(options=['posix', eo_name])
		utils.verify_ldap_object(group_dn, expected_attr={'objectClass': ['univentionFreeAttributes']}, strict=False)

		udm.modify_object('groups/group', dn=group_dn, options=['posix'])
		with pytest.raises(utils.LDAPObjectValueMissing, message='objectClass was not removed from group %r @ %r' % (group_name, group_dn)):
			utils.verify_ldap_object(group_dn, expected_attr={'objectClass': ['univentionFreeAttributes']}, strict=False, retry_count=0)
		utils.start_s4connector()

	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.xfail(reason='wrong version')
	def test_extended_attribute_boolean_syntax(self, udm):
		"""settings/extended_attribute with boolean syntax"""
		# versions:
		#  4.1-2: skip
		#  4.1-3: fixed
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'syntax': 'boolean',
			'mayChange': '1',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15'
		}
		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		userA = udm.create_user(**{properties['CLIName']: '0'})[0]
		userB = udm.create_user(**{properties['CLIName']: '1'})[0]
		utils.wait_for_connector_replication()
		utils.verify_ldap_object(userA, {properties['ldapMapping']: []})
		utils.verify_ldap_object(userB, {properties['ldapMapping']: ['1']})
		udm.modify_object('users/user', dn=userA, **{properties['CLIName']: '1'})
		udm.modify_object('users/user', dn=userB, **{properties['CLIName']: '0'})
		utils.verify_ldap_object(userA, {properties['ldapMapping']: ['1']})
		utils.verify_ldap_object(userB, {properties['ldapMapping']: []})

	@pytest.mark.skipif(not testing_utils.package_installed('univention-management-console-module-udm'), reason='Missing software: univention-management-console-module-udm')
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

	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_attributehook_value_mapping(self, udm, acc, hook_name, fn_hook):
		"""settings/extented_attribute LDAP modlist hook"""
		cli_name = uts.random_string()
		attr_name = 'univentionFreeAttribute15'
		with udm_test.UCSTestUDM() as udm:
			with open(fn_hook, 'w') as hook_module:
				hook_module.write("""
import univention.admin
import univention.admin.modules
import univention.admin.hook
import univention.admin.handlers.users.user
import univention.testing.utils

def mydebug(msg):
	univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, '40_extended_attribute_attributehook_value_mapping: {hook_name}: %s' % (msg,))

mydebug('TEST MODULE LOADED')

class {hook_name}(univention.admin.hook.AttributeHook):
	ldap_attribute_name = '{attr_name}'
	udm_attribute_name = '{cli_name}'

	def map_attribute_value_to_ldap(self, value):
		mydebug('map_attribute_value_to_ldap(%r)' % (value,))
		if value in (b'FALSE', b'yes'):
			return b'no'
		elif value in (b'TRUE', b'yes'):
			return b'yes'
		elif value in (b'', None):
			return b''
		else:
			# this is not great, but works reasonably well
			mydebug('map_attribute_value_to_ldap(%r) ==> found invalid value' % (value,))
			raise univention.admin.uexceptions.valueError('%s: LDAP Value may not be %r' % (self.ldap_attribute_name, value))

	def map_attribute_value_to_udm(self, value):
		mydebug('map_attribute_value_to_udm(%r)' % (value,))
		if value == 'yes':
			return 'TRUE'
		elif value == 'no':
			return 'FALSE'
		elif value in ('', None):
			return ''
		else:
			# this is not great, but works reasonably well
			mydebug('map_attribute_value_to_udm(%r) ==> found invalid value' % (value,))
			raise univention.admin.uexceptions.valueError('%s: UDM Value may not be %r' % (self.udm_attribute_name, value))
""".format(hook_name=hook_name, cli_name=cli_name, attr_name=attr_name))  # noqa: E101

			udm.create_object(
				'settings/extended_attribute',
				position=udm.UNIVENTION_CONTAINER,
				name=uts.random_name(),
				shortDescription=uts.random_string(),
				CLIName=cli_name,
				module='users/user',
				objectClass='univentionFreeAttributes',
				ldapMapping=attr_name,
				hook=hook_name,
				syntax='TrueFalseUpper',
				multivalue=0,
				valueRequired=0,
				mayChange=1,
			)
			udm.stop_cli_server()

			userA = udm.create_user(**{cli_name: 'TRUE'})[0]
			utils.verify_ldap_object(userA, {attr_name: [b'yes']})
			userB = udm.create_user(**{cli_name: 'FALSE'})[0]
			utils.verify_ldap_object(userB, {attr_name: [b'no']})
			with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
				userC = udm.create_user(**{cli_name: 'INVALID'})[0]

			udm.modify_object('users/user', dn=userB, **{cli_name: 'TRUE'})
			utils.verify_ldap_object(userB, {attr_name: [b'yes']})
			udm.modify_object('users/user', dn=userB, **{cli_name: 'FALSE'})
			utils.verify_ldap_object(userB, {attr_name: [b'no']})
			with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
				udm.modify_object('users/user', dn=userB, **{cli_name: 'not valid'})
