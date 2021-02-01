#!/usr/bin/python3
# vim:set fileencoding=utf-8 filetype=python tabstop=4 shiftwidth=4 expandtab:
# pylint: disable-msg=C0301,W0212,C0103,R0904

"""Unit test for univention.updater.mirror"""

import json
from copy import deepcopy
from os.path import join

import pytest
from lazy_object_proxy import Proxy

import univention.updater.mirror as M
from mockups import ARCH, DATA, MAJOR, MINOR, RJSON, gen_releases
from univention.lib.ucs import UCS_Version

UM = M.UniventionMirror


@pytest.fixture
def m(tmpdir, ucr, http):
    """
    Mock UCS repository mirror.
    """
    ucr({
        'repository/mirror/basepath': str(tmpdir / 'repo'),
        # 'repository/mirror/version/end': '%d.%d-%d' % (MAJOR, MINOR, PATCH),
        # 'repository/mirror/version/start': '%d.%d-%d' % (MAJOR, 0, 0),
        'repository/mirror/verify': 'no',
    })
    http({
        # 'univention-repository/': '',
        '': b'',
        '/': b'',
        RJSON: b'{"releases":[]}',
    })
    return Proxy(M.UniventionMirror)


@pytest.fixture(autouse=True)
def log(mockopen):
    """
    Mock log file for UCS repository mirror.
    """
    mockopen.write("/var/log/univention/repository.log", b"")


class TestUniventionMirror(object):

    """Unit test for univention.updater.mirror"""

    def test_config_repository(self, ucr, m):
        """Test setup from UCR repository/mirror."""
        ucr({
            'repository/mirror': 'no',
            'repository/mirror/server': 'example.net',
            'repository/mirror/port': '1234',
            'repository/mirror/prefix': 'prefix',
            'repository/mirror/sources': 'yes',
            'repository/mirror/httpmethod': 'POST',
            'repository/mirror/verify': 'yes',
        })
        m.config_repository()
        assert not m.online_repository
        assert m.repourl.hostname == 'example.net'
        assert m.repourl.port == 1234
        assert m.repourl.path == '/prefix/'
        assert m.sources
        assert m.http_method == 'POST'
        assert m.script_verify

    # TODO: Copy over test_updater

    def test_mirror_repositories(self, tmpdir, mocker, m):
        """Test mirror structure and apt-mirror called."""
        popen = mocker.patch("subprocess.Popen")
        m.mirror_repositories()
        assert (tmpdir / "repo" / "var").check(dir=1)
        assert (tmpdir / "repo" / "skel").check(dir=1)
        assert (tmpdir / "repo" / "mirror").check(dir=1)
        assert (tmpdir / "repo" / "mirror" / "univention-repository").check(link=1)
        assert "apt-mirror" in popen.call_args_list[0][0][0][0]

    def test_mirror_update_scripts(self, tmpdir, ucr, http, m):
        ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/b': 'yes',
            'repository/online/component/b/layout': 'flat',
            'repository/mirror/version/start': '%d.%d-%d' % (MAJOR, 0, 0),
            'repository/mirror/version/end': '%d.%d-%d' % (MAJOR, 0, 0),
        })
        uris = {
            '/dists/ucs%d%d%d/preup.sh' % (MAJOR, MINOR, 0, ): b'#!r_pre',
            '/dists/ucs%d%d%d/postup.sh' % (MAJOR, MINOR, 0, ): b'#!r_post',
            '/dists/ucs%d%d%d/main/binary-%s/Packages.gz' % (MAJOR, MINOR, 0, ARCH): DATA,
            '/%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, 0, 'a', 'all'): DATA,
            '/%d.%d/maintained/component/%s/%s/preup.sh' % (MAJOR, 0, 'a', 'all'): b'#!a_pre',
            '/%d.%d/maintained/component/%s/%s/postup.sh' % (MAJOR, 0, 'a', 'all'): b'#!a_post',
            '/%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, 0, 'a', ARCH): DATA,
            '/%d.%d/maintained/component/%s/Packages.gz' % (MAJOR, 0, 'b'): DATA,
            '/%d.%d/maintained/component/%s/preup.sh' % (MAJOR, 0, 'b'): b'#!b_pre',
            '/%d.%d/maintained/component/%s/postup.sh' % (MAJOR, 0, 'b'): b'#!b_post',
            RJSON: gen_releases([(MAJOR, MINOR, 0), ])
        }
        http(uris)
        m._get_releases()
        del uris[RJSON]
        m.mirror_update_scripts()
        for key, value in uris.items():
            if value == DATA:
                continue
            # "base_dir+mock" for the mock_open redirector
            # "base_dir+repo+mirror" as the configured repository_root
            # "mock+key" from the remote host prefix and struct
            filename = tmpdir / "repo" / 'mirror' / key
            assert filename.read_binary() == value

    def test_write_releases_json(self, tmpdir, http, m):
        releases = gen_releases([(MAJOR, MINOR, 0), (MAJOR, MINOR, 1)])
        http({RJSON: releases})
        m.write_releases_json()
        releases_json = tmpdir / 'repo' / 'mirror' / 'releases.json'
        assert json.loads(releases_json.read()) == json.loads(releases)

    def test_run(self, mocker, m):
        """Test full mirror run."""
        mirror_repositories = mocker.patch.object(M.UniventionMirror, "mirror_repositories")
        mirror_update_scripts = mocker.patch.object(M.UniventionMirror, "mirror_update_scripts")
        write_releases_json = mocker.patch.object(M.UniventionMirror, "write_releases_json")
        m.run()
        mirror_repositories.assert_called_once_with()
        mirror_update_scripts.assert_called_once_with()
        write_releases_json.assert_called_once_with()


class TestFilter(object):

    """Unit test for univention.updater.mirror.filter_releases_json"""

    RELEASES = json.loads(gen_releases([(5, 0, 0), (5, 0, 1), (5, 0, 2)]))
    VER4, VER5, VER6 = (UCS_Version((major, 0, 0)) for major in [4, 5, 6])

    def test_filter_releases_json(self, testdir):
        with open(join(testdir, 'mockup_upstream_releases.json'), 'r') as upstream_releases_fp:
            upstream_releases = json.load(upstream_releases_fp)
        with open(join(testdir, 'mockup_mirror_releases.json'), 'r') as mirror_releases_fp:
            expected_mirror_releases = json.load(mirror_releases_fp)

        mirrored_releases = deepcopy(upstream_releases)
        M.filter_releases_json(mirrored_releases, start=UCS_Version((3, 1, 1)), end=UCS_Version((4, 1, 0)))
        assert mirrored_releases == expected_mirror_releases

    def test_unchanged(self):
        data = deepcopy(self.RELEASES)
        M.filter_releases_json(data, start=self.VER4, end=self.VER6)
        assert data == self.RELEASES

    def test_same(self):
        data = deepcopy(self.RELEASES)
        M.filter_releases_json(data, start=self.VER5, end=UCS_Version((5, 0, 2)))
        assert data == self.RELEASES

    def test_before(self):
        data = deepcopy(self.RELEASES)
        M.filter_releases_json(data, start=self.VER4, end=self.VER4)
        assert data == {"releases": []}

    def test_after(self):
        data = deepcopy(self.RELEASES)
        M.filter_releases_json(data, start=self.VER6, end=self.VER6)
        assert data == {"releases": []}

    def test_empty(self):
        data = deepcopy(self.RELEASES)
        M.filter_releases_json(data, start=UCS_Version((5, 0, 3)), end=self.VER6)
        assert data == {"releases": []}
