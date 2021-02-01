#!/usr/bin/python3
import sys
from setuptools import setup

version = open("debian/changelog", "r").readline().split()[1][1:-1]

packages = ['univention', 'univention.updater']
if sys.version_info >= (3,):
    packages += ['univention.updater.scripts']

setup(
    packages=packages,
    package_dir={'': 'modules'},
    version=version,
)
