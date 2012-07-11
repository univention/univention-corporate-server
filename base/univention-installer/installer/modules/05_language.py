#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: timezone selection
#
# Copyright 2004-2012 Univention GmbH
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

#
# Results of previous modules are placed in self.all_results (dictionary)
# Results of this module need to be stored in the dictionary self.result (variablename:value[,value1,value2])
#

from objects import *
from local import _
import linecache
HEIGHT = 26
WIDTH = 40


class object(content):

	def checkname(self):
		return ['language']

	def profile_complete(self):
		return True

	def run_profiled(self):
		# set default (may be overridden by self.set_language()
		self.write_language_files("en_US.UTF-8", "en")

		lang_dict, langConfig, selectedLine, defaultLanguage = self.get_language_settings()
		language = defaultLanguage

		if self.cmdline.has_key('lang'):
			language = self.cmdline["lang"]
			if langConfig.get(language, ""):
				self.set_language(language)

	def get_language_settings(self):
		dict = {}
		langConfig = {}

		# this file comes from debian localechooser
		# langcode;language (en);language (orig);supported_environments;countrycode;fallbacklocale;langlist;console-data
		try:
			file = open('locale/languagelist')
		except:
			file = open('/lib/univention-installer/locale/languagelist')
		languages = file.readlines()

		# preselected language (kernel option lang)
		presLanguage = self.cmdline.get("lang", "en")

		counter = 0
		for line in languages:
			line = line.strip("\n")
			if line.startswith("#"): continue
			entries = line.split(';')
			langcode = entries[0]
			language_en = entries[1]
			language_orig = entries[2]
			supported_environments = entries[3]
			countrycode = entries[4]
			fallbacklocale = entries[5]
			langlist = entries[6]
			console_data = entries[7]

			# support only languages which are supported in debian text mode
			# installation
			if int(supported_environments) >= 4:
				continue

			counter = counter + 1
			#dict[language_en + " (" + language_orig + ")"] = [langcode, counter]
			dict[language_en] = [langcode, counter]
			langConfig[langcode] = {}
			langConfig[langcode]["fallbacklocale"] = fallbacklocale
			langConfig[langcode]["countrycode"] = countrycode
			langConfig[langcode]["language_en"] = language_en

			if langcode == presLanguage:
				selectedLangLine = counter

		return dict, langConfig, selectedLangLine, presLanguage

	def layout(self):
		dict, langConfig, selectedLine, defaultLanguage = self.get_language_settings()

		if self.all_results.has_key('language'):
			self.default = self.all_results['language']
		else:
			self.default = defaultLanguage

		self.elements.append(textline(_('Select system language'),self.minY-11,self.minX+5))
		self.elements.append(textline(_('(also applies to the installation process for supported languages):'),self.minY-10,self.minX+5))
		self.add_elem('LANGUAGE',select(dict, self.minY-8, self.minX+5, WIDTH, HEIGHT, selectedLine))

		self.move_focus(self.get_elem_id('LANGUAGE'))

	def input(self,key):
		if key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		else:
			return self.elements[self.current].key_event(key)

	def incomplete(self):
		return 0

	def helptext(self):
		return _('Language \n \n Select the language for your system.')

	def modheader(self):
		return _('Language')

	def profileheader(self):
		return 'Language'

	def get_default_kmap(self, language):
		try:
			file = open('locale/default-kmaps')
		except:
			file = open('/lib/univention-installer/locale/default-kmaps')

		for line in file:
			line = line.strip("\n")
			parts = line.split(":")
			if len(parts) > 1:
				if parts[0][0:4].upper() == language[0:4].upper():
					return parts[1]

		return "us"

	def set_language(self, language):
		dict, langConfig, selectedLine, defaultLanguage = self.get_language_settings()

		if not langConfig.get(language, ""):
			language = defaultLanguage

		defaultLocale = langConfig[language]["fallbacklocale"]
		defaultLanguageEn = langConfig[language]["language_en"]
		defaultCountryCode = langConfig[language]["countrycode"]
		defaultKmap = self.get_default_kmap(defaultLanguageEn)

		self.cmdline["DEFAULT_LOCALE"] = defaultLocale
		self.cmdline["DEFAULT_KMAP"] = defaultKmap
		self.cmdline["DEFAULT_LANGUAGE_EN"] = defaultLanguageEn
		self.cmdline["DEFAULT_COUNTRYCODE"] = defaultCountryCode
		self.cmdline["DEFAULT_LANGUAGE"] = language

		self.debug('Set LANGUAGE to %s\n' % language)

		# set language
		os.environ['LANGUAGE'] = "%s" % language

		self.write_language_files(defaultLocale, language)

		# set kmap (get a the default kmap)
		kmapFile = "/usr/keymaps/" + defaultKmap + ".kmap"
		if os.path.exists(kmapFile):
			os.system('/bin/loadkeys < %s 2>&1 > /dev/null' % kmapFile)

	def write_language_files(self, defaultLocale, language):
		# write default_locale to /etc/locale.gen in installer ramdisk
		# ==> required for translated installation progress dialog
		fp = open('/etc/locale.gen', 'w')
		fp.write("%s UTF-8\n" % defaultLocale)
		fp.close()

		# this is needed for the installation end message
		fp = open('/tmp/language', 'w')
		fp.write("%s" % language)
		fp.close()

	def result(self):
		result = {}
		language = self.get_elem('LANGUAGE').result()[0]
		self.set_language(language)
		result['language'] = language
		return result
