#!/usr/bin/python3

from setuptools import setup


version = open("debian/changelog").readline().split()[1][1:-1].split('A~')[0]

packages = ['univention', 'univention.updater', 'univention.updater.scripts']

setup(
    packages=packages,
    package_dir={'': 'modules'},
    version=version,
)
