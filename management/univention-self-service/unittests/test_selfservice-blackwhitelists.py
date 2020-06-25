from univention.management.console.error import ServerError

from univention.unittests.umc import import_umc_module, umc_requests
from univention.unittests.udm import mock_conn

import pytest

selfservice = import_umc_module('passwordreset')

@pytest.fixture
def ldap_database_file():
	return 'unittests/selfservice.ldif'


def test_blacklist_user_match(instance, mocker, ucr, ldap_database):
	feature = 'passwordreset'
	ucr['umc/self-service/{}/blacklist/users'.format(feature)] = 'hinderkampp'
	mocker.patch.object(selfservice, 'ucr', ucr)
	assert instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_user_nomatch(instance, mocker, ucr, ldap_database):
	feature = 'passwordreset'
	ucr['umc/self-service/{}/blacklist/users'.format(feature)] = 'hinderkampf'
	mocker.patch.object(selfservice, 'ucr', ucr)
	assert not instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_group_match(instance, mocker, ucr, ldap_database):
	feature = 'passwordreset'
	ucr['umc/self-service/{}/blacklist/groups'.format(feature)] = 'selfservice-group1'
	mocker.patch.object(selfservice, 'ucr', ucr)
	assert instance.is_blacklisted('hinderkampp', feature)


@pytest.fixture
def blacklist_ucr(mocker, ucr):
	ucr['umc/self-service/account-deregistration/blacklist/groups'] = 'Administrators,Domain Admins'
	ucr['umc/self-service/account-deregistration/blacklist/users'] = ''
	ucr['umc/self-service/account-deregistration/whitelist/groups'] = 'Domain Users'
	ucr['umc/self-service/account-deregistration/whitelist/users'] = ''
	ucr['umc/self-service/passwordreset/blacklist/groups'] = 'Administrators,Domain Admins'
	ucr['umc/self-service/passwordreset/whitelist/groups'] = 'Domain Users'
	ucr['umc/self-service/profiledata/blacklist/groups'] = 'Administrators,Domain Admins'
	ucr['umc/self-service/profiledata/blacklist/users'] = ''
	ucr['umc/self-service/profiledata/whitelist/groups'] = 'Domain Users'
	ucr['umc/self-service/profiledata/whitelist/users'] = ''
	mocker.patch.object(selfservice, 'ucr', ucr)
	return ucr

@pytest.fixture
def mocked_conn(mocker, ldap_database):
	lo, pos = mock_conn(ldap_database)
	mocker.patch.object(selfservice, 'get_admin_connection', return_value=[lo, pos])
	mocker.patch.object(selfservice, 'get_machine_connection', return_value=[lo, pos])
	import univention.management.console.ldap as umc_ldap
	mocker.patch.object(umc_ldap, '_getMachineConnection', return_value=[lo, pos])
	mocker.patch.object(umc_ldap, '_getAdminConnection', return_value=[lo, pos])

def test_blacklist_group_nomatch(instance, blacklist_ucr, mocked_conn):
	feature = 'passwordreset'
	blacklist_ucr['umc/self-service/{}/blacklist/groups'.format(feature)] = 'selfservice-group0'
	assert not instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_group_match_nested(instance, mocker, ucr, ldap_database):
	feature = 'passwordreset'
	ucr['umc/self-service/{}/blacklist/groups'.format(feature)] = 'selfservice-group2'
	mocker.patch.object(selfservice, 'ucr', ucr)
	assert instance.is_blacklisted('hinderkampp', feature)


def test_blacklist_whitelist_precedence(instance, mocker, ucr, ldap_database):
	feature = 'passwordreset'
	ucr['umc/self-service/{}/whitelist/groups'.format(feature)] = 'selfservice-group1'
	ucr['umc/self-service/{}/blacklist/groups'.format(feature)] = 'Administrators,Domain Admins,selfservice-group2'
	mocker.patch.object(selfservice, 'ucr', ucr)
	assert instance.is_blacklisted('hinderkampp', feature)
