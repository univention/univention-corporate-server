# -*- coding: utf-8 -*-
#
# Univention Webui
#  syntax.py
#
# Copyright 2004-2010 Univention GmbH
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

from uniparts import *
import os
import sys
import time
import ldap
import string
import re
import types
import copy
from types import *
import unimodule
import uniconf
from localwebui import _

class question_property(uniconf.uniconf):
	def mytype(self):
		return 'question_property'

	def myinit(self):
		lo=self.args['lo']
		property=self.args['property']
		fields=self.args.get('field', None)
		value=self.args.get('value', None)
		name=self.args.get('name', '')
		self.search=self.args.get('search', '')
		self.save = self.parent.save

		if value == None and self.search:
			value=property.syntax.any()
		elif value == None:
			value=property.syntax.new()

		if property.required:
			self.atts['required']="1"
		self.subfield=question_syntax('',self.atts,{'syntax': property.syntax, 'name': property.short_description, 'value': value, 'helptext': property.long_description, 'search': self.search, 'lo': lo})
		self.subobjs.append(self.subfield)

	def get_input(self):
		return self.subfield.get_input()

class question_syntax(uniconf.uniconf):
	# TODO: a syntax simpleDate ought to be used where a date is required maybe it can be used in unixTime
	def mytype(self):
		# FIXME
		return 'question_syntax'

	def myinit(self):

		self.lo = self.args.get('lo', None)
		self.syntax = self.args['syntax']
		value = self.args.get('value', None)
		name = self.args.get('name', '')
		attributes = self.atts
		self.search  =self.args.get('search', '')

		self.save = self.parent.save
		position = self.save.get('ldap_position')
		self.position = position

		self.subfields=[]

		# compare functions to sort dictionairies
		def compare_dicts_by_attr(attr):
			def compare_dicts(dict1,dict2):
				if attr in dict1.keys() and attr in dict2.keys():
					return cmp(dict1[attr],dict2[attr])
				else:
					return cmp(dict1,dict2)
			return compare_dicts

		def compare_dicts_by_two_attr(attr1,attr2):
			def compare_dicts(dict1,dict2):
				if attr1 in dict1.keys() and attr1 in dict2.keys():
					if dict1[attr1] == dict2[attr1] and attr2 in dict1.keys() and attr2 in dict2.keys():
						return cmp(dict1[attr2],dict2[attr2])
					else:
						return cmp(dict1[attr1],dict2[attr1])
				elif attr2 in dict1.keys() and attr2 in dict2.keys():
					return cmp(dict1[attr2],dict2[attr2])
				else:
					return cmp(dict1,dict2)
			return compare_dicts


		if self.atts.get('required', None):
			name="%s (*)" % name

		if self.syntax.name == 'boolean':

			if value != '1':
				value=''
			check_box=question_bool(name,self.atts,{'usertext': value, 'helptext':self.args.get('helptext', '')})
			self.subfields.append(check_box)
			self.subobjs.append(check_box)
		elif self.syntax.name == 'BOOLEAN':

			if value != 'TRUE':
				value=''
			check_box=question_bool(name,self.atts,{'usertext': value, 'helptext':self.args.get('helptext', '')})
			self.subfields.append(check_box)
			self.subobjs.append(check_box)
		elif self.syntax.name == 'OKORNOT':

			if value != 'OK':
				value=''
			check_box=question_bool(name,self.atts,{'usertext': value, 'helptext':self.args.get('helptext', '')})
			self.subfields.append(check_box)
			self.subobjs.append(check_box)

		elif self.syntax.name == 'network':
			network_choicelist = []

			domainPos = univention.admin.uldap.position(position.getDomain())
			networks = self.lo.searchDn('(objectClass=univentionNetworkClass)', base=domainPos.getBase(), scope='domain')

			network_choicelist.append({'item':-1,'name': '', 'description': _('None')})
			network_choicelist[-1]['selected'] = '1'
			if networks:
				oldlevel = ''
				item = 0
				for net in networks:
					tmppos = univention.admin.uldap.position(position.getBase())
					tmppos.setDn(net)
					(displaypos,displaydepth) = tmppos.getPrintable_depth()
					if not unicode(displaydepth) == oldlevel:
						item += 1
					oldlevel = unicode(displaydepth)
					network_choicelist.append({"item":item,"level":unicode(displaydepth),"name":net,"description":displaypos})
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'webui/syntax: network: %s level:%s ' % (displaydepth, displaypos) )
					if net == value:
						network_choicelist[-1]['selected'] = '1'

			network_choicelist.sort(compare_dicts_by_two_attr('item','description'))

			atts=copy.deepcopy(attributes)
			network_select = question_select(self.syntax.description,atts,{'choicelist':network_choicelist,'helptext':_('select network')})

			self.subfields.append(network_select)
			self.subobjs.append(network_select)

		elif self.syntax.name == 'fileMode' or self.syntax.name == 'directoryMode':
			if value:
				mode = int(value, 8)
			else:
				mode = 0

			if self.syntax.name == 'fileMode':
				l = [(04, _('Read')), (02, _('Write')), (01, _('Execute'))]
			else:
				l = [(04, _('Read')), (02, _('Write')), (01, _('Access'))]

			# self.subobjs.append(t)

			rows=[]
			headcols=[]

			t=text('',{},{'text':[name], 'type': 'description', 'helptext':self.args.get('helptext', '')})
			headcols.append(tablecol('',{"border":"0", 'type': 'description', 'colspan': '4'},{'obs':[t]}))
			rows.append(tablerow('',{'type': 'filemode'},{'obs':headcols}))
			self.subobjs.append(table('',{"border":"0"},{'obs':rows}))

			rows=[]
			headcols=[]
			t=text('',{},{'text':[''],'helptext':self.args.get('helptext', '')})
			headcols.append(tablecol('',{"border":"0", 'type': 'filemode'},{'obs':[t]}))
			for m, d in l:
				t=text('',{},{'text':[d],'helptext':self.args.get('helptext', '')})
				headcols.append(tablecol('',{"border":"0", 'type': 'filemode', 'align': 'center'},{'obs':[t]}))
			rows.append(tablerow('',{'type': 'filemode'},{'obs':headcols}))

			for u in [_('Owner'), _('Group'), _('Others')]:
				bodycols=[]
				t=text('',{},{'text':[u],'helptext':self.args.get('helptext', '')})
				bodycols.append(tablecol('',{"border":"0", 'type': 'filemode'},{'obs':[t]}))
				for m, d in l:
					if u == _('Owner'):
						m = m << 6
					elif u == _('Group'):
						m = m << 3
					if (mode & m) == m:
						v = 'selected'
					else:
						v = ''
					o=question_bool('', self.atts, {'usertext': v, 'helptext': self.args.get('helptext', '')})
					bodycols.append(tablecol('',{"border":"0", 'type': 'filemode', 'align': 'center'}, {'obs':[o]}))
					self.subfields.append(o)
				rows.append(tablerow('',{'type': 'filemode'},{'obs':bodycols}))

			self.subobjs.append(table('',{"border":"0"},{'obs':rows}))

		elif self.syntax.name == 'unixTimeInterval':

			units=[
				{'name': 'seconds', 'description': _('seconds')},
				{'name': 'minutes', 'description': _('minutes')},
				{'name': 'hours', 'description': _('hours')},
				{'name': 'days', 'description': _('days')},
			]
			try:
				value=int(value)
				unit=0 # seconds
				if value % 60 == 0:
					value=value / 60
					unit=1 #minutes
					if value % 60 == 0:
						value=value / 60
						unit=2 #hours
						if value % 24 == 0:
							value=value / 24
							unit=3 #days
				units[unit]['selected']='1'
			except ValueError:
				pass
			except TypeError:
				if len(value) == 2:
					if value[1] == 'seconds':
						units[0]['selected']='1'
					elif value[1] == 'minutes':
						units[1]['selected']='1'
					elif value[1] == 'hours':
						units[2]['selected']='1'
					elif value[1] == 'days':
						units[3]['selected']='1'
					value=value[0]

			tmp_atts=copy.deepcopy(self.atts)
			tmp_atts['width']='150'
			text_box=question_text(name,tmp_atts,{'usertext':unicode(value),'helptext':self.args.get('helptext', '')})
			self.subfields.append(text_box)
			unit_box=question_select('',tmp_atts,{'choicelist':units, 'helptext':'Unit of Time'})
			self.subfields.append(unit_box)

			self.subobjs.append(table('',{'type':'multi'},{'obs':[\
				tablerow('',{},{'obs':[\
					tablecol('',{'type':'multi'},{'obs':[text_box]}),\
					tablecol('',{'type':'multi'},{'obs':[unit_box]})\
				]})\
			]}))


		elif self.syntax.name == 'date':
			self.subfields.append(question_date(name,self.atts,{"usertext":value,"helptext":self.args.get('helptext', '')}))
			self.subobjs.append(self.subfields[0])

		elif self.syntax.name == 'passwd':

			required=""
			if self.atts.get('required', None):
				required=" (*)"

			self.subfields.append(question_secure("%s%s" % (_("Password"), required),self.atts,{"usertext":"","helptext":_("Please insert the new password")}))
			self.subfields.append(question_secure("%s%s" % (_("Password (retype)"), required),self.atts,{"usertext":"","helptext":_("Please retype the password to rule out typos.")}))

			rows=[]
			rows.append(tablerow("",{},{"obs":[\
					tablecol('',{'border':'0'},{'obs': [self.subfields[0]]})\
				]}))
			rows.append(tablerow("",{},{"obs":[\
					tablecol('',{'border':'0'},{'obs': [self.subfields[1]]})\
				]}))
			self.subobjs.append(table("",{'border':'0'},{"obs": rows}))


		elif self.syntax.type == 'select':

			if self.syntax.name == 'LDAP_Search':
				obj = self.save.get( 'edit_object', None )
				filter = self.syntax.filter
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'LDAPSEARCH: filter=%s' % str(filter) )
				if obj:
					prop = univention.admin.property()
					filter = prop._replace( filter, obj )
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'LDAPSEARCH: filter2=%s' % str(filter) )
				self.syntax._prepare( self.lo, filter )
				for dn, val, attr in self.syntax.values:
					attrs = self.lo.get( dn )
					mod = univention.admin.modules.identify( dn, attrs )
					object = univention.admin.objects.get( mod[ 0 ], None, self.lo, None, dn )
					univention.admin.objects.open( object )
					if ':' in val:
						val = val.split( ':', 1 )[ 1 ].strip()
						try:
							if val == 'dn':
								val = dn
							else:
								val = object[ val ]
								if isinstance( val, ( list, tuple ) ):
									val = val[ 0 ]
						except:
							val = ''
					else:
						if val == 'dn':
							val = dn
						else:
							if attrs.has_key(val):
								val = attrs[val]
							else:
								val = ''

					if ':' in attr:
						attr = attr.split( ':', 1 )[ 1 ].strip()
						try:
							if attr == 'dn':
								attr = dn
							else:
								attr = object[ attr ]
								if isinstance( attr, ( list, tuple ) ):
									attr = attr[ 0 ]
						except:
							attr = ''
					else:
						if attr == 'dn':
							attr = dn
						else:
							if attrs.has_key(attr):
								attr = attrs[attr]
							else:
								attr = ''

					# convert val and attr to lists
					if not isinstance( val, ( list, tuple ) ):
						val = [ val ]
					if not isinstance( attr, ( list, tuple ) ):
						attr = [ attr ]

					if not len(val) == len(attr):
						# length of val and attr differs ==> use first element of attr and all elements of val
						attr = [ attr[0] ] * len(val)

					# val and attr have same length ==> merge them
					self.syntax.choices.extend( zip(val, attr) )

				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'LDAPSEARCH: self.syntax.choices=%s' % str(self.syntax.choices) )

			choicelist=[]
			if self.search:
				choicelist.append({'name': '*', 'description': _('any')})
				if value == '*':
					choicelist[-1]['selected']='1'

			for opt_name, opt_value in self.syntax.choices:
				choicelist.append({'name': opt_name, 'description': opt_value})
				if opt_name == value:
					choicelist[-1]['selected']='1'
			self.subfields.append(question_select(name, self.atts,{'choicelist': choicelist,"helptext":self.args.get('helptext', '')}))
			self.subobjs.append(self.subfields[0])

		elif self.syntax.type == 'simple':

			if self.syntax.name == 'long_string':
				self.subfields.append(question_ltext(name,self.atts,{"usertext":value,"helptext":self.args.get('helptext', '')}))
				self.subobjs.append(self.subfields[0])
			elif self.syntax.name == 'iso8601Date':
				self.subfields.append(question_dojo_date_widget(name,self.atts,{"usertext":value,"helptext":self.args.get('helptext', '')}))
				self.subobjs.append(self.subfields[0])
			elif self.syntax.name == 'file' or self.syntax.name == 'binaryfile':
				self.subfields.append(question_file(name,self.atts,{"usertext":value,"filename":"","filesize":"","filetype":"","fileerror":"","helptext":self.args.get('helptext', '')}))
				self.subobjs.append(self.subfields[0])
			else:
				self.subfields.append(question_text(name,self.atts,{"usertext":value,"helptext":self.args.get('helptext', '')}))
				self.subobjs.append(self.subfields[0])

		elif self.syntax.type == 'simpleDate':
			self.subfields.append(question_date(name,self.atts,{"usertext":value,"helptext":self.args.get('helptext', '')}))
			self.subobjs.append(self.subfields[0])

		elif self.syntax.type == 'iso8601Date':
			self.subfields.append(question_dojo_date_widget(name,self.atts,{"usertext":value,"helptext":self.args.get('helptext', '')}))
			self.subobjs.append(self.subfields[0])

		elif self.syntax.type == 'complex':

			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'complex syntax')
			rows=[]
			index=0
			#TODO: required
			if value=='' or value==[]:
				value=[]
				for desc,syntax in self.syntax.subsyntaxes:
					value.append('')
			for desc, syntax in self.syntax.subsyntaxes:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'value=%s index=%d subsyntaxes=%s' % (unicode(value), index, self.syntax.subsyntaxes))
				self.subfields.append(question_syntax('',self.atts,
													  {'syntax':syntax,
													   'value':value[index],
													   "helptext":self.args.get('helptext', ''),
													   'name': desc,
													   'lo' : self.lo,
													   'search': self.search}))

				rows.append(tablerow("",{},{"obs":[
					tablecol('',{'border':'0'},{'obs': [self.subfields[-1]]})
					]}))
				index+=1
			self.subobjs.append(table("",{'border':'0'},{"obs": rows}))

	def get_input(self):

		if self.syntax.name == 'boolean':
			if self.subfields[0].get_input():
				value='1'
			else:
				value='0'
			return value
		elif self.syntax.name == 'BOOLEAN':
			if self.subfields[0].get_input():
				value='TRUE'
			else:
				value='FALSE'
			return value
		elif self.syntax.name == 'OKORNOT':
			if self.subfields[0].get_input():
				value='OK'
			else:
				value=''
			return value
		elif self.syntax.name == 'fileMode' or self.syntax.name == 'directoryMode':
			mode=0
			i=0
			for s in [6, 3, 0]:
				for m in [04, 02, 01]:
					m = m << s
					if self.subfields[i].get_input():
						mode = mode | m
					i += 1
			return '0%o' % mode
		elif self.syntax.name == 'unixTimeInterval':
			try:
				value=int(self.subfields[0].get_input())
				unit=self.subfields[1].get_input()
				if unit == 'days':
					value=value*24*60*60
				elif unit == 'hours':
					value=value*60*60
				elif unit == 'minutes':
					value=value*60
				value=unicode(value)
			except ValueError:
				value=(self.subfields[0].get_input(), self.subfields[1].get_input())
    			except TypeError:
				value=None
			return value
		elif self.syntax.name == 'passwd':
			if self.subfields[0].get_input() == self.subfields[1].get_input():
				return self.subfields[0].get_input()
			raise univention.admin.uexceptions.valueMismatch, 'Passwords do not match'
		elif self.syntax.type == 'select':
			return self.subfields[0].getselected()
		elif self.syntax.type in ('simple','simpleDate','date'):
			return self.subfields[0].get_input()
		elif self.syntax.type == 'complex':
			return map(lambda(x): x.get_input(), self.subfields)
