# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path
from subprocess import check_call
from typing import Iterable

import setuptools

from univention.config_registry_api import __version__

with open(Path(__file__).parent / "requirements.txt") as fp:
    requirements = fp.read().splitlines()

with open(Path(__file__).parent / "requirements_dev.txt") as fp:
    requirements_dev = fp.read().splitlines()

with open(Path(__file__).parent / "requirements_test.txt") as fp:
    requirements_test = fp.read().splitlines()


class BuildHTMLCommand(setuptools.Command):
    description = "generate HTML from RST"
    user_options = [("input-file=", "i", "input file")]

    def initialize_options(self):
        self.input_file = None

    def finalize_options(self):
        pass

    def run(self):
        for name in ("rst2html5.py", "rst2html5-3.py", "rst2html5", "rst2html5-3"):
            rst2_html5_exe = shutil.which(name)
            if rst2_html5_exe:
                break
        else:
            raise RuntimeError("Cannot find 'rst2html5'.")
        if self.input_file:
            target_dir = Path(self.input_file).parent / "static"
            if not target_dir.exists():
                print(f"mkdir -p {target_dir!s}")
                target_dir.mkdir(parents=True)
            target_file = target_dir / f"{str(Path(self.input_file).name)[:-3]}html"
            self.check_call([rst2_html5_exe, self.input_file, str(target_file)])
        else:
            for entry in self.recursive_scandir(Path(__file__).parent):
                if entry.is_file() and entry.name.endswith(".rst"):
                    target_dir = Path(entry.path).parent / "static"
                    if not target_dir.exists():
                        print(f"mkdir -p {target_dir!s}")
                        target_dir.mkdir(parents=True)
                    target_file = target_dir / f"{str(entry.name)[:-3]}html"
                    self.check_call([rst2_html5_exe, entry.path, str(target_file)])

    @classmethod
    def recursive_scandir(cls, path: Path) -> Iterable[os.DirEntry]:
        for entry in os.scandir(path):
            if entry.is_dir(follow_symlinks=False):
                yield from cls.recursive_scandir(entry.path)
            yield entry

    @classmethod
    def check_call(cls, cmd):
        print(f"Executing: {cmd!r}")
        check_call(cmd)


setuptools.setup(
    name="univention-config-registry-api",
    version=__version__,
    author="Univention GmbH",
    author_email="packages@univention.de",
    description="UCR HTTP API (aka 'Farad API')",
    long_description="UCR HTTP API (aka 'Farad API')",
    url="https://www.univention.de/",
    install_requires=requirements,
    setup_requires=["docutils", "pytest-runner"],
    tests_require=requirements_test,
    extras_require={
        "development": set(requirements + requirements_dev + requirements_test)
    },
    packages=["univention.config_registry_api"],
    python_requires=">=3.7",
    license="GNU Affero General Public License v3",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: AsyncIO",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    cmdclass={"build_html": BuildHTMLCommand},
)
