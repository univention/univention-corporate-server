#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test pagination of the UDM REST API search
## bugs: [59466]
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-rest

import pytest
import requests

from univention.testing.strings import random_name
from univention.testing.udm import UCSTestUDM


LIMIT = 2
PAGES = 3


@pytest.fixture(scope='module')
def pagination_users():
    """Create the users for the pagination tests only once per module."""
    with UCSTestUDM() as udm:
        prefix = random_name()
        dns = {udm.create_user(username=f'{prefix}{i}', wait_for=False)[0] for i in range(LIMIT * PAGES)}
        yield prefix, dns


def search_page(account, ldap_filter, page, limit=LIMIT):
    """Search users/user with pagination and return the DNs of one result page."""
    response = requests.get(
        'http://localhost/univention/udm/users/user/',
        params={'filter': ldap_filter, 'page': str(page), 'limit': str(limit)},
        headers={'Accept': 'application/json'},
        auth=(account.username, account.bindpw),
    )
    response.raise_for_status()
    return [obj['dn'] for obj in response.json().get('_embedded', {}).get('udm:object', [])]


# Note: the paged search sessions are keyed by the literal filter string (among others).
# Each test therefore uses an equivalent but differently written filter
# to get its own search session despite searching for the same users.


def test_search_pagination_forward(pagination_users, account):
    """Walking forward through the pages must return all objects exactly once"""
    prefix, expected_dns = pagination_users
    ldap_filter = f'(uid={prefix}*)'

    # walk forward through all pages one by one
    pages = [search_page(account, ldap_filter, page) for page in range(1, PAGES + 1)]
    assert all(len(page) == LIMIT for page in pages)
    dns = [dn for page in pages for dn in page]
    assert len(dns) == len(expected_dns), 'pages overlap'
    assert set(dns) == expected_dns

    # jumping to a later page without having requested the previous ones must work
    assert search_page(account, f'(&{ldap_filter})', PAGES) == pages[-1]


def test_search_pagination_rewind(pagination_users, account):
    """Requesting a page number that isn't larger than the previous one must not return empty results"""
    prefix, expected_dns = pagination_users
    ldap_filter = f'(|(uid={prefix}*))'

    # walk forward through all pages (creates the paged search session)
    pages = [search_page(account, ldap_filter, page) for page in range(1, PAGES + 1)]
    assert all(len(page) == LIMIT for page in pages)
    dns = [dn for page in pages for dn in page]
    assert len(dns) == len(expected_dns)
    assert set(dns) == expected_dns

    # Bug #59466: rewinding to a previous page must restart the search instead of returning empty results
    assert search_page(account, ldap_filter, 1) == pages[0]

    # requesting the same page again must return the same results
    assert search_page(account, ldap_filter, 1) == pages[0]

    # skipping forward multiple pages after a rewind must work as well
    assert search_page(account, ldap_filter, 3) == pages[2]
