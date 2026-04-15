# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Derive a PEP 440 version string from debian/changelog.

Consumed by sibling packages via setuptools' dynamic-version mechanism::

    [project]
    dynamic = ["version"]

    [tool.setuptools.dynamic]
    version = {attr = "univention.build_version.version"}

The module-level ``version`` attribute is computed at import time by parsing
``./debian/changelog`` relative to the current working directory which is
the project root during a PEP 517 build.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


_CHANGELOG_FIRST_LINE = re.compile(r"^\S+\s+\(([^)]+)\)")


def _base_version() -> str:
    """Read the upstream version from the top entry of debian/changelog."""
    changelog = Path.cwd() / "debian" / "changelog"
    with changelog.open() as f:
        first_line = f.readline()

    match = _CHANGELOG_FIRST_LINE.match(first_line)
    if not match:
        raise RuntimeError(
            f"Cannot parse debian/changelog first line: {first_line!r}"
        )
    raw = match.group(1)

    # Strip epoch: "1:2.3.4" -> "2.3.4"
    if ":" in raw:
        raw = raw.split(":", 1)[1]
    # Strip debian revision: "2.3.4-1univention1" -> "2.3.4"
    if "-" in raw:
        raw = raw.rsplit("-", 1)[0]
    # PEP 440 rejects "~"; Debian uses it as a pre-release marker. There's no
    # lossless mapping, so strip it and trust callers to bump the base version
    # before a real release if they need pre-release semantics.
    raw = raw.replace("~", "")

    return raw


def _short_sha() -> str | None:
    """Short git sha from CI env, falling back to local git invocation."""
    sha = os.environ.get("CI_COMMIT_SHORT_SHA")
    if sha:
        return sha
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short=7", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.strip() or None


def _is_default_branch() -> bool:
    """True only for GitLab pipelines running on the repo's default branch."""
    branch = os.environ.get("CI_COMMIT_BRANCH")
    default = os.environ.get("CI_DEFAULT_BRANCH")
    return bool(branch and default and branch == default)


def _compute() -> str:
    base = _base_version()
    if _is_default_branch():
        return base
    sha = _short_sha()
    return f"{base}.dev0+g{sha}" if sha else f"{base}.dev0"


version = _compute()
