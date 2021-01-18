#!/usr/bin/python3
# vim:set fileencoding=utf-8 filetype=python tabstop=4 shiftwidth=4 expandtab:
# pylint: disable-msg=C0301,R0903,R0913
from __future__ import print_function

import os.path
import sys
from io import StringIO, BytesIO
import subprocess

from six.moves import urllib_parse
from six.moves import urllib_response
import pytest

import univention.updater.tools as U  # noqa: E402
from univention.config_registry import ConfigRegistry
from mockups import MAJOR, MINOR, PATCH, ERRAT, MockPopen

try:
    from typing import Any, Dict, IO, List, Sequence, Union  # noqa F401
except ImportError:
    pass

if sys.version_info >= (3,):
    import builtins as builtins
else:
    import __builtin__ as builtins
    FileNotFoundError = IOError


@pytest.fixture(autouse=True)
def ucr(monkeypatch, tmpdir):
    db = tmpdir / "base.conf"
    monkeypatch.setenv("UNIVENTION_BASECONF", str(db))
    cr = ConfigRegistry()

    def extra(conf={}, **kwargs):
        cr.update(conf)
        cr.update(kwargs)
        cr.save()

    extra({
        'version/version': '%d.%d' % (MAJOR, MINOR),
        'version/patchlevel': '%d' % (PATCH,),
        'version/erratalevel': '%d' % (ERRAT,),
    })

    return extra


@pytest.fixture
def http(mocker):
    ressources = {}

    def extra(uris={}, **kwargs):
        uris.update(kwargs)
        uris = {os.path.join('/', key): value for key, value in uris.items()}
        ressources.update(uris)
        ressources.update(kwargs)

    def fopen(req, *args, **kwargs):
        url = req.get_full_url()
        p = urllib_parse.urlparse(url)
        try:
            res = ressources[p.path]
            if isinstance(res, Exception):
                raise res
            elif isinstance(res, bytes):
                return urllib_response.addinfourl(BytesIO(res), {"content-length": len(res)}, url, 200)
            else:
                return res
        except LookupError:
            raise U.urllib_error.HTTPError(url, 404, "Not Found", {}, None)

    director = mocker.patch("univention.updater.tools.urllib2.OpenerDirector", autospec=True)
    director.open.side_effect = fopen
    opener = mocker.patch("univention.updater.tools.urllib2.build_opener")
    opener.return_value = director
    U.UCSHttpServer.reinit()

    return extra


class MockFileManager(object):

    def __init__(self, tmpdir):
        # type: (Any) -> None
        self.files = {}  # type: Dict[str, Union[StringIO, BytesIO]]
        self._open = builtins.open
        self._tmpdir = tmpdir

    def open(self, name, mode='r', buffering=-1, **options):
        # type: (str, str, int, **Any) -> IO
        name = os.path.abspath(name)
        buf = self.files.get(name)

        if name.startswith(str(self._tmpdir)):
            return self._open(name, mode, buffering, **options)

        #    | pos | read | write
        # ===+=====+======+======
        # r  | 0   | pos  | -
        # r+ | 0   | pos  | pos
        # w  | 0   | -    | pos
        # w+ | 0   | pos  | pos
        # x  | 0   | -    | pos TODO
        # a  | end | -    | end FIXME
        # a+ | end | pos  | end FIXME
        if "w" in mode or (("r+" in mode or "a" in mode) and not buf):
            self.files[name] = buf = self._new(name, "b" in mode)
        elif "r" in mode and not buf:
            return self._open(name, mode, buffering, **options)

        buf = self.files[name]

        if "r" in mode:
            buf.seek(0)

        return buf

    def _new(self, name, binary=True):
        # type: (str, bool) -> Union[StringIO, BytesIO]
        buf = BytesIO() if binary else StringIO()  # type: Union[StringIO, BytesIO]
        setattr(buf, "name", name)
        setattr(buf, "close", lambda: None)
        return buf

    def write(self, name, text):
        # type: (str, bytes) -> None
        name = os.path.abspath(name)
        buf = self._new(name)
        assert isinstance(buf, BytesIO)
        self.files[name] = buf

    def read(self, name):
        # type: (str) -> bytes
        name = os.path.abspath(name)
        if name not in self.files:
            raise FileNotFoundError(2, "No such file or directory: '%s'" % name)

        buf = self.files[name]
        val = buf.getvalue()
        return val if isinstance(val, bytes) else val.encode("utf-8")


@pytest.fixture
def mockopen(monkeypatch, tmpdir):
    manager = MockFileManager(tmpdir)
    monkeypatch.setattr(builtins, "open", manager.open)
    return manager


@pytest.fixture
def mockpopen(monkeypatch):
    monkeypatch.setattr(subprocess, 'Popen', MockPopen)
    yield MockPopen
    MockPopen.mock_reset()
