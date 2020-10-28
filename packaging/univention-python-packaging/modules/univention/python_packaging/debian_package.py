# -*- coding: utf-8 -*-

#
# Use only Python 2 and 3 compatible code here!
#

"""
import setuptools
from debian_package import DebianPackage

dp = DebianPackage("../git/ucs/../univention-..")

setuptools.setup(
    name=dp.name,
    version=dp.version,
    ..
)

# or:

setuptools.setup(
    ..,
    **dp.as_setuptools_setup_kwargs()
)
"""

from email.utils import parseaddr
import io
import json
import os
try:
    from typing import Dict, Set, List
except ImportError:
    pass

from debian.changelog import Changelog
from debian import deb822


class DebianPackage(object):

    def __init__(self, package_path):   # type: (str) -> None
        self.package_path = package_path
        self.changelog_path = os.path.join(self.package_path, "debian", "changelog")
        self.control_path = os.path.join(self.package_path, "debian", "control")
        self._description = ""
        self._homepage = ""
        self._long_description = ""
        self._maintainer = ""
        self._maintainer_email = ""
        self._name = ""
        self._python_dependencies = set()  # type: Set[str]
        self._version = ""

    def _debian_to_python_package(self):  # type: () -> Dict[str, str]
        path = os.path.join(os.path.dirname(__file__), "debian_to_python_package.json")
        with open(path, "r") as fp:
            return json.load(fp)

    def _parse_changelog(self):
        with io.open(self.changelog_path, "r", encoding="utf-8") as fp:
            dch = Changelog(fp)
            self._name = dch.package
            # 14.0.0-12 would be renamed to 14.0.0.post12, so replace dash with dot:
            self._version = dch.version.full_version.replace("-", ".")

    def _parse_control(self):
        with io.open(self.control_path, "r", encoding="utf-8") as fp:
            for stanza in deb822.Sources.iter_paragraphs(fp):
                if "Source" in stanza:
                    self._maintainer, self._maintainer_email = parseaddr(stanza["Maintainer"])
                else:
                    # "Package"
                    dependencies = []
                    for key in ("Pre-Depends", "Depends"):
                        try:
                            dependencies.extend(d.strip() for d in stanza[key].split(","))
                        except KeyError:
                            pass
                    deb2py = self._debian_to_python_package()
                    for dep in dependencies:
                        try:
                            py_dep = deb2py[dep]
                        except KeyError:
                            print("Ignoring unknown dependency {!r}.".format(dep))
                            continue
                        if py_dep != "__ignore":
                            self._python_dependencies.add(py_dep)
                    self._description = stanza["Description"].split("\n")[0]
                    try:
                        self._long_description = "\n".join(stanza["Description"].split("\n")[1:])
                    except IndexError:
                        self._long_description = self._description
                    try:
                        self._homepage = stanza["Homepage"]
                    except KeyError:
                        self._homepage = "https://www.univention.de/"

    @property
    def description(self):  # type: () -> str
        if not self._description:
            self._parse_control()
        return self._description

    @property
    def homepage(self):  # type: () -> str
        if not self._homepage:
            self._parse_control()
        return self._homepage

    @property
    def long_description(self):  # type: () -> str
        if not self._long_description:
            self._parse_control()
        return self._long_description

    @property
    def maintainer(self):  # type: () -> str
        if not self._maintainer:
            self._parse_control()
        return self._maintainer

    @property
    def maintainer_email(self):  # type: () -> str
        if not self._maintainer_email:
            self._parse_control()
        return self._maintainer_email

    @property
    def name(self):  # type: () -> str
        if not self._name:
            self._parse_changelog()
        return self._name

    @property
    def python_dependencies(self):  # type: () -> List[str]
        if not self._python_dependencies:
            self._parse_control()
        return list(self._python_dependencies)

    @property
    def version(self):
        if not self._version:
            self._parse_changelog()
        return self._version

    install_requires = python_dependencies
    url = homepage

    def as_setuptools_setup_kwargs(self):
        return {
            "description": self.description,
            "install_requires": self.python_dependencies,
            "long_description": self.long_description,
            "maintainer": self.maintainer,
            "maintainer_email": self.maintainer_email,
            "name": self.name,
            "url": self.homepage,
            "version": self.version,
        }
