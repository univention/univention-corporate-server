#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2022 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
#

from setuptools import setup as orig_setup

import io
from debian.deb822 import Deb822
from debian.changelog import Changelog


def _get_version():
	changelog = Changelog(io.open('debian/changelog', 'r', encoding='utf-8'))
	return changelog.full_version


def _get_description(name):
	for package in Deb822.iter_paragraphs(io.open('debian/control', 'r', encoding='utf-8')):
		if package.get('Package') == name:
			description = package['Description']
			return description.split('\n .\n')[0]


def setup(name, **attrs):
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
	if 'version' not in attrs:
		attrs['version'] = _get_version()
	if 'description' not in attrs:
		attrs['description'] = _get_description(name)
	return orig_setup(**attrs)


setup(
	name='univention-unittests',
	packages=[
		'univentionunittests',
	],
	entry_points={"pytest11": ["univention-unittests-ucr = univentionunittests.ucr", "univention-unittests-umc = univentionunittests.umc", "univention-unittests-udm = univentionunittests.udm"]},
	package_dir={
		'univentionunittests': 'python/univention/unittests/',
	},
)
