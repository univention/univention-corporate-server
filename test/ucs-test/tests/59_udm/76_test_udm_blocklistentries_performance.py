#!/usr/share/ucs-test/runner pytest-3
## desc: Test blocklist performance
## tags: [udm,udm-settings,apptest]
## exposure: dangerous
## roles: [domaincontroller_master]
## packages:
##   - univention-directory-manager-tools

import time

import pytest

from univention.admin import configRegistry, modules
from univention.admin.uldap import getAdminConnection


def create_user(new, username, maildom):
    new['title'] = f'{username}-title'
    new['firstname'] = f'{username}-firstname'
    new['lastname'] = f'{username}-lastname'
    new['username'] = username
    new['description'] = f'{username}-description'
    new['mailPrimaryAddress'] = f'{username}@{maildom}'
    new['jpegPhoto'] = '/9j/4AAQSkZJRgABAQEBLAEsAAD/4Se4'
    new['organisation'] = f'{username}-organisation'
    new['employeeNumber'] = f'{username}-employeeNumber'
    new['employeeType'] = f'{username}-employeeType'
    new['homedrive'] = f'{username}-homedrive'
    new['sambahome'] = f'{username}-sambahome'
    new['scriptpath'] = f'{username}-scriptpath'
    new['profilepath'] = f'{username}-profilepath'
    new['mailAlternativeAddress'] = f'alt-{username}@{maildom}'
    new['mailForwardAddress'] = [f'for1-{username}@{maildom}', f'for2-{username}@{maildom}', f'for3-{username}@{maildom}', f'for4-{username}@{maildom}']
    new['e-mail'] = [f'mail1-{username}@{maildom}', f'mail2-{username}@{maildom}', f'mail3-{username}@{maildom}', f'mail4-{username}@{maildom}']
    new['phone'] = [f'123-{username}', f'456-{username}', f'789-{username}', f'101-{username}']
    new['roomNumber'] = ['1', '2', '3', '4']
    new['departmentNumber'] = ['1', '2', '3', '4']
    new['street'] = 'sdsaaf'
    new['postcode'] = '345456456462'
    new['city'] = 'fsdfsa'
    new['country'] = 'DE'
    new['homeTelephoneNumber'] = [f'123-{username}', f'456-{username}', f'789-{username}', f'101-{username}']
    new['mobileTelephoneNumber'] = [f'123-{username}', f'456-{username}', f'789-{username}', f'101-{username}']
    new['pagerTelephoneNumber'] = [f'123-{username}', f'456-{username}', f'789-{username}', f'101-{username}']
    new['password'] = 'univention'
    new.create()
    return new.dn


@pytest.fixture()
def blocklist_setup(random_string, udm):
    assert udm.list_objects('blocklists/list') == [], 'please remove all blocklists before starting this test'
    name = f'extreme setup {random_string()}'
    data = {
        'name': name,
        'blockingProperties': [
            'users/user mailPrimaryAddress',
            'users/user e-mail',
            'users/user title',
            'users/user firstname',
            'users/user lastname',
            'users/user username',
            'users/user description',
            'users/user jpegPhoto',
            'users/user organisation',
            'users/user employeeNumber',
            'users/user employeeType',
            'users/user homedrive',
            'users/user sambahome',
            'users/user scriptpath',
            'users/user profilepath',
            'users/user mailAlternativeAddress',
            'users/user mailForwardAddress',
            'users/user phone',
            'users/user roomNumber',
            'users/user departmentNumber',
            'users/user street',
            'users/user postcode',
            'users/user city',
            'users/user country',
            'users/user homeTelephoneNumber',
            'users/user mobileTelephoneNumber',
            'users/user pagerTelephoneNumber',
            'users/user homePostalAddress',
        ]
    }
    udm.create_object('blocklists/list', **data)


@pytest.fixture()
def mail_domain_name(udm, random_name):
    mail_domain_name = f'{random_name()}.{random_name()}'
    udm.create_object('mail/domain', name=mail_domain_name)
    return mail_domain_name


def test_create_1000_users_with_extreme_blocklist_setup(blocklist_setup, mail_domain_name):
    number_of_users = 1000
    lo, position = getAdminConnection()
    modules.update()
    users = modules.get('users/user')
    modules.init(lo, position, users)
    configRegistry['directory/manager/user/primarygroup/update'] = 'false'
    configRegistry['directory/manager/blocklist/enabled'] = 'true'
    start = time.time()
    user_dns = []
    try:
        for i in range(number_of_users):
            username = f'testuser-{i}'
            new = users.object(None, lo, position)
            user_dns.append(create_user(new, username, mail_domain_name))
    finally:
        end = time.time()
        for dn in user_dns:
            lo.delete(dn)
    duration = end - start
    assert duration < 250
