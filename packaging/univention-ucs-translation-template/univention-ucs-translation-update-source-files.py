#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Univention GmbH
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

from optparse import OptionParser

import sys
import os
import json
import univention.dh_umc as dh_umc
import univention.debhelper as dh_ucs
import univention.translationhelper as tlh
try:
        sys.path.insert( 0, '.' )
except BaseException, e:
	print "could not load dh_umc " + str(e)
	sys.exit(1)

if __name__ == '__main__':
	usage = '''%prog [options] -s source_dir -c language_code 
e.g.: -s /path/to/ucs-repository/ -c de'''
	parser = OptionParser(usage=usage)
	parser.add_option('-s', '--source', action='store', dest='source_dir', help='UCS source dir from which translation files are gathered, e.g. an UCS svn base dir')
	parser.add_option('-c', '--languagecode', action='store', dest='target_language', help='Target language code (e.g. de)')
	parser.add_option('-b', '--basefiles', action='store', dest='basefiles', default='.umc-modules', help='xml file basename (default: .umc-modules)')

	(options, args) = parser.parse_args()
	help_message = 'Use --help to show additional help.'

	if not options.source_dir:
		parser.error('Missing argument -s. %s' % help_message)
	
	if not options.target_language:
		parser.error('Missing argument -c. %s' % help_message)

	# make options.source_dir absolute
	options.source_dir = os.path.abspath(options.source_dir)
	# find all module files and move them to a language specific directory
	startdir=os.getcwd()
	base_translation_modules = tlh.find_base_translation_modules(startdir, options.source_dir, options.basefiles)	
	# generate .mo files in the correct directory
	dh_umc.LANGUAGES = ( options.target_language, )
	for modules in base_translation_modules:
		umc_modules = tlh.get_modules_from_path(modules['modulename'], os.path.join(options.source_dir, modules['packagedir']))
		for module in umc_modules:
			package_path_absolute = os.path.join(options.target_language, modules['packagedir'])
			tlh.update_package_translation_files(module, modules['modulename'], modules['packagedir'], options.source_dir, options.target_language, startdir)

	# special cases, e.g. univention-management-console-frontend
	specialmodules = []
	specialcases_file = "/usr/share/univention-ucs-translation-template/specialcases.json"
	if os.path.exists(specialcases_file):
		with open(specialcases_file, 'r') as f:
			specialmodules = json.loads(f.read())
	else:
		print "Error: Could not find file %s. Several files will not be handled." % specialcases_file

	for module in specialmodules:
		try:
			if module['action'] == 'update-po':
				tlh.translate_special_case(module, options.source_dir, startdir, options.target_language)
			elif module['action'] == 'get-template':
				tlh.get_template(module, options.source_dir, startdir, options.target_language)
		except Exception as e:
			print "Warning in special case: %s" % str(e)
	# end special case
