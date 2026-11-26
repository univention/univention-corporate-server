# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from debian.changelog import Changelog
from debian.deb822 import Deb822
from setuptools import Distribution, setup as orig_setup


class BinaryPackageDistribution(Distribution):
    def parse_config_files(self, filenames=None, ignore_option_errors=False):
        # These setup scripts describe separate distributions. The root
        # pyproject.toml describes only the main App Center distribution.
        super().parse_config_files(filenames=[], ignore_option_errors=ignore_option_errors)


def _get_description(name):
    for package in Deb822.iter_paragraphs(open('debian/control', encoding='utf-8')):
        if package.get('Package') == name:
            description = package['Description']
            return description.split('\n .\n')[0]


def setup(name, **attrs):
    attrs.setdefault('distclass', BinaryPackageDistribution)
    if 'version' not in attrs:
        with open('debian/changelog', encoding='utf-8') as stream:
            attrs['version'] = Changelog(stream).full_version
    if 'name' not in attrs:
        attrs['name'] = name
    if 'license' not in attrs:
        attrs['license'] = 'AGPL'
    if 'author_email' not in attrs:
        attrs['author_email'] = 'packages@univention.de'
    if 'author' not in attrs:
        attrs['author'] = 'Univention GmbH'
    if 'url' not in attrs:
        attrs['url'] = 'https://www.univention.de/'
    if 'description' not in attrs:
        attrs['description'] = _get_description(name)
    return orig_setup(**attrs)
