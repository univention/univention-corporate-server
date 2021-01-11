#!/usr/bin/python2.7
# vim:set fileencoding=utf-8 filetype=python tabstop=4 shiftwidth=4 expandtab:
"""Unit test for univention.updater.tools"""
# pylint: disable-msg=C0301,W0212,C0103,R0904

from __future__ import print_function

import unittest
from os.path import join
from tempfile import NamedTemporaryFile, mkdtemp
from shutil import rmtree
from mockups import (
    U, MAJOR, MINOR, PATCH, ARCH, DATA, ERRAT, PART,
    MockFile, MockConfigRegistry, MockUCSHttpServer, MockPopen,
    gen_releases, verbose,
)

UU = U.UniventionUpdater
RJSON = "releases.json"


class TestUniventionUpdater(unittest.TestCase):

    """Unit test for univention.updater.tools"""

    def setUp(self):
        """Create Updater mockup."""
        MockUCSHttpServer.mock_add(RJSON, gen_releases())
        self.u = U.UniventionUpdater(check_access=False)

    def _ucr(self, variables):
        """Fill UCR mockup."""
        for key, value in variables.items():
            self.u.configRegistry[key] = value

    def _uri(self, uris):
        """Fill URI mockup."""
        for key, value in uris.items():
            MockUCSHttpServer.mock_add(key, value)
            if RJSON in key:
                self.u._get_releases()

    def tearDown(self):
        """Clean up Updater mockup."""
        del self.u
        MockConfigRegistry._EXTRA = {}
        MockUCSHttpServer.mock_reset()
        MockPopen.mock_reset()

    def test_config_repository(self):
        """Test setup from UCR repository/online."""
        self._ucr({
            'repository/online': 'no',
            'repository/online/server': 'example.net',
            'repository/online/port': '1234',
            'repository/online/prefix': 'prefix',
            'repository/online/sources': 'yes',
            'repository/online/httpmethod': 'POST',
        })
        self.u.config_repository()
        self.assertFalse(self.u.online_repository)
        self.assertEqual(self.u.repourl.hostname, 'example.net')
        self.assertEqual(self.u.repourl.port, 1234)
        self.assertEqual(self.u.repourl.path, '/prefix/')
        self.assertTrue(self.u.sources)
        self.assertEqual(U.UCSHttpServer.http_method, 'POST')

    def test_ucs_reinit(self):
        """Test reinitialization."""
        self.assertFalse(self.u.is_repository_server)
        self.assertEqual(['maintained'], self.u.parts)
        self.assertEqual(ERRAT, self.u.erratalevel)

    def test_get_releases(self):
        self._uri({
            RJSON: gen_releases([(MAJOR, minor, patch) for minor in range(3) for patch in range(3)])
        })
        expected = [(U.UCS_Version((MAJOR, 1, patch)), dict(major=MAJOR, minor=1, patchlevel=patch, status="maintained")) for patch in range(3)]
        found = list(self.u.get_releases(start=expected[0][0], end=expected[-1][0]))
        self.assertEqual(expected, found)

    def test_get_next_version(self):
        """Test no next version."""
        ver = self.u.get_next_version(version=U.UCS_Version((MAJOR, MINOR, PATCH)))
        self.assertEqual(None, ver)

    def test_get_next_version_PATCH(self):
        """Test next patch version."""
        self._uri({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR, MINOR, PATCH + 1)])
        })
        ver = self.u.get_next_version(version=U.UCS_Version((MAJOR, MINOR, PATCH)))
        self.assertEqual(U.UCS_Version((MAJOR, MINOR, PATCH + 1)), ver)

    def test_get_next_version_MINOR(self):
        """Test next minor version."""
        self._uri({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR, MINOR + 1, 0)])
        })
        ver = self.u.get_next_version(version=U.UCS_Version((MAJOR, MINOR, PATCH)))
        self.assertEqual(U.UCS_Version((MAJOR, MINOR + 1, 0)), ver)

    def test_get_next_version_MAJOR(self):
        """Test next major version."""
        self._uri({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR + 1, 0, 0)])
        })
        ver = self.u.get_next_version(version=U.UCS_Version((MAJOR, MINOR, PATCH)))
        self.assertEqual(U.UCS_Version((MAJOR + 1, 0, 0)), ver)

    def test_get_all_available_release_updates(self):
        """Test next updates until blocked by missing current component."""
        self._ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/a/version': 'current',
        })
        self._uri({
            RJSON: gen_releases([(MAJOR, MINOR + 1, 0), (MAJOR + 1, 0, 0)]),
            '%d.%d/maintained/component/%s/all/Packages.gz' % (MAJOR, MINOR + 1, 'a'): DATA,
        })
        versions, components = self.u.get_all_available_release_updates()
        self.assertEqual([U.UCS_Version((MAJOR, MINOR + 1, 0))], versions)
        self.assertEqual({'a'}, components)

    def test_release_update_available_NO(self):
        """Test no update available."""
        self._uri({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR - 1, 0, 0)])
        })
        next = self.u.release_update_available()
        self.assertEqual(None, next)

    def test_release_update_available_PATCH(self):
        """Test next patch-level update."""
        NEXT = U.UCS_Version((MAJOR, MINOR, PATCH + 1))
        self._uri({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR, MINOR, PATCH + 1)])
        })
        next = self.u.release_update_available()
        self.assertEqual(NEXT, next)

    def test_release_update_available_MINOR(self):
        """Test next minor update."""
        NEXT = U.UCS_Version((MAJOR, MINOR + 1, 0))
        self._uri({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR, MINOR + 1, 0)])
        })
        next = self.u.release_update_available()
        self.assertEqual(NEXT, next)

    def test_release_update_available_MAJOR(self):
        """Test next major update."""
        NEXT = U.UCS_Version((MAJOR + 1, 0, 0))
        self._uri({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR + 1, 0, 0)])
        })
        next = self.u.release_update_available()
        self.assertEqual(NEXT, next)

    def test_release_update_available_CURRENT(self):
        """Test next update block because of missing current component."""
        self._ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/a/version': 'current',
        })
        self._uri({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR, MINOR + 1, 0)])
        })
        self.assertRaises(U.RequiredComponentError, self.u.release_update_available, errorsto='exception')

    def test_release_update_temporary_sources_list(self):
        """Test temporary sources list for update with one enabled component."""
        self._ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/b': 'no',
        })
        self._uri({
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, MINOR + 1, 'a', 'all'): DATA,
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, MINOR + 1, 'a', ARCH): DATA,
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, MINOR + 1, 'b', 'all'): DATA,
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, MINOR + 1, 'b', ARCH): DATA,
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR, MINOR + 1, 0)])
        })
        tmp = self.u.release_update_temporary_sources_list(U.UCS_Version((MAJOR, MINOR + 1, 0)))
        self.assertEqual({
            'deb file:///mock/ ucs%d%d%d main' % (MAJOR, MINOR + 1, 0, ),
            'deb file:///mock/%d.%d/maintained/component/ %s/%s/' % (MAJOR, MINOR + 1, 'a', 'all'),
            'deb file:///mock/%d.%d/maintained/component/ %s/%s/' % (MAJOR, MINOR + 1, 'a', ARCH),
        }, set(tmp))

    def test_current_version(self):
        """Test current version property."""
        ver = self.u.current_version
        self.assertTrue(isinstance(ver, U.UCS_Version))
        self.assertEqual(U.UCS_Version((3, 0, 1)), ver)

    def test_get_components(self):
        """Test enabled components."""
        self._ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/b': 'no',
        })
        c = {c.name for c in self.u.get_components()}
        self.assertEqual(c, {'a'})

    def test_get_components_MIRRORED(self):
        """Test localy mirrored components."""
        self._ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/b': 'no',
            'repository/online/component/c': 'yes',
            'repository/online/component/c/localmirror': 'yes',
            'repository/online/component/d': 'yes',
            'repository/online/component/d/localmirror': 'no',
            'repository/online/component/e': 'no',
            'repository/online/component/e/localmirror': 'yes',
            'repository/online/component/f': 'no',
            'repository/online/component/f/localmirror': 'no',
        })
        c = {c.name for c in self.u.get_components(only_localmirror_enabled=True)}
        self.assertEqual(c, {'a', 'c', 'e'})

    def test_get_current_components(self):
        """Test current components."""
        self._ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/a/version': '1.2-3',
            'repository/online/component/b': 'yes',
            'repository/online/component/c': 'yes',
            'repository/online/component/c/version': 'current',
            'repository/online/component/d': 'yes',
            'repository/online/component/d/version': '1.2-3 current',
            'repository/online/component/e': 'no',
        })
        c = {c.name for c in self.u.get_components(only_current=True)}
        self.assertEqual(c, {'c', 'd'})

    def test_get_all_components(self):
        """Test all defined components."""
        self._ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/b': 'no',
        })
        c = {c.name for c in self.u.get_components(all=True)}
        self.assertEqual(c, {'a', 'b'})

    def test_get_current_component_status_DISABLED(self):
        """Test status of disabled components."""
        self._ucr({
            'repository/online/component/a': 'no',
        })
        ORIG = U.Component.FN_APTSOURCES
        try:
            tmp = NamedTemporaryFile()
            U.Component.FN_APTSOURCES = tmp.name
            self.assertEqual(U.Component.DISABLED, self.u.component('a').status())
        finally:
            U.Component.FN_APTSOURCES = ORIG
            tmp.close()

    def test_get_current_component_status_PERMISSION(self):
        """Test status of authenticated components."""
        self._ucr({
            'repository/online/component/d': 'yes',
        })
        ORIG = U.Component.FN_APTSOURCES
        try:
            tmp = NamedTemporaryFile()
            print('deb http://host:port/prefix/0.0/maintained/component/ d/arch/', file=tmp)
            print('# credentials not accepted: d', file=tmp)
            tmp.flush()
            U.Component.FN_APTSOURCES = tmp.name
            self.assertEqual(U.Component.PERMISSION_DENIED, self.u.component('d').status())
        finally:
            U.Component.FN_APTSOURCES = ORIG
            tmp.close()

    def test_get_current_component_status_UNKNOWN(self):
        """Test status of unknown components."""
        self._ucr({
            'repository/online/component/d': 'yes',
        })
        ORIG = U.Component.FN_APTSOURCES
        try:
            tmp = NamedTemporaryFile()
            tmp.close()
            U.Component.FN_APTSOURCES = tmp.name
            self.assertEqual(U.Component.UNKNOWN, self.u.component('d').status())
        finally:
            U.Component.FN_APTSOURCES = ORIG

    def test_get_current_component_status_MISSING(self):
        """Test status of missing components."""
        self._ucr({
            'repository/online/component/b': 'yes',
        })
        ORIG = U.Component.FN_APTSOURCES
        try:
            tmp = NamedTemporaryFile()
            U.Component.FN_APTSOURCES = tmp.name
            self.assertEqual(U.Component.NOT_FOUND, self.u.component('b').status())
        finally:
            U.Component.FN_APTSOURCES = ORIG
            tmp.close()

    def test_get_current_component_status_OK(self):
        """Test status of components."""
        self._ucr({
            'repository/online/component/a': 'no',
            'repository/online/component/b': 'yes',
            'repository/online/component/c': 'yes',
            'repository/online/component/d': 'yes',
        })
        ORIG = U.Component.FN_APTSOURCES
        try:
            tmp = NamedTemporaryFile()
            print('deb http://host:port/prefix/0.0/maintained/component/ c/arch/', file=tmp)
            print('deb http://host:port/prefix/0.0/unmaintained/component/ d/arch/', file=tmp)
            tmp.flush()
            U.Component.FN_APTSOURCES = tmp.name
            self.assertEqual(U.Component.AVAILABLE, self.u.component('c').status())
            self.assertEqual(U.Component.AVAILABLE, self.u.component('d').status())
        finally:
            U.Component.FN_APTSOURCES = ORIG
            tmp.close()

    def test_get_component_defaultpackage_UNKNOWN(self):
        """Test default packages for unknown components."""
        self.assertEqual(set(), self.u.component('a').default_packages)

    def test_get_component_defaultpackage(self):
        """Test default packages for components."""
        self._ucr({
            'repository/online/component/b/defaultpackage': 'b',
            'repository/online/component/c/defaultpackages': 'ca cb',
            'repository/online/component/d/defaultpackages': 'da,db',
        })
        self.assertEqual({'b'}, self.u.component('b').default_packages)
        self.assertEqual({'ca', 'cb'}, self.u.component('c').default_packages)
        self.assertEqual({'da', 'db'}, self.u.component('d').default_packages)

    def test_is_component_default_package_installed_UNKNOWN(self):
        """Test unknown default package installation."""
        self.assertEqual(None, self.u.component('a').defaultpackage_installed())

    def test_is_component_default_package_installed_MISSING(self):
        """Test missing default package installation."""
        self._ucr({
            'repository/online/component/b/defaultpackage': 'b',
        })
        self.assertFalse(self.u.component('b').defaultpackage_installed())

    def test_is_component_default_package_installed_SINGLE(self):
        """Test single default package installation."""
        self._ucr({
            'repository/online/component/c/defaultpackages': 'c',
        })
        MockPopen.mock_stdout = 'Status: install ok installed\n'
        self.assertTrue(self.u.component('c').defaultpackage_installed())

    def test_is_component_default_package_installed_DOUBLE(self):
        """Test default package installation."""
        self._ucr({
            'repository/online/component/d/defaultpackages': 'da,db',
        })
        MockPopen.mock_stdout = 'Status: install ok installed\n' * 2
        self.assertTrue(self.u.component('d').defaultpackage_installed())

    def test_component_update_get_packages(self):
        """Test component update packages."""
        MockPopen.mock_stdout = 'Inst a [old] (new from)\nInst b (new from)\nRemv c (old PKG)\nRemv d PKG'
        installed, upgraded, removed = self.u.component_update_get_packages()
        self.assertEqual([('b', 'new')], installed)
        self.assertEqual([('a', 'old', 'new')], upgraded)
        self.assertEqual([('c', 'old'), ('d', 'unknown')], removed)

    def test_run_dist_upgrade(self):
        """Test running dist-upgrade."""
        base_dir = mkdtemp()
        self.mock_file = MockFile(join(base_dir, 'mock'))
        __builtins__.open = self.mock_file
        try:
            _rc = self.u.run_dist_upgrade()
            cmds = MockPopen.mock_get()
            cmd = cmds[0]
            if isinstance(cmd, (list, tuple)):
                cmd = ' '.join(cmd)
            self.assertTrue(' dist-upgrade' in cmd)
        finally:
            __builtins__.open = MockFile._ORIG
            rmtree(base_dir, ignore_errors=True)

    def test__iterate_release(self):
        """Test iterating releases."""
        start = U.UCS_Version((3, 0, 0))
        end = U.UCS_Version((4, 4, 1))
        ver = U.UCSRepoPool5()
        it = self.u._iterate_release(ver, start, end)
        self.assertEqual(next(it).mmp, (3, 0, 0))
        self.assertEqual(it.send(True).mmp, (4, 0, 0))
        self.assertEqual(it.send(True).mmp, (4, 1, 0))
        self.assertEqual(it.send(True).mmp, (4, 2, 0))
        self.assertEqual(it.send(True).mmp, (4, 3, 0))
        self.assertEqual(it.send(False).mmp, (4, 3, 1))
        self.assertEqual(it.send(True).mmp, (4, 4, 0))
        self.assertEqual(it.send(False).mmp, (4, 4, 1))
        with self.assertRaises(StopIteration):
            self.assertEqual(it.next(), (4, 4, 1))

    def test__get_component_baseurl_default(self):
        """Test getting default component configuration."""
        u = self.u.component('a').baseurl()
        self.assertEqual(self.u.repourl, u)

    def test__get_component_baseurl_custom(self):
        """Test getting custom component configuration."""
        self._ucr({
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/port': '4711',
        })
        u = self.u.component('a').baseurl()
        self.assertEqual('a.example.net', u.hostname)
        self.assertEqual(4711, u.port)

    def test__get_component_baseurl_local(self):
        """Test getting local component configuration."""
        MockConfigRegistry._EXTRA = {
            'local/repository': 'yes',
            'repository/online/server': 'a.example.net',
            'repository/online/port': '4711',
            'repository/online/component/a': 'yes',
        }
        self.u.ucr_reinit()
        u = self.u.component('a').baseurl()
        self.assertEqual('a.example.net', u.hostname)
        self.assertEqual(4711, u.port)

    def test__get_component_baseurl_nonlocal(self):
        """Test getting non local mirror component configuration."""
        MockConfigRegistry._EXTRA = {
            'local/repository': 'yes',
            'repository/online/component/a': 'yes',
            'repository/online/component/a/localmirror': 'no',
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/port': '4711',
        }
        self.u.ucr_reinit()
        u = self.u.component('a').baseurl()
        self.assertEqual('a.example.net', u.hostname)
        self.assertEqual(4711, u.port)

    def test__get_component_baseurl_mirror(self):
        """Test getting mirror component configuration."""
        MockConfigRegistry._EXTRA = {
            'local/repository': 'yes',
            'repository/online/component/a': 'yes',
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/port': '4711',
        }
        self.u.ucr_reinit()
        u = self.u.component('a').baseurl(for_mirror_list=True)
        self.assertEqual('a.example.net', u.hostname)
        self.assertEqual(4711, u.port)

    def test__get_component_baseurl_url(self):
        """Test getting custom component configuration."""
        self._ucr({
            'repository/online/component/a/server': 'https://a.example.net/',
        })
        u = self.u.component('a').baseurl()
        self.assertEqual('a.example.net', u.hostname)
        self.assertEqual(443, u.port)
        self.assertEqual('/', u.path)

    def test__get_component_server_default(self):
        """Test getting default component configuration."""
        s = self.u.component('a').server()
        self.assertEqual(self.u.repourl, s.mock_url)

    def test__get_component_server_custom(self):
        """Test getting custom component configuration."""
        self._ucr({
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/port': '4711',
        })
        s = self.u.component('a').server()
        self.assertEqual('a.example.net', s.mock_url.hostname)
        self.assertEqual(4711, s.mock_url.port)

    def test__get_component_server_local(self):
        """Test getting local component configuration."""
        MockConfigRegistry._EXTRA = {
            'local/repository': 'yes',
            'repository/online/server': 'a.example.net',
            'repository/online/port': '4711',
            'repository/online/component/a': 'yes',
        }
        self.u.ucr_reinit()
        s = self.u.component('a').server()
        self.assertEqual('a.example.net', s.mock_url.hostname)
        self.assertEqual(4711, s.mock_url.port)

    def test__get_component_server_nonlocal(self):
        """Test getting non local mirror component configuration."""
        MockConfigRegistry._EXTRA = {
            'local/repository': 'yes',
            'repository/online/component/a': 'yes',
            'repository/online/component/a/localmirror': 'no',
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/port': '4711',
        }
        self.u.ucr_reinit()
        s = self.u.component('a').server()
        self.assertEqual('a.example.net', s.mock_url.hostname)
        self.assertEqual(4711, s.mock_url.port)

    def test__get_component_server_mirror(self):
        """Test getting mirror component configuration."""
        MockConfigRegistry._EXTRA = {
            'local/repository': 'yes',
            'repository/online/component/a': 'yes',
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/port': '4711',
        }
        self.u.ucr_reinit()
        s = self.u.component('a').server(for_mirror_list=True)
        self.assertEqual('a.example.net', s.mock_url.hostname)
        self.assertEqual(4711, s.mock_url.port)

    def test__get_component_server_none(self):
        """Test getting custom component configuration."""
        self._ucr({
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/prefix': 'none',
        })
        s = self.u.component('a').server()
        self.assertEqual('a.example.net', s.mock_url.hostname)
        self.assertEqual('', s.mock_url.path)
        self.assertEqual(1, len(s.mock_uris))

    def test__get_component_version_short(self):
        """Test getting component versions in range from MAJOR.MINOR."""
        self._ucr({'repository/online/component/a/version': '%d.%d' % (MAJOR, MINOR)})
        ver = U.UCS_Version((MAJOR, MINOR, 0))
        comp_ver = self.u.component('a')._versions(None, None)
        self.assertEqual({ver}, set(comp_ver))

    def test__get_component_version_full(self):
        """Test getting component versions in range from MAJOR.MINOR-PATCH."""
        self._ucr({'repository/online/component/a/version': '%d.%d-%d' % (MAJOR, MINOR, PATCH)})
        comp_ver = self.u.component('a')._versions(None, None)
        self.assertEqual(set(), set(comp_ver))

    def test__get_component_version_current(self):
        """Test getting component versions in range from MAJOR.MINOR-PATCH."""
        self._ucr({'repository/online/component/a/version': 'current'})
        ver = U.UCS_Version((MAJOR, MINOR, 0))  # component.erratalevel!
        comp_ver = self.u.component('a')._versions(start=ver, end=ver)
        self.assertEqual({ver}, comp_ver)

    def test__get_component_version_empty(self):
        """Test getting component empty versions in range from MAJOR.MINOR-PATCH."""
        self._ucr({'repository/online/component/a/version': ''})
        ver = U.UCS_Version((MAJOR, MINOR, 0))  # component.erratalevel!
        comp_ver = self.u.component('a')._versions(start=ver, end=ver)
        self.assertEqual({ver}, set(comp_ver))

    def test_get_component_repositories_ARCH(self):
        """
        Test component repositories with architecture sub directories.
        """
        self._ucr({
            'repository/online/component/a': 'yes',
        })
        self._uri({
            '%d.%d/maintained/component/a/%s/Packages.gz' % (MAJOR, MINOR, 'all'): DATA,
            '%d.%d/maintained/component/a/%s/Packages.gz' % (MAJOR, MINOR, ARCH): DATA,
            RJSON: gen_releases(patches=[PATCH, PATCH + 1])
        })
        ver = U.UCS_Version((MAJOR, MINOR, PATCH))
        r = self.u.component('a').repositories(ver, ver)
        self.assertEqual({
            'deb file:///mock/%d.%d/maintained/component/ a/%s/' % (MAJOR, MINOR, 'all'),
            'deb file:///mock/%d.%d/maintained/component/ a/%s/' % (MAJOR, MINOR, ARCH),
        }, set(r))

    def test_get_component_repositories_NOARCH(self):
        """Test component repositories without architecture sub directories."""
        self._ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/a/layout': 'flat',
        })
        self._uri({
            '%d.%d/maintained/component/a/Packages.gz' % (MAJOR, MINOR): DATA,
        })
        ver = U.UCS_Version((MAJOR, MINOR, PATCH))
        r = self.u.component('a').repositories(ver, ver)
        self.assertEqual({
            'deb file:///mock/%d.%d/maintained/component/a/ ./' % (MAJOR, MINOR),
        }, set(r))

    def test_print_component_repositories(self):
        """Test printing component repositories."""
        self._ucr({
            'repository/online/component/a': 'yes',
        })
        self._uri({
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, MINOR, 'a', 'all'): DATA,
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, MINOR, 'a', ARCH): DATA,
        })
        tmp = self.u.print_component_repositories()
        self.assertEqual({
            'deb file:///mock/%d.%d/maintained/component/ %s/%s/' % (MAJOR, MINOR, 'a', 'all'),
            'deb file:///mock/%d.%d/maintained/component/ %s/%s/' % (MAJOR, MINOR, 'a', ARCH),
        }, set(tmp.splitlines()))

    def test_call_sh_files(self):
        """Test calling preup.sh / postup.sh scripts."""
        def structs():
            """Mockups for called scripts."""
            server = MockUCSHttpServer('server')
            struct_r = U.UCSRepoPool5(major=MAJOR, minor=MINOR, patchlevel=PATCH)
            preup_r = struct_r.path('preup.sh')
            postup_r = struct_r.path('postup.sh')
            struct_c = U.UCSRepoPool(major=MAJOR, minor=MINOR, part='%s/component' % (PART,), patch='c', arch=ARCH)
            preup_c = struct_c.path('preup.sh')
            postup_c = struct_c.path('postup.sh')

            yield (server, struct_r, 'preup', preup_r, 'r_pre')
            yield (server, struct_r, 'postup', postup_r, 'r_post')
            yield (server, struct_c, 'preup', preup_c, 'c_pre')
            yield (server, struct_c, 'postup', postup_c, 'c_post')
        tmp = NamedTemporaryFile()

        gen = self.u.call_sh_files(structs(), tmp.name, 'arg')

        # The Updater only yields the intent, the content is only available after the next step
        self.assertEqual(('update', 'pre'), gen.next())  # download
        self.assertEqual([], MockPopen.mock_get())
        self.assertEqual(('preup', 'pre'), gen.next())  # pre
        self.assertEqual([], MockPopen.mock_get())
        self.assertEqual(('preup', 'main'), gen.next())
        self.assertEqual(('pre', 'arg', 'c_pre'), MockPopen.mock_get()[0][1:])
        self.assertEqual(('preup', 'post'), gen.next())
        self.assertEqual(('arg', 'r_pre'), MockPopen.mock_get()[0][1:])
        self.assertEqual(('update', 'main'), gen.next())  # update
        self.assertEqual(('post', 'arg', 'c_pre'), MockPopen.mock_get()[0][1:])
        self.assertEqual(('postup', 'pre'), gen.next())  # post
        self.assertEqual([], MockPopen.mock_get())
        self.assertEqual(('postup', 'main'), gen.next())
        self.assertEqual(('pre', 'arg', 'c_post'), MockPopen.mock_get()[0][1:])
        self.assertEqual(('postup', 'post'), gen.next())
        self.assertEqual(('arg', 'r_post'), MockPopen.mock_get()[0][1:])
        self.assertEqual(('update', 'post'), gen.next())
        self.assertEqual(('post', 'arg', 'c_post'), MockPopen.mock_get()[0][1:])
        self.assertRaises(StopIteration, gen.next)  # done
        self.assertEqual([], MockPopen.mock_get())

    def test_get_sh_files(self):
        """Test preup.sh / postup.sh download."""
        server = MockUCSHttpServer('server')
        struct = U.UCSRepoPool5(major=MAJOR, minor=MINOR, part=PART, patchlevel=PATCH, arch=ARCH)
        preup_path = struct.path('preup.sh')
        server.mock_add(preup_path, b'#!preup_content')
        postup_path = struct.path('postup.sh')
        server.mock_add(postup_path, b'#!postup_content')
        repo = ((server, struct),)

        gen = U.UniventionUpdater.get_sh_files(repo)

        self.assertEqual((server, struct, 'preup', preup_path, '#!preup_content'), gen.next())
        self.assertEqual((server, struct, 'postup', postup_path, '#!postup_content'), gen.next())
        self.assertRaises(StopIteration, gen.next)

    def test_get_sh_files_bug27149(self):
        """Test preup.sh / postup.sh download for non-architecture component."""
        server = MockUCSHttpServer('server')
        struct = U.UCSRepoPoolNoArch(major=MAJOR, minor=MINOR, part='%s/component' % (PART,), patch='a')
        preup_path = struct.path('preup.sh')
        server.mock_add(preup_path, b'#!preup_content')
        postup_path = struct.path('postup.sh')
        server.mock_add(postup_path, b'#!postup_content')
        repo = ((server, struct),)

        gen = U.UniventionUpdater.get_sh_files(repo)

        self.assertEqual((server, struct, 'preup', preup_path, '#!preup_content'), gen.next())
        self.assertEqual((server, struct, 'postup', postup_path, '#!postup_content'), gen.next())
        self.assertRaises(StopIteration, gen.next)


if __name__ == '__main__':
    verbose()
    unittest.main()
