#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""help tools for the containers"""

from univention.admin import _ldap_cache


@_ldap_cache(ttl=2)
def default_container_for_objects(lo, domain):
    pathResult = lo.authz_connection.get('cn=directory,cn=univention,' + domain)
    default_dn = 'cn=directory,cn=univention,' + domain
    if not pathResult:
        pathResult = lo.authz_connection.get('cn=default containers,cn=univention,' + domain)
        default_dn = 'cn=default containers,cn=univention,' + domain
    return (pathResult, default_dn)


__path__ = __import__('pkgutil').extend_path(__path__, __name__)  # type: ignore
