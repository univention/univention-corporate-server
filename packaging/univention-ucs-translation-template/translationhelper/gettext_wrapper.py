#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2017 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.
import polib
import os
import subprocess


class POFileError(Exception):
	pass


def _clean_header(po_path):
	pof = polib.pofile(po_path)
	pof.header = ""
	pof.metadata.update({
		u'Content-Type': u'text/plain; charset=utf-8',
	})
	pof.metadata_is_fuzzy = None
	pof.save(po_path)


def create_empty_po(binary_pkg_name, new_po_path):
	_call('--force-po',
				'--sort-output',
				'--package-name={}'.format(binary_pkg_name),
				'--msgid-bugs-address=forge.univention.org',
				'--copyright-holder=Univention GmbH',
				# Supress warning about /dev/null being an unknown source type
				'--language', 'C',
				'-o', new_po_path,
				'/dev/null')
	_clean_header(new_po_path)


def install_mo():



def join_existing(language, output_file, input_files, cwd=None):
	if not os.path.isfile(output_file):
		raise POFileError("Can't join input files into {}. File does not exist.".format(output_file))
	if not isinstance(input_files, list):
		input_files = [input_files]
	# make input_files relative so the location lines in the resulting po
	# will be relative to cwd
	input_files = [os.path.relpath(p, start=cwd) for p in input_files]
	_call('--join-existing',
				# don't manipulate header, we do this in create_po
				'--omit-header',
				'--language', language,
				'-o', output_file,
				*input_files, cwd=cwd)


def _call(*args, **kwargs):
	call = ['xgettext', '--from-code=UTF-8']
	call.extend([arg for arg in args])
	try:
		subprocess.check_call(call, **kwargs)
	except subprocess.CalledProcessError as exc:
		raise POFileError("Error: xgettext exited unsuccessfully. Attempted command:\n{}".format(exc.cmd))
	except AttributeError as exc:
		raise POFileError("Operating System error during xgettext call:\n{}".format(exc.strerror))
