# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import pytest
from univention.testing.helm.auth_flavors.password_usage import (
    AuthPasswordUsageViaEnv, AuthPasswordUsageViaVolume)
from univention.testing.helm.auth_flavors.secret_generation import \
    AuthSecretGenerationUser
from univention.testing.helm.auth_flavors.username import (
    AuthUsernameViaConfigMap, AuthUsernameViaEnv)


class SettingsTestLdapSecret:
    secret_name = "release-name-udm-rest-api-ldap"
    prefix_mapping = {
        "auth.bindDn": "auth.username",
        "ldap.auth": "auth",
    }

class TestChartCreatesLdapSecretAsUser(SettingsTestLdapSecret, AuthSecretGenerationUser):
    pass

class TestUdmRestApiUsesLdapCredentialsByVolume(SettingsTestLdapSecret, AuthPasswordUsageViaVolume):
    volume_name = "secret-ldap"
    workload_name = "release-name-udm-rest-api"

class TestCronJobBlocklistCleanupUsesLdapCredentialsByVolume(SettingsTestLdapSecret, AuthPasswordUsageViaVolume):
    volume_name = "secret-ldap"
    workload_name = "release-name-udm-rest-api-blocklist-cleanup"
    workload_kind = "CronJob"

class TestCronJobBlocklistCleanupUsesLdapUserByConfigMap(SettingsTestLdapSecret, AuthUsernameViaConfigMap):
    config_map_name = "release-name-udm-rest-api"
    path_username = "data.UDM_API_USER"
    default_username = "cn=admin"

    @pytest.mark.skip("The username is currently hardcoded in the ConfigMap")
    def test_auth_plain_values_provide_username(self, chart): ...

    @pytest.mark.skip("The username is currently hardcoded in the ConfigMap")
    def test_auth_plain_values_username_is_templated(self, chart): ...

    def test_username_is_fixed(self, chart):
        result = chart.helm_template()
        config_map = result.get_resource(kind="ConfigMap", name=self.config_map_name)
        username = config_map.findone(self.path_username)
        assert username == "cn=admin"

class TestJobUpdateUniventionObjectIdentifierInitContainerUsesLdapCredentialsByVolume_WaitForLdap(SettingsTestLdapSecret, AuthPasswordUsageViaVolume):
    volume_name = "secret-ldap"
    workload_name = "release-name-udm-rest-api-1-update-univention-object-identifier"
    workload_kind = "Job"
    path_container = "..spec.template.spec.initContainers[?@.name=='wait-for-ldap']"

class TestJobUpdateUniventionObjectIdentifierUsesLdapCredentialsByEnv(SettingsTestLdapSecret, AuthPasswordUsageViaEnv):
    workload_name = "release-name-udm-rest-api-1-update-univention-object-identifier"
    workload_kind = "Job"
    sub_path_env_password = "env[?@name=='LDAP_ADMIN_PASSWORD']"

class TestJobUpdateUniventionObjectIdentifierUsesLdapUserByEnv(SettingsTestLdapSecret, AuthUsernameViaEnv):
    workload_name = "release-name-udm-rest-api-1-update-univention-object-identifier"
    workload_kind = "Job"
    sub_path_env_username = "env[?@name=='LDAP_ADMIN_USER']"
    default_username = "cn=admin,dc=univention-organization,dc=intranet"
    default_username = "cn=admin,dc=univention-organization,dc=intranet"
