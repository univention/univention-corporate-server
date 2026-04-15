# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import re

from univention.testing.helm.client.ldap import (ConnectionUri,
                                                 ConnectionUriViaConfigMap)


class TestUdmRestApiUsesLdapConnectionLdap(ConnectionUriViaConfigMap, ConnectionUri):
    """
    Verify the regular ldap client configuration in `/etc/ldap/ldap.conf`
    """
    config_map_name = "release-name-udm-rest-api-ldap-conf"

    path_ldap_conf = "data['ldap.conf']"

    def get_ldap_uri(self, result):
        """
        Special discovery required because the value is inside a generated
        configuration file.
        """
        config_map = result.get_resource(kind="ConfigMap", name=self.config_map_name)
        ldap_conf = config_map.findone(self.path_ldap_conf)
        re_match = re.search(r'^URI\s+(?P<ldap_uri>.*?)$', ldap_conf, flags=re.MULTILINE)
        return re_match.group('ldap_uri')


class TestJobUpdateUniventionObjectIdentifierUsesLdapConnection(ConnectionUri):
    workload_kind = "Job"
