#!/usr/bin/python3
import sys

from setuptools import setup


version = open("debian/changelog").readline().split()[1][1:-1].split('A~')[0]

packages = ['univention', 'univention.updater']
if sys.version_info >= (3,):
    packages += ['univention.updater.scripts']

setup(
    packages=packages,
    package_dir={'': 'modules'},
    version=version,)
