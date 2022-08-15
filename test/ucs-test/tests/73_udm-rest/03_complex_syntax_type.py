#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Check the type definition of a complex syntax in the OpenAPI schema
## tags: [udm,apptest,openapi]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-rest
## bugs: [53513, 50648]

import pytest
import base64
import bz2
import subprocess
import time
import requests
from requests.auth import HTTPBasicAuth

from univention.testing.udm_extensions import get_extension_filename, get_package_name, get_package_version
from univention.testing.strings import random_name, random_ucs_version, random_version
from univention.testing.utils import verify_ldap_object, wait_for_replication_and_postrun, UCSTestDomainAdminCredentials
from univention.testing.udm import UCSTestUDM


def get_openapi_schema():
	account = UCSTestDomainAdminCredentials()
	resp = requests.get("http://localhost/univention/udm/openapi.json", auth=HTTPBasicAuth(account.username, account.bindpw))
	resp.raise_for_status()
	return resp.json()


def restart_udmrest():
	subprocess.check_call(["systemctl", "restart", "univention-directory-manager-rest.service"])
	for i in range(10):
		try:
			get_openapi_schema()
		except requests.HTTPError as exc:
			if exc.response.status_code != 503:
				break
		else:
			break
		time.sleep(1)
	else:
		raise


def get_syntax_buffers():

	return {
		"UCSTESTComplexMultiValueKeyValueDict": '''
class UCSTESTComplexMultiValueKeyValueDict(complex):
	subsyntaxes = ((_('User'), UserMailAddress), (_('Access right'), IMAP_Right))
	subsyntax_key_value = True
''',
		"UCSTESTComplexMultiValueDict": '''
class UCSTESTComplexMultiValueDict(complex):
	subsyntaxes = [(_('Priority'), integer), (_('Mail server'), dnsHostname)]
	subsyntax_names = ('priority', 'mailserver',)
''',
		"UCSTESTComplexList": '''
class UCSTESTComplexList(complex):
	subsyntaxes = [('Type-string', string), ('Type-integer', integer)]
''',
	}


@pytest.fixture(scope="class", autouse=True)
def complex_syntax():

	extension_type = 'syntax'
	extension_buffers = get_syntax_buffers()

	package_name = get_package_name()
	package_version = get_package_version()
	app_id = '%s-%s' % (random_name(), random_version())
	version_start = random_ucs_version(max_major=2)
	version_end = random_ucs_version(min_major=5)

	with UCSTestUDM() as udm:
		udm.create_object(
			'container/cn',
			name='udm_%s' % (extension_type,),
			position=udm.UNIVENTION_CONTAINER,
			ignore_exists=True
		)
		for i, (extension_name, extension_buffer) in enumerate(extension_buffers.items()):
			extension_filename = get_extension_filename(extension_type, extension_name)
			extension_dn = udm.create_object(
				'settings/udm_%s' % extension_type,
				name=extension_name,
				data=base64.b64encode(bz2.compress(extension_buffer.encode("UTF-8"))).decode("ASCII"),
				filename=extension_filename,
				packageversion=package_version,
				appidentifier=app_id,
				package=package_name,
				ucsversionstart=version_start,
				ucsversionend=version_end,
				active='FALSE',
				position='cn=udm_%s,%s' % (extension_type, udm.UNIVENTION_CONTAINER)
			)

			udm.create_object(
				'settings/extended_attribute',
				position='cn=custom attributes,%s' % udm.UNIVENTION_CONTAINER,
				objectClass='univentionFreeAttributes',
				groupPosition='1',
				module='users/user',
				overwriteTab='0',
				shortDescription='UCS Test Extended Attribute',
				groupName='UCS TEST: test_udm_syntax',
				valueRequired='0',
				CLIName=extension_name,
				longDescription='UCS Test Extended Attribute',
				doNotSearch='0',
				tabName='UCS TEST',
				syntax=extension_name,
				tabAdvanced='0',
				name='UCStest-syntax-extension-%s' % extension_name,
				mayChange='1',
				multivalue='0',
				ldapMapping='univentionFreeAttribute%s' % str(i + 10),
				notEditable='0',
				tabPosition='1'
			)
			verify_ldap_object(extension_dn, {
				'cn': [extension_name],
				'univentionUDM%sFilename' % extension_type.capitalize(): [extension_filename],
				'univentionOwnedByPackage': [package_name],
				'univentionObjectType': ['settings/udm_%s' % extension_type],
				'univentionOwnedByPackageVersion': [package_version],
				'univentionUDM%sData' % extension_type.capitalize(): [bz2.compress(extension_buffer.encode('UTF-8'))],
				'univentionUDM%sActive' % extension_type.capitalize(): ['TRUE'],
			})

		wait_for_replication_and_postrun()
		udm.stop_cli_server()
		restart_udmrest()

		yield

	wait_for_replication_and_postrun()
	udm.stop_cli_server()
	restart_udmrest()


class Test_ComplexSyntaxTypes():

	def test_ComplexMultiValueKeyValueDictType(self):
		expected_type_definition = {
			u'additionalProperties': True,
			u'type': u'object',
			u'nullable': True
		}
		openapi_schema = get_openapi_schema()
		user_props = openapi_schema["components"]["schemas"]["users-user"]["properties"]["properties"]["properties"]
		assert "UCSTESTComplexMultiValueKeyValueDict" in user_props
		assert user_props["UCSTESTComplexMultiValueKeyValueDict"] == expected_type_definition

	def test_ComplexMultiValueDictType(self):
		expected_type_definition = {
			u'additionalProperties': True,
			u'type': u'object',
			u'nullable': True
		}
		openapi_schema = get_openapi_schema()
		user_props = openapi_schema["components"]["schemas"]["users-user"]["properties"]["properties"]["properties"]
		assert "UCSTESTComplexMultiValueDict" in user_props
		assert user_props["UCSTESTComplexMultiValueDict"] == expected_type_definition

	def test_ComplexListType(self):
		expected_type_definition = {
			u'uniqueItems': False,
			u'items': {
				u'oneOf': [
					{u'type': u'string', u'nullable': True},
					{u'type': u'integer', u'nullable': True}
				]},
			u'type': u'array',
			u'nullable': True
		}
		openapi_schema = get_openapi_schema()
		user_props = openapi_schema["components"]["schemas"]["users-user"]["properties"]["properties"]["properties"]
		assert "UCSTESTComplexList" in user_props
		assert user_props["UCSTESTComplexList"] == expected_type_definition
