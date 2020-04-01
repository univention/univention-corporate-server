# -*- coding: utf-8 -*-

#
# Use only Python 2 and 3 compatible code here!
#

from email.utils import parseaddr
import io
import os

import setuptools
from debian.changelog import Changelog
from debian.deb822 import Deb822


dch = Changelog(io.open("debian/changelog", "r", encoding="utf-8"))
dsc = Deb822(io.open("debian/control", "r", encoding="utf-8"))
realname, email_address = parseaddr(dsc["Maintainer"])

setuptools.setup(
    name=dch.package,
    version=dch.version.full_version,
    maintainer=realname,
    maintainer_email=email_address,
    description="Python interface to configuration registry",
    long_description="Python interface to configuration registry",
    url="https://docs.software-univention.de/ucs-python-api/univention.config_registry.html",
    install_requires=["six"],
    packages=["univention", "univention.config_registry"],
    scripts=["univention-config-registry"],
    license="GNU Affero General Public License v3",
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
)
