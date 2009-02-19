# -*- coding: utf-8 -*-
#
# Univention Package Database
#  Univention Console module
#
# Copyright (C) 2004-2009 Univention GmbH
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

import os, time, glob, copy, pickle, sre
import unimodule
import commands
from uniparts import *
from local import _
from syntax import *

import univention_baseconfig
import univention_pkgdb

SAVEPATH="/var/lib/univention-console"
PREFIX='SavedSearch-'
SUFFIX='.pickle'
class saveset:
	def __init__(self,path=SAVEPATH,prefix=PREFIX,suffix=SUFFIX):
		self.path=path
		self.prefix=prefix
		self.suffix=suffix

	def save(self, name, object ):
		filename = self.path + '/' + self.prefix + name + self.suffix
		try:
			file = open( filename, 'w' )
			pickle.dump( object, file )
		except Exception, e:
			univention_pkgdb.log( 'CMD: cannot save object to file ' + filename)
		file.close()

	def load(self,name ):
		filename = self.path + '/' + self.prefix + name + self.suffix
		try:
			file = open( filename, 'r' )
			object = pickle.load( file )
		except Exception, e:
			univention_pkgdb.log( 'CMD: cannot read object from file ' + filename)
		file.close()
		return object

	def list(self):
		pattern = self.path + '/' + self.prefix + '*' + self.suffix
		files=glob.glob(pattern)
		sets=[]
		for file in files:
			if os.path.isfile(file):
				tmp=sre.sub(self.path + '/' + self.prefix, '', file)
				name=sre.sub(self.suffix, '', tmp)
				sets.append(name)
		return sets

	def delete(self,name ):
		filename = self.path + '/' + self.prefix + name + self.suffix
		try:
			os.unlink( filename )
		except Exception, e:
			univention_pkgdb.log( 'CMD: cannot delete file ' + filename)

class simple:
	type='simple'

	def tostring(self, text):
		return text
	def new(self):
		return ''
	def any(self):
		return '*'

def create(a,b,c):
	return modpkgdb(a,b,c)

def myinfo():
	submodlist = []
	submodlist.append( unimodule.submodule( 'sys', _('Search systems'), _('System search') ))
	submodlist.append( unimodule.submodule( 'search',_('Search packages'),  _('Package search') ))
	submodlist.append( unimodule.submodule( 'problem',_('Problem identification'),  _('Problem identification') ))
	modlist = [ unimodule.virtualmodule("pkgdb", _('Softwaremonitor'), _('software packages in all systems'), submodlist) ]
	return unimodule.realmodule( "pkgdb", _('Softwaremonitor'), _('software packages in all systems'), virtualmodules=modlist )

def myrgroup():
	return ""

def mywgroup():
	return ""

def mymenunum():
	return 800

def mymenuicon():
	return 'icon/pkgdb.gif'

class modpkgdb(unimodule.unimodule):

	def mytype(self):
		return "dialog"

# Grundsätzlicher Ablauf: in myinit(self) wird die Benutzeroberfläche aufgebaut,
# sprich, es werden alle Eingabefelder, Buttons, usw. definiert, die der Benutzer
# sehen soll.
# In apply(self) werden diese Felder ausgewertet und abhängig davon Aktionen gestartet

	def myinit(self):

				#  #  #  #  #  #
		self.save=self.parent.save 	#
						##### so stehen lassen!
		if self.inithandlemessages():	#
			return	#  #  #  #  #  #

		if not(self.save.get("doinit")) or self.save.get("doinit")=="yes":
			doinit = True
		else:
			doinit = False

		SelectedStates={ '0': 'Unkown', '1':'Install', '2':'Hold', '3':'DeInstall', '4':'Purge' }
		InstStates={ '0': 'Ok', '1': 'ReInstReq', '2': 'Hold', '3': 'HoldReInstReq' }
		CurrentStates={ '0': 'NotInstalled', '1': 'UnPacked', '2': 'HalfConfigured', '3': 'UnInstalled', '4': 'HalfInstalled', '5': 'ConfigFiles', '6': 'Installed' }

		# only do this the first time we're called:
		if doinit:
			# default values
			self.save.put("doinit","no")

			# Baseconfig auslesen
			baseConfig=univention_baseconfig.baseConfig()
			baseConfig.load()

		else:
			baseConfig = self.save.get("baseConfig")

		menuselection_submodule = self.save.get("uc_submodule")
		menuselection = ''
		if menuselection_submodule and menuselection_submodule!='none':
			menuselection = menuselection_submodule
		else:
			menuselection = self.save.get("menuselection")

		if not menuselection:
			menuselection = 'sys'

		self.subobjs.append(table("",{'type':'content_header'},{"obs":[
				tablerow("",{},{"obs":[
					tablecol("",{'type':'about_layout'},{"obs":[
						header(_("Softwaremonitor"),{"type":"3"},{})
						]})
					]})
				]}))
		# Nach Systemen zeigen
		if menuselection=='sys':
			# ------------------------------------------------------------------------------
			# System-Suchfelder wählen
			# ------------------------------------------------------------------------------
			saverows=[]
			rows=[]
			dirrows=[]

			# ------------------------------------------------------------------------------
			# Suchefilter speichern und wiederholen
			# ------------------------------------------------------------------------------
			saverows.append(tablerow("", {}, {"obs":[
				tablecol("", {'type':'about_layout'}, {"obs":[]})
			]}))
			self.savesys_txt=question_text("", {"width":"400"}, {"usertext":""})
			self.savesys_ins=button(_("Save"), {'icon':'/style/ok.gif'}, {"helptext":""})
			saverows.append(tablerow("", {}, {"obs":[
				tablecol("", {'type':'about_layout'}, {"obs":[self.savesys_txt]}),
				tablecol("", {'type':'about_layout'}, {"obs":[self.savesys_ins]})
			]}))

			savesys_list=[]
			ss = saveset(SAVEPATH,'SavedSys-',SUFFIX)
			savedsyslist=ss.list()
			savesys_list.append({'name': '', 'description': '' })
			for savedsyselement in savedsyslist:
				if savedsyselement==self.save.get("saved_sysselection"):
					savesys_list.append({'name': savedsyselement, 'description': savedsyselement, 'selected': '1' })
				else:
					savesys_list.append({'name': savedsyselement, 'description': savedsyselement })

			self.savesys_button=button('',{},{'helptext':''})
			self.savesys_list=question_select("", {"width":"400"}, {"helptext":'',"choicelist":savesys_list,'button':self.savesys_button})
			self.savesys_del=button(_("Delete"), {'icon':'/style/cancel.gif'}, {"helptext":""})
			saverows.append(tablerow("", {}, {"obs":[
				tablecol("", {'type':'about_layout'}, {"obs":[self.savesys_list]}),
				tablecol("", {'type':'about_layout'}, {"obs":[self.savesys_del]})
			]}))


			self.subobjs.append(notebook('', {}, {'buttons': [(_('Search systems'), _('System search'))], 'selected': 0}))

			savetab=table("",{'type':'content_main'},{"obs":saverows})
			self.subobjs.append(savetab)

			# ------------------------------------------------------------------------------
			# Suchen
			# ------------------------------------------------------------------------------
			visible=self.save.get('browse_search_visible', 20)
			if visible > 100:
				visible=100
			start=self.save.get('browse_table_start', 0)

			search_types=[]
			search_types.append({'name': 'sysname',       'description': _('system-name') })
			search_types.append({'name': 'sysrole',       'description': _('system-type') })
			search_types.append({'name': 'sysversion',    'description': _('ucs-version') })

			query_types=[]
			query_types.append({'name': 'eq',    'description': _('equal') })
			query_types.append({'name': 'ne',    'description': _('not equal') })
			query_types.append({'name': 'gt',    'description': _('bigger') })
			query_types.append({'name': 'lt',    'description': _('lesser') })
			query_types.append({'name': 'ge',    'description': _('bigger or equal') })
			query_types.append({'name': 'le',    'description': _('lesser or equal') })

			# Datenbankzugriff
			sysrole_types=[]
			sysversion_types=[]

			pkgdb_connect_string = univention_pkgdb.sql_create_localconnectstring( baseConfig['hostname']  )
			if len(pkgdb_connect_string)>0:
				systemroles  = univention_pkgdb.sql_getall_systemroles( pkgdb_connect_string )
				if systemroles:
					for s in systemroles:
						sysrole_types.append({'name': s[0],  'description': s[0]})
				systemversions  = univention_pkgdb.sql_getall_systemversions( pkgdb_connect_string )
				if systemversions:
					for s in systemversions:
						sysversion_types.append({'name': s[0],  'description': s[0]})

			self.syschoices=self.save.get("syschoices")
			# syschoices enthält immer Tupel aus search_type und search_value
			# bei erstem Aufruf hier ein default-Paar eintragen
			if not self.syschoices:
				self.syschoices=[("sysname","eq","")]

			self.syssearch_rows=[]
			search_rules=[]

			for search_type, query_type, search_value in self.syschoices:
				search_rule=[]

				search_types_tmp = copy.deepcopy(search_types)
				for i in search_types_tmp:
					if i['name']==search_type:
						i['selected']='1'
				search_type_button=button('',{},{'helptext':''})
				search_type_select=question_select( _('filterobject'),{'width':'200'},{"helptext":'',"choicelist":search_types_tmp,'button':search_type_button})

				query_types_tmp = copy.deepcopy(query_types)
				for i in query_types_tmp:
					if i['name']==query_type:
						i['selected']='1'
				query_type_button=button('',{},{'helptext':''})
				query_type_select=question_select( _('filtercondition'),{'width':'200'},{"helptext":'',"choicelist":query_types_tmp,'button':query_type_button})

				search_del_select=question_bool(_('filter_del'),{},{'helptext':''})

				search_rule.append(tablecol('',{'type':'about_layout'},{'obs':[search_type_select]}))
				search_rule.append(tablecol('',{'type':'about_layout'},{'obs':[query_type_select]}))
				if search_type=='sysrole':
					sysrole_types_tmp = copy.deepcopy(sysrole_types)
					for i in sysrole_types_tmp:
						if i['name']==search_value:
							i['selected']='1'
					sysrole_type_button=button('',{},{'helptext':''})
					sysrole_type_select=question_select( _('filtertext'), {'width':'200'},{"helptext":'',"choicelist":sysrole_types_tmp,'button':sysrole_type_button})
					search_rule.append(tablecol('',{'type':'about_layout'},{'obs':[sysrole_type_select]}))
					search_text=sysrole_type_select
				elif search_type=='sysversion':
					sysversion_types_tmp = copy.deepcopy(sysversion_types)
					for i in sysversion_types_tmp:
						if i['name']==search_value:
							i['selected']='1'
					sysversion_type_button=button('',{},{'helptext':''})
					sysversion_type_select=question_select( _('filtertext'), {'width':'200'},{"helptext":'',"choicelist":sysversion_types_tmp,'button':sysversion_type_button})
					search_rule.append(tablecol('',{'type':'about_layout'},{'obs':[sysversion_type_select]}))
					search_text=sysversion_type_select
				else:
					# damit beim Aufruf bereits ein * in dem Filter steht
					if not search_value:
						search_value='*'

					search_text=question_text( _('filtertext'), {"width":"150"}, {"usertext":search_value})
					search_rule.append(tablecol('',{'type':'about_layout'},{'obs':[search_text]}))

				search_rule.append(tablecol('',{'type':'wizard_layout_bottom'},{'obs':[search_del_select]}))

				search_rules.append(search_rule)

				# Diese Liste wird im apply ausgewertet
				self.syssearch_rows.append((search_type_select, query_type_select, search_text, search_del_select ))

			self.add_syssearch_rule_button=button( _('filter_add'),{'icon':'/style/add.gif'},{'helptext':'Add Search-Rule'})
			self.syssearch_visible=question_text( _('results of page'), {'width':'200'}, {'usertext': str(visible)})
			self.syssearch_button=button(_('search'),{'icon':'/style/ok.gif'},{'helptext':''})


			# ------------------------------------------------------------------------------
			# Suchfilter darstellen
			# ------------------------------------------------------------------------------
			if search_rules:
				for rule in search_rules:
					self.subobjs.append(
						table("",{'type':'content_main'},{"obs":[
							tablerow('',{},{'obs': rule})
						]})
					)

			self.subobjs.append(
				table("",{'type':'content_main'},{"obs":[
					tablerow('',{},{'obs':[
						tablecol('',{'type':'about_layout'},{'obs':[self.add_syssearch_rule_button]})
					]}),
					tablerow('',{},{'obs':[
						tablecol('',{'type':'about_layout'},{'obs':[]})
					]}),
					tablerow('',{},{'obs':[
						tablecol('',{},{'obs':[
							table("",{},{"obs":[
								tablerow('',{},{'obs':[
									tablecol('',{'type':'about_layout'},{'obs':[self.syssearch_visible]}),
									tablecol('',{'type':'wizard_layout_bottom'},{'obs':[self.syssearch_button]})
								]})
							]})
						]})
					]})
				]})
			)

			# ------------------------------------------------------------------------------
			# Suche ausführen
			# ------------------------------------------------------------------------------
			result=self.save.get('browse_syssearch_result')
			if self.save.get('browse_syssearch') == '1' or result:
				cached = 1
				if not result:
					cached = 0
					result=[]

				nresults = len(result)
				if not result:
					nresults=0

					# Datenbankzugriffsmethode ermitteln
					pkgdb_connect_string = univention_pkgdb.sql_create_localconnectstring( baseConfig['hostname']  )
					if len(pkgdb_connect_string)==0:
						return

					query='true'
					for search_type, query_type, search_value in self.syschoices:
						# DB-Operator einordnen
						if query_type=='ne':
							qt='!~'
							re=1
						elif query_type=='gt':
							qt='>'
							re=0
						elif query_type=='lt':
							qt='<'
							re=0
						elif query_type=='ge':
							qt='>='
							re=0
						elif query_type=='le':
							qt='<='
							re=0
						else:
							qt='~'
							re=1

						# leeren Parameter korrigieren
						s = str(search_value)
						if s == 'ascii-null-escape':
							s = '0'
						elif s == 'None':
							s = ''

						if re==1:
							# vereinfachter regulären Ausdruck in Postgres-RE wandeln

							# Sternchen vorne
							s0 = ''
							if len(s) > 0:
								if s[0] == '*':
									s = s[1:]
								else:
									s0 = '^'

							# Sternchen hinten
							s1 = ''
							if len(s) > 0:
								if s[-1] == '*':
									s = s[:-1]
								else:
									s1 = '$'

							# komische Zeichen {string.punctuation ohne '.', '*', '-' und '_'} löschen
							# '*' in '.*' wandeln
							# '.' bleibt RE für beliebiges Zeichen
							sv=''
							for i in s:
								if i not in '!"#$%&\'()+,/:;<=>?@[\\]^`{|}~':
									if i == '*':
										sv = sv +'.*'
									else:
										sv = sv + i
							s = s0 + sv + s1

						else:
							# keine regulären Ausdruck bei größer oder kleiner

							# komische Zeichen {string.punctuation ohne '.', '-' und '_'} löschen
							# '.' maskieren
							sv=''
							for i in s:
								if i not in '!"#$%&\'()+,/:;<=>?@[\\]^`{|}~*':
									if i == '.':
										sv = sv +'\.'
									else:
										sv = sv + i
							s = sv

						sv = '\'' + s + '\''

						if search_type=='sysname' and len(str(search_value))>0 and str(search_value)!='None':
							query += ' and sysname'+qt+sv

						elif search_type=='sysrole' and len(str(search_value))>0 and str(search_value)!='None':
							query += ' and sysrole'+qt+sv

						elif search_type=='sysversion' and len(str(search_value))>0 and str(search_value)!='None':
							query += ' and sysversion'+qt+sv


					#univention_pkgdb.log( 'CMD: myinit: query='+str(query))
					if len(query)>4:
						resultTmp = univention_pkgdb.sql_get_systems_by_query( pkgdb_connect_string, query )
						result = []
						for p in resultTmp:
							result.append(p)
						nresults = len(result)
					else:
						result = []
						nresults = 0

				self.save.put('browse_syssearch_result', result)

				# ------------------------------------------------------------------------------
				# Suche darstellen
				# ------------------------------------------------------------------------------

				rows.append(tablerow("", {}, {"obs":[
					tablecol("", {'type':'bold','colspan':'4'}, {"obs":[
						header(_("%d Search result(s):") % nresults,{"type":"2"},{})
					]})
				]}))

				# Kopfzeile der Tabelle
				rows.append(tablerow("", {}, {"obs":[
					tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('system-name')     ]}) ]}),
					tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('ucs-role')        ]}) ]}),
					tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('current version') ]}) ]}),
					tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('collect date')    ]}) ]})
				]}))

				if result:
					for p in result[start:start+visible]:
						rows.append(tablerow("", {}, {"obs":[
							tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[0]]}) ]}),
							tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[2]]}) ]}),
							tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[1]]}) ]}),
							tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[3]]}) ]})
							]}))
				tabelle=table("",{'type':'content_main'},{"obs":rows})
				self.subobjs.append(tabelle)

				self.dirstab=longtable("",{'total': str(len(result)), 'start': str(start), 'visible': str(visible)},{"obs":dirrows})
				self.subobjs.append(self.dirstab)


		elif menuselection=='search':
			# ------------------------------------------------------------------------------
			# Paket-System-Suchfelder wählen
			# ------------------------------------------------------------------------------
			saverows=[]
			rows=[]
			dirrows=[]

			# ------------------------------------------------------------------------------
			# Suchefilter speichern und wiederholen
			# ------------------------------------------------------------------------------
			saverows.append(tablerow("", {}, {"obs":[
				tablecol("", {}, {"obs":[]})
			]}))
			self.savesearch_txt=question_text("", {"width":"400"}, {"usertext":""})
			self.savesearch_ins=button(_("Save"), {'icon':'/style/ok.gif'}, {"helptext":""})
			saverows.append(tablerow("", {}, {"obs":[
				tablecol("", {'type':'about_layout'}, {"obs":[self.savesearch_txt]}),
				tablecol("", {'type':'about_layout'}, {"obs":[self.savesearch_ins]})
			]}))

			savesearch_list=[]
			ss = saveset()
			savedsearchlist=ss.list()
			savesearch_list.append({'name': '', 'description': '' })
			for savedsearchelement in savedsearchlist:
				if savedsearchelement==self.save.get("saved_searchselection"):
					savesearch_list.append({'name': savedsearchelement, 'description': savedsearchelement, 'selected': '1' })
				else:
					savesearch_list.append({'name': savedsearchelement, 'description': savedsearchelement })

			self.savesearch_button=button('',{},{'helptext':''})
			self.savesearch_list=question_select("", {"width":"400"}, {"helptext":'',"choicelist":savesearch_list,'button':self.savesearch_button})
			self.savesearch_del=button(_("Delete"), {'icon':'/style/cancel.gif'}, {"helptext":""})
			saverows.append(tablerow("", {}, {"obs":[
				tablecol("", {'type':'about_layout'}, {"obs":[self.savesearch_list]}),
				tablecol("", {'type':'about_layout'}, {"obs":[self.savesearch_del]})
			]}))

			savetab=table("",{'type':'content_main'},{"obs":saverows})
			self.subobjs.append(notebook('', {}, {'buttons': [(_('Search packages'),  _('Package search'))], 'selected': 0}))
			self.subobjs.append(savetab)

			# ------------------------------------------------------------------------------
			# Suchen
			# ------------------------------------------------------------------------------
			visible=self.save.get('browse_search_visible', 20)
			if visible > 100:
				visible=100
			start=self.save.get('browse_table_start', 0)

			search_types=[]
			search_types.append({'name': 'pkgname',       'description': _('package-name') })
			search_types.append({'name': 'vername',       'description': _('package-version') })
			search_types.append({'name': 'selectedstate', 'description': _('package-selected-state') })
			search_types.append({'name': 'inststate',     'description': _('package-inst-state') })
			search_types.append({'name': 'currentstate',  'description': _('package-current-state') })
			search_types.append({'name': 'sysname',       'description': _('system-name') })
			search_types.append({'name': 'sysrole',       'description': _('system-type') })
			search_types.append({'name': 'sysversion',    'description': _('ucs-version') })

			query_types=[]
			query_types.append({'name': 'eq',    'description': _('equal') })
			query_types.append({'name': 'ne',    'description': _('not equal') })
			query_types.append({'name': 'gt',    'description': _('bigger') })
			query_types.append({'name': 'lt',    'description': _('lesser') })
			query_types.append({'name': 'ge',    'description': _('bigger or equal') })
			query_types.append({'name': 'le',    'description': _('lesser or equal') })


			# Datenbankzugriff
			sysrole_types=[]
			sysversion_types=[]
			selectedstate_types=[]
			inststate_types=[]
			currentstate_types=[]
			pkgdb_connect_string = univention_pkgdb.sql_create_localconnectstring( baseConfig['hostname']  )
			if len(pkgdb_connect_string)>0:
				systemroles  = univention_pkgdb.sql_getall_systemroles( pkgdb_connect_string )
				if systemroles:
					for s in systemroles:
						sysrole_types.append({'name': s[0],  'description': s[0]})
				systemversions  = univention_pkgdb.sql_getall_systemversions( pkgdb_connect_string )
				if systemversions:
					for s in systemversions:
						sysversion_types.append({'name': s[0],  'description': s[0]})
			for (key, item) in SelectedStates.items():
				selectedstate_types.append({'name': str(key), 'description': item })
			for (key, item) in InstStates.items():
				inststate_types.append({'name': str(key), 'description': item })
			for (key, item) in CurrentStates.items():
				currentstate_types.append({'name': str(key), 'description': item })

			self.choices=self.save.get("choices")
			# choices enthält immer Tupel aus search_type und search_value
			# bei erstem Aufruf hier ein default-Paar eintragen
			if not self.choices:
				self.choices=[("pkgname","eq","")]

			self.search_rows=[]
			search_rules=[]

			for search_type, query_type, search_value in self.choices:
				search_rule=[]

				search_types_tmp = copy.deepcopy(search_types)
				for i in search_types_tmp:
					if i['name']==search_type:
						i['selected']='1'
				search_type_button=button('',{},{'helptext':''})
				search_type_select=question_select( _('filterobject'),{'width':'200'},{"helptext":'',"choicelist":search_types_tmp,'button':search_type_button})

				query_types_tmp = copy.deepcopy(query_types)
				for i in query_types_tmp:
					if i['name']==query_type:
						i['selected']='1'
				query_type_button=button('',{},{'helptext':''})
				query_type_select=question_select( _('filtercondition'),{'width':'200'},{"helptext":'',"choicelist":query_types_tmp,'button':query_type_button})

				search_del_select=question_bool(_('filter_del'),{},{'helptext':''})

				search_rule.append(tablecol('',{'type':'about_layout'},{'obs':[search_type_select]}))
				search_rule.append(tablecol('',{'type':'about_layout'},{'obs':[query_type_select]}))
				if search_type=='sysrole':
					sysrole_types_tmp = copy.deepcopy(sysrole_types)
					for i in sysrole_types_tmp:
						if i['name']==search_value:
							i['selected']='1'
					sysrole_type_button=button('',{},{'helptext':''})
					sysrole_type_select=question_select( _('filtertext'), {'width':'200'},{"helptext":'',"choicelist":sysrole_types_tmp,'button':sysrole_type_button})
					search_rule.append(tablecol('',{'type':'about_layout'},{'obs':[sysrole_type_select]}))
					search_text=sysrole_type_select
				elif search_type=='sysversion':
					sysversion_types_tmp = copy.deepcopy(sysversion_types)
					for i in sysversion_types_tmp:
						if i['name']==search_value:
							i['selected']='1'
					sysversion_type_button=button('',{},{'helptext':''})
					sysversion_type_select=question_select( _('filtertext'), {'width':'200'},{"helptext":'',"choicelist":sysversion_types_tmp,'button':sysversion_type_button})
					search_rule.append(tablecol('',{'type':'about_layout'},{'obs':[sysversion_type_select]}))
					search_text=sysversion_type_select
				elif search_type=='selectedstate':
					selectedstate_types_tmp = copy.deepcopy(selectedstate_types)
					for i in selectedstate_types_tmp:
						if i['name']==search_value:
							i['selected']='1'
					selectedstate_type_button=button('',{},{'helptext':''})
					selectedstate_type_select=question_select( _('filtertext'), {'width':'200'},{"helptext":'',"choicelist":selectedstate_types_tmp,'button':selectedstate_type_button})
					search_rule.append(tablecol('',{'type':'about_layout'},{'obs':[selectedstate_type_select]}))
					search_text=selectedstate_type_select
				elif search_type=='inststate':
					inststate_types_tmp = copy.deepcopy(inststate_types)
					for i in inststate_types_tmp:
						if i['name']==search_value:
							i['selected']='1'
					inststate_type_button=button('',{},{'helptext':''})
					inststate_type_select=question_select( _('filtertext'), {'width':'200'}, {"helptext":'',"choicelist":inststate_types_tmp,'button':inststate_type_button})
					search_rule.append(tablecol('',{'type':'about_layout'},{'obs':[inststate_type_select]}))
					search_text=inststate_type_select
				elif search_type=='currentstate':
					currentstate_types_tmp = copy.deepcopy(currentstate_types)
					for i in currentstate_types_tmp:
						if i['name']==search_value:
							i['selected']='1'
					currentstate_type_button=button('',{},{'helptext':''})
					currentstate_type_select=question_select( _('filtertext'), {'width':'200'},{"helptext":'',"choicelist":currentstate_types_tmp,'button':currentstate_type_button})
					search_rule.append(tablecol('',{'type':'about_layout'},{'obs':[currentstate_type_select]}))
					search_text=currentstate_type_select
				else:
					# damit beim Aufruf bereits ein * in dem Filter steht
					if not search_value:
						search_value='*'

					search_text=question_text( _('filtertext'), {"width":"150"}, {"usertext":search_value})
					search_rule.append(tablecol('',{'type':'about_layout'},{'obs':[search_text]}))

				search_rule.append(tablecol('',{'type':'wizard_layout_bottom'},{'obs':[search_del_select]}))

				search_rules.append(search_rule)

				# Diese Liste wird im apply ausgewertet
				self.search_rows.append((search_type_select, query_type_select, search_text, search_del_select ))

			self.add_search_rule_button=button( _('filter_add'),{'icon':'/style/add.gif'},{'helptext':'Add Search-Rule'})
			self.search_visible=question_text( _('results of page'), {'width':'200'}, {'usertext': str(visible)})
			self.search_button=button(_('search'),{'icon':'/style/ok.gif'},{'helptext':''})

			# ------------------------------------------------------------------------------
			# Suchfilter darstellen
			# ------------------------------------------------------------------------------

			if search_rules:
				for rule in search_rules:
					self.subobjs.append(
						table("",{'type':'content_main'},{"obs":[
							tablerow('',{},{'obs': rule})
						]})
					)

			self.subobjs.append(
				table("",{'type':'content_main'},{"obs":[
					tablerow('',{},{'obs':[
						tablecol('',{'type':'about_layout'},{'obs':[self.add_search_rule_button]})
					]}),
					tablerow('',{},{'obs':[
						tablecol('',{'type':'about_layout'},{'obs':[]})
					]}),
					tablerow('',{},{'obs':[
						tablecol('',{},{'obs':[
							table("",{},{"obs":[
								tablerow('',{},{'obs':[
									tablecol('',{'type':'about_layout'},{'obs':[self.search_visible]}),
									tablecol('',{'type':'wizard_layout_bottom'},{'obs':[self.search_button]})
								]})
							]})
						]})
					]})
				]})
			)

			# ------------------------------------------------------------------------------
			# Suche ausführen
			# ------------------------------------------------------------------------------
			result=self.save.get('browse_search_result')
			if self.save.get('browse_search') == '1' or result:
				cached = 1
				if not result:
					cached = 0
					result=[]

				nresults = len(result)
				if not result:
					nresults=0

					# Datenbankzugriffsmethode ermitteln
					pkgdb_connect_string = univention_pkgdb.sql_create_localconnectstring( baseConfig['hostname']  )
					if len(pkgdb_connect_string)==0:
						return

					query='true'
					need_join_systems=0
					for search_type, query_type, search_value in self.choices:
						# DB-Operator einordnen
						if query_type=='ne':
							qt='!~'
							re=1
						elif query_type=='gt':
							qt='>'
							re=0
						elif query_type=='lt':
							qt='<'
							re=0
						elif query_type=='ge':
							qt='>='
							re=0
						elif query_type=='le':
							qt='<='
							re=0
						else:
							qt='~'
							re=1

						# State-Search ist nie ein RE
						if search_type=='selectedstate' or search_type=='inststate' or search_type=='currentstate':
							re=0
							# in diesen Fall auch keine Mustersuche
							if qt=='~':
								qt = '='
							elif qt=='!~':
								qt = '!='

						# leeren Parameter korrigieren
						s = str(search_value)
						if s == 'ascii-null-escape':
							s = '0'
						elif s == 'None':
							s = ''

						if re==1:
							# vereinfachter regulären Ausdruck in Postgres-RE wandeln

							# Sternchen vorne
							s0 = ''
							if len(s) > 0:
								if s[0] == '*':
									s = s[1:]
								else:
									s0 = '^'

							# Sternchen hinten
							s1 = ''
							if len(s) > 0:
								if s[-1] == '*':
									s = s[:-1]
								else:
									s1 = '$'

							# komische Zeichen {string.punctuation ohne '.', '*', '-' und '_'} löschen
							# '*' in '.*' wandeln
							# '.' bleibt RE für beliebiges Zeichen
							sv=''
							for i in s:
								if i not in '!"#$%&\'()+,/:;<=>?@[\\]^`{|}~':
									if i == '*':
										sv = sv +'.*'
									else:
										sv = sv + i
							s = s0 + sv + s1

						else:
							# keine regulären Ausdruck bei größer oder kleiner

							# komische Zeichen {string.punctuation ohne '.', '-' und '_'} löschen
							# '.' maskieren
							sv=''
							for i in s:
								if i not in '!"#$%&\'()+,/:;<=>?@[\\]^`{|}~*':
									if i == '.':
										sv = sv +'\.'
									else:
										sv = sv + i
							s = sv

						sv = '\'' + s + '\''

						if search_type=='sysname' and len(str(search_value))>0 and str(search_value)!='None':
							query += ' and sysname'+qt+sv

						elif search_type=='sysrole' and len(str(search_value))>0 and str(search_value)!='None':
							query += ' and sysrole'+qt+sv
							need_join_systems=1

						elif search_type=='sysversion' and len(str(search_value))>0 and str(search_value)!='None':
							query += ' and sysversion'+qt+sv
							need_join_systems=1

						elif search_type=='pkgname' and len(str(search_value))>0 and str(search_value)!='None':
							query += ' and pkgname'+qt+sv

						elif search_type=='vername' and len(str(search_value))>0 and str(search_value)!='None':
							query += ' and vername'+qt+sv

						elif search_type=='selectedstate' and len(str(search_value))>0 and str(search_value)!='None':
							query += ' and selectedstate'+qt+sv

						elif search_type=='inststate' and len(str(search_value))>0 and str(search_value)!='None':
							query += ' and inststate'+qt+sv

						elif search_type=='currentstate' and len(str(search_value))>0 and str(search_value)!='None':
							query += ' and currentstate'+qt+sv

					if len(query)>4:
						result = univention_pkgdb.sql_get_packages_in_systems_by_query( pkgdb_connect_string, query, need_join_systems )
						nresults = len(result)
					else:
						result = []
						nresults = 0

				self.save.put('browse_search_result', result)

				# ------------------------------------------------------------------------------
				# Suche darstellen
				# ------------------------------------------------------------------------------

				rows.append(tablerow("", {}, {"obs":[
					tablecol("", {'type':'bold', 'colspan':'7'}, {"obs":[ header(_("%d Search result(s):") % nresults,{"type":"2"},{}) ]})
				]}))

				# Kopfzeile der Tabelle
				rows.append(tablerow("", {}, {"obs":[
					tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('system')       ]}) ]}),
					tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('package')      ]}) ]}),
					tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('version')      ]}) ]}),
					tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('collect date') ]}) ]}),
					tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('selectstate')  ]}) ]}),
					tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('inststate')    ]}) ]}),
					tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('currentstate') ]}) ]})
				]}))

				if result:
					for p in result[start:start+visible]:
						rows.append(tablerow("", {}, {"obs":[
							tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[0]]}) ]}),
							tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[1]]}) ]}),
							tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[2]]}) ]}),
							tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[3]]}) ]}),
							tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[SelectedStates[str(p[5])]]}) ]}),
							tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[    InstStates[str(p[6])]]}) ]}),
							tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[ CurrentStates[str(p[7])]]}) ]})
							]}))

				tabelle=table("",{'type':'content_main'},{"obs":rows})
				self.subobjs.append(tabelle)

				self.dirstab=longtable("",{'total': str(len(result)), 'start': str(start), 'visible': str(visible)},{"obs":dirrows})
				self.subobjs.append(self.dirstab)


		elif menuselection=='problem':
			rows=[]
			dirrows=[]
			saverows=[]
			problemlist=[]
			start=0

			visible=self.save.get('browse_problem_visible', 20)
			if visible > 100:
				visible=100
			start=self.save.get('browse_table_start', 0)

			if self.save.get('compareVersion') not in ['', None]:
				compareVersion=self.save.get('compareVersion')
			else:
				compareVersion='%s-%s' % (baseConfig['version/version'], baseConfig['version/patchlevel'])
				if baseConfig.has_key('version/security-patchlevel'):
					compareVersion = '%s-%s' % (compareVersion, baseConfig['version/security-patchlevel'])

			list=[
				 {'name': "actualSystems", 'description': _('Not updated systems')},
				 {'name': "failedPackages", 'description': _('Incomplete installed packages')}
				 ]

			problemlist.append({'name': '', 'description': '' })
			for l in list:
				if l['name'] == self.save.get("saved_problemlistselection"):
					problemlist.append({'name': l['name'], 'description': l['description'], 'selected': '1' })
				else:
					problemlist.append({'name': l['name'], 'description': l['description'] })

			self.problemlist_button=button('',{},{'helptext':''})
			self.problemlist_select=question_select(_('Check'), {"width":"250"}, {"helptext":'',"choicelist":problemlist,'button':self.problemlist_button})
			self.problem_start_button=button(_("Start check"), {'icon':'/style/ok.gif'}, {"helptext":""})
			self.problem_visible=question_text( _('results of page'), {'width':'200'}, {'usertext': str(visible)})

			saverows.append(tablerow("", {}, {"obs":[
				tablecol("", {}, {"obs":[]}),
			]}))
			if self.save.get("saved_problemlistselection") == 'actualSystems':
				self.compareVersion_text=question_text( _('To compare with version'), {"width":"100"}, {"usertext": compareVersion})
				saverows.append(tablerow("", {}, {"obs":[
					tablecol("", {'type':'about_layout'}, {"obs":[self.problemlist_select]}),
					tablecol("", {'type':'about_layout'}, {"obs":[self.compareVersion_text]}),
				]}))
			else:
				saverows.append(tablerow("", {}, {"obs":[
					tablecol("", {'type':'about_layout'}, {"obs":[self.problemlist_select]}),
				]}))

			saverows.append(tablerow("", {}, {"obs":[
				tablecol("", {}, {"obs":[
					table("",{},{"obs":[
						tablerow("", {}, {"obs":[
							tablecol("", {'type':'about_layout'}, {"obs":[self.problem_visible]}),
							tablecol("", {'type':'wizard_layout_bottom'}, {"obs":[self.problem_start_button]}),
						]})
					]})
				]})
			]}))

			savetab=table("",{'type':'content_main'},{"obs":saverows})



			self.subobjs.append(notebook('', {}, {'buttons': [(_('Problem identification'),  _('Problem identification'))], 'selected': 0}))

			self.subobjs.append(savetab)

			result=self.save.get('browse_problemsearch_result')
			if ( self.save.get('browse_problemsearch') == '1' or result ) and self.save.get("saved_problemlistselection"):
				cached = 1
				if not result:
					cached = 0
					result=[]

				nresults = len(result)
				if not result:
					nresults=0

					# Datenbankzugriffsmethode ermitteln
					pkgdb_connect_string = univention_pkgdb.sql_create_localconnectstring( baseConfig['hostname']  )
					if len(pkgdb_connect_string)==0:
						return

					if self.save.get("saved_problemlistselection") == 'actualSystems':
						resultTmp = univention_pkgdb.sql_get_systems_by_query( pkgdb_connect_string, 'sysversion<\'%s\'' % compareVersion )
					elif self.save.get("saved_problemlistselection") == 'failedPackages':
						resultTmp = univention_pkgdb.sql_get_packages_in_systems_by_query( pkgdb_connect_string, 'currentstate!=\'0\' and currentstate!=\'6\' and selectedstate!=\'3\'', '1')
					else:
						resultTmp = []
					result = []
					for p in resultTmp:
						result.append(p)
					nresults = len(result)

				self.save.put('browse_syssearch_result', result)

				# ------------------------------------------------------------------------------
				# Suche darstellen
				# ------------------------------------------------------------------------------

				self.subobjs.append(
					table("",{'type':'content_main'},{"obs":[
						tablerow("", {}, {"obs":[
							tablecol("", {'type':'about_layout'}, {"obs":[
								header(_("%d Search result(s):") % nresults,{"type":"2"},{})
							]})
						]})
					]})
				)
				if nresults > 0:


					if self.save.get("saved_problemlistselection") == 'actualSystems':
						# Kopfzeile der Tabelle
						rows.append(tablerow("", {}, {"obs":[
							tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('system-name')     ]}) ]}),
							tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('ucs-role')        ]}) ]}),
							tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('current version') ]}) ]}),
							tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('collect date')    ]}) ]})
						]}))
					elif self.save.get("saved_problemlistselection") == 'failedPackages':
						rows.append(tablerow("", {}, {"obs":[
							tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('system')       ]}) ]}),
							tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('package')      ]}) ]}),
							tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('version')      ]}) ]}),
							tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('collect date') ]}) ]}),
							tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('selectstate')  ]}) ]}),
							tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('inststate')    ]}) ]}),
							tablecol("", {'type':'bold'}, {"obs":[ text("", {}, {"text":[ _('currentstate') ]}) ]})
						]}))

					if result:
						if self.save.get("saved_problemlistselection") == 'actualSystems':
							for p in result[start:start+visible]:
								rows.append(tablerow("", {}, {"obs":[
									tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[0]]}) ]}),
									tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[2]]}) ]}),
									tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[1]]}) ]}),
									tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[3]]}) ]})
									]}))
						elif self.save.get("saved_problemlistselection") == 'failedPackages':

							for p in result[start:start+visible]:
								rows.append(tablerow("", {}, {"obs":[
									tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[0]]}) ]}),
									tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[1]]}) ]}),
									tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[2]]}) ]}),
									tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[p[3]]}) ]}),
									tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[SelectedStates[str(p[5])]]}) ]}),
									tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[    InstStates[str(p[6])]]}) ]}),
									tablecol("", {'type':'normal'}, {"obs":[ text("", {}, {"text":[ CurrentStates[str(p[7])]]}) ]})
									]}))
					tabelle=table("",{'type':'content_main'},{"obs":rows})
					self.subobjs.append(tabelle)

					self.dirstab=longtable("",{'total': str(len(result)), 'start': str(start), 'visible': str(visible)},{"obs":dirrows})
					self.subobjs.append(self.dirstab)

		self.save.put("baseConfig",baseConfig)
		self.save.put("menuselection", menuselection)

	def apply(self):
		if self.applyhandlemessages():
			return

		old_start=self.save.get('browse_table_start', 0)
		if hasattr(self, 'dirstab'):
			self.save.put('browse_table_start', self.dirstab.getcontent())

		menuselection_submodule = self.save.get("uc_submodule")
		menuselection = menuselection_submodule
		if not menuselection:
			menuselection = self.save.get("menuselection")

		if menuselection=='sys':
			# ------------------------------------------------------------------------------
			# Suchfelder wählen
			# ------------------------------------------------------------------------------
			visible=self.syssearch_visible.get_input()
			if visible:
				try:
					self.save.put('browse_search_visible', int(visible))
				except:
					self.save.put('browse_search_visible', 20)

			# ------------------------------------------------------------------------------
			# load searchset
			# ------------------------------------------------------------------------------
			if self.savesys_button.pressed():
				univention_pkgdb.log( 'CMD: savesys_button')
				if self.savesys_list.getselected() and self.savesys_list.getselected()!="":
					selection=self.savesys_list.getselected()
					univention_pkgdb.log( 'CMD: savessys_list='+selection)
					ss = saveset(SAVEPATH,'SavedSys-',SUFFIX)
					save_obj = {}
					save_obj = ss.load(selection)
					self.save.put("syschoices",save_obj['syschoices'])
					self.save.put("saved_sysselection", selection)
					self.save.put('browse_syssearch_result', None)
			else:
				choices=[]
				# alle Suchzeilen durchgehen, pruefen, ob eine entfernt werden soll,
				# die anderen Zeilen wieder für nä. Aufruf speichenr
				if self.syssearch_rows:
					choices_valid = 0
					for type, query, text, del_button in self.syssearch_rows:
						t = type.getselected()
						q = query.getselected()
						d = del_button.selected()
						if d=="selected":
							pass
						else:
							ti = text.get_input()
							if ti == 'ascii-null-escape':
								ti = '0'
							elif ti == 'None':
								ti = ''
							choices.append(( t, q, ti ))
						if t==None:
							choices_valid = 1
					if choices_valid == 0:
						self.save.put("syschoices",choices)

				if self.add_syssearch_rule_button.pressed():
					# add new empty row
					choices.append(("sysname", "eq", ""))

				if self.syssearch_button.pressed():
					self.save.put('browse_syssearch_result', None)
					self.save.put('browse_syssearch', '1')
				else:
					self.save.put('browse_syssearch', '0')

			# ------------------------------------------------------------------------------
			# save searchset
			# ------------------------------------------------------------------------------
			if self.savesys_ins.pressed():
				if self.savesys_txt.xvars["usertext"]=="":
					univention_pkgdb.log( 'CMD: savesys_ins empty')
				else:
					univention_pkgdb.log( 'CMD: savessys_ins')
					ss = saveset(SAVEPATH,'SavedSys-',SUFFIX)
					filename = self.savesys_txt.xvars["usertext"]
					save_obj = {}
					save_obj['syschoices']=choices
					ss.save( filename, save_obj )

			# ------------------------------------------------------------------------------
			# delete searchset
			# ------------------------------------------------------------------------------
			if self.savesys_del.pressed():
				univention_pkgdb.log( 'CMD: savesys_del')
				if self.savesys_list.getselected() and self.savesys_list.getselected()!="":
					selection=self.savesys_list.getselected()
					ss = saveset(SAVEPATH,'SavedSys-',SUFFIX)
					ss.delete( selection )

		elif menuselection=='search':
			# ------------------------------------------------------------------------------
			# Suchfelder wählen
			# ------------------------------------------------------------------------------
			visible=self.search_visible.get_input()
			if visible:
				try:
					self.save.put('browse_search_visible', int(visible))
				except:
					self.save.put('browse_search_visible', 20)

			# ------------------------------------------------------------------------------
			# load searchset
			# ------------------------------------------------------------------------------
			if self.savesearch_button.pressed():
				univention_pkgdb.log( 'CMD: savesearch_button')
				if self.savesearch_list.getselected() and self.savesearch_list.getselected()!="":
					selection=self.savesearch_list.getselected()
					univention_pkgdb.log( 'CMD: savesearch_list='+selection)
					ss = saveset()
					save_obj = {}
					save_obj = ss.load(selection)
					self.save.put("choices",save_obj['choices'])
					self.save.put("saved_searchselection", selection)
					self.save.put('browse_search_result', None)
			else:
				choices=[]
				# alle Suchzeilen durchgehen, pruefen, ob eine entfernt werden soll,
				# die anderen Zeilen wieder für nä. Aufruf speichenr
				if self.search_rows:
					choices_valid = 0
					for type, query, text, del_button in self.search_rows:
						t = type.getselected()
						q = query.getselected()
						d = del_button.selected()
						if d=="selected":
							pass
						else:
							ti = text.get_input()
							if ti == 'ascii-null-escape':
								ti = '0'
							elif ti == 'None':
								ti = ''
							choices.append(( t, q, ti ))
						if t==None:
							choices_valid = 1
					if choices_valid == 0:
						self.save.put("choices",choices)

				if self.add_search_rule_button.pressed():
					# add new empty row
					choices.append(("pkgname", "eq", ""))

				if self.search_button.pressed():
					self.save.put('browse_search_result', None)
					self.save.put('browse_search', "1")
				else:
					self.save.put('browse_search', "0")

			# ------------------------------------------------------------------------------
			# save searchset
			# ------------------------------------------------------------------------------
			if self.savesearch_ins.pressed():
				if self.savesearch_txt.xvars["usertext"]=="":
					univention_pkgdb.log( 'CMD: savesearch_ins empty')
				else:
					univention_pkgdb.log( 'CMD: savesearch_ins')
					ss = saveset()
					filename = self.savesearch_txt.xvars["usertext"]
					save_obj = {}
					save_obj['choices']=choices
					ss.save( filename, save_obj )

			# ------------------------------------------------------------------------------
			# delete searchset
			# ------------------------------------------------------------------------------
			if self.savesearch_del.pressed():
				univention_pkgdb.log( 'CMD: savesearch_del')
				if self.savesearch_list.getselected() and self.savesearch_list.getselected()!="":
					selection=self.savesearch_list.getselected()
					ss = saveset()
					ss.delete( selection )
		elif menuselection == 'problem':

			visible=self.problem_visible.get_input()
			if visible:
				try:
					self.save.put('browse_problem_visible', int(visible))
				except:
					self.save.put('browse_problem_visible', 20)

			if self.problemlist_button.pressed():
				if self.problemlist_select.getselected() and self.problemlist_select.getselected()!="":
					selection=self.problemlist_select.getselected()
					self.save.put("saved_problemlistselection", selection)

			try:
				text=self.compareVersion_text.get_input()
				if text not in ['', None]:
					self.save.put("compareVersion", text)
			except:
				pass

			if self.problem_start_button.pressed():
				self.save.put('browse_problemsearch_result', None)
				self.save.put('browse_problemsearch', '1')
