#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Verify the signature implementation
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from __future__ import annotations

import os
from pathlib import Path
from subprocess import call
from types import TracebackType
from typing import Iterator, cast

import pytest

from univention.config_registry import handler_set

from dockertest import Appcenter


CACHE = Path("/var/cache/univention-appcenter")
META = Path("/var/www/meta-inf")


class SyncedAppcenter(Appcenter):
    def __init__(self) -> None:
        Appcenter.__init__(self)
        self.vv = self.ucr.get('version/version')
        self.all_versions = ['4.1', '4.2', '4.3', '4.4', '5.0']
        self.upstream_appcenter = 'https://appcenter.software-univention.de'
        handler_set([
            'appcenter/index/verify=true',
        ])

    def reset_local_cache(self) -> None:
        handler_set([
            'repository/app_center/server=%s' % (self.upstream_appcenter),
        ])
        call(['univention-app', 'update'])
        handler_set([
            'repository/app_center/server=http://%(hostname)s.%(domainname)s' % self.ucr,
        ])

    def download(self, f: str) -> None:
        p = Path("/var/www") / f
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            p.unlink()

        call(['wget', '-O', p.as_posix(), f'{self.upstream_appcenter}/{f}'])

    def download_index_json(self) -> None:
        for version in self.all_versions:
            self.download(f'meta-inf/{version}/index.json.gz')
            self.download(f'meta-inf/{version}/all.tar.zsync')
            self.download(f'meta-inf/{version}/all.tar.gz')

    def download_index_json_gpg(self) -> None:
        for version in self.all_versions:
            self.download(f'meta-inf/{version}/index.json.gz.gpg')
            self.download(f'meta-inf/{version}/all.tar.gpg')

    def remove_from_cache(self, f: str) -> None:
        p = CACHE / f
        if p.exists():
            p.unlink()

    def file_exists_in_cache(self, f: str) -> bool:
        return (CACHE / f).exists()

    def test_index_without_gpg(self) -> None:
        self.download_index_json()
        assert call(['univention-app', 'update']) != 0

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        Appcenter.__exit__(self, exc_type, exc_val, exc_tb)


@pytest.fixture(scope="module")
def test_appcenter() -> Iterator[SyncedAppcenter]:
    with SyncedAppcenter() as sac:
        yield cast(SyncedAppcenter, sac)


@pytest.fixture()
def appcenter(test_appcenter: SyncedAppcenter) -> Iterator[SyncedAppcenter]:
    test_appcenter.download_index_json()
    test_appcenter.download_index_json_gpg()
    yield test_appcenter
    test_appcenter.reset_local_cache()


def test_index_with_gpg(appcenter: SyncedAppcenter) -> None:
    assert call(['univention-app', 'update']) == 0


def test_modify_index(appcenter: SyncedAppcenter, ucr) -> None:
    f = META / appcenter.vv
    # this just so that all.tar gets newly synced
    appcenter.remove_from_cache(f"{ucr['hostname']}.{ucr['domainname']}/{appcenter.vv}/.etags")
    tar = (f / "all.tar").as_posix()
    call(["tar", "--append", "-f", tar, "-C", "/proc", "uptime"])
    call(["zsyncmake", "-z", "-u", f"{ucr['repository/app_center/server']}/meta-inf/{appcenter.vv}/all.tar.gz", tar, "-o", f"{tar}.zsync"])
    assert call(['univention-app', 'update']) != 0


def test_modify_inst(appcenter: SyncedAppcenter) -> None:
    filename = 'tecart_20151204.inst'
    basename, ext = os.path.splitext(filename)
    appcenter.remove_from_cache(filename)
    f = f'univention-repository/{appcenter.vv}/maintained/component/{basename}/{ext}'
    appcenter.download(f)
    (Path("/var/www") / f).write_text("## SIGNATURE TEST ###")
    call(['univention-app', 'update'])
    # Check only if the file was removed from the local cache
    assert not appcenter.file_exists_in_cache(filename)
