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

import os
import sys
import fnmatch
import re
import getpass
from email.Utils import formatdate
import socket
import shutil
import traceback
import univention.debhelper as dh_ucs
import univention.dh_umc as dh_umc

# do not translate modules with these names, as they are examples and thus not worth the effort
MODULE_BLACKLIST = [ 
 'PACKAGENAME',
 '0001-6-7'
 ]

def reversereplace(s, old, new, occurrence):
	li = s.rsplit(old, occurrence)
	return new.join(li)

def update_package_translation_files(module, modulename, packagedir, source_dir, target_language, startdir):
	curr_dir = os.getcwd()
	try:
		# create directories for package translation
		translated_package_dir_absolute = os.path.normpath("%s/%s/%s" %(startdir, target_language, packagedir))
		if not os.path.exists(translated_package_dir_absolute):
			os.makedirs(translated_package_dir_absolute)
		p = os.path.join(source_dir, packagedir)
		print "update_package_translation_files module: %s" % module
		os.chdir(p)
		if not module['core']:
			# build python po files
			for po_file in module.python_po_files:
				po_file_full_path = translated_package_dir_absolute+"/"+po_file
				if not os.path.exists(os.path.dirname(po_file_full_path)):
					os.makedirs(os.path.dirname(po_file_full_path))
				dh_umc.create_po_file( po_file_full_path, modulename, module.python_files )

			# build javascript PO files
			for po_file in module.js_po_files:
				po_file_full_path = translated_package_dir_absolute+"/"+po_file
				if not os.path.exists(os.path.dirname(po_file_full_path)):
					os.makedirs(os.path.dirname(po_file_full_path))
				# using python as language seems to work better than perl
				dh_umc.create_po_file( po_file_full_path, modulename, module.js_files, 'python' )

		# xml always has to be present
		for lang, po_file in module.xml_po_files:
			po_file_full_path = translated_package_dir_absolute+"/"+po_file
			if not os.path.exists(os.path.dirname(po_file_full_path)):
				os.makedirs(os.path.dirname(po_file_full_path))
			dh_umc.module_xml2po( module,po_file_full_path, lang )

	except OSError as e:
		print traceback.format_exc()
		print "error in update_package_translation_files: %s" % str(e)
	print ""
	os.chdir(curr_dir)

def update_and_install_translation_files_to_correct_path(module, target_language, package_path_absolute, startdir):
	if not module['core']:
		for po_file in module.python_po_files:
			if os.path.isfile(os.path.join(package_path_absolute, po_file)):
				dh_umc.create_mo_file(os.path.join(package_path_absolute, po_file))
				dh_ucs.doIt('install', '-D', os.path.join(package_path_absolute, po_file.replace('.po', '.mo')), os.path.join(startdir, 'usr/share/locale/%s/LC_MESSAGES/%s.mo' % (target_language, module['package'])))
				os.unlink(os.path.join(package_path_absolute, po_file.replace('.po', '.mo')))
		for po_file in module.js_po_files:
			if os.path.isfile(os.path.join(package_path_absolute, po_file)):
				dh_umc.create_json_file(os.path.join(package_path_absolute, po_file))
				dh_ucs.doIt( 'install', '-D', os.path.join(package_path_absolute, po_file.replace('.po', '.json')), os.path.join(startdir, 'usr/share/univention-management-console-frontend/js/umc/modules/i18n/%s/%s.json' % (target_language, module['Module'] ) ))
				os.unlink(os.path.join(package_path_absolute, po_file.replace('.po', '.json')))
	# xml always has to be present
	for lang, po_file in module.xml_po_files:
		if os.path.isfile(os.path.join(package_path_absolute, po_file)):
			dh_umc.create_mo_file(os.path.join(package_path_absolute, po_file))
			dh_ucs.doIt('install', '-D', os.path.join(package_path_absolute, po_file.replace('.po', '.mo')), os.path.join(startdir, 'usr/share/univention-management-console/i18n/%s/%s.mo' % (target_language, module['Module'])))
			os.unlink(os.path.join(package_path_absolute, po_file.replace('.po', '.mo')))

# special case e.g. univention-management-modules-frontend: translation files are built with a makefile
def translate_special_case(module, source_dir, start_dir, target_language):
	curr_dir = os.getcwd()
	package_base_path = os.path.join(source_dir, module['packagedir'])
        os.chdir(package_base_path)

	output_dir = os.path.join(start_dir, target_language, module['packagedir'], module['po_subdir'] )
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)

	# find source files
	matches = []
	for root, dirnames, filenames in os.walk('.'):
                for filename in filenames:
			if fnmatch.fnmatch(os.path.join(root,filename), module['inputfiles']):
				matches.append(os.path.join(root,filename))
	
	print "matching %s: %s" % (module['inputfiles'], matches)

	dh_umc.create_po_file( output_dir+'/%s.po' % target_language, module['packagename'], matches )

	os.chdir(curr_dir)

def translate_special_case_po_to_target(module, start_dir, target_language):
	curr_dir = os.getcwd()
	package_base_path = os.path.join(start_dir, target_language, module['packagedir'])
	os.chdir(package_base_path)

	po_file = package_base_path + '/%s/%s.po' % (module['po_subdir'], target_language)

	module['language'] = target_language
	output_name = os.path.join(start_dir, module['outputdir'] % module)
	print "output name: %s" % output_name
	if not os.path.exists(os.path.dirname(output_name)):
		os.makedirs(os.path.dirname(output_name))

	if module['target'] == 'json':
		dh_umc.create_json_file(po_file)
		shutil.move(reversereplace(po_file, 'po', 'json', 1), output_name)
	elif module['target'] == 'mo':
		dh_umc.create_mo_file(po_file)
		shutil.move(reversereplace(po_file, 'po', 'mo', 1), output_name)

	os.chdir(curr_dir)

def get_modules_from_path(modulename, modulepath):
	modules = []
	curr_dir = os.getcwd()
	os.chdir(modulepath)
	try:
		# read package content with dh_umc
		modules = dh_umc.read_modules(modulename, False)
	except AttributeError as e:
		print "%s attributeerror in module, trying to load as core module" % str(e)
		try: 
			modules = dh_umc.read_modules(modulename, True)
		except AttributeError as e:
			print "%s core module load failed" % str(e)
		# successfully loaded as core module
		else:
			for module in modules:
				module['core'] = True
	else:
		for module in modules:
			module['core'] = False

	os.chdir(curr_dir)
	return modules

def find_base_translation_modules(startdir, source_dir, module_basefile_name):
	print 'looking in %s' % source_dir
	print 'looking for files matching %s' % module_basefile_name
	os.chdir(source_dir)
	matches = []
	for root, dirnames, filenames in os.walk('.'):
		for filename in fnmatch.filter(filenames, "*" + module_basefile_name):
			matches.append(os.path.join(root,filename))

	base_translation_modules = []

	pattern_get_package_name = ".*/(.*)/debian/.*%s$" % module_basefile_name
	regex = re.compile(pattern_get_package_name)
	for match in matches:
		print match
		packagenameresult = regex.search(match)
		if packagenameresult:
			packagename = packagenameresult.group(1)

			modulename = os.path.basename(match.replace(module_basefile_name, ''))
			if modulename in MODULE_BLACKLIST:
				print "Ignoring module %s: Module is blacklisted\n" % modulename
				continue

			packagedir = os.path.dirname(os.path.dirname(match))
			print "Found package: %s" % packagedir
			module = {} 
			module['modulename'] = modulename
			module['packagename'] = packagename
			module['packagedir'] = packagedir
			base_translation_modules.append(module)
		else:
			print "could not obtain packagename from directory %s" % match
		
	os.chdir(startdir)
	return base_translation_modules

def create_new_package(new_package_dir, target_language, target_locale, language_name, startdir):
	new_package_dir_debian = os.path.join(new_package_dir, 'debian')
	if not os.path.exists(new_package_dir_debian):
		print "creating directory: %s" % new_package_dir_debian
		os.makedirs(new_package_dir_debian)

	translation_package_name = "univention-ucs-translation-%s" % target_language
	translation_creator = getpass.getuser()
	translation_host = socket.getfqdn()
	with open(os.path.join(new_package_dir_debian, 'copyright'), 'w') as f:
		f.write("""Copyright 2013-2014 Univention GmbH

http://www.univention.de/

All rights reserved.

The source code of the software contained in this package
as well as the source package itself are made available
under the terms of the GNU Affero General Public License version 3
(GNU AGPL V3) as published by the Free Software Foundation.

Binary versions of this package provided by Univention to you as
well as other copyrighted, protected or trademarked materials like
Logos, graphics, fonts, specific documentations and configurations,
cryptographic keys etc. are subject to a license agreement between
you and Univention and not subject to the GNU AGPL V3.

In the case you use the software under the terms of the GNU AGPL V3,
the program is provided in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License with the Debian GNU/Linux or Univention distribution in file
/usr/share/common-licenses/AGPL-3; if not, see
<http://www.gnu.org/licenses/>.""")

	with open(os.path.join(new_package_dir_debian, 'changelog'), 'w') as f:
		f.write("""%s (1.0.0-1) unstable; urgency=low

  * Initial release

 -- %s <%s@%s>  %s""" % (translation_package_name, translation_creator, translation_creator, translation_host, formatdate()))
		
	with open(os.path.join(new_package_dir_debian, 'rules'), 'w') as f:
		f.write("""#!/usr/bin/make -f
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

override_dh_auto_test:
	#ucslint
	dh_auto_test

%:
	dh $@""")
	

	with open(os.path.join(new_package_dir_debian, 'control'), 'w') as f:
                f.write("""Source: %s
Section: univention
Priority: optional
Maintainer: %s <%s@%s>
Build-Depends: debhelper (>= 7.0.50~),
 ucslint,
 univention-config-dev,
 univention-management-console-dev
Standards-Version: 3.8.2

Package: %s
Architecture: all
Depends: ${misc:Depends},
 univention-management-console
Description: UCS Management Console translation files
 This package is part of Univention Corporate Server (UCS),
 an integrated, directory driven solution for managing
 corporate environments. For more information about UCS,
 refer to: http://www.univention.de/""" % (translation_package_name, translation_creator, translation_creator, socket.getfqdn(), translation_package_name))
	# compat
	with open(os.path.join(new_package_dir_debian, 'compat'), 'w') as f:
		f.write("7")
	with open(os.path.join(new_package_dir_debian, '%s.postinst' % translation_package_name), 'w') as f:
		f.write("""#!/bin/sh
#DEBHELPER#

eval $(ucr shell locale)
new_locale="%s"
case "${locale}" in
	*"${new_locale}"*) echo "Locale ${new_locale} already known" ;;
	*)	ucr set locale="${locale} ${new_locale}" ;;
esac

ucr set umc/server/languages/%s_%s?"%s"

exit 0""" % (target_locale, target_language.lower(), target_language.upper(), language_name))

	language_dict = {"lang": target_language}
	with open(os.path.join(new_package_dir_debian, '%s.install' % translation_package_name), 'w') as f:
		f.write("""usr/share/univention-management-console-frontend/js/umc/* usr/share/univention-management-console-frontend/js/umc	
usr/share/univention-management-console/i18n/%(lang)s/* usr/share/univention-management-console/i18n/%(lang)s
usr/share/locale/%(lang)s/LC_MESSAGES/* usr/share/locale/%(lang)s/LC_MESSAGES""" % language_dict )

	with open(os.path.join(new_package_dir_debian, '%s.dirs' % translation_package_name), 'w') as f:
		f.write("""usr/share/univention-management-console-frontend/js/umc/modules/i18n/%(lang)s
usr/share/univention-management-console-frontend/js/umc/i18n/%(lang)s
usr/share/univention-management-console-frontend/js/umc/help
usr/share/univention-management-console/i18n/%(lang)s
usr/share/locale/%(lang)s/LC_MESSAGES
""" % language_dict)

	### Move source files and installed .mo files to new package dir
	shutil.copytree(os.path.join(startdir, 'usr'), os.path.join(new_package_dir, 'usr'))
	shutil.rmtree(os.path.join(startdir, 'usr'))

	shutil.copytree(os.path.join(startdir, target_language), os.path.join(new_package_dir, target_language))
	shutil.rmtree(os.path.join(startdir, target_language))

def get_template(module, source_dir, start_dir, target_language):
	curr_dir = os.getcwd()
	package_base_path = os.path.join(source_dir, module['packagedir'])
        os.chdir(package_base_path)
	module['language'] = target_language

	# find source file
	source_file_dir = os.path.join(package_base_path, module['inputfile'])
	if not os.path.exists(source_file_dir):
		raise Exception("Could not find template/file %s" % source_file_dir)

	output_dir = os.path.join(start_dir, target_language, module['packagedir'], module['targetfile'] % module)
	if not os.path.exists(os.path.dirname(output_dir)):
		os.makedirs(os.path.dirname(output_dir))

	print "copy from %s" % source_file_dir
	print "copy to %s" % output_dir

	shutil.copy(source_file_dir, output_dir)

	os.chdir(curr_dir)
	
def install_template(module, start_dir, target_language):
	curr_dir = os.getcwd()
	package_base_path = start_dir
	os.chdir(package_base_path)
	module['language'] = target_language

	source_file_dir = os.path.join(package_base_path, 
		target_language, 
		module['packagedir'], 
		module['inputfile'] % module)

	output_name = os.path.join(package_base_path, module['outputfile'] % module)
	if not os.path.exists(os.path.dirname(output_name)):
		os.makedirs(os.path.dirname(output_name))

	print "copy from %s" % source_file_dir
	print "copy to %s" % output_name
	shutil.copy(source_file_dir, output_name)

	os.chdir(curr_dir)
