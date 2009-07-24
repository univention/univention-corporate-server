#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages Univention Config Registry variables
#
# Copyright (C) 2006-2009 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# python imports
import locale
import md5
import operator
import os
import string
import copy
from time import sleep

import subprocess
import notifier
import notifier.popen

# module specific imports
## translation
import translation as trans
## ucr
from univention.config_registry import ConfigRegistry
#import univention.config_registry as ucr
## debug
import univention.debug as ud
## dialog types
import _types

# umc specific imports
import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.handlers as umch
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct
import univention.management.console.values as umcv


import notifier.popen

#TODO soll dievorausgewaehlte standard lokale nicht der aktuellen system lokale entsprechen?
# bisher wird sie anhand der vorauswahl asgewählty
_ = umc.Translation( 'univention.management.console.wizards.localization' ).translate

icon = 'localization/module'
short_description = _( 'Localization' )
long_description = _( 'Change the localization settings' )
categories = [ 'wizards' ]

add_locale_country_ddb = _types.DropDownBox(_("Additional locales:"))
add_locale_multi_ddb = _types.MultiValueList("", [], required=False)

command_description = {
	'localization/modify/choose_language' : umch.command(
		short_description = _( 'Modify localization' ),
		long_description = _( 'Selection of the preferred language' ),
		method = 'choose_language',
		values = { },
		startup = True
	),
	'localization/modify/choose_locale' : umch.command(
		short_description = _( 'Modify localization' ),
		long_description = _( 'Modification of the localization' ),
		method = 'choose_locale',
		values = { 
		'add_locale_country' : add_locale_country_ddb,
		'add_locale_multi' : add_locale_multi_ddb },
	),
	'localization/modify/set_locale' : umch.command(
		short_description = _( 'Modify localization' ),
		long_description = _( 'Modification of the localization' ),
		method = 'set_locale',
	),
}

class handler( umch.simpleHandler):
	force_encoding = "utf-8"
	timezone_err = ""

	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )

	def choose_language( self, object ):
		res = umcp.Response( object )
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_language options: %s' % str( object.options ) )

		# get umc language to preselect the language
		ucr = ConfigRegistry()
		ucr.load()
		umc_locale = ucr.get("umc/web/language")
		if umc_locale == None or len(umc_locale) < 1:
			umc_locale = "en_GB"
		# get all supported utf8 locales
		supported_locales = self.get_available_locales(filter=self.force_encoding)

		# create a list of languages based on the supported locales
		language_sel_items = []
		already_selected = []
		for supported_locale in supported_locales:
			ud.debug( ud.ADMIN, ud.INFO, "supported_locale: %s" % supported_locale)
			if len(supported_locale) >= 5:
				long_key = supported_locale[0:5]
			if len(supported_locale) >= 2:
				short_key = supported_locale[0:2]

			# try to find a translation of the language based on xx_XX
			if long_key and long_key in trans.language_code_to_name:
				if not long_key in already_selected:
					already_selected.append(long_key)
					# find translation in the following order - original language/umc language/engilish(GB)/english (default)
					lname_id = trans.language_code_to_name[long_key]["default"]
					lname = lname_id
					if long_key in trans.language_code_to_name[long_key]:
						lname = trans.language_code_to_name[long_key][long_key]
					elif umc_locale in trans.language_code_to_name[long_key]:
						lname = trans.language_code_to_name[long_key][umc_locale]
					elif "en_GB" in trans.language_code_to_name[long_key]:
						lname = trans.language_code_to_name[long_key]["en_GB"]
					elif "en" in trans.language_code_to_name[long_key]:
						lname = trans.language_code_to_name[long_key]["en"]
					if lname != "":
						language_sel_items.append(["%s - (%s)" % (_(lname_id), lname), long_key])
			# try to find a translation of the language based on xx
			elif short_key and short_key in trans.language_code_to_name:
				if not short_key in already_selected:
					already_selected.append(short_key)
					# find translation in the following order - original language/umc language/engilish(GB)/english
					lname_id = trans.language_code_to_name[short_key]["default"]
					lname = lname_id
					if short_key in trans.language_code_to_name[short_key]:
						lname = trans.language_code_to_name[short_key][short_key]
					elif umc_locale in trans.language_code_to_name[short_key]:
						lname = trans.language_code_to_name[short_key][umc_locale]
					elif "en_GB" in trans.language_code_to_name[short_key]:
						lname = trans.language_code_to_name[short_key]["en_GB"]
					elif "en" in trans.language_code_to_name[short_key]:
						lname = trans.language_code_to_name[short_key]["en"]
					if lname != "":		  
						language_sel_items.append(["%s - (%s)" % (_(lname_id), lname), short_key])
			else:
				ud.debug( ud.ADMIN, ud.WARN, 'could not find a language name for locale %s' % supported_locale)
				language_sel_items.append( [_("Unknown locale - %s") % supported_locale , supported_locale[0:2] ])

		language_sel_items.sort()

		# find the best default selection based on the umc language
		# eg. if umc_locale is de_DE.UTF-8 then choose de_DE instead of de (if de_DE is available)
		default_selection = ""
		for language_sel_item in language_sel_items:
			if umc_locale.startswith(language_sel_item[1]) and len(language_sel_item[1]) > len(default_selection):
				default_selection = language_sel_item[1]


		if len(default_selection) > 0:
			language_sel = umcd.Selection(('language_code', _types.DropDownBox(_("Please choose your preferred language:"),language_sel_items)), default = default_selection)
		else:
			language_sel = umcd.Selection(('language_code', _types.DropDownBox(_("Please choose your preferred language:"),language_sel_items)))


		# create an icon
		lang_img = umcd.Image( 'localization/flag', umct.SIZE_NORMAL )

		# create a next button
		next_cmd = umcp.Command( args = [ 'localization/modify/choose_locale' ] )
		next_act = umcd.Action( next_cmd, [ language_sel.id() ] ) 
		next_btn = umcd.Button( _( 'Next' ), 'actions/ok', actions = [ next_act ] )

		# build the page
		result = umcd.List()
		result.add_row( [ lang_img, language_sel ] )
		result.add_row( [ next_btn ] )

		res.dialog = [ result ]
		# create a result including the new page (no revamp function needed)
		self.finished( object.id(), res, success = True)
	
	def choose_locale( self, object):
		res = umcp.Response( object )
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale options: %s' % str( object.options ) )
		

		# create a list of possible locales based on the language code
		full_locale_list = self.get_available_locales(filter=self.force_encoding)
		language_locales = []
		if object.options != None and "language_code" in object.options:
			language_code = object.options["language_code"]
		else:
			language_code = "en"

		################################
		# Default locale drop down box #
		################################
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale create default locale drop down box' )
		# get locale/default
		ucr = ConfigRegistry()
		ucr.load()
		locale_default = ucr.get("locale/default")
		if locale_default == None or len(locale_default) < 5:
			locale_default = ""
		else:
			locale_default = locale_default[0:4]

		# get a list of all supported locales and sort out which do not belong to this country code
		for item in self.get_available_locales(filter=self.force_encoding):
			if item.startswith(language_code) or (locale_default != "" and item.startswith(locale_default)):
				language_locales.append(item)

		# create a drop down box to select the default locale (LanguageName (CountryName))
		default_locale_items = []
		for language_locale in language_locales:
			## get the language id
			language_id = language_locale[0:2].lower()
			## get the country code
			country_id = language_locale[3:5].upper()
			## get the translation (id) based on the country id
			if country_id in trans.country_tab:
				country_name = trans.country_tab[country_id]
			else:
				country_name = language_locale
			## add to the list of default locales
			if language_id in trans.language_code_to_name:
				language_name = trans.language_code_to_name[language_id]["default"]
				default_locale_items.append( ["%s (%s)" % (_(language_name),_(country_name)), language_locale])
			else:
				default_locale_items.append( [_("Unknown language code %s (%s)") % (language_id ,_(country_name)), language_locale])

		# preselect a locale
		for item in default_locale_items:
			if item[1].startswith(language_code):
			    sel = item[1]
			    break
		locale_default = sel


		# create the drop down box
		if locale_default != None:
			default_locale_sel = umcd.Selection(('locale_default', _types.DropDownBox(_("Default locale:"), default_locale_items)), default = locale_default)		
		else:
			default_locale_sel = umcd.Selection(('locale_default', _types.DropDownBox(_("Default locale:"), default_locale_items)))		
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale create default locale drop down box - done' )

		###############################
		# unsupported locale warnings #
		###############################
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale generate warnings')
		unsupported_locales = []
		unsupported_default_locale = False
		all_supported_locales = self.get_available_locales()
		# if locale_default is not None and not supported
		if locale_default and not locale_default in all_supported_locales:
			unsupported_default_locale = True
		system_locales = self.get_system_locales()
		for locale in system_locales:
			if locale not in all_supported_locales:
				unsupported_locales.append(locale)
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale generate warnings - done')

		##########################
		# Timezone drop down box #
		##########################
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale create timezone drop down box')

		# create a timezone drop down box based on the entrys in the pre-selected default locales
		time_zones = []
		for language_locale in language_locales:
			## get the country code
			country_code = language_locale[3:5].upper()
			if country_code in trans.zone_tab:
				## get timezone by country code
				country_timezones = trans.zone_tab[country_code]
				for country_timezone in country_timezones:
					ud.debug( ud.ADMIN, ud.INFO, "append country_timezone check: %s" % country_timezone)
					## sort out timezones by country timezone
					if not country_timezone in time_zones:
						ud.debug( ud.ADMIN, ud.INFO, "append country_timezone add: %s" % country_timezone)
						time_zones.append(country_timezone)
		## find the default timezone
		### get local timezone
		local_timezone = ""
		if os.path.exists("/etc/timezone"):
			local_timezone = open("/etc/timezone").readline().strip()
			found = False
			if local_timezone != "":
				for time_zone in time_zones:
					if time_zone == local_timezone:
						found = True
						break
				if not found:
					time_zones.append(local_timezone)

		## translate the names in the timezone drop down box
		ud.debug( ud.ADMIN, ud.INFO, "translate the names in the timezone drop down box")
		tmp = time_zones
		time_zones = []
		for item in tmp:
			i = item.split("/")
			if len(i) == 2:	
				time_zones.append(["%s/%s" % (_(i[0]),_(i[1])),item])
		time_zones.sort()
		ud.debug( ud.ADMIN, ud.INFO, "done")

		## create the drop down box
		if local_timezone != None and local_timezone != "":
			timezone_sel = umcd.Selection(('timezone', _types.DropDownBox(_("Timezone:"), time_zones)), default = local_timezone)
		else:
			timezone_sel = umcd.Selection(('timezone', _types.DropDownBox(_("Timezone:"), time_zones)))

		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale create timezone drop down box - done')

		#################################
		# Keyboard layout drop down box #
		#################################
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale create kyboard layout drop down box')

		#get default keymap
		ucr = ConfigRegistry()
		ucr.load()
		keymap_default = ucr.get("locale/keymap")
		if keymap_default == None:
			keymap_default = ""
		keymap_default.strip()

		tmp = self.get_keymaps()
		keymaps = []
		keymap_default_found = False
		for key in tmp:
			item = tmp[key]
			if type(item) == type({}) and "file" in item and "dir" in item:
				filename = item['file'].split(".")[0].strip()
				name = "%s:%s" % (item['dir'], filename)
				if filename == keymap_default:
					keymap_default_found = True
				keymaps.append([name, filename])
		keymaps.sort()

		if keymap_default_found:
			ud.debug( ud.ADMIN, ud.INFO, "step - 3")
			keymap_sel = umcd.Selection(('keymap', _types.DropDownBox(_("Keyboard layout:"), keymaps)), default = keymap_default)
		else:
			ud.debug( ud.ADMIN, ud.INFO, "step - 4")
			keymap_sel = umcd.Selection(('keymap', _types.DropDownBox(_("Keyboard layout:"), keymaps)))		
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale create kyboard layout drop down box - done')

		######################################
		# Additional locales multi value box #
		######################################

		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale create additional locales multi value box')
		# create a drop down box and select the default locale (LanguageName (CountryName))
		full_language_country_list = []
		already_added = []
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale generate a list of all available locales')
		for language_locale in self.get_available_locales(filter=self.force_encoding):
			ud.debug( ud.ADMIN, ud.INFO, "localization/modify/choose_locale get country_id")
			## get the country code
			country_id = language_locale[3:5].upper()
			ud.debug( ud.ADMIN, ud.INFO, "localization/modify/choose_locale country_id='%s'" % country_id)
			## get the language id
			language_id = language_locale[0:2].lower()
			ud.debug( ud.ADMIN, ud.INFO, "localization/modify/choose_locale language_id='%s'" % language_id)
			## get the translation (id) based on the country id
			if country_id in trans.country_tab:
				country_name = trans.country_tab[country_id]
			else:
				country_name = language_locale
			ud.debug( ud.ADMIN, ud.INFO, "localization/modify/choose_locale country_name='%s'" % country_name)
			## add "Language (Country)" to the list
			ud.debug( ud.ADMIN, ud.INFO, "localization/modify/choose_locale find translation for %s" % language_id)
			if language_id in trans.language_code_to_name:
				ud.debug( ud.ADMIN, ud.INFO, "localization/modify/choose_locale found")
				language_name = trans.language_code_to_name[language_id]["default"]
				ud.debug( ud.ADMIN, ud.INFO, "localization/modify/choose_locale using language_name='%s'" % language_name)
				if  "%s%s" % (language_name, country_name) not in already_added:
					full_language_country_list.append( [ "%s (%s)" % ( _(language_name), _(country_name) ), language_locale ] )
					already_added.append("%s (%s)" % ( _(language_name), _(country_name) ))
			else:
				full_language_country_list.append( [_("Unknown language code %s (%s)") % (language_id ,_(country_name)), language_locale])
				already_added.append("Unknown language code %s (%s)" % (language_id ,_(country_name)))
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale generate a list of all available locales - done')

		# sort by item[0] (language string)
		full_language_country_list.sort()

		visible_system_locales = [] # a list of all locales (ucr-variable locales - only utf8 - filtered by full_language_country_list)
		hidden_system_locales = [] # a list of all system locales which are not in the visible_system_locales list (e.g. non utf8 locales)
		for item in system_locales:
			item = item.strip()
			for items in full_language_country_list:
				if items[1].strip() == item:
					visible_system_locales.append([items[1],items[0]])

		hidden_system_locales = copy.copy(system_locales)
		for item in visible_system_locales:
			if item[0] in hidden_system_locales:
				hidden_system_locales.remove(item[0])
		for item in unsupported_locales:
			if item in hidden_system_locales:
				hidden_system_locales.remove(item)
					
		# create the "language (country)" selection box
		add_locale_country_ddb.set_choices(full_language_country_list)
		add_locale_country = umcd.make(self["localization/modify/choose_locale"]["add_locale_country"]) 

		# create the multi value drop down box
		add_locale_items = copy.copy(visible_system_locales)
		for unsupported_locale in unsupported_locales:
			add_locale_items.append([unsupported_locale, unsupported_locale])
		add_locale = umcd.make(	self["localization/modify/choose_locale"]["add_locale_multi"], 
					fields = [ add_locale_country ], 
					default = add_locale_items )
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale create additional locales multi value box - done')

		#####################
		# ok/cancel Buttons #
		#####################
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale generate buttons')
		# create ok button
		ok_cmd = umcp.Command( 	args = [ 'localization/modify/set_locale' ], 
					opts = { 'hidden_system_locales' : hidden_system_locales,
						 'language_code' : language_code } )
		ok_act = umcd.Action( ok_cmd, [ default_locale_sel.id(), timezone_sel.id(), keymap_sel.id(), add_locale.id() ] ) #TODO geht nicht 
		ok_btn = umcd.SetButton( actions = [ ok_act ] )

		# create cancel button
		cancel_cmd = umcp.Command( args = [ 'localization/modify/choose_language' ] )
		cancel_act = umcd.Action( cancel_cmd, [ ] ) 
		cancel_btn = umcd.Button( label = _( 'Back' ), tag = 'actions/cancel', actions = [ cancel_act ] )
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale generate buttons - done')

		#####################
		# build page layout #
		#####################
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale generate page')
		result = umcd.List()

		# warnings
		if unsupported_default_locale:
			result.add_row([umcd.Text(_("Warning: The Univention-Config-Registry variable locale/default contains the unsupported locale '%s'.") % locale_default)])
		if len(unsupported_locales) > 0:
			for locale in unsupported_locales:
				result.add_row([umcd.Text(_("Warning: The Univention-Config-Registry variable 'locale' contains the unsupported value '%s'.") % locale)])

		# other elements
		result.add_row( [ default_locale_sel ] )
		result.add_row( [ timezone_sel ] )
		result.add_row( [ keymap_sel ] )
		result.add_row( [ add_locale ] )
		result.add_row( [ ok_btn, cancel_btn] )

		# return the page
		res.dialog = [result]
		self.finished( object.id(), res, success = True)
		ud.debug( ud.ADMIN, ud.INFO, 'localization/modify/choose_locale generate page - done')

	# apply the new localization settings
	def set_locale( self, object):
		res = umcp.Response( object )
		result = umcd.List()
		ok = True
		if object.options:
			locale_default = object.options.get("locale_default")
			keymap = object.options.get("keymap")
			add_locale_multi = object.options.get("add_locale_multi")
			timezone = object.options.get("timezone")
			hidden_system_locales = object.options.get("hidden_system_locales")
			if not hidden_system_locales:
			    hidden_system_locales = []
			language_code = object.options.get("language_code")

			if locale_default and keymap and add_locale_multi and timezone and language_code:
				# formating default locale
				locale_default_str = locale_default.replace(" ",":").strip()
				ud.debug( ud.ADMIN, ud.INFO, "formated locale/default='%s'" % locale_default_str)
	
				# formating timezone
				timezone_str = timezone.strip()
				ud.debug( ud.ADMIN, ud.INFO, "formated timezone='%s'" % timezone)
	
				# formating keymap
				keymap_str = keymap.strip()
				ud.debug( ud.ADMIN, ud.INFO, "formated locale/keymap='%s'" % keymap_str)
	
				# formating additional locales
				system_locales = []
				for locale in hidden_system_locales:
					system_locales.append(locale.replace(" ",":"))
				for locale in add_locale_multi:
					locale = locale.replace(" ",":")
					if not locale in system_locales:
						system_locales.append(locale.replace(" ",":"))
				if locale_default_str not in system_locales:
					system_locales.append(locale_default_str)
				system_locales.sort()
	
				system_locales_str = ""
				for locale in system_locales:
					system_locales_str += "%s " % locale
				system_locales_str = system_locales_str.replace("\"","\\\"").strip()
				ud.debug( ud.ADMIN, ud.INFO, "<br>Setting ucr locale='%s'" % system_locales_str)
	
	
				# setting default locale
				default_locale_proc = subprocess.Popen( ["/usr/sbin/univention-config-registry set locale/default=\"%s\"" % locale_default_str ], 
									stdout=subprocess.PIPE, 
									stderr=subprocess.PIPE, 
									shell=True )
				default_locale_proc.wait()
				default_locale_out, default_locale_err = default_locale_proc.communicate()
				if default_locale_err:

					result.add_row( [ umcd.Text(_("An error has occurred. The default system locale could not be generated.")) ] )
					result.add_row( [ umcd.Text(_("Error message: %s" % default_locale_err)) ] )
					ok = False

				# setting timezone
				timezone_err = self.set_timezone(timezone_str)
				if timezone_err != "":
					result.add_row( [ umcd.Text(_("An error has occurred. The timezone could not be set.")) ] )
					result.add_row( [ umcd.Text(_("Error message: %s" % timezone_err)) ] )
					ok = False

				# setting keymap
				keymap_proc = subprocess.Popen( ["TERM=xterm /usr/sbin/univention-config-registry set locale/keymap=\"%s\"" % keymap_str], 
								stdout=subprocess.PIPE, 
								stderr=subprocess.PIPE, 
								shell=True )
				keymap_proc.wait()
				keymap_proc_out, keymap_proc_err = keymap_proc.communicate()
				if keymap_proc_err:
					result.add_row( [ umcd.Text(_("An error has occurred. The keymap could not be set.")) ] )
					result.add_row( [ umcd.Text(_("Error message: %s" % keymap_proc_err)) ] )
					ok = False
	
				# setting additional locales
				additional_locale_proc = subprocess.Popen( [	"/usr/sbin/univention-config-registry set locale=\"%s\"" % system_locales_str ], 
										stdout=subprocess.PIPE, 
										stderr=subprocess.PIPE, 
										shell=True )
				additional_locale_proc.wait()
				additional_locale_out, additional_locale_err = additional_locale_proc.communicate()
				if additional_locale_err:
					result.add_row( [ umcd.Text(_("An error has occurred. The additional system locales could not be generated.")) ] )
					result.add_row( [ umcd.Text(_("Error message: %s" % additional_locale_err)) ] )
					ok = False
				if ok:
					self.choose_locale(object)
			else:
			    if not locale_default:
				result.add_row( [ umcd.Text(_("Missing parameter locale_default.")) ] )
				ok = False
			    if not keymap:
				result.add_row( [ umcd.Text(_("Missing parameter keymap.")) ] )							
				ok = False
			    if not add_locale_multi:
				result.add_row( [ umcd.Text(_("Missing parameter add_locale_multi.")) ] )
				ok = False
			    if not timezone:		
				result.add_row( [ umcd.Text(_("Missing parameter timezone.")) ] )
				ok = False
			    if not language_code:
				result.add_row( [ umcd.Text(_("Missing parameter language_code.")) ] )
				ok = False
			    else:
				result.add_row( [ umcd.Text(_("An internal Error has occurred.")) ] )
				ok = False
		else:
		    result.add_row( [ umcd.Text(_("An internal Error has occurred.")) ] )
		    ok = False
#		else:
		result.add_row( [ umcd.Text(_("An internal Error has occurredsaasassa.")) ] )
		ok = False
	
		res.dialog = [result]
		self.finished( object.id(), res, success = ok)
# TODO report feature benutzen
#		self.finished( object.id(), None, report="Fehler - FALSE", success = False)

	# return values are None, [], or ["xx_YY.UTF8", ...]
	def get_available_locales(self, filter="") :
		locale_support_file="/usr/share/i18n/SUPPORTED"
		if os.path.exists(locale_support_file):
			supported_locales = []
			for line in open(locale_support_file).readlines():
				if len(line.strip()) > 0:
					if filter == "":
						supported_locales.append(line.strip())
					elif filter != None:
						encoding = line[6:6+len(filter)]
						if encoding.lower() == filter:
							supported_locales.append(line.strip())

					
			return supported_locales
		else:
			return []


	# retruns all keymaps and the default keymap
	# e.g. { 'hash' : {'dir': 'qwerty', 'file': 'sk-prog-qwerty.kmap.gz}, ...}
	def get_keymaps(self):
		md5_dictonary={}
		if os.path.exists('/etc/console/boottime.kmap.gz'):
			for dir in os.listdir('/usr/share/keymaps/i386/'):
				if os.path.isdir(os.path.join('/usr/share/keymaps/i386/', dir)):
					for file in os.listdir(os.path.join('/usr/share/keymaps/i386/', dir)):
						filename=os.path.join(os.path.join('/usr/share/keymaps/i386/', dir), file)
						md5_sum=md5.md5(string.join(open(filename).readlines())).hexdigest()
						if dir != "include":
							md5_dictonary[md5_sum]={'file' : file, 'dir': dir}
		return md5_dictonary

	# retuns the system locales e.g. ['de_DE.UTF-8 UTF-8', 'de_DE@euro ISO-8859-15']
	def get_system_locales(self):
		ucr = ConfigRegistry()
		ucr.load()
		system_locales = ucr.get("locale")
		if system_locales == None:
			system_locales = []
		else:
			tmp = []
			for item in system_locales.split(" "):
				tmp.append(item.replace(":"," "))
			system_locales = tmp
		return system_locales

	# sets the system timezone based on the univention-system-setup-timezone scripts
	def set_timezone( self, timezone):
		fp = open( '/var/cache/univention-system-setup/profile', 'w' )
		fp.write( "UMC_MODE=true\n" )
		fp.write("timezone=%s" % timezone)
		fp.close()

		cb = notifier.Callback( self._set_timezone, None )
		func = notifier.Callback( self._set_timezone_run, None )
		thread = notifier.threads.Simple( 'timezone', func, cb )
		thread.run()
		while not thread.finished():
			sleep(0.2)
		ud.debug( ud.ADMIN, ud.INFO, "return: '%s'" % thread._result )
		return thread._result

	# belongs to set_timezone
	def _set_timezone_run( self, object ):
		_path = '/usr/lib/univention-system-setup/scripts/timezone/'
		failed = []
		for script in os.listdir( _path ):
			filename = os.path.join( _path, script )
			ud.debug( ud.ADMIN, ud.INFO, 'run script: %s' % filename )
			if os.path.isfile( filename ):
				if os.system( filename ):
					failed.append( script )
		if len(failed) > 0:
			return _( 'The following scripts failed: %(scripts)s' ) % { 'scripts' : ', '.join( failed )}
		else:
			return ""

	# belongs to set_timezone
	def _set_timezone( self, thread, result, object ):
		return
