#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test metrics endpoint of UDM REST API
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-rest

import pytest
from prometheus_client.parser import text_string_to_metric_families

from univention.admin.rest.client import UDM as UDMClient, Forbidden
from univention.config_registry import ucr
from univention.testing.utils import UCSTestDomainAdminCredentials


class UDMClient(UDMClient):

    @classmethod
    def primary_connection(cls, username, password):
        return cls.http('https://%s/univention/udm/' % (ucr['ldap/master'],), username, password)

    @classmethod
    def test_connection(cls):
        account = UCSTestDomainAdminCredentials(ucr)
        return cls.primary_connection(account.username, account.bindpw)


@pytest.fixture
def udm_rest_client():
    return UDMClient.test_connection()


def _get_family(metrics, name):
    for m in metrics:
        if m.name == name:
            return m
    return None


def _get_sample(family, labels):
    for sample in family.samples:
        if sample.labels == labels:
            return sample
    return None


def test_metrics_endpoint(udm_rest_client, ucr, subtests):
    text = udm_rest_client.client.request('GET', udm_rest_client.uri + '-/metrics', expect_json=False)
    metrics = list(text_string_to_metric_families(text))

    domainname = ucr['domainname']

    with subtests.test("version_ucs_info"):
        family = _get_family(metrics, 'version_ucs_info')
        assert family is not None

        sample = _get_sample(
            family,
            {
                'domain': domainname,
                'errata': ucr['version/erratalevel'],
                'license-uuid': ucr['uuid/license'],
                'patch': ucr['version/patchlevel'],
                'system-uuid': ucr['uuid/system'],
                'ucs': ucr['version/version'],
            },
        )
        assert sample is not None
        assert sample.value == 1

    with subtests.test("version_nubus_info"):
        family = _get_family(metrics, 'version_nubus_info')
        assert family is not None

        sample = _get_sample(
            family,
            {
                'domain': domainname,
                'platform': 'ucs',
            },
        )
        assert sample is not None
        assert sample.value == 1

    # # no samples expected in UCS
    with subtests.test("version_n4k_info"):
        family = _get_family(metrics, 'version_n4k_info')
        assert family is not None
        assert len(family.samples) == 0

    with subtests.test("users_user_total"):
        family = _get_family(metrics, 'users_user_total')
        assert family is not None

        sample = _get_sample(
            family,
            {'domain': domainname},
        )
        assert sample is not None
        assert sample.value > 1 or sample.value == -1

    with subtests.test("settings_license_users_limit_total"):
        family = _get_family(metrics, 'settings_license_users_limit_total')
        assert family is not None

        sample = _get_sample(
            family,
            {'domain': domainname},
        )
        assert sample is not None
        assert sample.value >= 50


def test_metrics_endpoint_authorization(udm, ucr, subtests):
    _, user1 = udm.create_user(groups=['cn=udm-rest-metrics,cn=groups,{ldap/base}'.format(**ucr)])
    _, user2 = udm.create_user()
    with subtests.test("access_allowed"):
        udm_rest_client = UDMClient.primary_connection(user1, "univention")
        assert udm_rest_client.client.request('GET', udm_rest_client.uri + '-/metrics', expect_json=False)
    with subtests.test("access_disallowed"):
        udm_rest_client = UDMClient.primary_connection(user2, "univention")
        with pytest.raises(Forbidden):
            udm_rest_client.client.request('GET', udm_rest_client.uri + '-/metrics', expect_json=False)
