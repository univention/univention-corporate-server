#!/usr/bin/python3
import sys

from setuptools import setup

from debian.changelog import Changelog


dch = Changelog(open('debian/changelog'))


packages = ['univention', 'univention.updater']
if sys.version_info >= (3,):
    packages += ['univention.updater.scripts']

setup(
    packages=packages,
    package_dir={'': 'modules'},
    version=dch.version.full_version.split('A~')[0],
)
