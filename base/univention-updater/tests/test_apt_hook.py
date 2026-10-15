#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Unit test for the APT hook preventing the removal of the UCS role packages"""

import os
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

import pytest


HOOK = Path(__file__).resolve().parent.parent / "script" / "univention-apt-hook"

loader = SourceFileLoader("univention_apt_hook", str(HOOK))
hook = module_from_spec(spec_from_loader(loader.name, loader))
loader.exec_module(hook)

HEADER = [
    "VERSION 2",
    "APT::Architecture=amd64",
    "DPkg::Pre-Install-Pkgs::=/usr/share/univention-updater/univention-apt-hook",
    "",
]
# apt purge linux-image-5.10-amd64 univention-server-master+
CONTAINER_SWITCH = [
    "univention-docker-container-mode - < 5.0.0-2 /var/cache/apt/archives/univention-docker-container-mode_5.0.0-2_all.deb",
    "univention-container-role-common - < 15.0.10-2 /var/cache/apt/archives/univention-container-role-common_15.0.10-2_all.deb",
    "univention-role-server-common 15.0.10-2 > - **REMOVE**",
    "univention-container-role-server-common - < 15.0.10-2 /var/cache/apt/archives/univention-container-role-server-common_15.0.10-2_all.deb",
    "linux-image-5.10-amd64 5.10.226-1~deb10u1 > - **REMOVE**",
    "univention-container-role-common - < 15.0.10-2 **CONFIGURE**",
]
# apt purge linux-image-5.10-amd64
KERNEL_PURGE = [
    "univention-server-master 15.0.10-2 > - **REMOVE**",
    "univention-bind 14.0.6-1 > - **REMOVE**",
    "univention-role-server-common 15.0.10-2 > - **REMOVE**",
    "linux-image-5.10-amd64 5.10.226-1~deb10u1 > - **REMOVE**",
]
# univention-backup2master
BACKUP2MASTER = [
    "univention-server-backup 17.0.4 > - **REMOVE**",
    "univention-server-master - < 17.0.4 /var/cache/apt/archives/univention-server-master_17.0.4_all.deb",
    "univention-server-master - < 17.0.4 **CONFIGURE**",
]
UPGRADE = [
    "univention-server-master 16.0.6 < 17.0.4 /var/cache/apt/archives/univention-server-master_17.0.4_all.deb",
    "univention-role-server-common 16.0.6 < 17.0.4 /var/cache/apt/archives/univention-role-server-common_17.0.4_all.deb",
    "linux-image-6.1.0-29-amd64 6.1.123-1 > - **REMOVE**",
]


def test_parse():
    remove, install = hook.parse(HEADER + CONTAINER_SWITCH)
    assert remove == {"univention-role-server-common", "linux-image-5.10-amd64"}
    assert install == {"univention-docker-container-mode", "univention-container-role-common", "univention-container-role-server-common"}


def test_parse_wrong_version():
    with pytest.raises(ValueError):
        hook.parse(["VERSION 3", ""])


@pytest.mark.parametrize("actions,expected", [
    (KERNEL_PURGE, {"univention-server-master", "univention-role-server-common"}),
    (CONTAINER_SWITCH, {"univention-role-server-common"}),
    (["univention-role-common 17.0.4 > - **REMOVE**"], {"univention-role-common"}),
    (BACKUP2MASTER, set()),
    ([*BACKUP2MASTER, "univention-role-server-common 17.0.4 > - **REMOVE**"], {"univention-role-server-common"}),
    (["univention-server-backup 17.0.4 > - **REMOVE**", "univention-server-backup 17.0.4 > - **REMOVE**"], {"univention-server-backup"}),
    (UPGRADE, set()),
    (["univention-container-role-server-common 15.0.10-2 > - **REMOVE**"], set()),
])
def test_blocked(actions, expected):
    assert hook.blocked(*hook.parse(HEADER + actions)) == expected


@pytest.fixture
def run(tmp_path):
    def run(actions, override=False):
        script = HOOK.read_text().replace(hook.FILE_OVERRIDE, str(tmp_path / "override"))
        if override:
            (tmp_path / "override").touch()
        read, write = os.pipe()
        os.write(write, "\n".join(HEADER + actions + [""]).encode())
        os.close(write)
        os.dup2(read, 20)
        try:
            return subprocess.run(
                [sys.executable, "-c", script],
                env={"APT_HOOK_INFO_FD": "20"},
                pass_fds=(20,),
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            os.close(20)
            os.close(read)

    return run


def test_main_blocks(run):
    result = run(KERNEL_PURGE)
    assert result.returncode == 1
    assert "W: univention-apt-hook: !!! ERROR !!!" in result.stderr
    assert "    univention-role-server-common univention-server-master\n" in result.stderr


def test_main_allows(run):
    result = run(UPGRADE)
    assert result.returncode == 0
    assert result.stderr == ""


def test_main_override(run):
    result = run(KERNEL_PURGE, override=True)
    assert result.returncode == 0
    assert "removing univention-role-server-common univention-server-master" in result.stderr
