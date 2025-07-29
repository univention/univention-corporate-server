#!/usr/bin/python2.7
#
# Python VNC automate
#
# SPDX-FileCopyrightText: 2016-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


class Config:
    # All information that is relevant for an UCS-installation is stored
    # in here.
    # E.g.: IP address of the VM, DNS server, additional apps to install,
    # update after installation (bool), ...
    def __init__(
            self, ip, role='master', language='en', password="univention",
            update_ucs_after_install=True, dns_server_ip="",
            use_multiple_partitions=False, install_all_additional_components=False,
            ldap_base="dc=mydomain,dc=test",
    ):
        self.ip = ip
        self.role = role
        # Use an ISO 639-1 language code here:
        self.language = language
        self.password = password
        self.update_ucs_after_install = update_ucs_after_install
        self.dns_server_ip = dns_server_ip
        self.use_multiple_partitions = use_multiple_partitions
        self.install_all_additional_components = install_all_additional_components
        self.ldap_base = ldap_base
