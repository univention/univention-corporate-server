#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention System Setup
# cleanup script called after the appliance wizard setup
#
# Copyright 2011-2019 Univention GmbH
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

import sys
import shutil
import os.path
from tempfile import mkdtemp
from univention.management.console.modules.setup import util

PATH_CLEANUP_PRE_SCRIPTS = '/usr/lib/univention-system-setup/cleanup-pre.d/'
PATH_CLEANUP_POST_SCRIPTS = '/usr/lib/univention-system-setup/cleanup-post.d/'


def cleanup():
	temp_dir = mkdtemp()

	pre_dir = os.path.join(temp_dir, 'pre')
	post_dir = os.path.join(temp_dir, 'post')

	shutil.copytree(PATH_CLEANUP_PRE_SCRIPTS, pre_dir)
	shutil.copytree(PATH_CLEANUP_POST_SCRIPTS, post_dir)

	# Run cleanup-pre scripts
	util.run_scripts_in_path(pre_dir, sys.stdout, "cleanup-pre")

	# Run cleanup-post scripts
	util.run_scripts_in_path(post_dir, sys.stdout, "cleanup-post")

	shutil.rmtree(temp_dir)

	sys.exit(0)


if __name__ == "__main__":
	cleanup()
