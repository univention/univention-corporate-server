#!/usr/bin/python3
# vim:set fileencoding=utf-8 filetype=python tabstop=4 shiftwidth=4 expandtab:
# pylint: disable-msg=C0301,W0212,C0103,R0904

"""Unit test for univention.updater.tools"""

from __future__ import print_function

from tempfile import NamedTemporaryFile

import pytest
from lazy_object_proxy import Proxy

import univention.updater.tools as U
from mockups import ARCH, DATA, ERRAT, MAJOR, MINOR, PATCH, RJSON, gen_releases

UU = U.UniventionUpdater


@pytest.fixture
def u(http):
    """
    Mock UCS updater.
    """
    http({
        '': b'',
        '/': b'',
        RJSON: b'{"releases":[]}',
    })
    return Proxy(U.UniventionUpdater)


@pytest.fixture(autouse=True)
def log(mockopen):
    """
    Mock log file for UCS updater.
    """
    mockopen.write("/var/log/univention/updater.log", b"")


class TestUniventionUpdater(object):

    """Unit test for univention.updater.tools"""

    def test_config_repository(self, ucr, u):
        """Test setup from UCR repository/online."""
        ucr({
            'repository/online': 'no',
            'repository/online/server': 'example.net',
            'repository/online/port': '1234',
            'repository/online/prefix': 'prefix',
            'repository/online/sources': 'yes',
            'repository/online/httpmethod': 'POST',
        })
        u.config_repository()
        assert not u.online_repository
        assert u.repourl.hostname == 'example.net'
        assert u.repourl.port == 1234
        assert u.repourl.path == '/prefix/'
        assert u.sources
        assert U.UCSHttpServer.http_method == 'POST'

    def test_ucs_reinit(self, u):
        """Test reinitialization."""
        assert not u.is_repository_server
        assert ERRAT == u.erratalevel

    def test_get_releases(self, u, http):
        http({
            RJSON: gen_releases([(MAJOR, minor, patch) for minor in range(3) for patch in range(3)]),
        })
        expected = [(U.UCS_Version((MAJOR, 1, patch)), dict(major=MAJOR, minor=1, patchlevel=patch, status="maintained")) for patch in range(3)]
        found = list(u.get_releases(start=expected[0][0], end=expected[-1][0]))
        assert expected == found

    def test_get_next_version(self, u):
        """Test no next version."""
        ver = u.get_next_version(version=U.UCS_Version((MAJOR, MINOR, PATCH)))
        assert ver is None

    def test_get_next_version_PATCH(self, u, http):
        """Test next patch version."""
        http({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR, MINOR, PATCH + 1)])
        })
        ver = u.get_next_version(version=U.UCS_Version((MAJOR, MINOR, PATCH)))
        assert U.UCS_Version((MAJOR, MINOR, PATCH + 1)) == ver

    def test_get_next_version_MINOR(self, u, http):
        """Test next minor version."""
        http({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR, MINOR + 1, 0)])
        })
        ver = u.get_next_version(version=U.UCS_Version((MAJOR, MINOR, PATCH)))
        assert U.UCS_Version((MAJOR, MINOR + 1, 0)) == ver

    def test_get_next_version_MAJOR(self, u, http):
        """Test next major version."""
        http({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR + 1, 0, 0)])
        })
        ver = u.get_next_version(version=U.UCS_Version((MAJOR, MINOR, PATCH)))
        assert U.UCS_Version((MAJOR + 1, 0, 0)) == ver

    def test_get_all_available_release_updates(self, ucr, u, http):
        """Test next updates until blocked by missing current component."""
        ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/a/version': 'current',
        })
        http({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR, MINOR + 1, 0), (MAJOR + 1, 0, 0)]),
            '/%d.%d/maintained/component/%s/all/Packages.gz' % (MAJOR, MINOR + 1, 'a'): DATA,
            '/%d.%d/maintained/component/%s/amd64/Packages.gz' % (MAJOR, MINOR + 1, 'a'): DATA,
        })
        versions, components = u.get_all_available_release_updates()
        assert [U.UCS_Version((MAJOR, MINOR + 1, 0))] == versions
        assert {'a'} == components

    def test_release_update_available_NO(self, u, http):
        """Test no update available."""
        http({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR - 1, 0, 0)])
        })
        next_u = u.release_update_available()
        assert next_u is None

    def test_release_update_available_PATCH(self, u, http):
        """Test next patch-level update."""
        NEXT_u = U.UCS_Version((MAJOR, MINOR, PATCH + 1))
        http({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR, MINOR, PATCH + 1)])
        })
        next_u = u.release_update_available()
        assert NEXT_u == next_u

    def test_release_update_available_MINOR(self, u, http):
        """Test next minor update."""
        NEXT_u = U.UCS_Version((MAJOR, MINOR + 1, 0))
        http({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR, MINOR + 1, 0)])
        })
        next_u = u.release_update_available()
        assert NEXT_u == next_u

    def test_release_update_available_MAJOR(self, u, http):
        """Test next major update."""
        NEXT_u = U.UCS_Version((MAJOR + 1, 0, 0))
        http({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR + 1, 0, 0)])
        })
        next_u = u.release_update_available()
        assert NEXT_u == next_u

    def test_release_update_available_CURRENT(self, ucr, u, http):
        """Test next update block because of missing current component."""
        ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/a/version': 'current',
        })
        http({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR, MINOR + 1, 0)])
        })
        assert u.release_update_available() is None

    def test_release_update_temporary_sources_list(self, ucr, u, http):
        """Test temporary sources list for update with one enabled component."""
        ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/b': 'no',
        })
        http({
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, MINOR + 1, 'a', 'all'): DATA,
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, MINOR + 1, 'a', ARCH): DATA,
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, MINOR + 1, 'b', 'all'): DATA,
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, MINOR + 1, 'b', ARCH): DATA,
            RJSON: gen_releases([(MAJOR, MINOR, PATCH), (MAJOR, MINOR + 1, 0)])
        })
        tmp = u.release_update_temporary_sources_list(U.UCS_Version((MAJOR, MINOR + 1, 0)))
        assert {
            'deb https://updates.software-univention.de/ ucs%d%d%d main' % (MAJOR, MINOR + 1, 0, ),
            'deb https://updates.software-univention.de/%d.%d/maintained/component/ %s/%s/' % (MAJOR, MINOR + 1, 'a', 'all'),
            'deb https://updates.software-univention.de/%d.%d/maintained/component/ %s/%s/' % (MAJOR, MINOR + 1, 'a', ARCH),
        } == set(tmp)

    def test_current_version(self, u):
        """Test current version property."""
        ver = u.current_version
        assert isinstance(ver, U.UCS_Version)
        assert U.UCS_Version((3, 0, 1)) == ver

    def test_run_dist_upgrade(self, u, mockpopen):
        """Test running dist-upgrade."""
        u.run_dist_upgrade()
        cmds = mockpopen.mock_get()
        cmd = cmds[0]
        if isinstance(cmd, (list, tuple)):
            cmd = ' '.join(cmd)
        assert ' dist-upgrade' in cmd

    def test_print_component_repositories(self, ucr, http, u):
        """Test printing component repositories."""
        ucr({
            'repository/online/component/a': 'yes',
        })
        http({
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, MINOR, 'a', 'all'): DATA,
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, MINOR, 'a', ARCH): DATA,
            RJSON: gen_releases(patches=[PATCH, PATCH + 1]),
        })
        tmp = u.print_component_repositories()
        assert {
            'deb https://updates.software-univention.de/%d.%d/maintained/component/ %s/%s/' % (MAJOR, MINOR, 'a', 'all'),
            'deb https://updates.software-univention.de/%d.%d/maintained/component/ %s/%s/' % (MAJOR, MINOR, 'a', ARCH),
        } == set(tmp.splitlines())

    def test_call_sh_files(self, u, http, mockpopen):
        """Test calling preup.sh / postup.sh scripts."""
        def structs():
            """Mockups for called scripts."""
            struct_r = U.UCSRepoPool5(major=MAJOR, minor=MINOR, patchlevel=PATCH)
            preup_r = struct_r.path('preup.sh')
            postup_r = struct_r.path('postup.sh')
            struct_c = U.UCSRepoPool(major=MAJOR, minor=MINOR, part='maintained/component', patch='c', arch=ARCH)
            preup_c = struct_c.path('preup.sh')
            postup_c = struct_c.path('postup.sh')

            yield (u.server, struct_r, 'preup', preup_r, b'r_pre')
            yield (u.server, struct_r, 'postup', postup_r, b'r_post')
            yield (u.server, struct_c, 'preup', preup_c, b'c_pre')
            yield (u.server, struct_c, 'postup', postup_c, b'c_post')
        tmp = NamedTemporaryFile()

        gen = u.call_sh_files(structs(), tmp.name, 'arg')

        # The Updater only yields the intent, the content is only available after the next step
        assert ('update', 'pre') == next(gen)  # download
        assert [] == mockpopen.mock_get()
        assert ('preup', 'pre') == next(gen)  # pre
        assert [] == mockpopen.mock_get()
        assert ('preup', 'main') == next(gen)
        assert ('pre', 'arg', 'c_pre') == mockpopen.mock_get()[0][1:]
        assert ('preup', 'post') == next(gen)
        assert ('arg', 'r_pre') == mockpopen.mock_get()[0][1:]
        assert ('update', 'main') == next(gen)  # update
        assert ('post', 'arg', 'c_pre') == mockpopen.mock_get()[0][1:]
        assert ('postup', 'pre') == next(gen)  # post
        assert [] == mockpopen.mock_get()
        assert ('postup', 'main') == next(gen)
        assert ('pre', 'arg', 'c_post') == mockpopen.mock_get()[0][1:]
        assert ('postup', 'post') == next(gen)
        assert ('arg', 'r_post') == mockpopen.mock_get()[0][1:]
        assert ('update', 'post') == next(gen)
        assert ('post', 'arg', 'c_post') == mockpopen.mock_get()[0][1:]
        with pytest.raises(StopIteration):
            next(gen)
        assert [] == mockpopen.mock_get()

    def test_get_sh_files(self, u, http):
        """Test preup.sh / postup.sh download."""
        struct = U.UCSRepoPool5(major=MAJOR, minor=MINOR, patchlevel=PATCH, arch=ARCH)
        preup_path = struct.path('preup.sh')
        postup_path = struct.path('postup.sh')
        http({
            preup_path: b'#!preup_content',
            postup_path: b'#!postup_content',
            RJSON: gen_releases([(MAJOR, MINOR, PATCH)]),
        })
        repo = ((u.server, struct),)

        gen = U.UniventionUpdater.get_sh_files(repo)

        assert (u.server, struct, 'preup', preup_path, b'#!preup_content') == next(gen)
        assert (u.server, struct, 'postup', postup_path, b'#!postup_content') == next(gen)
        with pytest.raises(StopIteration):
            next(gen)

    def test_get_sh_files_bug27149(self, u, http):
        """Test preup.sh / postup.sh download for non-architecture component."""
        struct = U.UCSRepoPoolNoArch(major=MAJOR, minor=MINOR, part='maintained/component', patch='a')
        preup_path = struct.path('preup.sh')
        postup_path = struct.path('postup.sh')
        http({
            preup_path: b'#!preup_content',
            postup_path: b'#!postup_content',
            RJSON: gen_releases([(MAJOR, MINOR, PATCH)]),
        })
        repo = ((u.server, struct),)

        gen = U.UniventionUpdater.get_sh_files(repo)

        assert (u.server, struct, 'preup', preup_path, b'#!preup_content') == next(gen)
        assert (u.server, struct, 'postup', postup_path, b'#!postup_content') == next(gen)
        with pytest.raises(StopIteration):
            next(gen)


class TestComponents(object):

    def test_get_components(self, ucr, u):
        """Test enabled components."""
        ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/b': 'no',
        })
        c = {c.name for c in u.get_components()}
        assert c == {'a'}

    def test_get_components_MIRRORED(self, ucr, u):
        """Test localy mirrored components."""
        ucr({
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
        c = {c.name for c in u.get_components(only_localmirror_enabled=True)}
        assert c == {'a', 'c', 'e'}

    def test_get_current_components(self, ucr, u):
        """Test current components."""
        ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/a/version': '1.2-3',
            'repository/online/component/b': 'yes',
            'repository/online/component/c': 'yes',
            'repository/online/component/c/version': 'current',
            'repository/online/component/d': 'yes',
            'repository/online/component/d/version': '1.2-3 current',
            'repository/online/component/e': 'no',
        })
        c = {c.name for c in u.get_components(only_current=True)}
        assert c == {'c', 'd'}

    def test_get_all_components(self, ucr, u):
        """Test all defined components."""
        ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/b': 'no',
        })
        c = {c.name for c in u.get_components(all=True)}
        assert c == {'a', 'b'}

    def test_get_current_component_status_DISABLED(self, ucr, u, mockopen):
        """Test status of disabled components."""
        ucr({
            'repository/online/component/a': 'no',
        })
        mockopen.write(U.Component.FN_APTSOURCES, b"")
        assert U.Component.DISABLED == u.component('a').status()

    def test_get_current_component_status_PERMISSION(self, ucr, u, mockopen):
        """Test status of authenticated components."""
        ucr({
            'repository/online/component/d': 'yes',
        })
        mockopen.write(
            U.Component.FN_APTSOURCES,
            b'deb http://host:port/prefix/0.0/maintained/component/ d/arch/\n'
            b'# credentials not accepted: d\n')
        assert U.Component.PERMISSION_DENIED == u.component('d').status()

    def test_get_current_component_status_UNKNOWN(self, ucr, u, mockopen):
        """Test status of unknown components."""
        ucr({
            'repository/online/component/d': 'yes',
        })
        mockopen[U.Component.FN_APTSOURCES] = IOError()
        assert U.Component.UNKNOWN == u.component('d').status()

    def test_get_current_component_status_MISSING(self, ucr, u, mockopen):
        """Test status of missing components."""
        ucr({
            'repository/online/component/b': 'yes',
        })
        mockopen.write(U.Component.FN_APTSOURCES, b"")
        assert U.Component.NOT_FOUND == u.component('b').status()

    def test_get_current_component_status_OK(self, ucr, u, mockopen):
        """Test status of components."""
        ucr({
            'repository/online/component/a': 'no',
            'repository/online/component/b': 'yes',
            'repository/online/component/c': 'yes',
            'repository/online/component/d': 'yes',
        })
        mockopen.write(
            U.Component.FN_APTSOURCES,
            b'deb http://host:port/prefix/0.0/maintained/component/ c/arch/\n'
            b'deb http://host:port/prefix/0.0/unmaintained/component/ d/arch/\n')
        assert U.Component.AVAILABLE == u.component('c').status()
        assert U.Component.AVAILABLE == u.component('d').status()

    def test_get_component_defaultpackage_UNKNOWN(self, u):
        """Test default packages for unknown components."""
        assert set() == u.component('a').default_packages

    def test_get_component_defaultpackage(self, ucr, u):
        """Test default packages for components."""
        ucr({
            'repository/online/component/b/defaultpackage': 'b',
            'repository/online/component/c/defaultpackages': 'ca cb',
            'repository/online/component/d/defaultpackages': 'da,db',
        })
        assert {'b'} == u.component('b').default_packages
        assert {'ca', 'cb'} == u.component('c').default_packages
        assert {'da', 'db'} == u.component('d').default_packages

    def test_is_component_default_package_installed_UNKNOWN(self, u):
        """Test unknown default package installation."""
        assert u.component('a').defaultpackage_installed() is None

    def test_is_component_default_package_installed_MISSING(self, ucr, u):
        """Test missing default package installation."""
        ucr({
            'repository/online/component/b/defaultpackage': 'b',
        })
        assert not u.component('b').defaultpackage_installed()

    def test_is_component_default_package_installed_SINGLE(self, ucr, u, mockpopen):
        """Test single default package installation."""
        ucr({
            'repository/online/component/c/defaultpackages': 'c',
        })
        mockpopen.mock_stdout = b'Status: install ok installed\n'
        assert u.component('c').defaultpackage_installed()

    def test_is_component_default_package_installed_DOUBLE(self, ucr, u, mockpopen):
        """Test default package installation."""
        ucr({
            'repository/online/component/d/defaultpackages': 'da,db',
        })
        mockpopen.mock_stdout = b'Status: install ok installed\n' * 2
        assert u.component('d').defaultpackage_installed()

    def test_component_update_get_packages(self, u, mockpopen):
        """Test component update packages."""
        mockpopen.mock_stdout = b'Inst a [old] (new from)\nInst b (new from)\nRemv c (old PKG)\nRemv d PKG'
        installed, upgraded, removed = u.component_update_get_packages()
        assert [('b', 'new')] == installed
        assert [('a', 'old', 'new')] == upgraded
        assert [('c', 'old'), ('d', 'unknown')] == removed

    def test__get_component_baseurl_default(self, u):
        """Test getting default component configuration."""
        a_baseurl = u.component('a').baseurl()
        assert u.repourl == a_baseurl

    def test__get_component_baseurl_custom(self, ucr, u):
        """Test getting custom component configuration."""
        ucr({
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/port': '4711',
        })
        a_baseurl = u.component('a').baseurl()
        assert 'a.example.net' == a_baseurl.hostname
        assert 4711 == a_baseurl.port

    def test__get_component_baseurl_local(self, ucr, u):
        """Test getting local component configuration."""
        ucr({
            'local/repository': 'yes',
            'repository/online/server': 'a.example.net',
            'repository/online/port': '4711',
            'repository/online/component/a': 'yes',
        })
        u.ucr_reinit()
        a_baseurl = u.component('a').baseurl()
        assert 'a.example.net' == a_baseurl.hostname
        assert 4711 == a_baseurl.port

    def test__get_component_baseurl_nonlocal(self, ucr, u):
        """Test getting non local mirror component configuration."""
        ucr({
            'local/repository': 'yes',
            'repository/online/component/a': 'yes',
            'repository/online/component/a/localmirror': 'no',
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/port': '4711',
        })
        u.ucr_reinit()
        a_baseurl = u.component('a').baseurl()
        assert 'a.example.net' == a_baseurl.hostname
        assert 4711 == a_baseurl.port

    def test__get_component_baseurl_mirror(self, ucr, u):
        """Test getting mirror component configuration."""
        ucr({
            'local/repository': 'yes',
            'repository/online/component/a': 'yes',
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/port': '4711',
        })
        u.ucr_reinit()
        a_baseurl = u.component('a').baseurl(for_mirror_list=True)
        assert 'a.example.net' == a_baseurl.hostname
        assert 4711 == a_baseurl.port

    def test__get_component_baseurl_url(self, ucr, u):
        """Test getting custom component configuration."""
        ucr({
            'repository/online/component/a/server': 'https://a.example.net/',
        })
        a_baseurl = u.component('a').baseurl()
        assert 'a.example.net' == a_baseurl.hostname
        assert 443 == a_baseurl.port
        assert '/' == a_baseurl.path

    def test__get_component_server_default(self, u):
        """Test getting default component configuration."""
        a_server = u.component('a').server()
        assert u.repourl == a_server.baseurl

    def test__get_component_server_custom(self, ucr, u):
        """Test getting custom component configuration."""
        ucr({
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/port': '4711',
        })
        a_server = u.component('a').server()
        assert 'a.example.net' == a_server.baseurl.hostname
        assert 4711 == a_server.baseurl.port

    def test__get_component_server_local(self, ucr, u):
        """Test getting local component configuration."""
        ucr({
            'local/repository': 'yes',
            'repository/online/server': 'a.example.net',
            'repository/online/port': '4711',
            'repository/online/component/a': 'yes',
        })
        u.ucr_reinit()
        a_server = u.component('a').server()
        assert 'a.example.net' == a_server.baseurl.hostname
        assert 4711 == a_server.baseurl.port

    def test__get_component_server_nonlocal(self, ucr, u):
        """Test getting non local mirror component configuration."""
        ucr({
            'local/repository': 'yes',
            'repository/online/component/a': 'yes',
            'repository/online/component/a/localmirror': 'no',
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/port': '4711',
        })
        u.ucr_reinit()
        a_server = u.component('a').server()
        assert 'a.example.net' == a_server.baseurl.hostname
        assert 4711 == a_server.baseurl.port

    def test__get_component_server_mirror(self, ucr, u):
        """Test getting mirror component configuration."""
        ucr({
            'local/repository': 'yes',
            'repository/online/component/a': 'yes',
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/port': '4711',
        })
        u.ucr_reinit()
        a_server = u.component('a').server(for_mirror_list=True)
        assert 'a.example.net' == a_server.baseurl.hostname
        assert 4711 == a_server.baseurl.port

    def test__get_component_server_none(selfi, ucr, u):
        """Test getting custom component configuration."""
        ucr({
            'repository/online/component/a/server': 'a.example.net',
            'repository/online/component/a/prefix': 'none',
        })
        a_server = u.component('a').server()
        assert 'a.example.net' == a_server.baseurl.hostname
        assert '' == a_server.baseurl.path

    def test__get_component_version_short(self, ucr, u, http):
        """Test getting component versions in range from MAJOR.MINOR."""
        ucr({'repository/online/component/a/version': '%d.%d' % (MAJOR, MINOR)})
        http({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH)]),
        })
        ver = U.UCS_Version((MAJOR, MINOR, 0))
        comp_ver = u.component('a')._versions(None, None)
        assert {ver} == set(comp_ver)

    def test__get_component_version_full(self, ucr, u, http):
        """Test getting component versions in range from MAJOR.MINOR-PATCH."""
        ucr({'repository/online/component/a/version': '%d.%d-%d' % (MAJOR, MINOR, PATCH)})
        http({
            RJSON: gen_releases([(MAJOR, MINOR, PATCH)]),
        })
        comp_ver = u.component('a')._versions(None, None)
        assert set() == set(comp_ver)

    def test__get_component_version_current(self, ucr, u, http):
        """Test getting component versions in range from MAJOR.MINOR-PATCH."""
        ucr({'repository/online/component/a/version': 'current'})
        http({
            RJSON: gen_releases([(MAJOR, MINOR, 0)]),
        })
        ver = U.UCS_Version((MAJOR, MINOR, 0))  # component.erratalevel!
        comp_ver = u.component('a')._versions(start=ver, end=ver)
        assert {ver} == comp_ver

    def test__get_component_version_empty(self, ucr, u, http):
        """Test getting component empty versions in range from MAJOR.MINOR-PATCH."""
        ucr({'repository/online/component/a/version': ''})
        http({
            RJSON: gen_releases([(MAJOR, MINOR, 0)]),
        })
        ver = U.UCS_Version((MAJOR, MINOR, 0))  # component.erratalevel!
        comp_ver = u.component('a')._versions(start=ver, end=ver)
        assert {ver} == set(comp_ver)

    def test_get_component_repositories_ARCH(self, ucr, http, u):
        """
        Test component repositories with architecture sub directories.
        """
        ucr({
            'repository/online/component/a': 'yes',
        })
        http({
            '%d.%d/maintained/component/a/%s/Packages.gz' % (MAJOR, MINOR, 'all'): DATA,
            '%d.%d/maintained/component/a/%s/Packages.gz' % (MAJOR, MINOR, ARCH): DATA,
            RJSON: gen_releases(patches=[PATCH, PATCH + 1]),
        })
        ver = U.UCS_Version((MAJOR, MINOR, PATCH))
        a_repo = u.component('a').repositories(ver, ver)
        assert {
            'deb https://updates.software-univention.de/%d.%d/maintained/component/ a/%s/' % (MAJOR, MINOR, 'all'),
            'deb https://updates.software-univention.de/%d.%d/maintained/component/ a/%s/' % (MAJOR, MINOR, ARCH),
        } == set(a_repo)

    def test_get_component_repositories_NOARCH(self, ucr, http, u):
        """Test component repositories without architecture sub directories."""
        ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/a/layout': 'flat',
        })
        http({
            '%d.%d/maintained/component/a/Packages.gz' % (MAJOR, MINOR): DATA,
            RJSON: gen_releases(patches=[PATCH, PATCH + 1]),
        })
        ver = U.UCS_Version((MAJOR, MINOR, PATCH))
        a_repo = u.component('a').repositories(ver, ver)
        assert {
            'deb https://updates.software-univention.de/%d.%d/maintained/component/a/ ./' % (MAJOR, MINOR),
        } == set(a_repo)


@pytest.mark.parametrize('prefix', ["", "/p"])
def test_UCSHttpServer(prefix):
    url = U.UcsRepoUrl({"_/server": "hostname"}, "_")
    a = U.UCSHttpServer(url)
    b = U.UCSHttpServer(url + prefix)
    assert (a == b) != bool(prefix)
