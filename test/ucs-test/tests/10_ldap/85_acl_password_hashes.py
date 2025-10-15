#!/usr/share/ucs-test/runner python3
## desc: Member servers must no be able to access password hashes
## roles:
##  - memberserver
## exposure: careful
## bugs:
##  - 56796

from univention import uldap


ATTRIBUTES_WITH_HASHES = {'krb5Key', 'pwhistory', 'userPassword', 'sambaNTPassword', 'sambaLMPassword', 'sambaPasswordHistory'}


def test_memberserver_cannot_access_password_hashes():
    """A member server should never be able to read password hashes."""
    lo = uldap.getMachineConnection(ldap_master=True)
    search_results = lo.search('|((uid=Administrator)(univentionServerRole=master)(univentionServerRole=backup)(univentionServerRole=slave))')
    search_results.extend(lo.search('(|(objectClass=person)(objectClass=krb5Principal)(objectClass=univentionHost))', sizelimit=500))
    for result in search_results:
        attributes = set(result[1].keys())
        assert attributes.intersection(ATTRIBUTES_WITH_HASHES) == set(), f'Memberserver has access to password hashes of {result[0]}'
