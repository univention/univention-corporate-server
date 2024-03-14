#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Test Extended Attributes integration
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import os
import subprocess
from contextlib import contextmanager

from univention.config_registry import ConfigRegistry
from univention.testing.utils import verify_ldap_object
import univention.testing.strings as uts

from dockertest import tiny_app

import pytest


ucr = ConfigRegistry()
ucr.load()


@contextmanager
def build_app(app_name, generic_user_activation, generic_user_activation_attribute=None, generic_user_activation_option=None):
    app = tiny_app(name=app_name)
    try:
        app.set_ini_parameter(
            GenericUserActivation=generic_user_activation,
            GenericUserActivationAttribute=generic_user_activation_attribute,
            GenericUserActivationOption=generic_user_activation_option,
        )
        yield app
    finally:
        app.uninstall()
        app.remove()


def run_app_tests(appcenter, app, udm, activation_name, app_name, attribute_dn=None, attribute_description=None, attrs=None):
    attribute_dn = attribute_dn or f'cn={activation_name},cn={app.app_name},cn=custom attributes,cn=univention,{ucr.get("ldap/base")}'
    attribute_description = attribute_description or f'Activate user for {app.app_name}'
    app.add_to_local_appcenter()
    appcenter.update()
    app.install()
    # app.verify(joined=False)
    schema_file = f'/usr/share/univention-appcenter/apps/{app.app_name}/{app.app_name}.schema'
    assert os.path.exists(schema_file)
    subprocess.call(['univention-ldapsearch', '-b', attribute_dn])
    verify_ldap_object(attribute_dn, {'univentionUDMPropertyShortDescription': [attribute_description], 'univentionUDMPropertySyntax': ['TrueFalseUp']})
    attrs = (attrs or {}).copy()
    attrs['username'] = uts.random_string()
    attrs['lastname'] = uts.random_string()
    attrs['password'] = uts.random_string()
    attrs[activation_name] = 'TRUE'
    user = udm.create_object('users/user', **attrs)
    subprocess.call(['univention-ldapsearch', '-b', user])
    verify_ldap_object(user, {activation_name: ['TRUE']})
    return user


@pytest.mark.exposure('dangerous')
def test_schema_generation(appcenter, udm, app_name):
    activation_name = f'{app_name}Activated'
    generic_user_activation = True
    with build_app(app_name, generic_user_activation, activation_name) as app:
        run_app_tests(appcenter, app, udm, activation_name, app_name)


@pytest.mark.exposure('dangerous')
def test_own_schema(appcenter, udm):
    app_name = 'extattrownschemaconstname'
    activation_name = f'{app_name}-active'
    generic_user_activation = activation_name
    with build_app(app_name, generic_user_activation, activation_name) as app:
        schema_content = f"""attributetype ( 1.3.6.1.4.1.10176.5000.7.7.7.1.1
    NAME '{app.app_name}-active'
    DESC 'Attribute created MANUALLY'
    SYNTAX 1.3.6.1.4.1.1466.115.121.1.7 EQUALITY booleanMatch
    SINGLE-VALUE
    )

objectclass ( 1.3.6.1.4.1.10176.5000.7.7.7.2.1
    NAME '{app.app_name}-user'
    DESC 'Class created MANUALLY'
    AUXILIARY
    MAY ( {app.app_name}-active )
    SUP top
    )"""
        app.add_script(schema=schema_content)
        attributes_content = f"""[{activation_name}]
Type=ExtendedAttribute
Syntax=Boolean
Description=This is my custom activation
BelongsTo={app.app_name}-user"""
        app.add_script(attributes=attributes_content)
        run_app_tests(appcenter, app, udm, activation_name, app.app_name, attribute_description='This is my custom activation')


@pytest.mark.exposure('dangerous')
def test_attributes_file_without_attribute(appcenter, udm, app_name):
    option_name = f'{app_name}User'
    activation_name = f'{app_name}Activated'
    additional_name = f'{app_name}-myAttr'
    generic_user_activation = True
    with build_app(app_name, generic_user_activation, activation_name) as app:
        attributes_content = f"""[{additional_name}]
Type=ExtendedAttribute
Module=users/user
Syntax=String
Description=This is my attribute
DescriptionDe=Das ist mein Attribut
LongDescription=This is my attribute. And it rocks!
LongDescriptionDe=Das ist mein Attribut. Und es ist dufte!
"""
        app.add_script(attributes=attributes_content)
        user = run_app_tests(appcenter, app, udm, activation_name, app_name, attrs={additional_name: 'Hello'})
        verify_ldap_object(f'cn={option_name},cn={app_name},cn=custom attributes,cn=univention,{ucr.get("ldap/base")}', should_exist=False)
        verify_ldap_object(f'cn={additional_name},cn={app_name},cn=custom attributes,cn=univention,{ucr.get("ldap/base")}', {
            'univentionUDMPropertyShortDescription': ['This is my attribute'],
            'univentionUDMPropertyLongDescription': ['This is my attribute. And it rocks!'],
            'univentionUDMPropertySyntax': ['string'],
        })
        verify_ldap_object(user, {activation_name: ['TRUE'], additional_name: ['Hello']})
    verify_ldap_object(f'cn={additional_name},cn={app_name},cn=custom attributes,cn=univention,{ucr.get("ldap/base")}', should_exist=False)


@pytest.mark.exposure('dangerous')
def test_attributes_file_with_attribute(appcenter, udm, app_name):
    option_name = f'{app_name}User'
    activation_name = f'{app_name}Activated'
    additional_name = f'{app_name}-myAttr'
    generic_user_activation = True
    with build_app(app_name, generic_user_activation, activation_name) as app:
        attributes_content = f"""[{activation_name}]
Type=ExtendedAttribute
Module=users/user
Syntax=Boolean
Description=This is my custom activation
Position=cn=custom attributes,cn=univention
[{additional_name}]
Type=ExtendedAttribute
Module=users/user
Syntax=String
Description=This is my attribute
DescriptionDe=Das ist mein Attribut
"""
        app.add_script(attributes=attributes_content)
        attribute_dn = f'cn={activation_name},cn=custom attributes,cn=univention,{ucr.get("ldap/base")}'
        user = run_app_tests(appcenter, app, udm, activation_name, app_name, attribute_dn, 'This is my custom activation', {additional_name: 'Hello'})
        verify_ldap_object(user, {activation_name: ['TRUE'], additional_name: ['Hello']})
        verify_ldap_object(f'cn={option_name},cn={app_name},cn=custom attributes,cn=univention,{ucr.get("ldap/base")}', should_exist=False)
