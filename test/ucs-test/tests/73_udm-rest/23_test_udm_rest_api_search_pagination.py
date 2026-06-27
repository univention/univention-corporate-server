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

from univention.admin.rest.client import UDM
from univention.testing import utils
from univention.testing.strings import random_name
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM


PAGE_SIZE = 2
PAGES = 3


@pytest.fixture(scope='module')
def ucr_mod():
    """Per `module` auto-reverting UCR instance."""
    with UCSTestConfigRegistry() as ucr:
        yield ucr


@pytest.fixture(scope='module')
def pagination_users(ucr_mod):
    """Create the users for the pagination tests only once per module."""
    ucr_mod.handler_set([
        'ldap/overlay/sssvlv=true',
        'ldap/overlay/sssvlv/max=32',
        'ldap/overlay/sssvlv/maxperconn=32',
        'ldap/overlay/sssvlv/maxkeys=2',
    ])
    utils.restart_slapd()
    with UCSTestUDM() as udm:
        prefix = random_name()
        dns = {
            udm.create_user(username=f'{prefix}{i}', wait_for=False)[0]
            for i in range(PAGE_SIZE * PAGES)
        }
        try:
            yield prefix, dns
        finally:
            utils.restart_slapd()


def search_page(account, ldap_filter, page, page_size=PAGE_SIZE, pagination=False):
    """Search users/user with pagination and return the DNs of one result page."""
    response = requests.get(
        'http://localhost/univention/udm/users/user/',
        params={'filter': ldap_filter, 'page': str(page), 'page_size': str(page_size), 'pagination': str(int(pagination))},
        headers={'Accept': 'application/json'},
        auth=(account.username, account.bindpw),
    )
    response.raise_for_status()
    return [obj['dn'] for obj in response.json().get('_embedded', {}).get('udm:object', [])]


# Note: the paged search sessions are keyed by the literal filter string (among others).
# Each test therefore uses an equivalent but differently written filter
# to get its own search session despite searching for the same users.


@pytest.mark.parametrize('sssvlv', [True, False])
def test_search_pagination_forward(pagination_users, account, sssvlv):
    """Walking forward through the pages must return all objects exactly once"""
    prefix, expected_dns = pagination_users
    ldap_filter = f'(uid={prefix}*)'

    # walk forward through all pages one by one
    pages = [search_page(account, ldap_filter, page, pagination=sssvlv) for page in range(1, PAGES + 1)]
    assert all(len(page) == PAGE_SIZE for page in pages)
    dns = [dn for page in pages for dn in page]
    assert len(dns) == len(expected_dns), 'pages overlap'
    assert set(dns) == expected_dns

    # jumping to a later page without having requested the previous ones must work
    assert search_page(account, f'(&{ldap_filter})', PAGES, pagination=True) == pages[-1]


def test_search_pagination_rewind(pagination_users, account):
    """Requesting a page number that isn't larger than the previous one must not return empty results"""
    prefix, expected_dns = pagination_users
    ldap_filter = f'(|(uid={prefix}*))'

    # walk forward through all pages (creates the paged search session)
    pages = [search_page(account, ldap_filter, page, pagination=True) for page in range(1, PAGES + 1)]
    assert all(len(page) == PAGE_SIZE for page in pages)
    dns = [dn for page in pages for dn in page]
    assert len(dns) == len(expected_dns)
    assert set(dns) == expected_dns

    # Bug #59466: rewinding to a previous page must restart the search instead of returning empty results
    assert search_page(account, ldap_filter, 1, pagination=True) == pages[0]

    # requesting the same page again must return the same results
    assert search_page(account, ldap_filter, 1, pagination=True) == pages[0]

    # skipping forward multiple pages after a rewind must work as well
    assert search_page(account, ldap_filter, 3, pagination=True) == pages[2]


@pytest.fixture
def users_module(account):
    udm = UDM.http('http://localhost/univention/udm/', account.username, account.bindpw)
    return udm.get('users/user')


def dns(page_or_objects):
    return [obj.dn for obj in page_or_objects]


def test_search_page_metadata(pagination_users, users_module):
    """A paginated search returns page metadata and page items."""
    prefix, expected_dns = pagination_users

    page = users_module.search_page(
        filter=f'(uid={prefix}*)',
        page=1,
        page_size=PAGE_SIZE,
        sort_by='username',
        pagination=True,
    )

    assert page.page == 1
    assert page.page_size == PAGE_SIZE
    assert page.total == len(expected_dns)
    assert page.last_page == PAGES
    assert page.has_next
    assert not page.has_prev
    assert len(page) == PAGE_SIZE
    assert set(dns(page)).issubset(expected_dns)


@pytest.mark.parametrize('sssvlv', [True, False])
def test_search_page_navigation_forward(pagination_users, users_module, sssvlv):
    """Walking forward through SearchPage.next() must return all objects exactly once."""
    prefix, expected_dns = pagination_users

    page = users_module.search_page(
        filter=f'(uid={prefix}*)',
        page=1,
        page_size=PAGE_SIZE,
        sort_by='username',
        pagination=sssvlv,
    )

    pages = []
    while page:
        pages.append(dns(page))
        page = page.next()

    assert len(pages) == PAGES
    assert all(len(page_dns) == PAGE_SIZE for page_dns in pages)

    found_dns = [dn for page_dns in pages for dn in page_dns]
    assert len(found_dns) == len(expected_dns), 'pages overlap'
    assert set(found_dns) == expected_dns


def test_search_page_navigation_prev_and_first(pagination_users, users_module):
    """SearchPage.prev() and SearchPage.first() must navigate back correctly."""
    prefix, _expected_dns = pagination_users

    first_page = users_module.search_page(
        filter=f'(|(uid={prefix}*))',
        page=1,
        page_size=PAGE_SIZE,
        sort_by='username',
        pagination=True,
    )
    second_page = first_page.next()
    assert second_page is not None

    assert dns(second_page.prev()) == dns(first_page)
    assert dns(second_page.first()) == dns(first_page)


def test_search_page_jump_to_later_page(pagination_users, users_module):
    """Jumping to a later page without requesting previous pages must work."""
    prefix, _expected_dns = pagination_users

    first_page = users_module.search_page(
        filter=f'(uid={prefix}*)',
        page=1,
        page_size=PAGE_SIZE,
        sort_by='username',
        pagination=True,
    )
    last_page = first_page.last()

    jumped_page = users_module.search_page(
        filter=f'(&(uid={prefix}*))',
        page=PAGES,
        page_size=PAGE_SIZE,
        sort_by='username',
        pagination=True,
    )

    assert last_page is not None
    assert dns(jumped_page) == dns(last_page)


def test_search_page_rewind(pagination_users, users_module):
    """Requesting an earlier page again must not return empty results."""
    prefix, expected_dns = pagination_users

    pages = [
        users_module.search_page(
            filter=f'(|(uid={prefix}*))',
            page=page,
            page_size=PAGE_SIZE,
            sort_by='username',
            pagination=True,
        )
        for page in range(1, PAGES + 1)
    ]

    found_dns = [dn for page in pages for dn in dns(page)]
    assert len(found_dns) == len(expected_dns)
    assert set(found_dns) == expected_dns

    rewind = users_module.search_page(
        filter=f'(|(uid={prefix}*))',
        page=1,
        page_size=PAGE_SIZE,
        sort_by='username',
        pagination=True,
    )
    assert dns(rewind) == dns(pages[0])

    same_page = users_module.search_page(
        filter=f'(|(uid={prefix}*))',
        page=1,
        page_size=PAGE_SIZE,
        sort_by='username',
        pagination=True,
    )
    assert dns(same_page) == dns(pages[0])

    skip_forward = users_module.search_page(
        filter=f'(|(uid={prefix}*))',
        page=3,
        page_size=PAGE_SIZE,
        sort_by='username',
        pagination=True,
    )
    assert dns(skip_forward) == dns(pages[2])


@pytest.mark.parametrize('sssvlv', [True, False])
def test_search_paginated_iterator(pagination_users, users_module, sssvlv):
    """search_paginated() must transparently iterate over all pages."""
    prefix, expected_dns = pagination_users

    objects = list(users_module.search_paginated(
        filter=f'(uid={prefix}*)',
        page_size=PAGE_SIZE,
        sort_by='username',
        pagination=sssvlv,
    ))

    assert len(objects) == len(expected_dns)
    assert {obj.dn for obj in objects} == expected_dns


# @pytest.mark.parametrize('sssvlv', [True, False])
# def test_search_with_page_arguments_returns_single_page(pagination_users, users_module, sssvlv):
#     """Module.search(..., page_size=..., page=...) must remain usable as a page iterator."""
#     prefix, expected_dns = pagination_users
#
#     objects = list(users_module.search(
#         filter=f'(uid={prefix}*)',
#         page=2,
#         page_size=PAGE_SIZE,
#         sort_by='username',
#         pagination=sssvlv,
#     ))
#
#     assert len(objects) == PAGE_SIZE
#     assert {obj.dn for obj in objects}.issubset(expected_dns)
