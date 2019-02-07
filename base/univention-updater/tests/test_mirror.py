#!/usr/bin/python2.7
# vim:set fileencoding=utf-8 filetype=python tabstop=4 shiftwidth=4 expandtab:
"""Unit test for univention.updater.mirror"""
# pylint: disable-msg=C0301,W0212,C0103,R0904
import os
import unittest
from tempfile import mkdtemp
from shutil import rmtree
from mockups import (
    U, M, MAJOR, MINOR, PATCH, ARCH,
    MockFile, MockConfigRegistry, MockUCSHttpServer, MockPopen,
)

UM = M.UniventionMirror
DATA = 'x' * U.MIN_GZIP


class TestUniventionMirror(unittest.TestCase):

    """Unit test for univention.updater.tools"""

    def setUp(self):
        """Create Mirror mockup."""
        self._uri({
            # 'univention-repository/': '',
            '': '',
            '/': '',
        })
        self.base_dir = mkdtemp()
        self.mock_file = MockFile(os.path.join(self.base_dir, 'mock'))
        __builtins__.open = self.mock_file
        MockConfigRegistry._EXTRA = {
            'repository/mirror/basepath': os.path.join(self.base_dir, 'repo'),
            # 'repository/mirror/version/end': '%d.%d-%d' % (MAJOR, MINOR, PATCH),
            # 'repository/mirror/version/start': '%d.%d-%d' % (MAJOR, 0, 0),
            'repository/mirror/architectures': ' '.join(ARCH),
            'repository/mirror/verify': 'no',
        }
        self.m = M.UniventionMirror()

    def _ucr(self, variables):
        """Fill UCR mockup."""
        for key, value in variables.items():
            self.m.configRegistry[key] = value

    def _uri(self, uris):
        """Fill URI mockup."""
        for key, value in uris.items():
            MockUCSHttpServer.mock_add(key, value)

    def tearDown(self):
        """Clean up Mirror mockup."""
        __builtins__.open = MockFile._ORIG
        rmtree(self.base_dir, ignore_errors=True)
        del self.base_dir
        del self.m
        MockConfigRegistry._EXTRA = {}
        MockUCSHttpServer.mock_reset()
        MockPopen.mock_reset()

    def test_config_repository(self):
        """Test setup from UCR repository/mirror."""
        self._ucr({
            'repository/mirror': 'no',
            'repository/mirror/server': 'example.net',
            'repository/mirror/port': '1234',
            'repository/mirror/prefix': 'prefix',
            'repository/mirror/sources': 'yes',
            'repository/mirror/httpmethod': 'POST',
            'repository/mirror/verify': 'yes',
        })
        self.m.config_repository()
        self.assertFalse(self.m.online_repository)
        self.assertEqual(self.m.repourl.hostname, 'example.net')
        self.assertEqual(self.m.repourl.port, 1234)
        self.assertEqual(self.m.repourl.path, '/prefix/')
        self.assertTrue(self.m.sources)
        self.assertEqual(self.m.http_method, 'POST')
        self.assertTrue(self.m.script_verify)

    # TODO: Copy over test_updater

    def test_mirror_repositories(self):
        """Test mirror structure and apt-mirror called."""
        self.mock_file.mock_whitelist.add('/var/log/univention')
        self.m.mirror_repositories()
        self.assertTrue(os.path.isdir(os.path.join(self.base_dir, 'repo', 'var')))
        self.assertTrue(os.path.isdir(os.path.join(self.base_dir, 'repo', 'skel')))
        self.assertTrue(os.path.isdir(os.path.join(self.base_dir, 'repo', 'mirror')))
        self.assertTrue(os.path.islink(os.path.join(self.base_dir, 'repo', 'mirror', 'univention-repository')))
        cmds = MockPopen.mock_get()
        cmd = cmds[0]
        if isinstance(cmd, (list, tuple)):
            cmd = cmd[0]
        self.assertTrue('apt-mirror' in cmd)

    def test_mirror_update_scripts(self):
        self._ucr({
            'repository/online/component/a': 'yes',
            'repository/online/component/b': 'yes',
            'repository/mirror/version/start': '%d.%d-%d' % (MAJOR, 0, 0),
            'repository/mirror/version/end': '%d.%d-%d' % (MAJOR, 0, 0),
        })
        uris = {
            '%d.%d/maintained/%d.%d-%d/%s/Packages.gz' % (MAJOR, 0, MAJOR, 0, 0, 'all'): DATA,
            '%d.%d/maintained/%d.%d-%d/%s/preup.sh' % (MAJOR, 0, MAJOR, 0, 0, 'all'): '#!r_pre',
            '%d.%d/maintained/%d.%d-%d/%s/postup.sh' % (MAJOR, 0, MAJOR, 0, 0, 'all'): '#!r_post',
            '%d.%d/maintained/%d.%d-%d/%s/Packages.gz' % (MAJOR, 0, MAJOR, 0, 0, ARCH): DATA,
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, 0, 'a', 'all'): DATA,
            '%d.%d/maintained/component/%s/%s/preup.sh' % (MAJOR, 0, 'a', 'all'): '#!a_pre',
            '%d.%d/maintained/component/%s/%s/postup.sh' % (MAJOR, 0, 'a', 'all'): '#!a_post',
            '%d.%d/maintained/component/%s/%s/Packages.gz' % (MAJOR, 0, 'a', ARCH): DATA,
            '%d.%d/maintained/component/%s/Packages.gz' % (MAJOR, 0, 'b'): DATA,
            '%d.%d/maintained/component/%s/Packages.gz' % (MAJOR, 0, 'b'): DATA,
            '%d.%d/maintained/component/%s/preup.sh' % (MAJOR, 0, 'b'): '#!b_pre',
            '%d.%d/maintained/component/%s/postup.sh' % (MAJOR, 0, 'b'): '#!b_post',
        }
        self._uri(uris)
        self.m.mirror_update_scripts()
        for key, value in uris.items():
            if not value != DATA:
                continue
            # "base_dir+mock" for the mock_open redirector
            # "base_dir+repo+mirror" as the configured repository_root
            # "mock+key" from the remote host prefix and struct
            filename = os.path.join(self.base_dir, 'mock', self.base_dir.lstrip('/'), 'repo', 'mirror', 'mock', key)
            fd_script = open(filename, 'r')
            try:
                script = fd_script.read()
            finally:
                fd_script.close()
            self.assertEqual(script, value)

    def test_run(self):
        """Test full mirror run."""
        pass  # TODO


class TestUniventionMirrorList(unittest.TestCase):

    """Test listing locally available repositories."""

    def setUp(self):
        """Create Mirror mockup."""
        self.base_dir = mkdtemp()
        MockConfigRegistry._EXTRA = {
            'repository/mirror/basepath': self.base_dir,
        }
        self._uri({
            '': '',
            '/': '',
            'univention-repository/': '',
        })
        self.m = M.UniventionMirror()
        repos = (
                (U.UCS_Version((MAJOR, MINOR, PATCH)), False),
                (U.UCS_Version((MAJOR, MINOR, PATCH)), True),
                (U.UCS_Version((MAJOR, MINOR, PATCH + 1)), False),
                (U.UCS_Version((MAJOR, MINOR, PATCH + 1)), True),
                (U.UCS_Version((MAJOR, MINOR + 1, PATCH)), True),
                (U.UCS_Version((MAJOR, MINOR + 1, PATCH + 1)), True),
        )
        self.repos = []
        for ver, maintained in repos:
            major_minor = U.UCS_Version.FORMAT % ver
            maint_unmain = maintained and 'maintained' or 'unmaintained'
            major_minor_patch = U.UCS_Version.FULLFORMAT % ver
            dirname = os.path.join(self.base_dir, 'mirror', major_minor, maint_unmain, major_minor_patch)
            M.makedirs(dirname)
            self.repos.append((dirname, ver, maintained))

    def _uri(self, uris):
        """Fill URI mockup."""
        for key, value in uris.items():
            MockUCSHttpServer.mock_add(key, value)

    def tearDown(self):
        """Clean up Mirror mockup."""
        rmtree(self.base_dir, ignore_errors=True)
        del self.base_dir
        del self.m
        MockConfigRegistry._EXTRA = {}

    def assertDeepEqual(self, seq1, seq2):
        """Tests that two lists or tuples are equal."""
        if isinstance(seq1, list) and isinstance(seq2, list):
            self.assertEqual(len(seq1), len(seq2))
            for elem1, elem2 in zip(seq1, seq2):
                self.assertDeepEqual(elem1, elem2)
        elif isinstance(seq1, tuple) and isinstance(seq2, tuple):
            self.assertEqual(len(seq1), len(seq2))
            for elem1, elem2 in zip(seq1, seq2):
                self.assertDeepEqual(elem1, elem2)
        else:
            self.assertEqual(seq1, seq2)

    def test_default(self):
        """Test default."""
        result = self.m.list_local_repositories()
        self.assertEqual(len(result), 4)
        self.assertDeepEqual(result, [_ for _ in self.repos if _[2]])

    def test_start(self):
        """Test start version."""
        ver = U.UCS_Version((MAJOR, MINOR + 1, PATCH))
        result = self.m.list_local_repositories(start=ver)
        self.assertEqual(len(result), 2)
        self.assertDeepEqual(result, [_ for _ in self.repos if _[1] >= ver and _[2]])

    def test_end(self):
        """Test end version."""
        ver = U.UCS_Version((MAJOR, MINOR, PATCH))
        result = self.m.list_local_repositories(end=ver)
        self.assertEqual(len(result), 1)
        self.assertDeepEqual(result, [_ for _ in self.repos if _[1] <= ver and _[2]])

    def test_maintained(self):
        """Test maintained off."""
        result = self.m.list_local_repositories(maintained=False)
        self.assertEqual(len(result), 0)
        self.assertEqual(result, [])

    def test_unmaintained(self):
        """Test unmaintained on."""
        result = self.m.list_local_repositories(unmaintained=True)
        self.assertEqual(len(result), 6)
        # Check sorted by version
        self.assertDeepEqual([_[1] for _ in result], [_[1] for _ in self.repos])
        self.assertDeepEqual(sorted(result), sorted(self.repos))


if __name__ == '__main__':
    if False:
        import univention.debug as ud
        ud.init('stderr', ud.NO_FUNCTION, ud.NO_FLUSH)
        ud.set_level(ud.NETWORK, ud.ALL + 1)
    if False:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    unittest.main()
