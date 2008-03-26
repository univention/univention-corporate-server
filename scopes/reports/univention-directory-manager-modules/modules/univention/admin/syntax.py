# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  syntax definitions
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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

import re, string, types, math, time, operator
import univention.debug
import univention.admin.modules
import univention.admin.uexceptions
import univention.admin.localization
import base64
import copy

translation=univention.admin.localization.translation('univention/admin')
_=translation.translate

choice_update_functions = []
def __register_choice_update_function(func):
	choice_update_functions.append(func)

def update_choices():
	''' udpate choices which are defined in LDAP '''
	for func in choice_update_functions:
		func()

class simple:
	type='simple'

	def tostring(self, text):
		return text
	def new(self):
		return ''
	def any(self):
		return '*'

class select:
	type='select'

	def parse(self, text):
		for choice in self.choices:
			if choice[0] == text:
				return text
	def tostring(self, text):
		return text
	def new(self):
		return ''
	def any(self):
		return '*'

class complex:
	type='complex'
	def parse(self, texts):
		parsed=[]

		if len(texts) < len(self.subsyntaxes):
			raise univention.admin.uexceptions.valueInvalidSyntax, _("not enough arguments")
			p=s.parse(texts[i])

		if len(texts) > len(self.subsyntaxes):
			raise univention.admin.uexceptions.valueInvalidSyntax, _("too many arguments")
			p=s.parse(texts[i])

		for i in range(0, len(self.subsyntaxes)):
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'syntax.py: self.subsyntax[%s] is %s, texts is %s' % (i,self.subsyntaxes[i],  texts))
			if type( self.subsyntaxes[i][1] ) == types.InstanceType:
				s=self.subsyntaxes[i][1]
			else:
				s=self.subsyntaxes[i][1]()
			if texts[i] == None:
				raise univention.admin.uexceptions.valueInvalidSyntax, _("Invalid syntax")
			p=s.parse(texts[i])
			if not p:
				return
			parsed.append(p)
		return parsed

	def tostring(self, texts):
		import string
		newTexts=[]
		if len(self.subsyntaxes) != len(texts):
			return ''
		else:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'syntax.py: text: %s' % str(texts) )
			for i in range(0,len(texts)):
				if  texts[i]:
					if type( self.subsyntaxes[i][1] ) == types.InstanceType:
						res=self.subsyntaxes[i][1].parse(texts[i])
					else:
						res=self.subsyntaxes[i][1]().parse(texts[i])
					if res:
						newTexts.append(res)
				elif self.all_required == 1:
					return ''

		if not newTexts:
			return ''
		return string.join(newTexts, ' ')

	def new(self):
		s=[]
		for desc, syntax in self.subsyntaxes:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'syntax.py: syntax is %s, text is %s, type is %s' % (syntax, desc, type(syntax)) )
			if type( syntax ) == types.InstanceType:
				s.append(syntax.new())
			else:
				s.append(syntax().new())
		return s

	def any(self):
		s=[]
		for desc, syntax in self.subsyntaxes:
			if type( syntax ) == types.InstanceType:
				s.append(syntax.any())
			else:
				s.append(syntax().any())
		return s

class none(simple):
	name="none"
	pass

class module:
	type='module'
	name='module'

	def __init__(self, type, filter='', description=''):
		self.module_type=type
		self.filter=filter
		self.description=description

		if self.filter == '' or self.description == '':
			mymodule = __import__( 'univention/admin/handlers/%s' % type)
			if self.filter == '' and hasattr(mymodule,'syntax_filter'):
				self.filter=mymodule.syntax_filter
			if self.description == '':
				self.description=mymodule.short_description

	def tostring(self, text):
		return text
	def new(self):
		return ''
	def any(self):
		return '*'
	def parse(self, text):
		return text

class string(simple):
	name='string'
	min_length=0
	max_length=0

	def parse(self, text):
		return text

class long_string(string):
	name='long_string'

class file(string):
	name='file'

class binaryfile(file):
	name='binaryfile'
	def tostring(self, text):
		if text and text[0]:
			encoded=base64.encodestring(text[0])
			return encoded
		else:
			return ''

class integer(simple):
	name='integer'
	min_length=1
	max_length=0
	_re = re.compile('^[0-9]+$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Value must be a number!")

class boolean(simple):
	name='boolean'
	min_length=1
	max_length=1
	_re = re.compile('^[01]?$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Value must be 0 or 1")

class filesize(simple):
	name='filesize'
	min_length=1
	max_length=0
	_re = re.compile('^[0-9]+(|[gGmMkK])(|[bB])$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Value must be an integer followed by one of GB,MB,KB,B or nothing (equals B)!")

class mail_folder_name(simple):
	name='mail_folder_name'

	def parse(self,text):
		if  "!" in text or " " in text or "\t" in text:
			raise univention.admin.uexceptions.valueError, _("Value may not contain whitespace or exclamation mark !")
		else:
			return text

class string_numbers_letters_dots(simple):
	name='string_numbers_letters_dots'

	_re = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9._-]*([a-zA-Z0-9]$)')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Value may not contain other than numbers, letters and dots!")

class string_numbers_letters_dots_spaces(simple):
	name='string_numbers_letters_dots_spaces'

	_re = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9._ -]*([a-zA-Z0-9]$)')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Value may not contain other than numbers, letters, dots and spaces!")


class phone(simple):
	name='phone'
	min_length=1
	max_length=16
	_re = re.compile('(?u)[a-zA-Z0-9._ ()\/+-]*$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Value may not contain other than numbers, letters and dots!")

class uid(simple):
	name='uid'
	min_length=1
	max_length=16
	_re = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9._-]*([a-zA-Z0-9]$)')

	def parse(self, text):
		if self._re.match(text) != None and text != 'admin':
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Value may not contain other than numbers, letters and dots, and may not be admin!")

class uid_umlauts(simple):
	name='uid'
	min_length=1
	max_length=16
	_re = re.compile('(?u)(^\w[\w -.]*\w$)|\w*$')

	def parse(self, text):
		if self._re.match(text) != None and text != 'admin':
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Value may not contain other than numbers, letters and dots, and may not be admin!")

class gid(simple):
	name='gid'
	min_length=1
	max_length=32
	_re = re.compile('(?u)^\w([\w -.]*\w)?$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Value may not contain other than numbers, letters and dots!")

class sharePath(simple):
	name='sharePath'
	_re = re.compile('.*".*')

	def parse(self, text):
		if not text[0] == '/':
			raise univention.admin.uexceptions.valueInvalidSyntax, _(', a path must begin with "/"!')
		if self._re.match(text) == None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _('Value may not contain double quotes (")!')

class passwd(simple):
	name="passwd"
	min_length=8
	max_length=0
	_re1 = re.compile(r"[A-Z]")
	_re2 = re.compile(r"[a-z]")
	_re3 = re.compile(r"[0-9]")

	def parse(self, text):
		if len(text) >= self.min_length:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _('The password is to short, at least 8 characters needed.')
class userPasswd(simple):
	name="passwd"

	def parse(self, text):
		if text and len(text) > 0:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _('Empty password not allowed!')

class hostName(simple):
	name='hostName'
	min_length=0
	max_length=0
	# hostname based upon RFC 952: <let>[*[<let-or-digit-or-hyphen>]<let-or-digit>]
	_re = re.compile("(^[a-zA-Z])(([a-zA-Z0-9-_]*)([a-zA-Z0-9]$))?$")

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Not a valid hostname!")

class windowsHostName(simple):
	name='windowsHostName'
	min_length=0
	max_length=0
	# hostname based upon RFC 952: <let>[*[<let-or-digit-or-hyphen>]<let-or-digit>]
	# windows hostnames are allowed to begin with digits
	_re = re.compile('^([0-9]*)([a-zA-Z])(([a-zA-Z0-9-_]*)([a-zA-Z0-9]$))?$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Not a valid windows hostname!")

class ipAddress(simple):
	name='ipAddress'
	min_length=7
	max_length=15
	_re = re.compile('^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$')

	def parse(self, text):
		if text and self._re.match(text) != None:
			for q in text.split('.'):
				if int(q) > 255:
					raise univention.admin.uexceptions.valueError, _("Not a valid IP address!")
					return
			return text
		raise univention.admin.uexceptions.valueError, _("Not a valid IP address!")

class hostOrIP(simple):
	name='host'
	min_length=0
	max_length=0

	def ipAddress(self, text):
		_re = re.compile('(^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$)')
		if text and _re.match(text) != None:
			for q in text.split('.'):
				if int(q) > 255:
					return False
			return True
		else:
			return False

	def hostName(self, text):
		_re = re.compile("(^[a-zA-Z])(([a-zA-Z0-9-]*)([a-zA-Z0-9]$))?$")
		if text and _re.match(text) != None:
			return True
		else:
			return False

	def parse(self, text):
		if self.hostName(text) or self.ipAddress(text):
			return text
		else:
			raise univention.admin.uexceptions.valueError, _('Not a valid hostname or IP address!')

class netmask(simple):
	name='netmask'
	min_length=1
	max_length=15

	def netmaskBits(self, dotted):
		def splitDotted(ip):
			quad = [0, 0, 0, 0]

			i = 0
			for q in ip.split('.'):
				if i > 3: break
				quad[i] = int(q)
				i += 1

			return quad

		dotted=splitDotted(dotted)

		bits = 0
		for d in dotted:
			for i in range(0,8):
				if ((d & 2**i) == 2**i):
					bits += 1
		return bits

	def parse(self, text):
		_ip=ipAddress()
		_int=integer()
		errors=0
		try:
			_ip.parse(text)
			return "%d" % self.netmaskBits(text)
		except Exception, e:
			try:
				_int.parse(text)
				if int(text) > 0 and int(text) < 32:
					return text
			except Exception, e:
				errors=1
		if errors:
			raise univention.admin.uexceptions.valueError, _("Not a valid netmask!")

class ipRange(complex):
	name='ipRange'
	subsyntaxes=[(_('First Address'), ipAddress), (_('Last Address'), string)]
	all_required=1

	def tostring(self, texts):
		if texts and texts[0] and texts[1]:
			return texts[0]+'  '+texts[1]
		else:
			return ''

class ipProtocol(select):
	name='ipProtocol'
	choices=[(_('tcp'), 'TCP'), (_('udp'), 'UDP')]

class absolutePath(simple):
	name='absolutePath'
	min_length=1
	max_length=0
	_re = re.compile('^/.*')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError,_("Not an absolute path!")

class emailAddress(simple):
	name='emailAddress'
	min_length=4
	max_length=256
	_re = re.compile('((^[a-zA-Z0-9])[a-zA-Z0-9._-]*)@[a-zA-Z0-9._-]+$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError,_("Not a valid email address!")

class emailAddressTemplate(simple):
	name='emailAddress'
	min_length=4
	max_length=0
	_re = re.compile('((^[a-zA-Z<>\[\]:])[a-zA-Z0-9<>\[\]:._-]*)@[a-zA-Z0-9._-]+$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError,_("Not a valid email address!")

class date(simple):
	name='date'
	min_length=5
	max_length=0
	_re_iso = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
	_re_de = re.compile('^[0-9]+.[0-9]+.[0-9]+$')

	def parse(self, text):
		if self._re_iso.match(text) != None:
			year, month, day = map(lambda(x): int(x), text.split('-'))
			if year > 1960 and year < 2100 and month < 13 and day < 31:
				return text
		if self._re_de.match(text) != None:
			day, month, year = map(lambda(x): int(x), text.split('.'))
			if year > 0 and year < 99 and month < 13 and day < 32:
				return text
		raise univention.admin.uexceptions.valueError,_("Not a valid Date")

class reverseLookupSubnet(simple):
	name='reverseLookupSubnet'
	min_length=1
	max_length=15
	_re = re.compile('^[0-9]+(\.[0-9]+)?(\.[0-9]+)?$')

	def parse(self, text):
		if self._re.match(text) != None:
			for q in text.split('.'):
				if int(q) > 255:
					return
			return text
		raise univention.admin.uexceptions.valueError,_("An IP subnet consists of one to three numbers ranging from 0 to 255 separated by dots.")

class reverseLookupZoneName(simple):
	name='reverseLookupZoneName'
	min_length=14
	max_length=30 #?
	_re=re.compile('^[0-9]+(\.[0-9]+)?(\.[0-9]+)?\.in-addr\.arpa$')

	def parse(self, text):
		if self._re.match(text) != None:
			t=text.replace('in-addr.arpa', '')
			for q in t.split('.'):
				if int(q) > 255:
					return
			return text
		raise univention.admin.uexceptions.valueError,_("The name of a reverse zone consists of the reversed subnet address followed by .in-addr.arpa. Example: \"0.168.192.in-addr.arpa\"")

class dnsName(simple):
	name='dnsName'
	_re = re.compile('^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9.]$')

	def parse(self, text):
		if text==None:
			raise univention.admin.uexceptions.valueError, _("Missing value!")
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError, _("Value may not contain other than numbers, letters and dots!")

class dnsName_umlauts(simple):
	name='dnsName_umlauts'
	_re = re.compile('(?u)(^\w[\w -.]*\w$)|\w*$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError, _("Value may not contain other than numbers, letters and dots!")

class dnsNameDot(simple):
	name='dnsName'
	_re = re.compile('^[0-9a-zA-Z.-]+$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text

		raise univention.admin.uexceptions.valueError, _("Value may not contain other than numbers, letters and dots!")


class dnsMX(complex):
	name='dnsMX'
	subsyntaxes=[(_('Priority'), integer), (_('Mail Server'), dnsNameDot)]
	all_required=1

class dnsSRVName(complex):
	name='dnsSRVName'
	subsyntaxes=[(_('Service'), string), (_('Protocol'), ipProtocol)]
	all_required=1

class dnsSRVLocation(complex):
	name='dnsSRVLocation'
	subsyntaxes=[(_('Priority'), integer), (_('Weight'), integer), (_('Port'), integer), (_('Server'), dnsName)]
	all_required=1

class unixTime(simple):
	name='unixTime'
	_re=re.compile('^[0-9]+$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError,_("Not a valid time format")
class unixTimeInterval(simple):
	name='unixTimeInterval'
	_re=re.compile('^[0-9]+$')

	def parse(self, text):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'TIME %s'%str(text))
		if text[0]:
			try:
				if self._re.match(text) != None:
					return text
			except TypeError:
				pass
			raise univention.admin.uexceptions.valueError,_("Not a valid time interval")
		else:
			return 'None'

class dhcpHWAddressHardware(select):
	name='dhcpHWAddressHardware'
	choices=[('ethernet', _('Ethernet')), ('fddi', _('FDDI')), ('token-ring', _('Token-Ring'))]

class macAddress(simple):
	name='macAddress'
	_re=re.compile('^[0-9a-fA-F][0-9a-fA-F]??$')

	def parse(self, text):
		c=''
		if not text:
			raise univention.admin.uexceptions.valueError,_("Value must have 6 two digit hexadecimal numbers separated by \"-\" or \":\" !")

		if text.find(":") != -1:
			c=':'
		elif text.find("-") != -1:
			c='-'

		if c:
			ls = text.split(c)
			i=0
			for num in ls:
				if not self._re.match(num):
					return None
				i+=1
			if i==6:
				return text.replace('-',':').lower()
		raise univention.admin.uexceptions.valueError,_("Value must have 6 two digit hexadecimal numbers separated by \"-\" or \":\" !")

class dhcpHWAddress(complex):
	name='dhcpHWAddress'
	subsyntaxes=[(_('Type'), dhcpHWAddressHardware), (_('Address'), macAddress)]
	all_required=1

class printerName(simple):
	name='printerName'
	min_length=1
	max_length=16
	_re = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9_-]*([a-zA-Z0-9]$)')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Value may not contain other than numbers, letters, underscore (\"_\") and minus (\"-\")!")

class printerModel(complex):
	name='PrintDriver'
	subsyntaxes=[(_('Driver'), string), (_('Description'), string)]
	all_required=1

class printersList(string):
	name='printersList'

class printerURI(string):
	name='printerURI'

class packageList(string):
	name='packageList'

class userAttributeList(string):
	name='userAttributeList'
	def parse(self, text):
		return text

class ldapDn(simple):
	name='ldapDn'
	_re=re.compile('^([^=,]+=[^=,]+,)*[^=,]+=[^=,]+$')

	def parse(self, text):
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError,_("Not a valid LDAP DN")

class consoleACL(simple):
	name='consoleACL'
	def parse(self, text):
		return text
class consoleOperations(simple):
	name='consoleOperations'
	def parse(self, text):
		return text

class ldapServer(simple):
	name='ldapServer'
	def parse(self, text):
		return text
class printerServer(simple):
	name='printerServer'
	def parse(self, text):
		return text
class kolabHomeServer(simple):
	name='kolabHomeServer'
	def parse(self, text):
		return text
class mailDomain(simple):
	name='mailDomain'
	def parse(self, text):
		return text

class kolabInvitationPolicy(string):
	name='kolabInvitationPolicy'
	searchFilter='(&(uid=*)(objectClass=posixAccount)(mailPrimaryAddress=*))'
	description=_('Invitation Policy')
	def parse(self, text):
		return text
class sharedFolderUserACL(string):
	_re=re.compile('^([^\s]+@[^\s]+|anyone)+(\s(none|read|post|append|write|all))$')
	name='sharedFolderUserACL'
	searchFilter='(&(uid=*)(objectClass=posixAccount)(mailPrimaryAddress=*)(!(objectClass=univentionHost)))'
	description=_('Shared folder user ACL')
	def parse(self, text):
		text = text.strip()
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError,_("Not a valid shared folder ACL")

class sharedFolderGroupACL(string):
	_re=re.compile('^.+(\s(none|read|post|append|write|all))$')
	name='sharedFolderGroupACL'
	searchFilter='(&(cn=*)(objectClass=posixGroup))'
	description=_('Shared folder group ACL')
	def parse(self, text):
		text = text.strip()
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError,_("Not a valid shared folder ACL")

class ldapDnOrNone(simple):
	name='ldapDnOrNone'
	_re=re.compile('^([^=,]+=[^=,]+,)*[^=,]+=[^=,]+$')

	def parse(self, text):
		if not text or text == 'None':
			return text
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError,_("Not a valid LDAP DN")

class ldapObjectClass(simple):
	name='ldapObjectClass'

	def parse(self, text):
		return text

class ldapAttribute(simple):
	name='ldapAttribute'

	def parse(self, text):
		return text

class XResolution(simple):
	name='XResolution'
	_re=re.compile('^[0-9]+x[0-9]+$')

	def parse(self, text):
		if self._re.match(text):
			return text
		raise univention.admin.uexceptions.valueError,_("Value consists of two integer numbers separated by an \"x\" (e.g. \"1024x768\")")

class XSync(simple):
	name='XSync'
	_re=re.compile('^[0-9]+(-[0-9]+)?( +[0-9]+(-[0-9]+)?)*$')

	def parse(self, text):
		if self._re.match(text):
			return text
		raise univention.admin.uexceptions.valueError,_("Value consists of two integer numbers separated by a \"-\" (e.g. \"30-70\")")

class XColorDepth(simple):
	name='XColorDepth'
	_re=re.compile('^[0-9]+$')

	def parse(self, text):
		return text

class XModule(select):
	name='XModule'
	choices=[
		('', ''),
		('apm', 'apm'),
		('ark', 'Ark'),
		('ati', 'ATI'),
		('chips', 'chips'),
		('cirrus', 'Cirrus'),
		('cyrix', 'Cyrix'),
		('dummy', 'dummy'),
		('fbdev', 'fbdev'),
		('fglrx', 'fglrx (AMD/ATI closed source)'),
		('glide', 'glide'),
		('glint', 'glint'),
		('i128', 'I128'),
		('i740', 'I740'),
		('i810', 'I810'),
		('imstt', 'Imstt'),
		('mga', 'MGA'),
		('neomagic', 'Neomagic'),
		('newport', 'Newport'),
		('nsc', 'NSC'),
		('nv', 'NV'),
		('nvidia', 'NVidia (closed source)'),
		('rendition', 'Rendition'),
		('s3', 'S3'),
		('s3virge', 'S3 Virge'),
		('savage', 'S3 Savage'),
		('siliconmotion', 'Siliconmotion'),
		('sis', 'SiS'),
		('tdfx','tdfx'),
		('tga', 'Tga'),
		('trident', 'Trident'),
		('tseng', 'Tseng'),
		('vesa', 'Vesa'),
		('vga', 'VGA'),
		('via', 'VIA'),
		('vmware', 'VMWare')
	]

class XMouseProtocol(select):
	name='XMouseProtocol'
	choices=[
		('', ''),
		('Auto', 'Auto'),
		('IMPS/2', 'IMPS/2'),
		('PS/2', 'PS/2'),
		('ExplorerPS/2', 'ExplorerPS/2'),
		('usb', 'USB'),
		('ThinkingMouse', 'ThinkingMouse'),
		('ThinkingMousePS/2', 'ThinkingMousePS/2'),
		('NetScrollPS/2', 'NetScrollPS/2'),
		('IntelliMouse', 'IntelliMouse'),
		('NetMousePS/2', 'NetMousePS/2'),
		('GlidePoint', 'GlidePoint'),
		('GlidePointPS/2', 'GlidePointPS/2'),
		('MouseManPlusPS/2', 'MouseManPlusPS/2'),
		('ms', 'Serial')
	]

class XMouseDevice(select):
	name='XMouseDevice'
	choices=[
		('', ''),
		('/dev/psaux', 'PS/2'),
		('/dev/input/mice', 'USB'),
		('/dev/ttyS0', 'Serial')
	]

class XKeyboardLayout(select):
	name='XKeyboardLayout'
	choices=[
		('', ''),
		('al', 'Albanian'),
		('en_US', 'American (en_US)'),
		('ar', 'Arabic'),
		('am', 'Armenian'),
		('by', 'Belarusian'),
		('be', 'Belgian'),
		('ben', 'Bengali'),
		('br', 'Brazilian'),
		('mm', 'Burmese'),
		('kan', 'Canada'),
		('hr', 'Croatian'),
		('bg', 'Cyrillic (bg)'),
		('sr', 'Cyrillic (sr)'),
		('cz', 'Czech'),
		('cz_qwerty', 'Czech (qwerty)'),
		('dk', 'Danish'),
		('dvorak', 'Dvorak'),
		('ee', 'Estonian'),
		('fi', 'Finnish'),
		('fr', 'French'),
		('fr-latin9', 'French (fr-latin9)'),
		('ge_la', 'Georgian (ge_la)'),
		('ge_ru', 'Georgian (ge_ru)'),
		('de', 'Germany'),
		('gb', 'Great Britain'),
		('guj', 'Gujarati'),
		('gur', 'Gurmukhi'),
		('dev', 'Hindi'),
		('el', 'ISO8859-7 Greek'),
		('is', 'Icelandic'),
		('iu', 'Inuktitut'),
		('ir', 'Iranian'),
		('ie', 'Irish'),
		('il', 'Israelian'),
		('il_phonetic', 'Israelian (phonetic)'),
		('it', 'Italian'),
		('lo', 'Lao'),
		('la', 'Latin American'),
		('lv', 'Latvian'),
		('lt', 'Lithuanian'),
		('mk', 'Macedonian'),
		('ml', 'Malayalam'),
		('mt', 'Maltese'),
		('mt_us', 'Maltese (US layout)'),
		('nl', 'Nederland'),
		('latin', 'Northern Europe'),
		('no', 'Norwegian'),
		('ogham', 'Ogham'),
		('ori', 'Oriya'),
		('pc', 'PC-Type'),
		('pl', 'Polish'),
		('pl2', 'Polish (qwerty)'),
		('pt', 'Portuguese'),
		('ro', 'Romanian'),
		('ru', 'Russian'),
		('sapmi', 'Samegiella'),
		('sk', 'Slovak'),
		('sk_qwerty', 'Slovak (qwerty)'),
		('si', 'Slovene'),
		('es', 'Spanish'),
		('se', 'Swedish'),
		('syr', 'Syriac'),
		('syr_phonetic', 'Syriac (phonetic)'),
		('tj', 'Tajik'),
		('tml', 'Tamil'),
		('tel', 'Telugu'),
		('th', 'Thai'),
		('tr', 'Turkish'),
		('ua', 'Ukrainian'),
		('us', 'United States'),
		('yu', 'Yugoslav')
	]

class soundModule(select):
	name='soundModule'
	choices=[
		('', ''),
		('auto', 'auto detect'),
		('ali5455', 'ALi5455 audio support'),
		('cmpci', 'C-Media PCI (CMI8338/8738)'),
		('ac97_codec', 'Creative SBLive! (EMU10K1)'),
		('cs46xx', 'Crystal SoundFusion (CS4280/461x)'),
		('cs4281', 'Crystal Sound CS4281'),
		('swarm_cs4297a', 'Crystal Sound CS4297a (for Swarm)'),
		('es1370', 'Ensoniq AudioPCI (ES1370)'),
		('es1371', 'Creative Ensoniq AudioPCI 97 (ES1371)'),
		('esssolo1', 'ESS Technology Solo1'),
		('maestro', 'ESS Maestro, Maestro2, Maestro2E driver'),
		('maestro3', 'ESS Maestro3/Allegro driver'),
		('forte', 'ForteMedia FM801 driver'),
		('i810_audio', 'Intel ICH (i8xx), SiS 7012, NVidia nForce Audio or AMD 768/811x'),
		('harmony', 'PA Harmony audio driver'),
		('ite8172', 'IT8172G Sound'),
		('rme96xx', 'RME Hammerfall (RME96XX) support'),
		('sonicvibes', 'S3 SonicVibes'),
		('vwsnd', 'SGI Visual Workstation sound'),
		('hal2', 'SGI HAL2 sound'),
		('ite8172', 'IT8172G Sound'),
		('nec_vrc5477', 'NEC Vrc5477 AC97 sound'),
		('au1000', 'Au1x00 Sound'),
		('trident', 'Trident 4DWave DX/NX, SiS 7018 or ALi 5451 PCI Audio Core'),
		('msnd_classic', 'Support for Turtle Beach MultiSound Classic, Tahiti, Monterey'),
		('msnd_pinnacle', 'Support for Turtle Beach MultiSound Pinnacle, Fiji'),
		('via82cxxx_audio','VIA 82C686 Audio Codec'),
		('ad1816','AD1816(A) based cards'),
		('ad1889','AD1889 based cards (AD1819 codec)'),
		('sgalaxy','Aztech Sound Galaxy (non-PnP) cards'),
		('adlib_card','Adlib Cards'),
		('aci ','ACI mixer (miroSOUND PCM1-pro/PCM12/PCM20)'),
		('cs4232','Crystal CS4232 based (PnP) cards'),
		('sscape','Ensoniq SoundScape support'),
		('gus','Gravis Ultrasound support'),
		('trix','MediaTrix AudioTrix Pro support'),
		('ad1848 ','Microsoft Sound System support'),
		('nm256_audio','NM256AV/NM256ZX audio support'),
		('mad16','OPTi MAD16 and/or Mozart based cards'),
		('pas2','ProAudioSpectrum 16 support'),
		('pss','PSS (AD1848, ADSP-2115, ESC614) support'),
		('sb','100% Sound Blaster compatibles (SB16/32/64, ESS, Jazz16) support'),
		('awe_wave ','AWE32 synth'),
		('kahlua','XpressAudio Sound Blaster emulation'),
		('wavefront ','Full support for Turtle Beach WaveFront (Tropez Plus, Tropez, Maui) synth/soundcards'),
		('opl3sa','Yamaha OPL3-SA1 audio controller'),
		('opl3sa2','Yamaha OPL3-SA2 and SA3 based PnP cards'),
		('ymfpci','Yamaha YMF7xx PCI audio (native mode)'),
		('aedsp16 ','Gallant Audio Cards (SC-6000 and SC-6600 based)'),
		('vidc_mod ','VIDC 16-bit sound'),
		('waveartist ','Netwinder WaveArtist'),
	]

class moduleSearch(ldapDn):
	name='moduleSearch'
	description='FIXME'

class groupDn(ldapDn):
	name='groupDn'

class userDn(ldapDn):
	name='userDn'

class hostDn(ldapDn):
	name='hostDn'

class userID(integer):
	name='userID'
	searchFilter='(&(uid=*)(objectClass=posixAccount)(!(objectClass=univentionHost)))'
	description=_('User ID')

class groupID(integer):
	name='groupID'
	searchFilter='(&(cn=*)(objectClass=posixGroup))'
	description=_('Group ID')

class shareHost(string):
	name='shareHost'

class windowsTerminalServer(string):
        name='windowsTerminalServer'
        searchFilter='(&(cn=*)(objectClass=univentionWindows))'
        description=_('Windows Terminal Server Hosts')

class linuxTerminalServer(string):
        name='linuxTerminalServer'
        searchFilter='(&(cn=*)(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer)))'
        description=_('Linux Terminal Server Hosts')

class authenticationServer(string):
        name='authenticationServer'
        searchFilter='(&(cn=*)(objectClass=univentionDomainController))'
        description=_('Authentication Server')

class fileServer(string):
        name='fileServer'
        searchFilter='(&(cn=*)(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer)))'
        description=_('FileServer')

class repositoryServer(string):
	name='repositoryServer'

class policyPrinterServer(string):
	name='policyPrinterServer'

class kdeProfiles(string):
	name='kdeProfiles'

class genericSelect(string):
	name='genericSelect'

class primaryGroup(ldapDn):
	name='primaryGroup'
	searchFilter='objectClass=posixGroup'
	description=_('Primary Group')

class primaryGroup2(ldapDn):
	name='primaryGroup'
	searchFilter='objectClass=posixGroup'
	description=_('Primary Group')

class network(ldapDnOrNone):
	name='network'
	searchFilter='objectClass=univentionNetworkClass'
	description=_('Network')


class dnsEntry(ldapDnOrNone):
	name='dnsEntry'
	searchFilter='(&(objectClass=dnsZone)(relativeDomainName=@)'
	description=_('DNS Entry')

class dnsEntryReverse(ldapDnOrNone):
	name='dnsEntryReverse'
	searchFilter='(&(objectClass=dnsZone)(relativeDomainName=@)'
	description=_('DNS Entry Reverse')

class dhcpEntry(ldapDnOrNone):
	name='dhcpEntry'
	searchFilter='(&(objectClass=dnsZone)(relativeDomainName=@)'
	description=_('DHCP Entry')

class dnsEntryNetwork(ldapDnOrNone):
	name='dnsEntryNetwork'
	searchFilter='(&(objectClass=dnsZone)(relativeDomainName=@)'
	description=_('DNS Entry')

class dnsEntryReverseNetwork(ldapDnOrNone):
	name='dnsEntryReverseNetwork'
	searchFilter='(&(objectClass=dnsZone)(relativeDomainName=@)'
	description=_('DNS Entry Reverse')

class dhcpEntryNetwork(ldapDnOrNone):
	name='dhcpEntryNetwork'
	searchFilter='(&(objectClass=dnsZone)(relativeDomainName=@)'
	description=_('DHCP Entry')

class share(ldapDnOrNone):
	name='share'
	searchFilter='(objectClass=univentionShare)'
	description=_('Share')

if __name__ == '__main__':
	s=date()
	print s.parse('31.12.02')
	m=dnsMX()
	print m.parse(['7', 'test.univentoin.de'])
	q=dnsSRVName()
	print q.parse(['ldap','tcp'])
	d=ldapDn()
	print d.parse('dc=foo,dc=bar,dc=test')
class AllowDenyIgnore(select):
	name='AllowDenyIgnore'
	choices=[
		('', ''),
		('allow', 'allow'),
		('deny', 'deny'),
		('ignore', 'ignore')
	]

class AllowDeny(select):
	name='AllowDeny'
	choices=[
		('', ''),
		('allow', 'allow'),
		('deny', 'deny')
	]
class booleanNone(select):
	name='booleanNone'
	choices=[
		('', ''),
		('yes', 'Yes'),
		('no', 'No')
	]

class TrueFalse(select):
	name='booleanNone'
	choices=[
		('', ''),
		('true', 'True'),
		('false', 'False')
	]

class TrueFalseUpper(select):
	name='BOOLEANNone'
	choices=[
		('', ''),
		('TRUE', 'TRUE'),
		('FALSE', 'FALSE')
	]
class TrueFalseUp(select):
	name='BOOLEAN'
	choices=[
		('TRUE', 'TRUE'),
		('FALSE', 'FALSE')
	]

class OkOrNot(select):
	name='OKORNOT'
	choices=[
		('OK', 'OK'),
		('Not', 'KO'),
	]

class ddnsUpdateStyle(select):
	name='booleanNone'
	choices=[
		('', ''),
		('ad-hoc', 'ad-hoc'),
		('interim', 'interim'),
		('none', 'none')
	]

class ddnsUpdates(select):
	name='booleanNone'
	choices=[
		('', ''),
		('on', 'on'),
		('off', 'off')
	]

class netbiosNodeType(select):
	name='netbiosNodeType'
	choices=[
		('', ''),
		('1', '1 B-node: Broadcast - no WINS'),
		('2', '2 P-node: Peer - WINS only'),
		('4', '4 M-node: Mixed - broadcast, then WINS'),
		('8', '8 H-node: Hybrid - WINS, then broadcast'),
	]

class kdeProfile(select):
	name='kdeProfile'
	choices=[
		('', 'none'),
		('/home/kde.restricted', 'restricted'),
		('/home/kde.lockeddown', 'locked down'),
	]



class language(select):
	name='language'
	choices=[
		('', ''),
		('af_ZA', 'Afrikaans/South Africa'),
		('sq_AL', 'Albanian/Albania'),
		('am_ET', 'Amharic/Ethiopia'),
		('ar_AE', 'Arabic/United Arab Emirates'),
		('ar_BH', 'Arabic/Bahrain'),
		('ar_DZ', 'Arabic/Algeria'),
		('ar_EG', 'Arabic/Egypt'),
		('ar_IN', 'Arabic/India'),
		('ar_IQ', 'Arabic/Iraq'),
		('ar_JO', 'Arabic/Jordan'),
		('ar_KW', 'Arabic/Kuwait'),
		('ar_LB', 'Arabic/Lebanon'),
		('ar_LY', 'Arabic/Libyan Arab Jamahiriya'),
		('ar_MA', 'Arabic/Morocco'),
		('ar_OM', 'Arabic/Oman'),
		('ar_QA', 'Arabic/Qatar'),
		('ar_SA', 'Arabic/Saudi Arabia'),
		('ar_SD', 'Arabic/Sudan'),
		('ar_SY', 'Arabic/Syrian Arab Republic'),
		('ar_TN', 'Arabic/Tunisia'),
		('ar_YE', 'Arabic/Yemen'),
		('an_ES', 'Aragonese/Spain'),
		('hy_AM', 'Armenian/Armenia'),
		('az_AZ', 'Azeri/Azerbaijan'),
		('eu_ES@euro', 'Basque/Spain'),
		('be_BY', 'Belarusian/Belarus'),
		('bn_BD', 'Bengali/BD'),
		('bn_IN', 'Bengali/India'),
		('bs_BA', 'Bosnian/Bosnia and Herzegowina'),
		('br_FR@euro', 'Breton/France'),
		('bg_BG', 'Bulgarian/Bulgaria'),
		('ca_ES@euro', 'Catalan/Spain'),
		('zh_CN', 'Chinese/P.R. of China'),
		('zh_HK', 'Chinese/Hong Kong'),
		('zh_SG', 'Chinese/Singapore'),
		('zh_TW', 'Chinese/Taiwan R.O.C.'),
		('kw_GB', 'Cornish/Britain'),
		('hr_HR', 'Croatian/Croatia'),
		('cs_CZ', 'Czech/Czech Republic'),
		('da_DK', 'Danish/Denmark'),
		('nl_BE@euro', 'Dutch/Belgium'),
		('nl_NL@euro', 'Dutch/Netherlands'),
		('en_AU', 'English/Australia'),
		('en_BW', 'English/Botswana'),
		('en_CA', 'English/Canada'),
		('en_DK', 'English/Denmark'),
		('en_GB', 'English/Great Britain'),
		('en_HK', 'English/Hong Kong'),
		('en_IE@euro', 'English/Ireland'),
		('en_IN', 'English/India'),
		('en_NZ', 'English/New Zealand'),
		('en_PH', 'English/Philippines'),
		('en_SG', 'English/Singapore'),
		('en_US', 'English/USA'),
		('en_ZA', 'English/South Africa'),
		('en_ZW', 'English/Zimbabwe'),
		('eo_EO', 'Esperanto/Esperanto'),
		('et_EE', 'Estonian/Estonia'),
		('fo_FO', 'Faroese/Faroe Islands'),
		('fi_FI@euro', 'Finnish/Finland'),
		('fr_BE@euro', 'French/Belgium'),
		('fr_CA', 'French/Canada'),
		('fr_CH', 'French/Switzerland'),
		('fr_FR@euro', 'French/France'),
		('fr_LU@euro', 'French/Luxemburg'),
		('gl_ES@euro', 'Galician/Spain'),
		('ka_GE', 'Georgian/Georgia'),
		('de_AT@euro', 'German/Austria'),
		('de_BE@euro', 'German/Belgium'),
		('de_CH', 'German/Switzerland'),
		('de_DE', 'German/Germany'),
		('de_DE@euro', 'German/Germany(euro)'),
		('de_LU@euro', 'German/Luxemburg'),
		('el_GR@euro', 'Greek/Greece'),
		('kl_GL', 'Greenlandic/Greenland'),
		('he_IL', 'Hebrew/Israel'),
		('iw_IL', 'Hebrew/Israel'),
		('hi_IN', 'Hindi/India'),
		('hu_HU', 'Hungarian/Hungary'),
		('is_IS', 'Icelandic/Iceland'),
		('id_ID', 'Indonesian/Indonesia'),
		('ga_IE@euro', 'Irish/Ireland'),
		('it_CH', 'Italian/Switzerland'),
		('it_IT@euro', 'Italian/Italy'),
		('ja_JP', 'Japanese/Japan'),
		('ko_KR', 'Korean/Republic of Korea'),
		('lo_LA', 'Lao/Laos'),
		('lv_LV', 'Latvian/Latvia'),
		('lt_LT', 'Lithuanian/Lithuania'),
		('lug_UG', 'Luganda/Uganda'),
		('mk_MK', 'Macedonian/Macedonia'),
		('ms_MY', 'Malay/Malaysia'),
		('ml_IN', 'Malayalam/India'),
		('mt_MT', 'Maltese/malta'),
		('gv_GB', 'Manx Gaelic/Britain'),
		('mi_NZ', 'Maori/New Zealand'),
		('mr_IN', 'Marathi/India'),
		('mn_MN', 'Mongolian/Mongolia'),
		('se_NO', 'Northern Saami/Norway'),
		('no_NO', 'Norwegian/Norway'),
		('nn_NO', 'Norwegian, Nynorsk/Norway'),
		('oc_FR', 'Occitan/France'),
		('fa_IR', 'Persian/Iran'),
		('pl_PL', 'Polish/Poland'),
		('pt_BR', 'Portuguese/Brasil'),
		('pt_PT@euro', 'Portuguese/Portugal'),
		('ro_RO', 'Romanian/Romania'),
		('ru_RU', 'Russian/Russia'),
		('ru_UA', 'Russian/Ukraine'),
		('gd_GB', 'Scots Gaelic/Great Britain'),
		('sr_YU@cyrillic', 'Serbian/Yugoslavia'),
		('sk_SK', 'Slovak/Slovak'),
		('sl_SI', 'Slovenian/Slovenia'),
		('st_ZA', 'Sotho/South Africa'),
		('es_AR', 'Spanish/Argentina'),
		('es_BO', 'Spanish/Bolivia'),
		('es_CL', 'Spanish/Chile'),
		('es_CO', 'Spanish/Colombia'),
		('es_CR', 'Spanish/Costa Rica'),
		('es_DO', 'Spanish/Dominican Republic'),
		('es_EC', 'Spanish/Ecuador'),
		('es_ES@euro', 'Spanish/Spain'),
		('es_GT', 'Spanish/Guatemala'),
		('es_HN', 'Spanish/Honduras'),
		('es_MX', 'Spanish/Mexico'),
		('es_NI', 'Spanish/Nicaragua'),
		('es_PA', 'Spanish/Panama'),
		('es_PE', 'Spanish/Peru'),
		('es_PR', 'Spanish/Puerto Rico'),
		('es_PY', 'Spanish/Paraguay'),
		('es_SV', 'Spanish/El Salvador'),
		('es_US', 'Spanish/USA'),
		('es_UY', 'Spanish/Uruguay'),
		('es_VE', 'Spanish/Venezuela'),
		('sv_FI@euro', 'Swedish/Finland'),
		('sv_SE', 'Swedish/Sweden'),
		('tl_PH', 'Tagalog/Philippines'),
		('tg_TJ', 'Tajik/Tajikistan'),
		('ta_IN', 'Tamil/India'),
		('tt_RU', 'Tatar/Tatarstan'),
		('te_IN', 'Telgu/India'),
		('th_TH', 'Thai/Thailand'),
		('ti_ER', 'Tigrigna/Eritrea'),
		('ti_ET', 'Tigrigna/Ethiopia'),
		('tr_TR', 'Turkish/Turkey'),
		('uk_UA', 'Ukrainian/Ukraine'),
		('ur_PK', 'Urdu/Pakistan'),
		('uz_UZ', 'Uzbek/Uzbekistan'),
		('vi_VN', 'Vietnamese/Vietnam'),
		('wa_BE@euro', 'Walloon/Belgium'),
		('cy_GB', 'Welsh/Great Britain'),
		('xh_ZA', 'Xhosa/South Africa'),
		('yi_US', 'Yiddish/USA'),
		('zu_ZA', 'Zulu/South Africa'),
	]

class Month(select):
	name='language'
	choices=[
		('', ''),
		('all', _( 'all' ) ),
		('January', _( 'January' ) ),
		('February', _( 'February' ) ),
		('March', _( 'March' ) ),
		('April', _( 'April' ) ),
		('May', _( 'May' ) ),
		('June', _( 'June' ) ),
		('July', _( 'July' ) ),
		('August', _( 'August' ) ),
		('September', _( 'September' ) ),
		('October', _( 'October' ) ),
		('November', _( 'November' ) ),
		('December', _( 'December' ) ),
	]

class Weekday(select):
	name='language'
	choices=[
		('', ''),
		('all', _( 'all' ) ),
		('Monday', _( 'Monday' ) ),
		('Tuesday', _( 'Tuesday' ) ),
		('Wednesday', _( 'Wednesday' ) ),
		('Thursday', _( 'Thursday' ) ),
		('Friday', _( 'Friday' ) ),
		('Saturday', _( 'Saturday' ) ),
		('Sunday', _( 'Sunday' ) ),
	]

class Day(select):
	name='day'
	choices=[
		('', ''),
		('all', _( 'all' ) ),
		('00', '0'),
		('1', '1'),
		('2', '2'),
		('3', '3'),
		('4', '4'),
		('5', '5'),
		('6', '6'),
		('7', '7'),
		('8', '8'),
		('9', '9'),
		('10', '10'),
		('11', '11'),
		('12', '12'),
		('13', '13'),
		('14', '14'),
		('15', '15'),
		('16', '16'),
		('17', '17'),
		('18', '18'),
		('19', '19'),
		('20', '20'),
		('21', '21'),
		('22', '22'),
		('23', '23'),
		('24', '24'),
		('25', '25'),
		('26', '26'),
		('27', '27'),
		('28', '28'),
		('29', '29'),
		('30', '30'),
		('31', '31'),
	]

class Hour(select):
	name='hour'
	choices=[
		('', ''),
		('all', _( 'all' ) ),
		('00', '0'),
		('1', '1'),
		('2', '2'),
		('3', '3'),
		('4', '4'),
		('5', '5'),
		('6', '6'),
		('7', '7'),
		('8', '8'),
		('9', '9'),
		('10', '10'),
		('11', '11'),
		('12', '12'),
		('13', '13'),
		('14', '14'),
		('15', '15'),
		('16', '16'),
		('17', '17'),
		('18', '18'),
		('19', '19'),
		('20', '20'),
		('21', '21'),
		('22', '22'),
		('23', '23'),
	]

class HourSimple(select):
	name='hour'
	choices=[
		('00', '0'),
		('1', '1'),
		('2', '2'),
		('3', '3'),
		('4', '4'),
		('5', '5'),
		('6', '6'),
		('7', '7'),
		('8', '8'),
		('9', '9'),
		('10', '10'),
		('11', '11'),
		('12', '12'),
		('13', '13'),
		('14', '14'),
		('15', '15'),
		('16', '16'),
		('17', '17'),
		('18', '18'),
		('19', '19'),
		('20', '20'),
		('21', '21'),
		('22', '22'),
		('23', '23'),
	]

class HourSimple(select):
	name='hour'
	choices=[
		('00', '0'),
		('1', '1'),
		('2', '2'),
		('3', '3'),
		('4', '4'),
		('5', '5'),
		('6', '6'),
		('7', '7'),
		('8', '8'),
		('9', '9'),
		('10', '10'),
		('11', '11'),
		('12', '12'),
		('13', '13'),
		('14', '14'),
		('15', '15'),
		('16', '16'),
		('17', '17'),
		('18', '18'),
		('19', '19'),
		('20', '20'),
		('21', '21'),
		('22', '22'),
		('23', '23'),
	]

class Minute(select):
	name='minute'
	choices=[
		('', ''),
		('all', _( 'all' ) ),
		('00', '0'),
		('5', '5'),
		('10', '10'),
		('15', '15'),
		('20', '20'),
		('25', '25'),
		('30', '30'),
		('35', '35'),
		('40', '40'),
		('45', '45'),
		('50', '50'),
		('55', '55'),
	]

class MinuteSimple(select):
	name='minute'
	choices=[
		('00', '0'),
		('5', '5'),
		('10', '10'),
		('15', '15'),
		('20', '20'),
		('25', '25'),
		('30', '30'),
		('35', '35'),
		('40', '40'),
		('45', '45'),
		('50', '50'),
		('55', '55'),
	]

class MinuteSimple(select):
	name='minute'
	choices=[
		('00', '0'),
		('5', '5'),
		('10', '10'),
		('15', '15'),
		('20', '20'),
		('25', '25'),
		('30', '30'),
		('35', '35'),
		('40', '40'),
		('45', '45'),
		('50', '50'),
		('55', '55'),
	]

class fileMode(simple):
	name='fileMode'
	def parse(self, text):
		return text

class directoryMode(fileMode):
	name='directoryMode'

class sambaGroupType(select):
	name='sambagrouptype'
	choices=[
		('2', _('Domain Group')),
		('3', _('Local Group')),
		('5', _('Well-Known Group'))
	]

class sambaLogonHours(string):
	name='sambaLogonHours'

class printQuotaGroup(complex):
	name='printQuotaGroup'
	searchFilter='(&(cn=*)(objectClass=posixGroup))'
	subsyntaxes=[(_('Soft-Limit'), integer), (_('Hard-Limit'), integer), (_('Group'), string)]
	all_required=0


class printQuotaUser(complex):
	name='printQuotaUser'
	searchFilter='(&(uid=*)(objectClass=posixAccount)(!(objectClass=univentionHost)))'
	subsyntaxes=[(_('Soft-Limit'), integer), (_('Hard-Limit'), integer), (_('User'), string)]
	all_required=0


class printQuotaGroupsPerUser(complex):
	name='printQuotaUser'
	searchFilter='(&(uid=*)(objectClass=posixAccount)(!(objectClass=univentionHost)))'
	subsyntaxes=[(_('Soft-Limit'), integer), (_('Hard-Limit'), integer), (_('Group'), string)]
	all_required=0


class printerShare(string):
	name='printerShare'

class spoolHost(string):
	name='spoolHost'

class service(string):
	name='service'

class nfssync(select):
	name='nfssync'
	choices=[
		('sync', _( 'synchronous' ) ),
		('async', _( 'asynchronous' ) )
	]

class univentionAdminModules(select):
	name='univentionAdminModules'
	# we need a fallback
	choices=[('computers/managedclient', 'Computer: Managed Client'), ('computers/domaincontroller_backup', 'Computer: Domain Controller Backup'), ('computers/domaincontroller_master', 'Computer: Domain Controller Master'), ('computers/domaincontroller_slave', 'Computer: Domain Controller Slave'), ('computers/trustaccount', 'Computer: Domain Trust Account'), ('computers/ipmanagedclient', 'Computer: IP Managed Client'), ('computers/macos', 'Computer: Mac OS X Client'), ('computers/memberserver', 'Computer: Member Server'), ('computers/mobileclient', 'Computer: Mobile Client'), ('computers/thinclient', 'Computer: Thin Client'), ('computers/windows', 'Computer: Windows'), ('container/cn', 'Container: Container'), ('container/dc', 'Container: Domain'), ('container/ou', 'Container: Organizational Unit'), ('dhcp/host', 'DHCP: Host'), ('dhcp/pool', 'DHCP: Pool'), ('dhcp/server', 'DHCP: Server'), ('dhcp/service', 'DHCP: Service'), ('dhcp/shared', 'DHCP: Shared Network'), ('dhcp/sharedsubnet', 'DHCP: Shared Subnet'), ('dhcp/subnet', 'DHCP: Subnet'), ('dns/alias', 'DNS: Alias Record'), ('dns/forward_zone', 'DNS: Forward Lookup Zone'), ('dns/host_record', 'DNS: Host Record'), ('dns/ptr_record', 'DNS: Pointer'), ('dns/reverse_zone', 'DNS: Reverse Lookup Zone'), ('dns/srv_record', 'DNS: Service Record'), ('dns/zone_mx_record', 'DNS: Zone Mail Exchanger'), ('dns/zone_txt_record', 'DNS: Zone Text'), ('groups/group', 'Group: Group'), ('mail/folder', 'Mail: IMAP Folder'), ('mail/domain', 'Mail: Mail Domains'), ('mail/lists', 'Mail: Mailing Lists'), ('networks/network', 'Networks: Network'), ('policies/autostart', 'Policy: Autostart'), ('policies/clientdevices', 'Policy: Client Devices'), ('policies/dhcp_scope', 'Policy: DHCP Allow/Deny'), ('policies/dhcp_boot', 'Policy: DHCP Boot'), ('policies/dhcp_dns', 'Policy: DHCP DNS'), ('policies/dhcp_dnsupdate', 'Policy: DHCP DNS Update'), ('policies/dhcp_leasetime', 'Policy: DHCP Lease Time'), ('policies/dhcp_netbios', 'Policy: DHCP Netbios'), ('policies/dhcp_routing', 'Policy: DHCP Routing'), ('policies/dhcp_statements', 'Policy: DHCP Statements'), ('policies/desktop', 'Policy: Desktop'), ('policies/xfree', 'Policy: Display'), ('policies/ldapserver', 'Policy: LDAP Server'), ('policies/mailquota', 'Policy: Mail Quota'), ('policies/maintenance', 'Policy: Maintenance'), ('policies/managedclientpackages', 'Policy: Packages Managed Client'), ('policies/masterpackages', 'Policy: Packages Master'), ('policies/memberpackages', 'Policy: Packages Member'), ('policies/mobileclientpackages', 'Policy: Packages Mobile Client'), ('policies/slavepackages', 'Policy: Packages Slave'), ('policies/pwhistory', 'Policy: Password Policy'), ('policies/print_quota', 'Policy: Print Quota'), ('policies/printserver', 'Policy: Print Server'), ('policies/release', 'Policy: Release'), ('policies/repositoryserver', 'Policy: Repository Server'), ('policies/repositorysync', 'Policy: Repository Sync'), ('policies/sound', 'Policy: Sound'), ('policies/thinclient', 'Policy: Thin Client'), ('policies/admin_container', 'Policy: Univention Admin Container Settings'), ('policies/admin_user', 'Policy: Univention Admin View'), ('policies/share_userquota', 'Policy: Userquota-Policy'), ('policies/windowsinstallation', 'Policy: Windows Installation'), ('settings/default', 'Preferences: Default'), ('settings/directory', 'Preferences: Path'), ('settings/admin', 'Preferences: Univention Admin Global Settings'), ('settings/user', 'Preferences: Univention Admin User Settings'), ('settings/xconfig_choices', 'Preferences: X Configuration Choices'), ('shares/printer', 'Print-Share: Printer'), ('shares/printergroup', 'Print-Share: Printer Group'), ('settings/customattribute', 'Settings: Attribute'), ('settings/license', 'Settings: License'), ('settings/lock', 'Settings: Lock'), ('settings/packages', 'Settings: Package List'), ('settings/printermodel', 'Settings: Printer Driver List'), ('settings/printeruri', 'Settings: Printer URI List'), ('settings/prohibited_username', 'Settings: Prohibited Usernames'), ('settings/sambaconfig', 'Settings: Samba Configuration'), ('settings/sambadomain', 'Settings: Samba Domain'), ('settings/service', 'Settings: Service'), ('settings/usertemplate', 'Settings: User Template'), ('shares/share', 'Share: Directory'), ('settings/cn', 'Univention Settings'), ('users/user', 'User'), ('users/passwd', 'User: Password'), ('users/self', 'User: Self')]
	def parse(self, text):
		for choice in self.choices:
			if choice[0] == text:
				return text
		raise univention.admin.uexceptions.valueInvalidSyntax, _('"%s" is not a Univention Admin Module.') % text

# Unfortunatly, Python doesn't seem to support (static) class methods;
# however, (static) class variables such as "choices" seem to work;
# so, we'll modify "choices" using this global method
def univentionAdminModules_update():
	temp = []
	for name, mod in univention.admin.modules.modules.items():
		if not univention.admin.modules.virtual( mod ):
			temp.append( ( name, univention.admin.modules.short_description( mod ) ) )

	univentionAdminModules.choices = sorted( temp, key = operator.itemgetter( 1 ) )

__register_choice_update_function(univentionAdminModules_update)

class univentionAdminWizards(select):
	name='univentionAdminWizards'
	# we need a fallback
	choices=[('None', 'None'), ('computers/computer', 'Computer'), ('dhcp/dhcp', 'DHCP'), ('dns/dns', 'DNS'), ('groups/group', 'Groups'), ('mail/mail', 'Mail'), ('networks/network', 'Network'), ('policies/policy', 'Policies'), ('shares/print', 'Printers'), ('shares/share', 'Shares'), ('users/user', 'Users')]

def univentionAdminWizards_update():
	univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'RUN univentionAdminWizards_update')
	temp = []
	done = []

	for name, mod in univention.admin.modules.modules.items():
		if univention.admin.modules.wantsWizard( mod ):
			subs = univention.admin.modules.childModules( mod )
			if subs:
				done.extend( subs )
				temp.append( ( name, univention.admin.modules.wizardMenuString( mod ) ) )

	for name, mod in univention.admin.modules.modules.items():
		if name in done: continue
		if univention.admin.modules.wantsWizard( mod ) and not univention.admin.modules.childModules( mod ):
			temp.append( ( name, univention.admin.modules.wizardMenuString( mod ) ) )

	univentionAdminWizards.choices = sorted( temp, key = operator.itemgetter( 1 ) )
	univentionAdminWizards.choices.insert( 0, ( 'None', _( 'None' ) ) )
__register_choice_update_function(univentionAdminWizards_update)

class univentionAdminWebModules(select):
	name='univentionAdminWebModules'
	choices = [('modabout',_('About')), ('modbrowse',_('Browse')),( 'modwizard',_('Wizards')), ('modself',_('Personal Settings'))]
	# make no sense here: 'modedit', 'modlogout', 'modrelogin', 'modspacer'

class listAttributes(select):
	name = 'listAttributes'
	def parse(self, text):
		return text

class timeSpec(select):
	name = 'timeSpec'
	_times  = [(time, time) for hour in range(0, 24)
				for minute in range(0, 60, 15)
				for time in ('%02d:%02d' % (hour, minute),)]
	choices = [
		('', _('No Reboot')),
		('now', _('Immediately')),
	] + _times

class optionsUsersUser(select):
	name = 'optionsUsersUser'
	choices = [
		('groupware', _('Groupware Account')),
		('kerberos', _('Kerberos Principal')),
		('person', _('Personal Information')),
		('samba', _('Samba Account')),
		('posix', _('Posix Account')),
		('mail', _('Mail Account')),
	]

class CTX_BrokenTimedoutSession( select ):
	'''The keys of the choices are the hexdecimal values that represent
	the options value within the munged dial flags'''
	name = 'CTX_BrokenTimedoutSession'
	choices = (
		( '0000', _( 'Disconnect' ) ),
		( '0400', _( 'Reset' ) ),
		)

class CTX_ReconnectSession( select ):
	'''The keys of the choices are the hexdecimal values that represent
	the options value within the munged dial flags'''
	name = 'CTX_ReconnectSession'
	choices = (
		( '0000', _( 'All Clients' ) ),
		( '0200', _( 'Previously used Client' ) ),
		)

class CTX_Shadow( select ):
	'''The keys of the choices are the hexdecimal values that represent
	the options value within the munged dial flags'''
	name = 'CTX_Shadow'
	choices = (
		( '00000000', _( 'Disabled' ) ),
		( '01000000', _( 'Enabled: Input: on, Message: on' ) ),
		( '02000000', _( 'Enabled: Input: on, Message: off' ) ),
		( '03000000', _( 'Enabled: Input: off, Message: on' ) ),
		( '04000000', _( 'Enabled: Input: off, Message: off' ) ),
		)
class CTX_RASDialin( select ):
	'''The keys of the choices are the hexdecimal values that represent
	the options value within the munged dial flags'''
	name = 'CTX_RASDialin'
	choices = (
		( 'E', _( 'Disabled' ) ),
		( 'w', _( 'Enabled: Set by Caller' ) ),
		( 'k', _( 'Enabled: No Call Back' ) ),
		)
	#( ' ', _( 'Enabled: Preset To' ) ),


class nagiosHostsEnabledDn(simple):
	name='nagiosHostsEnabledDn'
	def parse(self, text):
		return text


class nagiosServiceDn(simple):
	name='nagiosServiceDn'
	def parse(self, text):
		return text

class configRegistry(simple):
	name='configRegistry'
	def parse(self, text):
		return text


class LDAP_Search( select ):
	FILTER_PATTERN = '(&(objectClass=univentionSyntax)(cn=%s))'

	def __init__( self, syntax_name = None, filter = None,
				  attribute = [], base = '', value = 'dn',
				  viewonly = False ):
		self.__syntax = syntax_name
		if filter:
		  	self.__syntax = None
			self.filter = filter
			self.attributes = attribute
			self.__base = base
			self.__value = value

		self.choices = []
		self.name = self.__class__.__name__
		self.viewonly = viewonly

	def parse( self, text ):
		return text

	def _load( self, lo ):
		if not self.__syntax:
			if self.viewonly:
				self.__value = 'dn'
			return
		try:
			filter = LDAP_Search.FILTER_PATTERN % self.__syntax
			dn, attrs = lo.search( filter = filter )[ 0 ]
		except:
			return

		if dn:
			self.__dn = dn
			self.filter = attrs[ 'univentionSyntaxLDAPFilter' ][ 0 ]
			self.attributes = attrs[ 'univentionSyntaxLDAPAttribute' ]
			if attrs.has_key( 'univentionSyntaxLDAPBase' ):
				self.__base = attrs[ 'univentionSyntaxLDAPBase' ][ 0 ]
			else:
				self.__base = ''
			if attrs.has_key( 'univentionSyntaxLDAPValue' ):
				self.__value = attrs[ 'univentionSyntaxLDAPValue' ][ 0 ]
			else:
				self.__value = 'dn'
			if attrs[ 'univentionSyntaxViewOnly' ][ 0 ] == 'TRUE':
				self.viewonly = True
				self.__value = 'dn'

	def _prepare( self, lo, filter = None ):
		if not filter:
			filter = self.filter
		self.choices = []
		self.values = []
		for dn, attrs in lo.search( filter = filter, base = self.__base ):
			if not self.viewonly:
				self.values.append( ( dn, self.__value, self.attributes[ 0 ] ) )
			else:
				self.values.append( ( dn, self.attributes ) )

class nfsMounts(complex):
	name='nfsMounts'
	subsyntaxes=[(_('NFS-Share'), LDAP_Search( filter = 'objectClass=univentionShareNFS', attribute = [ 'shares/share: printablename' ], value = 'shares/share: dn' )), ('Mount point', string)]
	all_required=1

