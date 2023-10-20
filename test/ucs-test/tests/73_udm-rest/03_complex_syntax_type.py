#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Check the type definition of a complex syntax in the OpenAPI schema
## tags: [udm,apptest,openapi]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-rest
## bugs: [53513, 50648]

import base64
import bz2
import subprocess
import time

import pytest
import requests
from requests.auth import HTTPBasicAuth

from univention.testing.strings import random_name, random_ucs_version, random_version
from univention.testing.udm import UCSTestUDM
from univention.testing.udm_extensions import get_extension_filename, get_package_name, get_package_version
from univention.testing.utils import UCSTestDomainAdminCredentials, verify_ldap_object, wait_for_replication_and_postrun


def get_openapi_schema():
    account = UCSTestDomainAdminCredentials()
    resp = requests.get("http://localhost/univention/udm/openapi.json", auth=HTTPBasicAuth(account.username, account.bindpw))
    resp.raise_for_status()
    return resp.json()


def restart_udmrest():
    subprocess.check_call(["systemctl", "restart", "univention-directory-manager-rest.service"])
    for _i in range(10):
        try:
            get_openapi_schema()
        except requests.HTTPError as exc:
            if exc.response.status_code != 503:
                raise
        else:
            break
        time.sleep(1)


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
    app_id = f'{random_name()}-{random_version()}'
    version_start = random_ucs_version(max_major=2)
    version_end = random_ucs_version(min_major=5)

    with UCSTestUDM() as udm:
        udm.create_object(
            'container/cn',
            name=f'udm_{extension_type}',
            position=udm.UNIVENTION_CONTAINER,
            ignore_exists=True,
        )
        for i, (extension_name, extension_buffer) in enumerate(extension_buffers.items()):
            extension_filename = get_extension_filename(extension_type, extension_name)
            extension_dn = udm.create_object(
                f'settings/udm_{extension_type}',
                name=extension_name,
                data=base64.b64encode(bz2.compress(extension_buffer.encode("UTF-8"))).decode("ASCII"),
                filename=extension_filename,
                packageversion=package_version,
                appidentifier=app_id,
                package=package_name,
                ucsversionstart=version_start,
                ucsversionend=version_end,
                active='FALSE',
                position=f'cn=udm_{extension_type},{udm.UNIVENTION_CONTAINER}',
            )

            udm.create_object(
                'settings/extended_attribute',
                position=f'cn=custom attributes,{udm.UNIVENTION_CONTAINER}',
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
                name=f'UCStest-syntax-extension-{extension_name}',
                mayChange='1',
                multivalue='0',
                ldapMapping=f'univentionFreeAttribute{str(i + 10)}',
                notEditable='0',
                tabPosition='1',
            )
            verify_ldap_object(extension_dn, {
                'cn': [extension_name],
                f'univentionUDM{extension_type.capitalize()}Filename': [extension_filename],
                'univentionOwnedByPackage': [package_name],
                'univentionObjectType': [f'settings/udm_{extension_type}'],
                'univentionOwnedByPackageVersion': [package_version],
                f'univentionUDM{extension_type.capitalize()}Data': [bz2.compress(extension_buffer.encode('UTF-8'))],
                f'univentionUDM{extension_type.capitalize()}Active': ['TRUE'],
            })

        wait_for_replication_and_postrun()
        udm.stop_cli_server()
        restart_udmrest()

        yield

    wait_for_replication_and_postrun()
    udm.stop_cli_server()
    restart_udmrest()


class Test_ComplexSyntaxTypes:

    def test_ComplexMultiValueKeyValueDictType(self):
        expected_type_definition = {
            'additionalProperties': {'type': 'string', 'nullable': True},
            'type': 'object',
            'nullable': True,
        }
        openapi_schema = get_openapi_schema()
        user_props = openapi_schema["components"]["schemas"]["users-user.request-patch"]["properties"]["properties"]["properties"]
        assert "UCSTESTComplexMultiValueKeyValueDict" in user_props
        assert user_props["UCSTESTComplexMultiValueKeyValueDict"] == expected_type_definition

    def test_ComplexMultiValueDictType(self):
        expected_type_definition = {
            'type': 'object',
            'nullable': True,
            'additionalProperties': False,
            'properties': {
                    'priority': {'type': 'integer', 'nullable': True},
                    'mailserver': {'type': 'string', 'nullable': True},
            },
            'required': ['priority', 'mailserver'],
        }
        openapi_schema = get_openapi_schema()
        user_props = openapi_schema["components"]["schemas"]["users-user.request-patch"]["properties"]["properties"]["properties"]
        assert "UCSTESTComplexMultiValueDict" in user_props
        assert user_props["UCSTESTComplexMultiValueDict"] == expected_type_definition

    def test_ComplexListType(self):
        expected_type_definition = {
            'uniqueItems': False,
            'items': {
                'oneOf': [
                    {'type': 'string', 'nullable': True},
                    {'type': 'integer', 'nullable': True},
                ]},
            'type': 'array',
            'nullable': True,
        }
        openapi_schema = get_openapi_schema()
        user_props = openapi_schema["components"]["schemas"]["users-user.request-patch"]["properties"]["properties"]["properties"]
        assert "UCSTESTComplexList" in user_props
        assert user_props["UCSTESTComplexList"] == expected_type_definition
