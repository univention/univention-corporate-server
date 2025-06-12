#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test tombstone functionality in UDM REST API
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-rest
# execute with: --tb=native -s -l -vv --cov-report=term-missing  --cov-report=html --cov=univention.admin.rest.async_client

import pytest

import univention.admin.modules
from univention.admin.rest.client import NotFound, UnprocessableEntity
from univention.config_registry import ucr as _ucr
from univention.testing.strings import random_string


univention.admin.modules.update()
pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/rest/enable-delegative-administration'), reason='authz not activated')


@pytest.fixture
def test_undelete_functionality(udm_client):
    users_user = udm_client.get('users/user')
    test_user = users_user.new()
    username = f"test-{random_string()}"

    test_user.properties.update({
        'username': username,
        'firstname': 'Test',
        'lastname': 'User',
        'password': 'univention',
    })

    test_user.save()
    original_dn = test_user.dn
    test_user.delete()

    # Verify user is deleted
    with pytest.raises(NotFound):
        users_user.get(original_dn)

    undeleted_user = users_user.undelete(original_dn)

    # Verify user exists and has same properties
    assert undeleted_user.dn == original_dn
    assert undeleted_user.properties['username'] == username
    assert undeleted_user.properties['firstname'] == 'Test'
    assert undeleted_user.properties['lastname'] == 'User'

    undeleted_user.delete()


@pytest.fixture
def test_undelete_nonexistent_object(udm_client):
    """Test undeleting a non-existent object throws appropriate error"""
    users_user = udm_client.get('users/user')
    fake_dn = f"uid=nonexistent-{random_string()},cn=users,{udm_client.domain}"

    with pytest.raises(UnprocessableEntity):
        users_user.undelete(fake_dn)


@pytest.fixture
def test_undelete_not_deleted_object(udm_client):
    """Test attempting to undelete an object that exists but wasn't deleted"""
    # Create a test user
    users_user = udm_client.get('users/user')
    test_user = users_user.new()
    username = f"test-{random_string()}"

    test_user.properties.update({
        'username': username,
        'firstname': 'Test',
        'lastname': 'User',
        'password': 'univention',
    })
    test_user.save()

    # Try to undelete an object that exists
    with pytest.raises(UnprocessableEntity):
        users_user.undelete(test_user.dn)

    test_user.delete()
