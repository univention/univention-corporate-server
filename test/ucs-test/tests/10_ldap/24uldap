#!/usr/share/ucs-test/runner python3
## desc: test all univention.uldap methods
## bugs: [40041]
## versions:
##  4.1-2: fixed
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
##  - domaincontroller_slave
##  - memberserver
## exposure: careful

from os import environ
from os.path import exists
from tempfile import NamedTemporaryFile

import ldap
from unittest import TestCase, main, skip, skipUnless

from univention import uldap
from univention.config_registry import ConfigRegistry
from univention.testing.utils import retry_on_error


ucr = ConfigRegistry()
ucr.load()


class FakeUcr:

    def __init__(self, values, defaults=True):
        self.values = dict(ucr.items()) if defaults else {}
        self.values.update(values)
        self.tmp = None

    def __enter__(self):
        self.tmp = NamedTemporaryFile()
        self.tmp.write(b'# univention_ base.conf\n\n')
        for key, value in self.values.items():
            self.tmp.write(f'\n{key}: {value}'.encode())
        self.tmp.flush()
        environ['UNIVENTION_BASECONF'] = self.tmp.name

    def __exit__(self, exc_type, exc_value, traceback):
        self.tmp.close()
        self.tmp = None
        del environ['UNIVENTION_BASECONF']


class TestParentDn(TestCase):

    def testBase(self):
        assert uldap.parentDn('dc=de', 'dc=de') is None

    def testOne(self):
        # Before r70653 Bug #40129 returned None
        assert uldap.parentDn('dc=de') == ''

    def testTwo(self):
        assert uldap.parentDn('dc=univention,dc=de') == 'dc=de'

    def testMultivalued(self):
        assert uldap.parentDn('a=1+b=2,dc=de') == 'dc=de'


class TestExplodeDn(TestCase):

    def testOne(self):
        assert uldap.explodeDn('dc=de') == ['dc=de']

    def testTwo(self):
        assert uldap.explodeDn('dc=univention,dc=de') == ['dc=univention', 'dc=de']

    def testMultivalued(self):
        assert uldap.explodeDn('a=1+b=2,dc=de') == ['a=1+b=2', 'dc=de']


@skipUnless(exists('/etc/ldap.secret'), 'Missing ldap.secret')
class TestAdminConnection(TestCase):

    def testDefault(self):
        access = uldap.getAdminConnection()
        assert isinstance(access, uldap.access)

    def testLocalhost(self):
        with FakeUcr({'ldap/master': 'localhost'}):
            access = uldap.getAdminConnection(reconnect=False)
            assert isinstance(access, uldap.access) is True


@skipUnless(exists('/etc/ldap-backup.secret'), 'Missing ldap-backup.secret')
class TestBackupConnection(TestCase):

    def testDefault(self):
        access = uldap.getBackupConnection()
        assert isinstance(access, uldap.access)

    def testServerDown(self):
        with FakeUcr({'ldap/master': '255.255.255.255', 'ldap/backup': ''}):
            self.assertRaises(ldap.SERVER_DOWN, uldap.getMachineConnection, reconnect=False)


@skipUnless(exists('/etc/machine.secret'), 'Missing machine.secret')
class TestMachineConnection(TestCase):

    def testDefault(self):
        access = uldap.getMachineConnection()
        assert isinstance(access, uldap.access)
        assert access.host == ucr.get('ldap/master')

    def testNonMaster(self):
        access = uldap.getMachineConnection(ldap_master=False, reconnect=False)
        assert isinstance(access, uldap.access)
        assert access.host == ucr.get('ldap/server/name')

    def testAdditionDefaultDown(self):
        with FakeUcr({'ldap/server/name': '255.255.255.255', 'ldap/server/addition': ucr.get('ldap/server/name')}):
            ucr_fake = ConfigRegistry()
            ucr_fake.load()
            access = uldap.getMachineConnection(ldap_master=False, reconnect=False)
            assert isinstance(access, uldap.access)
            assert access.host == ucr_fake.get('ldap/server/addition')

    def testAdditionDefaultUp(self):
        alt_servers = [f'127.0.0.{i}' for i in range(1, 200)]
        with FakeUcr({'ldap/server/addition': ' '.join(alt_servers)}):
            ucr_fake = ConfigRegistry()
            ucr_fake.load()
            access = uldap.getMachineConnection(ldap_master=False, reconnect=False, start_tls=0)
            assert isinstance(access, uldap.access)
            assert access.host == ucr_fake.get('ldap/server/name')

    @skipUnless(exists('/var/run/slapd/ldapi'), 'Missing local LDAP server')
    def testRandomServer(self):
        def __testRandomServer():
            for role in ('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave'):
                # test first server
                alt_servers = [f'127.0.0.{i}' for i in range(1, 200)]
                with FakeUcr({'server/role': role, 'ldap/server/addition': ' '.join(alt_servers)}):
                    ucr_fake = ConfigRegistry()
                    ucr_fake.load()
                    for _ in range(0, 10):
                        access = uldap.getMachineConnection(ldap_master=False, reconnect=False, start_tls=0, random_server=True)
                        assert isinstance(access, uldap.access)
                        assert access.host in [ucr_fake.get('ldap/server/name')]  # on DC systems, the local system is used first

                # test other servers
                alt_servers = [f'127.0.0.{i}' for i in range(1, 200)]
                with FakeUcr({'server/role': role, 'ldap/server/name': 'does.not.exist', 'ldap/server/addition': ' '.join(alt_servers)}):
                    ucr_fake = ConfigRegistry()
                    ucr_fake.load()
                    used_servers = []
                    n = 10
                    for _ in range(0, n):
                        access = uldap.getMachineConnection(ldap_master=False, reconnect=False, start_tls=0, random_server=True)
                        assert isinstance(access, uldap.access)
                        assert access.host in alt_servers  # only servers of ldap/server/addition should be returned, if ldap/server/name is not available
                        used_servers.append(access.host)
                    # Servers should be in random order
                    assert ''.join(used_servers) not in ''.join(alt_servers)

            # test memberserver
            alt_servers = [f'127.0.0.{i}' for i in range(1, 20)]
            with FakeUcr({'server/role': 'memberserver', 'ldap/server/name': 'does.not.exist', 'ldap/server/addition': ' '.join(alt_servers)}):
                ucr_fake = ConfigRegistry()
                ucr_fake.load()
                possible_servers = [ucr_fake.get('ldap/server/name')] + alt_servers
                used_servers = []
                n = 10
                min_servers = 3
                for _ in range(0, n):
                    access = uldap.getMachineConnection(ldap_master=False, reconnect=False, start_tls=0, random_server=True)
                    assert isinstance(access, uldap.access)
                    assert access.host in possible_servers
                    used_servers.append(access.host)
                # At least (min_servers - 1) different servers from ldap/server/addition
                assert len(set(used_servers)) >= min_servers
                # Servers should be in random order
                assert ''.join(used_servers) not in ''.join(possible_servers)

        retry_on_error(__testRandomServer, exceptions=(AssertionError, ), retry_count=10, delay=0)

    @skipUnless(exists('/var/run/slapd/ldapi'), 'Missing local LDAP server')
    def testNonRandomServer(self):
        expected_server = '127.1.1.1'
        alt_servers = ['255.255.255.255'] * 2 + [expected_server] + [f'127.0.0.{i}' for i in range(1, 200)]
        with FakeUcr({'ldap/server/name': '255.255.255.255', 'ldap/server/addition': ' '.join(alt_servers)}):
            ucr_fake = ConfigRegistry()
            ucr_fake.load()
            possible_servers = [ucr_fake.get('ldap/server/name')] + alt_servers
            used_servers = []
            n = 10
            for _ in range(0, n):
                access = uldap.getMachineConnection(ldap_master=False, reconnect=False, start_tls=0)
                assert isinstance(access, uldap.access)
                assert access.host in possible_servers
                used_servers.append(access.host)
            # Should always be expected_server
            assert len(set(used_servers)) >= 1
            assert expected_server == used_servers[0]

    def testServerDown(self):
        with FakeUcr({'ldap/server/name': '255.255.255.255', 'ldap/server/addition': ''}):
            self.assertRaises(ldap.SERVER_DOWN, uldap.getMachineConnection, ldap_master=False, reconnect=False)


@skipUnless(exists('/var/run/slapd/ldapi'), 'Missing local LDAP server')
class TestAccess(TestCase):

    def testDefault(self):
        access = uldap.access()
        assert isinstance(access, uldap.access)

    def testIPv6(self):
        access = uldap.access(host='ip6-localhost', start_tls=0)
        assert access.uri == 'ldap://ip6-localhost:7389'

    def testPort(self):
        access = uldap.access(port=7389)
        assert access.uri == 'ldap://localhost:7389'

    def testLdaps(self):
        access = uldap.access(use_ldaps=True)
        assert access.uri == 'ldaps://localhost:7636'

    def testUri(self):
        access = uldap.access(uri='ldapi:///')
        assert access.uri == 'ldapi:///'


@skipUnless(exists('/var/run/slapd/ldapi'), 'Missing local LDAP server')
class TestAccessUsage(TestCase):

    def setUp(self):
        self.uut = uldap.access()

    def testGet(self):
        result = self.uut.get('cn=Subschema', ['entryDN'], required=True)
        assert result == {'entryDN': [b'cn=Subschema']}

    def testGetAttr(self):
        result = self.uut.getAttr('cn=Subschema', 'entryDN', required=True)
        assert result == [b'cn=Subschema']

    def testSearch(self):
        result = self.uut.search(
            base='',
            scope='base',
            attr=['subschemaSubentry'],
            unique=True,
            required=True,
        )
        assert result == [('', {'subschemaSubentry': [b'cn=Subschema']})]

    def testSearchDn(self):
        result = self.uut.searchDn(
            base='',
            scope='base',
            unique=True,
            required=True,
        )
        assert result == ['']

    @skip('TODO')
    def testGetPolicies(self):
        self.uut.getPolicies()

    def testGetSchema(self):
        result = self.uut.get_schema()
        assert isinstance(result, ldap.schema.subentry.SubSchema)

    @skip('TODO')
    def testAdd(self):
        self.uut.add()

    @skip('TODO')
    def testModify(self):
        self.uut.modify()

    @skip('TODO')
    def testModifyS(self):
        self.uut.modify_s()

    @skip('TODO')
    def testRename(self):
        self.uut.rename()

    @skip('TODO')
    def testDelete(self):
        self.uut.delete()


if __name__ == '__main__':
    main()
