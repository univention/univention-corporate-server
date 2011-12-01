# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  syntax definitions
#
# Copyright 2004-2011 Univention GmbH
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

import re, string, math, time, operator
import ipaddr
import inspect
import univention.debug
import univention.admin.modules
import univention.admin.uexceptions
import univention.admin.localization
import base64
import copy
import sys, os
import shlex

translation=univention.admin.localization.translation('univention/admin')
_=translation.translate

#
# load all additional syntax files from */site-packages/univention/admin/syntax.d/*.py
#
def import_syntax_files():
	for dir in sys.path:
		if os.path.exists( os.path.join( dir, 'univention/admin/syntax.py' ) ):
			if os.path.isdir( os.path.join( dir, 'univention/admin/syntax.d/' ) ):
				for f in os.listdir( os.path.join( dir, 'univention/admin/syntax.d/' ) ):
					if f.endswith('.py'):
						fn = os.path.join( dir, 'univention/admin/syntax.d/', f )
						try:
							fd = open( fn, 'r' )
							exec fd in univention.admin.syntax.__dict__
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.import_syntax_files: importing "%s"' % fn)
						except:
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.syntax.import_syntax_files: loading %s failed' % fn )


choice_update_functions = []
def __register_choice_update_function(func):
	choice_update_functions.append(func)

def update_choices():
	''' update choices which are defined in LDAP '''
	for func in choice_update_functions:
		func()

def is_syntax( syntax_obj, syntax_type ):
	"""Returns True if the syntax object/class matches the given type."""

	return type( syntax_obj ) == type and issubclass( syntax_obj, syntax_type ) or isinstance( syntax_obj, syntax_type )

class ClassProperty( object ):
	'''A decorator that can be used to define read-only class properties'''
	def __init__( self, getter ):
		self.getter = getter

	def __get__( self, instance, owner ):
		return self.getter( owner )

# widget sizes
SIZES = ( 'OneThird', 'Half', 'TwoThirds', 'One', 'FourThirds', 'OneAndAHalf', 'FiveThirds' )

class ISyntax( object ):
	'''A base class for all syntax classes'''
	size = 'One'

	@ClassProperty
	def name( cls ):
		return cls.__name__

	@ClassProperty
	def type( cls ):
		return cls.__name__

	@classmethod
	def tostring(self, text):
		return text

class simple( ISyntax ):
	regex = None
	error_message = _( 'Invalid value' )

	@classmethod
	def parse( self, text ):
		if self.regex is None or self.regex.match( text ) is not None:
			return text
		else:
			raise univention.admin.uexceptions.valueError( self.error_message )

	@classmethod
	def new(self):
		return ''

	@classmethod
	def any(self):
		return '*'

class select( ISyntax ):
	"""Select item from list of choices.
	self.choice = [(id, _("Display text"), ...]
	"""
	empty_value = False

	@classmethod
	def parse(self, text):
		# for the UDM CLI
		if not hasattr( self, 'choices' ):
			return text

		if text in map( lambda x: x[ 0 ], self.choices ) or ( not text and select.empty_value ):
			return text

	@classmethod
	def new(self):
		return ''

	@classmethod
	def any(self):
		return '*'

class MultiSelect( ISyntax ):
	choices = ()
	empty_value = True
	error_message = _( 'Invalid value' )

	@classmethod
	def parse( self, value ):
		# required for UDM CLI
		if isinstance( value, basestring ):
			value = map( lambda x: x, shlex.split( value ) )

		if not self.empty_value and not value:
			raise univention.admin.uexceptions.valueError( _( 'An empty value is not allowed' ) )
		key_list = map( lambda x: x[ 0 ], self.choices )
		for item in value:
			if not item in key_list:
				raise univention.admin.uexceptions.valueError( self.error_message )

		return value

class complex( ISyntax ):
	delimiter = ' '
	# possible delimiters:
	# delimiter = '='   ==> single string is used to concatenate all subitems
	# delimiter = [ '', ': ', '=', '' ] ==> list of strings: e.g. 4 delimiter strings given to concatenate 3 subitems
	min_elements = None
	all_required = True

	@classmethod
	def parse(self, texts):
		parsed=[]

		if self.min_elements is not None:
			count = self.min_elements
		else:
			count = len( self.subsyntaxes )

		if len(texts) < count:
			raise univention.admin.uexceptions.valueInvalidSyntax, _("not enough arguments")
			p=s.parse(texts[i])

		if len(texts) > len( self.subsyntaxes ):
			raise univention.admin.uexceptions.valueInvalidSyntax, _("too many arguments")
			p=s.parse(texts[i])

		for i in range( len( texts ) ):
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'syntax.py: self.subsyntax[%s] is %s, texts is %s' % (i,self.subsyntaxes[i],  texts))
			if not inspect.isclass( self.subsyntaxes[ i ][ 1 ] ):
				s = self.subsyntaxes[ i ][ 1 ]
			else:
				s = self.subsyntaxes[ i ][ 1 ]()
			if texts[i] == None:
				if min_elements is None or ( i + 1 ) < min_elements:
					raise univention.admin.uexceptions.valueInvalidSyntax, _("Invalid syntax")
			p = s.parse( texts[ i ] )
			if not p:
				break
			parsed.append(p)
		return parsed

	@classmethod
	def tostring(self, texts):
		import string
		newTexts=[]
		if len(self.subsyntaxes) != len(texts):
			return ''
		else:
			for i in range(0,len(texts)):
				if  texts[i]:
					if not inspect.isclass( self.subsyntaxes[ i ][ 1 ] ):
						res=self.subsyntaxes[i][1].parse(texts[i])
					else:
						res=self.subsyntaxes[i][1]().parse(texts[i])
					if res:
						newTexts.append(res)
				elif self.all_required == True:
					return ''

		if not newTexts:
			return ''

		txt = ''
		if type(self.delimiter) == type([]):
			for i in range(0,len(newTexts)):
				txt += self.delimiter[i] + newTexts[i]
			txt += self.delimiter[-1]
		elif type(self.delimiter) == type(''):
			txt = self.delimiter.join(newTexts)

		return txt

	@classmethod
	def new(self):
		s=[]
		for desc, syntax in self.subsyntaxes:
			if not inspect.isclass( syntax ):
				s.append(syntax.new())
			else:
				s.append(syntax().new())
		return s

	def any(self):
		s=[]
		for desc, syntax in self.subsyntaxes:
			if not inspect.isclass( syntax ):
				s.append(syntax.any())
			else:
				s.append(syntax().any())
		return s

class UDM_Objects( ISyntax ):
	udm_modules = ()
	udm_filter = ''
	key = 'dn'
	label = None
	regex = re.compile( '^([^=,]+=[^=,]+,)*[^=,]+=[^=,]+$' )
	static_values = None
	empty_value = False
	depends = None
	error_message = _( "Not a valid LDAP DN" )
	simple = False # by default a MultiObjectSelect widget is used; if simple == True a ComboBox is used

	@classmethod
	def parse( self, text ):
		if not self.empty_value and not text:
			raise univention.admin.uexceptions.valueError( _( 'An empty value is not allowed' ) )
		if not text or not self.regex or self.regex.match( text ) != None:
			return text
		raise univention.admin.uexceptions.valueError( self.error_message )

class UDM_Attribute( ISyntax ):
	udm_module =None
	udm_filter = ''
	attribute = None
	is_complex = False
	key_index = 0
	label_index = 0
	label_format = None
	regex = None
	static_values = None
	empty_value = False
	depends = None
	error_message = _( 'Invalid value' )

	@classmethod
	def parse( self, text ):
		if not self.empty_value and not text:
			raise univention.admin.uexceptions.valueError( _( 'An empty value is not allowed' ) )
		if not text or not self.regex or self.regex.match( text ) != None:
			return text
		raise univention.admin.uexceptions.valueError( self.error_message )

class none(simple):
	pass

class string(simple):
	min_length=0
	max_length=0

	@classmethod
	def parse(self, text):
		return text

class string64(simple):

	@classmethod
	def parse(self, text):
		self.min_length=0
		self.max_length=64

		if len(text) > self.max_length:
			raise univention.admin.uexceptions.valueError( _('The value must not be longer than %d characters.') % self.max_length)
		return text

class OneThirdString( string ):
	size = 'OneThird'

class HalfString( string ):
	size = 'Half'

class TwoThirdsString( string ):
	size = 'TwoThirds'

class FourThirdsString( string ):
	size = 'FourThirds'

class OneAndAHalfString( string ):
	size = 'OneAndAHalf'

class FiveThirdsString( string ):
	size = 'FiveThirds'

# upload classes
class Upload( ISyntax ):
	@classmethod
	def parse( self, value ):
		return value

class Base64Upload( Upload ):
	@classmethod
	def parse( self, value ):
		try:
			dummy = base64.decodestring( value )
		except:
			raise univention.admin.uexceptions.valueError( _( 'Not a valid Base64 string: %s' ) % str( value ) )
		return value

class jpegPhoto( Upload ):
	@classmethod
	def tostring(self, text):
		if text and text[0]:
			encoded=base64.encodestring(text[0])
			return encoded
		else:
			return ''

class integer(simple):
	"""
	>>> integer().parse('1')
	'1'
	>>> integer().parse('0')
	'0'
	>>> integer().parse('-1') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> integer().parse('1.1') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> integer().parse('text') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> integer().parse('') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""
	min_length=1
	max_length=0
	_re = re.compile('^[0-9]+$')
	size = 'OneThird'

	@classmethod
	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Value must be a number!")

class boolean(simple):
	"""
	>>> boolean().parse('')
	''
	>>> boolean().parse('0')
	'0'
	>>> boolean().parse('1')
	'1'
	>>> boolean().parse('2') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> boolean().parse('0.1') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> boolean().parse('text') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""
	min_length=1
	max_length=1
	regex = re.compile('^[01]?$')
	error_message = _( "Value must be 0 or 1" )

	@classmethod
	def parse(self, text):
		if isinstance( text, bool ):
			return text and '1' or '0'
		return simple.parse( text )

class filesize(simple):
	"""
	>>> filesize().parse('0')
	'0'
	>>> filesize().parse('1b')
	'1b'
	>>> filesize().parse('2kB')
	'2kB'
	>>> filesize().parse('3Mb')
	'3Mb'
	>>> filesize().parse('4GB')
	'4GB'
	>>> filesize().parse('5pb') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> filesize().parse('-6') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> filesize().parse('-7.8') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> filesize().parse('text') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""
	min_length=1
	max_length=0
	regex = re.compile('^[0-9]+(|[gGmMkK])(|[bB])$')
	error_message = _( "Value must be an integer followed by one of GB,MB,KB,B or nothing (equals B)!" )

class mail_folder_name(simple):
	"""
	>>> mail_folder_name().parse('folder_name')
	'folder_name'
	>>> mail_folder_name().parse('folder name') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> mail_folder_name().parse('folder\tname') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> mail_folder_name().parse('folder!name') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""
	@classmethod
	def parse(self,text):
		if  "!" in text or " " in text or "\t" in text:
			raise univention.admin.uexceptions.valueError, _("Value may not contain whitespace or exclamation mark !")
		else:
			return text

class mail_folder_type(select):
	"""
	>>> mail_folder_type().parse('')
	''
	>>> mail_folder_type().parse('mail')
	'mail'
	>>> mail_folder_type().parse('event')
	'event'
	>>> mail_folder_type().parse('contact')
	'contact'
	>>> mail_folder_type().parse('task')
	'task'
	>>> mail_folder_type().parse('note')
	'note'
	>>> mail_folder_type().parse('journal')
	'journal'
	>>> mail_folder_type().parse('invalid')
	"""
	name='mail_folder_type'
	choices=[
		('',        _('undefined') ),
		('mail',    _('mails' ) ),
		('event',   _('events') ),
		('contact', _('contacts') ),
		('task',    _('tasks') ),
		('note',    _('notes') ),
		('journal', _('journals') ),
	]

class string_numbers_letters_dots(simple):
	"""
	>>> string_numbers_letters_dots().parse('a') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots().parse('A') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots().parse('0') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots().parse('aA')
	'aA'
	>>> string_numbers_letters_dots().parse('a.A')
	'a.A'
	>>> string_numbers_letters_dots().parse('a_A')
	'a_A'
	>>> string_numbers_letters_dots().parse('a-A')
	'a-A'
	>>> string_numbers_letters_dots().parse('.') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots().parse('_') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots().parse('-') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots().parse('/') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""

	regex = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9._-]*([a-zA-Z0-9]$)')
	error_message = _( 'Value must not contain anything other than digits, letters or dots, must be at least 2 characters long, and start and end with a digit or letter!' )

class string_numbers_letters_dots_spaces(simple):
	"""
	>>> string_numbers_letters_dots_spaces().parse('a') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces().parse('A') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces().parse('0') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces().parse('aA')
	'aA'
	>>> string_numbers_letters_dots_spaces().parse('a.A')
	'a.A'
	>>> string_numbers_letters_dots_spaces().parse('a_A')
	'a_A'
	>>> string_numbers_letters_dots_spaces().parse('a-A')
	'a-A'
	>>> string_numbers_letters_dots_spaces().parse('a A')
	'a A'
	>>> string_numbers_letters_dots_spaces().parse('.') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces().parse('_') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces().parse('-') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces().parse(' ') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces().parse('/') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""

	regex = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9._ -]*([a-zA-Z0-9]$)')
	error_message = _("Value must not contain anything other than digits, letters, dots or spaces, must be at least 2 characters long, and start and end with a digit or letter!")

class phone(simple):
	"""
	>>> phone().parse('+49 421 22232-0')
	'+49 421 22232-0'
	>>> phone().parse('++49 (0)700 Vanity')
	'++49 (0)700 Vanity'
	>>> phone().parse('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._ ()\/+-')
	'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._ ()\\\/+-'
	>>> phone().parse('^°!$§%&[]{}<>|*~#",.;:') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""
	min_length=1
	max_length=16
	regex = re.compile('(?u)[a-zA-Z0-9._ ()\\\/+-]*$')
	error_message = _("Value must not contain anything other than digits, letters, dots, brackets, slash, plus, or minus!")

class IA5string(string):
	"""
	>>> IA5string().parse(''' !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~''')
	' !\"#$%&\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'
	>>> IA5string().parse('öäüÖÄÜß€') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""

	@classmethod
	def parse(self, text):
		try:
			text.decode("utf-8").encode('ascii')
		except UnicodeEncodeError:
			raise univention.admin.uexceptions.valueError, _("Field must only contain ASCII characters!")
		return text

class uid(simple):
	"""
	>>> uid().parse('a') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid().parse('A') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid().parse('0') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid().parse('aA')
	'aA'
	>>> uid().parse('a.A')
	'a.A'
	>>> uid().parse('a_A')
	'a_A'
	>>> uid().parse('a-A')
	'a-A'
	>>> uid().parse('.') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid().parse('_') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid().parse('-') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid().parse('/') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid().parse('admin') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid().parse('Admin')
	'Admin'
	"""
	min_length=1
	max_length=16
	regex = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9._-]*([a-zA-Z0-9]$)')
	error_message = _("Value must not contain anything other than digits, letters, dots, dash or underscore, must be at least 2 characters long, must start and end with a digit or letter, and must not be admin!")

class uid_umlauts(simple):
	name='uid'
	min_length=1
	max_length=16
	_re = re.compile('(?u)(^\w[\w -.]*\w$)|\w*$')

	@classmethod
	def parse(self, text):
		if self._re.match(text.decode("utf-8")) != None and text != 'admin':
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Username must only contain numbers, letters and dots, and may not be 'admin'!")

class uid_umlauts_lower_except_first_letter(simple):
	min_length=1
	max_length=16
	_re = re.compile('(?u)(^\w[\w -.]*\w$)|\w*$')

	@classmethod
	def parse(self, text):
		unicode_text=text.decode("utf-8")
		for c in unicode_text[1:]:
			if c.isupper():
				raise univention.admin.uexceptions.valueError, _("Only the first letter of the username may be uppercase!")

		if self._re.match(unicode_text) != None and unicode_text != 'admin':
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Username must only contain numbers, letters and dots, and may not be 'admin'!")

class gid(simple):
	min_length=1
	max_length=32
	regex = re.compile( '(?u)^\w([\w -.]*\w)?$' )
	error_message = _("Value may not contain other than numbers, letters and dots!")

class sharePath( simple ):
	regex = re.compile('.*".*')
	error_message = _('Value may not contain double quotes (")!')

	@classmethod
	def parse(self, text):
		if not text[0] == '/':
			raise univention.admin.uexceptions.valueInvalidSyntax, _(', a path must begin with "/"!')
		for path in ["tmp", "root", "proc", "dev", "sys"]:
			if re.match("(^/%s$)|(^/%s/)" % (path, path), os.path.realpath(text)):
				raise univention.admin.uexceptions.valueError, _('Path may not start with "%s" !') % path

		return simple.parse( text )

class passwd(simple):
	min_length=8
	max_length=0
	_re1 = re.compile(r"[A-Z]")
	_re2 = re.compile(r"[a-z]")
	_re3 = re.compile(r"[0-9]")

	@classmethod
	def parse(self, text):
		if len(text) >= self.min_length:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _('The password is too short, at least %d characters needed.') % self.min_length

class userPasswd(simple):
	@classmethod
	def parse(self, text):
		if text and len(text) > 0:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _('Empty password not allowed!')

class hostName(simple):
	min_length=0
	max_length=0
	# hostname based upon RFC 952: <let>[*[<let-or-digit-or-hyphen>]<let-or-digit>]
	regex = re.compile("(^[a-zA-Z0-9])(([a-zA-Z0-9-_]*)([a-zA-Z0-9]$))?$")
	error_message = _("This is not a valid hostname.")

class DNS_Name(simple):
	# Regular expression for DNS entries (based on RFC 1123)
	regex = re.compile("(^[a-zA-Z0-9])(([a-zA-Z0-9-_.]*)([a-zA-Z0-9]$))?$")
	error_message = _("This is not a valid DNS entry name.")

class windowsHostName(simple):
	min_length=0
	max_length=0
	# hostname based upon RFC 952: <let>[*[<let-or-digit-or-hyphen>]<let-or-digit>]
	# windows hostnames are allowed to begin with digits
	regex = re.compile('^([0-9]*)([a-zA-Z])(([a-zA-Z0-9-_]*)([a-zA-Z0-9]$))?$')
	error_message = _("Not a valid windows hostname!")

class ipv4Address(simple):
	# match IPv4 (0.0.0.0 is allowed)
	@classmethod
	def parse(self, text):
		try:
			return str(ipaddr.IPv4Address(text))
		except ValueError:
			raise univention.admin.uexceptions.valueError, _("Not a valid IP address!")

class ipAddress(simple):

	# match IPv4 (0.0.0.0 is allowed) or IPv6 address (with IPv4-mapped IPv6)
	@classmethod
	def parse(self, text):
		try:
			return str(ipaddr.IPAddress(text))
		except ValueError:
			raise univention.admin.uexceptions.valueError, _("Not a valid IP address!")

class hostOrIP(simple):
	min_length=0
	max_length=0

	# match IPv4 (0.0.0.0 is allowed) or IPv6 address (with IPv4-mapped IPv6)
	@classmethod
	def ipAddress(self, text):
		try:
			ipaddr.IPAddress(text)
			return True
		except ValueError:
			return False

	@classmethod
	def hostName(self, text):
		_re = re.compile("(^[a-zA-Z])(([a-zA-Z0-9-]*)([a-zA-Z0-9]$))?$")
		if text and _re.match(text) != None:
			return True
		else:
			return False

	@classmethod
	def parse(self, text):
		if self.hostName(text) or self.ipAddress(text):
			return text
		else:
			raise univention.admin.uexceptions.valueError, _('Not a valid hostname or IP address!')

class v4netmask(simple):
	min_length=1
	max_length=15

	@classmethod
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

	@classmethod
	def parse(self, text):
		_ip=ipv4Address()
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

class netmask(simple):
	@classmethod
	def parse(self, text):
		if text.isdigit() and int(text) > 0 and int(text) < max(ipaddr.IPV4LENGTH, ipaddr.IPV6LENGTH):
			return str(int(text))
		try:
			return str(ipaddr.IPv4Network('0.0.0.0/%s' % (text, )).prefixlen)
		except ValueError:
			pass
		raise univention.admin.uexceptions.valueError, _("Not a valid netmask!")

class IPv4_AddressRange( complex ):
	subsyntaxes = (
		(_('First Address'), ipv4Address),
		(_( 'Last Address'), TwoThirdsString),
		)

class IP_AddressRange( complex ):
	subsyntaxes = (
		(_('First Address'), ipAddress),
		(_( 'Last Address'), ipAddress),
		)

class ipProtocol(select):
	choices=[ ( 'tcp', 'TCP' ), ('udp', 'UDP' ) ]

class ipProtocolSRV(select):
	choices=[ ( 'tcp', 'TCP' ), ( 'udp', 'UDP' ), ( 'msdcs', 'MSDCS' ), ( 'sites', 'SITES' ) ]
	size = 'OneThird'

class absolutePath(simple):
	min_length=1
	max_length=0
	_re = re.compile('^/.*')

	@classmethod
	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError,_("Not an absolute path!")

class emailAddress(simple):
	@classmethod
	def parse(self, text):
		if '@' not in text:
			raise univention.admin.uexceptions.valueError,_('Not a valid email address! (No "@"-character to separate local-part and domain-part)')
		return text

class emailAddressTemplate(simple):
	min_length=4
	max_length=0
	_re = re.compile("^.*@.*$")

	@classmethod
	def parse(self, text):
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError,_("Not a valid email address!")

class iso8601Date(simple):
	'''A date of the format:
	yyyy-ddd   (2009-213)
	yyyy-mm    (2009-05)
	yyyy-mm-dd (2009-05-13)
	yyyy-Www   (2009-W21)
	yyyy-Www-D (2009-W21-4)
	with the dashes being optional
	'''

	# regexp-source: http://regexlib.com/REDetails.aspx?regexp_id=2092
	regex = re.compile('^(\d{4}(?:(?:(?:\-)?(?:00[1-9]|0[1-9][0-9]|[1-2][0-9][0-9]|3[0-5][0-9]|36[0-6]))?|(?:(?:\-)?(?:1[0-2]|0[1-9]))?|(?:(?:\-)?(?:1[0-2]|0[1-9])(?:\-)?(?:0[1-9]|[12][0-9]|3[01]))?|(?:(?:\-)?W(?:0[1-9]|[1-4][0-9]|5[0-3]))?|(?:(?:\-)?W(?:0[1-9]|[1-4][0-9]|5[0-3])(?:\-)?[1-7])?)?)$')
	error_message = _("The given date does not conform to iso8601, example: \"2009-01-01\".")

class date(simple):
	"""
	Either a date in ISO (YYYY-MM-DD) or German (DD.MM.YY) format.
	Bug: Centuries are always stripped!

	>>> date().parse('21.12.03')
	'21.12.03'
	>>> date().parse('1961-01-01')
	'01.01.61'
	>>> date().parse('2061-01-01')
	'01.01.61'
	>>> date().parse('01.02.00')
	'01.02.00'
	>>> date().parse('01.02.99')
	'01.02.99'
	>>> date().parse('00.00.01') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	>>> date().parse('01x02y03') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:

	Bug #20230:
	>>> date().parse('31.2.1') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	name='date'
	min_length=5
	max_length=0
	_re_iso = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
	_re_de = re.compile('^[0-9]{1,2}\.[0-9]{1,2}\.[0-9]+$')

	@classmethod
	def parse(self, text):
		if self._re_iso.match(text) != None:
			year, month, day = map(lambda(x): int(x), text.split('-'))
			if 1960 < year < 2100 and 1 <= month <= 12 and 1 <= day <= 31:
				return '%02d.%02d.%s' % ( day, month, str( year )[ 2 : ] )
		if self._re_de.match(text) != None:
			day, month, year = map(lambda(x): int(x), text.split('.'))
			if 0 <= year <= 99 and 1 <= month <= 12 and 1 <= day <= 31:
				return text
		raise univention.admin.uexceptions.valueError,_("Not a valid Date")

class reverseLookupSubnet(simple):
	#               <-                      0-255                     ->  *dot  <-                      0-255                     ->
	regex_IPv4 = r'((([1-9]?[0-9])|(1[0-9]{0,2})|(2([0-4][0-9]|5[0-5])))\.){1,2}(([1-9]?[0-9])|(1[0-9]{0,2})|(2([0-4][0-9]|5[0-5])))'
	# normal IPv6 address without "::" substitution, leading zeroes must be preserved, at most 31 nibbles
	regex_IPv6 = r'(([0-9a-f]{4}:){0,7}[0-9a-f]{1,3})|(([0-9a-f]{4}:){0,6}[0-9a-f]{1,4})'
	regex = re.compile(r'^((%s)|(%s))$' % (regex_IPv4, regex_IPv6, ))
	error_message = _('A subnet for reverse lookup consists of the first one to three parts of an IPv4 address (example: "192.168.0") or of the first 1 to 31 nibbles of an IPv6 address with leading zeroes and without :: substitution (example: "2001:0db8:010")')

class reverseLookupZoneName(simple):
	#                       <-    IPv6 reverse zone   -> <-                           IPv4 reverse zone                           ->
	#                       nibble dot-separated ...arpa   <-                      0-255                     -> dot-separated .arpa
	regex = re.compile(r'^((([0-9a-f]\.){1,31}ip6\.arpa)|(((([1-9]?[0-9])|(1[0-9]{0,2})|(2([0-4][0-9]|5[0-5])))\.){1,3}in-addr.arpa))$')
	error_message = _("The name of a reverse zone for IPv4 consists of the reversed subnet address followed by .in-addr.arpa (example: \"0.168.192.in-addr.arpa\") or for IPv6 in nibble format followed by .ip6.arpa (example: \"0.0.0.0.0.0.1.0.8.b.d.0.1.0.0.2.ip6.arpa\")")

class dnsName(simple):
	_re = re.compile('^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9.]$')

	@classmethod
	def parse(self, text):
		if text==None:
			raise univention.admin.uexceptions.valueError, _("Missing value!")
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError, _("Value may not contain other than numbers, letters and dots!")

class dnsName_umlauts(simple):
	regex = re.compile('(?u)(^\w[\w -.]*\w$)|\w*$')
	error_message = _("Value may not contain other than numbers, letters and dots!")

class dnsNameDot(simple):
	regex = re.compile('^[0-9a-zA-Z.-]+$')
	error_message = _("Value may not contain other than numbers, letters and dots!")

class keyAndValue(complex):
	delimiter = ' = '
	subsyntaxes = [(_('Key'), string), (_('Value'), string)]
	all_required = 1

class dnsMX(complex):
	subsyntaxes=[(_('Priority'), integer), (_('Mail server'), dnsNameDot)]
	all_required=1

class dnsSRVName(complex):
	"""DNS Service Record.

	>>> dnsSRVName().parse(['ldap', 'tcp'])
	['ldap', 'tcp']
	"""
	min_elements = 2
	all_required = False
	subsyntaxes = ( ( _( 'Service' ), TwoThirdsString ), ( _( 'Protocol' ), ipProtocolSRV ), ( _( 'Extension' ), string ) )

class postalAddress( complex ):
	delimiter = ', '
	subsyntaxes = [ ( _( 'Street' ), string ), ( _( 'Postal code' ), OneThirdString ), ( _( 'City' ), TwoThirdsString ) ]
	all_required = True

class dnsSRVLocation(complex):
	subsyntaxes=[(_('Priority'), integer), (_('Weighting'), integer), (_('Port'), integer), (_('Server'), dnsName)]
	all_required=1

class unixTime(simple):
	regex = re.compile('^[0-9]+$')
	error_message = _("Not a valid time format")

class TimeUnits( select ):
	size = 'Half'
	choices = (
		( 'seconds', _( 'seconds' ) ),
		( 'minutes', _( 'minutes' ) ),
		( 'hours', _( 'hours' ) ),
		( 'days', _( 'days' ) )
		)

class UNIX_TimeInterval( complex ):
	min_elements = 1
	subsyntaxes = ( ( '', integer ), ( '', TimeUnits ) )

class NetworkType( select ):
	choices = ( ( 'ethernet', _( 'Ethernet' ) ), ( 'fddi', _( 'FDDI' ) ), ( 'token-ring', _( 'Token-Ring' ) ) )

class MAC_Address( simple ):
	regex = re.compile( '^([0-9a-fA-F]{1,2}[:-]){5}[0-9a-fA-F]{1,2}$' )
	error_message = _( 'This is not a valid MAC address. It must have 6 two digit hexadecimal numbers separated by \"-\" or \":\"' )
	size = 'TwoThirds'

	@classmethod
	def parse( self, text ):
		simple.parse( text )
		return text.replace( '-', ':' ).lower()

class DHCP_HardwareAddress( complex ):
	subsyntaxes = ( ( _( 'Type' ), NetworkType ), ( _( 'Address' ), MAC_Address ) )
	all_required=1

class Packages( UDM_Attribute ):
	udm_module = 'settings/packages'
	attribute = 'packageList'
	label_format = '%(name)s: %($attribute$)s'

class userAttributeList(string):
	@classmethod
	def parse(self, text):
		return text

class ldapDn(simple):
	"""LDAP distinguished name.

	>>> ldapDn().parse('dc=foo,dc=bar,dc=test')
	'dc=foo,dc=bar,dc=test'
	"""
	regex = re.compile('^([^=,]+=[^=,]+,)*[^=,]+=[^=,]+$')
	error_message = _("Not a valid LDAP DN")

class UMC_OperationSet( UDM_Objects ):
	udm_modules = ( 'settings/umc_operationset', )
	label = '%(description)s (%(name)s)'
	simple = True

class UMC_CommandPattern( complex ):
	subsyntaxes = ( ( _( 'Command pattern' ), string ), ( _( 'Option Pattern' ), string ) )
	min_elements = 1
	all_required = False # empty values are allowed

class LDAP_Server( UDM_Objects ):
	udm_modules = ( 'computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave' )
	label = '%(fqdn)s'
	simple = True

class IMAP_POP3( select ):
	choices = (
		( 'IMAP', _('IMAP') ),
		( 'POP3', _('POP3') ),
		)

class IMAP_Right( select ):
	choices = (
		( 'none', _( 'No access' ) ),
		( 'read', _( 'Read' ) ),
		( 'post', _( 'Post' ) ),
		( 'append', _( 'Append' ) ),
		( 'write', _( 'Write' ) ),
		( 'all', _( 'All' ) )
		)

class UserMailAddress( UDM_Objects ):
	udm_modules = ( 'users/user', )
	udm_filter = '(mailPrimaryAddress=*)'
	key = '%(mailPrimaryAddress)s'
	static_values = ( ( 'anyone', _( 'Anyone' ) ), )
	regex = re.compile( '^([^\s]+@[^\s]+|anyone)$' )

class GroupName( UDM_Objects ):
	udm_modules = ( 'groups/group', )
	key = '%(name)s'
	regex = re.compile( '^.+$' )
	simple = True

class UserName( UDM_Objects ):
	udm_modules = ( 'users/user', )
	key = '%(username)s'
	regex = re.compile( '^.+$' )
	simple = True

class SharedFolderUserACL( complex ):
	subsyntaxes = ( ( _( 'User' ), UserMailAddress ), ( _( 'Access right' ), IMAP_Right ) )

class SharedFolderGroupACL( complex ):
	subsyntaxes = ( ( _( 'Group' ), GroupName ), ( _( 'Access right' ), IMAP_Right ) )

class ldapDnOrNone(simple):
	_re=re.compile('^([^=,]+=[^=,]+,)*[^=,]+=[^=,]+$')

	@classmethod
	def parse(self, text):
		if not text or text == 'None':
			return text
		if self._re.match(text) != None:
			return text
		raise univention.admin.uexceptions.valueError,_("Not a valid LDAP DN")

class ldapObjectClass(simple):
	@classmethod
	def parse(self, text):
		return text

class ldapAttribute(simple):
	@classmethod
	def parse(self, text):
		return text

class XResolution(simple):
	regex = re.compile('^[0-9]+x[0-9]+$')
	error_message = _("Value consists of two integer numbers separated by an \"x\" (e.g. \"1024x768\")")

class XSync(simple):
	regex = re.compile('^[0-9]+(-[0-9]+)?( +[0-9]+(-[0-9]+)?)*$')
	error_message = _("Value consists of two integer numbers separated by a \"-\" (e.g. \"30-70\")")

class XColorDepth(simple):
	regex = re.compile('^[0-9]+$')

class XModule(select):
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
		('geode', 'Geode GX2/LX'),
		('glide', 'glide'),
		('glint', 'glint'),
		('i128', 'I128'),
		('i740', 'I740'),
		('i810', 'I810'),
		('imstt', 'IMSTT'),
		('intel', 'Intel'),
		('mach64', 'Mach64 (ATI)'),
		('mga', 'MGA'),
		('neomagic', 'Neomagic'),
		('newport', 'Newport'),
		('nsc', 'NSC'),
		('nv', 'NV'),
		('nvidia', 'NVidia (closed source)'),
		('openchrome', 'OpenChrome (VIA)'),
		('r128', 'ATI Rage'),
		('radeonhd', 'Radeon (AMD/ATI)'),
		('rendition', 'Rendition'),
		('s3', 'S3'),
		('s3virge', 'S3 Virge'),
		('savage', 'S3 Savage'),
		('siliconmotion', 'Siliconmotion'),
		('sis', 'SiS'),
		('sisusb', 'SiS USB'),
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

class XDisplayPosition(select):
	choices=[
		('', ''),
		('left', _('Left of primary display')),
		('right', _('Right of primary display')),
		('above', _('Above primary display')),
		('below', _('Below primary display'))
	]

class XMouseDevice(select):
	choices=[
		('', ''),
		('/dev/psaux', 'PS/2'),
		('/dev/input/mice', 'USB'),
		('/dev/ttyS0', 'Serial')
	]

class XKeyboardLayout(select):
	choices=[
		('', ''),
		('ad', 'Andorra'),
		('af', 'Afghanistan'),
		('al', 'Albania'),
		('am', 'Armenia'),
		('ara', 'Arabic'),
		('az', 'Azerbaijan'),
		('ba', 'Bosnia and Herzegovina'),
		('bd', 'Bangladesh'),
		('be', 'Belgium'),
		('bg', 'Bulgaria'),
		('brai', 'Braille'),
		('br', 'Brazil'),
		('bt', 'Bhutan'),
		('by', 'Belarus'),
		('ca', 'Canada'),
		('cd', 'Congo, Democratic Republic of the'),
		('ch', 'Switzerland'),
		('cn', 'China'),
		('cz', 'Czechia'),
		('de', 'Germany'),
		('dk', 'Denmark'),
		('ee', 'Estonia'),
		('epo', 'Esperanto'),
		('es', 'Spain'),
		('et', 'Ethiopia'),
		('fi', 'Finland'),
		('fo', 'Faroe Islands'),
		('fr', 'France'),
		('gb', 'United Kingdom'),
		('ge', 'Georgia'),
		('gh', 'Ghana'),
		('gn', 'Guinea'),
		('gr', 'Greece'),
		('hr', 'Croatia'),
		('hu', 'Hungary'),
		('ie', 'Ireland'),
		('il', 'Israel'),
		('in', 'India'),
		('iq', 'Iraq'),
		('ir', 'Iran'),
		('is', 'Iceland'),
		('it', 'Italy'),
		('jp', 'Japan'),
		('kg', 'Kyrgyzstan'),
		('kh', 'Cambodia'),
		('kr', 'Korea, Republic of'),
		('kz', 'Kazakhstan'),
		('la', 'Laos'),
		('latam', 'Latin American'),
		('lk', 'Sri Lanka'),
		('lt', 'Lithuania'),
		('lv', 'Latvia'),
		('ma', 'Morocco'),
		('mao', 'Maori'),
		('me', 'Montenegro'),
		('mk', 'Macedonia'),
		('mm', 'Myanmar'),
		('mn', 'Mongolia'),
		('mt', 'Malta'),
		('mv', 'Maldives'),
		('nec_vndr/jp', 'Japan (PC-98xx Series)'),
		('ng', 'Nigeria'),
		('nl', 'Netherlands'),
		('no', 'Norway'),
		('np', 'Nepal'),
		('pk', 'Pakistan'),
		('pl', 'Poland'),
		('pt', 'Portugal'),
		('ro', 'Romania'),
		('rs', 'Serbia'),
		('ru', 'Russia'),
		('se', 'Sweden'),
		('si', 'Slovenia'),
		('sk', 'Slovakia'),
		('sn', 'Senegal'),
		('sy', 'Syria'),
		('th', 'Thailand'),
		('tj', 'Tajikistan'),
		('tm', 'Turkmenistan'),
		('tr', 'Turkey'),
		('ua', 'Ukraine'),
		('us', 'USA'),
		('uz', 'Uzbekistan'),
		('vn', 'Vietnam'),
		('za', 'South Africa')
	]

class soundModule(select):
	choices=[
		('', ''),
		('auto', 'auto detect'),
		( 'snd-ad1816a', 'AD1816A, AD1815' ),
		( 'snd-adlib', 'AdLib FM' ),
		( 'snd-ak4114', 'AK4114 IEC958 (S/PDIF) receiver by Asahi Kasei' ),
		( 'snd-ak4117', 'AK4117 IEC958 (S/PDIF) receiver by Asahi Kasei' ),
		( 'snd-ali5451', 'ALI M5451' ),
		( 'snd-opl3-synth', 'ALSA driver for OPL3 FM synth' ),
		( 'snd-sb16-csp', 'ALSA driver for SB16 Creative Signal Processor' ),
		( 'snd-sb-common', 'ALSA lowlevel driver for Sound Blaster cards' ),
		( 'snd-interwave', 'AMD InterWave' ),
		( 'snd-interwave-stb', 'AMD InterWave STB with TEA6330T' ),
		( 'snd-ad1889', 'Analog Devices AD1889 ALSA sound driver' ),
		( 'snd-atiixp', 'ATI IXP AC97 controller' ),
		( 'snd-atiixp-modem', 'ATI IXP MC97 controller' ),
		( 'aedsp16', 'Audio Excel DSP 16 Driver Version 1.3' ),
		( 'snd-au8810', 'Aureal vortex 8810' ),
		( 'snd-au8820', 'Aureal vortex 8820' ),
		( 'snd-au8830', 'Aureal vortex 8830' ),
		( 'snd-als100', 'Avance Logic ALS1X0' ),
		( 'snd-als300', 'Avance Logic ALS300' ),
		( 'snd-als4000', 'Avance Logic ALS4000' ),
		( 'snd-azt3328', 'Aztech AZF3328 (PCI168)' ),
		( 'snd-sgalaxy', 'Aztech Sound Galaxy' ),
		( 'snd-azt2320', 'Aztech Systems AZT2320' ),
		( 'snd-bt87x', 'Brooktree Bt87x audio driver' ),
		( 'snd-ca0106', 'CA0106' ),
		( 'snd-cs4232', 'Cirrus Logic CS4232' ),
		( 'snd-cs4236', 'Cirrus Logic CS4235-9' ),
		( 'snd-cs4281', 'Cirrus Logic CS4281' ),
		( 'snd-cmi8330', 'C-Media CMI8330' ),
		( 'snd-cmipci', 'C-Media CMI8x38 PCI' ),
		( 'snd-vx-lib', 'Common routines for Digigram VX drivers' ),
		( 'snd-cs5535audio', 'CS5535 Audio' ),
		( 'snd-dt019x', 'Diamond Technologies DT-019X / Avance Logic ALS-007' ),
		( 'snd-mixart', 'Digigram miXart' ),
		( 'snd-pcxhr', 'Digigram pcxhr 0.8.4' ),
		( 'snd-vx222', 'Digigram VX222 V2/Mic' ),
		( 'snd-vxpocket', 'Digigram VXPocket' ),
		( 'snd-dummy', 'Dummy soundcard (/dev/null)' ),
		( 'snd-virmidi', 'Dummy soundcard for virtual rawmidi devices' ),
		( 'snd-darla20', 'Echoaudio Darla20 soundcards driver' ),
		( 'snd-darla24', 'Echoaudio Darla24 soundcards driver' ),
		( 'snd-echo3g', 'Echoaudio Echo3G soundcards driver' ),
		( 'snd-gina20', 'Echoaudio Gina20 soundcards driver' ),
		( 'snd-gina24', 'Echoaudio Gina24 soundcards driver' ),
		( 'snd-indigodj', 'Echoaudio Indigo DJ soundcards driver' ),
		( 'snd-indigoio', 'Echoaudio Indigo IO soundcards driver' ),
		( 'snd-indigo', 'Echoaudio Indigo soundcards driver' ),
		( 'snd-layla20', 'Echoaudio Layla20 soundcards driver' ),
		( 'snd-layla24', 'Echoaudio Layla24 soundcards driver' ),
		( 'snd-mia', 'Echoaudio Mia soundcards driver' ),
		( 'snd-mona', 'Echoaudio Mona soundcards driver' ),
		( 'snd-emu10k1', 'EMU10K1' ),
		( 'snd-emu10k1x', 'EMU10K1X' ),
		( 'snd-emu8000-synth', 'Emu8000 synth plug-in routine' ),
		( 'snd-ens1370', 'Ensoniq AudioPCI ES1370' ),
		( 'snd-ens1371', 'Ensoniq/Creative AudioPCI ES1371+' ),
		( 'snd-sscape', 'ENSONIQ SoundScape PnP driver' ),
		( 'snd-es968', 'ESS AudioDrive ES968' ),
		( 'snd-es18xx', 'ESS ES18xx AudioDrive' ),
		( 'snd-es1688-lib', 'ESS ESx688 lowlevel module' ),
		( 'snd-es1968', 'ESS Maestro' ),
		( 'snd-maestro3', 'ESS Maestro3 PCI' ),
		( 'snd-es1938', 'ESS Solo-1' ),
		( 'snd-fm801', 'ForteMedia FM801' ),
		( 'snd-ad1848', 'Generic AD1848/AD1847/CS4248' ),
		( 'snd-cs4231', 'Generic CS4231' ),
		( 'snd-es1688', 'Generic ESS ES1688/ES688 AudioDrive' ),
		( 'snd-i2c', 'Generic i2c interface for ALSA' ),
		( 'snd-util-mem', 'Generic memory management routines for soundcard memory allocation' ),
		( 'snd-gusclassic', 'Gravis UltraSound Classic' ),
		( 'snd-gusextreme', 'Gravis UltraSound Extreme' ),
		( 'snd-gusmax', 'Gravis UltraSound MAX' ),
		( 'snd-ice1712', 'ICEnsemble ICE1712 (Envy24)' ),
		( 'snd-ice17xx-ak4xxx', 'ICEnsemble ICE17xx <-> AK4xxx AD/DA chip interface' ),
		( 'snd-cs8427', 'IEC958 (S/PDIF) receiver & transmitter by Cirrus Logic' ),
		( 'snd-intel8x0', 'Intel 82801AA,82901AB,i810,i820,i830,i840,i845,MX440; SiS 7012; Ali 5455' ),
		( 'snd-intel8x0m', 'Intel 82801AA,82901AB,i810,i820,i830,i840,i845,MX440; SiS 7013; NVidia MCP/2/2S/3 modems' ),
		( 'snd-hda-intel', 'Intel HDA driver' ),
		( 'kahlua', 'Kahlua VSA1 PCI Audio' ),
		( 'snd-korg1212', 'korg1212' ),
		( 'snd-serial-u16550', 'MIDI serial u16550' ),
		( 'snd-miro', 'Miro miroSOUND PCM1 pro, PCM12, PCM20 Radio' ),
		( 'pss', 'Module for PSS sound cards (based on AD1848, ADSP-2115 and ESC614).' ),
		( 'snd-mtpav', 'MOTU MidiTimePiece AV multiport MIDI' ),
		( 'snd-mpu401', 'MPU-401 UART' ),
		( 'snd-nm256', 'NeoMagic NM256AV/ZX' ),
		( 'snd-opl4-lib', 'OPL4 driver' ),
		( 'snd-opl4-synth', 'OPL4 wavetable synth driver' ),
		( 'snd-opti92x-ad1848', 'OPTi92X - AD1848' ),
		( 'snd-opti92x-cs4231', 'OPTi92X - CS4231' ),
		( 'snd-opti93x', 'OPTi93X' ),
		( 'sb', 'OSS Soundblaster ISA PnP and legacy sound driver' ),
		( 'snd-riptide', 'riptide' ),
		( 'snd-rme32', 'RME Digi32, Digi32/8, Digi32 PRO' ),
		( 'snd-rme9652', 'RME Digi9652/Digi9636' ),
		( 'snd-rme96', 'RME Digi96, Digi96/8, Digi96/8 PRO, Digi96/8 PST, Digi96/8 PAD' ),
		( 'snd-hdsp', 'RME Hammerfall DSP' ),
		( 'snd-hdspm', 'RME HDSPM' ),
		( 'snd-sb16-dsp', 'Routines for control of 16-bit SoundBlaster cards and clones' ),
		( 'snd-sb8-dsp', 'Routines for control of 8-bit SoundBlaster cards and clones' ),
		( 'snd-ad1848-lib', 'Routines for control of AD1848/AD1847/CS4248' ),
		( 'snd-opl3-lib', 'Routines for control of AdLib FM cards (OPL2/OPL3/OPL4 chips)' ),
		( 'snd-ak4xxx-adda', 'Routines for control of AK452x / AK43xx AD/DA converters' ),
		( 'snd-cs4231-lib', 'Routines for control of CS4231(A)/CS4232/InterWave & compatible chips' ),
		( 'snd-cs4236-lib', 'Routines for control of CS4235/4236B/4237B/4238B/4239 chips' ),
		( 'snd-emu10k1-synth', 'Routines for control of EMU10K1 WaveTable synth' ),
		( 'snd-emux-synth', 'Routines for control of EMU WaveTable chip' ),
		( 'snd-mpu401-uart', 'Routines for control of MPU-401 in UART mode' ),
		( 'snd-tea575x-tuner', 'Routines for control of TEA5757/5759 Philips AM/FM radio tuner chips' ),
		( 'snd-tea6330t', 'Routines for control of the TEA6330T circuit via i2c bus' ),
		( 'snd-gus-lib', 'Routines for Gravis UltraSound soundcards' ),
		( 'snd-sonicvibes', 'S3 SonicVibes PCI' ),
		( 'snd-sb8', 'Sound Blaster 1.0/2.0/Pro' ),
		( 'snd-sb16', 'Sound Blaster 16' ),
		( 'snd-sbawe', 'Sound Blaster AWE' ),
		( 'snd-pdaudiocf', 'Sound Core PDAudio-CF' ),
		( 'snd-usb-usx2y', 'TASCAM US-X2Y Version 0.8.7.2' ),
		( 'snd-trident', 'Trident 4D-WaveDX/NX & SiS SI7018' ),
		( 'trident', 'Trident 4DWave/SiS 7018/ALi 5451 and Tvia/IGST CyberPro5050 PCI Audio Driver' ),
		( 'snd-wavefront', 'Turtle Beach Wavefront' ),
		( 'snd-ac97-codec', 'Universal interface for Audio Codec \'97' ),
		( 'snd-ak4531-codec', 'Universal routines for AK4531 codec' ),
		( 'snd-usb-audio', 'USB Audio' ),
		( 'snd-usb-lib', 'USB Audio/MIDI helper module' ),
		( 'snd-ice1724', 'VIA ICEnsemble ICE1724/1720 (Envy24HT/PT)' ),
		( 'snd-via82xx', 'VIA VT82xx audio' ),
		( 'snd-via82xx-modem', 'VIA VT82xx modem' ),
		( 'snd-ymfpci', 'Yamaha DS-1 PCI' ),
		( 'snd-opl3sa2', 'Yamaha OPL3SA2+' ),
	]

class GroupDN( UDM_Objects ):
	udm_modules = ( 'groups/group', )

class UserDN( UDM_Objects ):
	udm_modules = ( 'users/user', )

class HostDN( UDM_Objects ):
	udm_modules = ( 'computers/computer', )

class UserID( UDM_Objects ):
	udm_modules = ( 'users/user', )
	key = '%(uidNumber)s'
	label = '%(username)s'
	regex = re.compile( '^[0-9]+$' )
	static_values = ( ( '0', 'root' ), )

class GroupID( UDM_Objects ):
	udm_modules = ( 'groups/group', )
	key = '%(gidNumber)s'
	label = '%(name)s'
	regex = re.compile( '^[0-9]+$' )
	static_values = ( ( '0', 'root' ), )

class IComputer_FQDN( UDM_Objects ):
	udm_modules = ()
	key = '%(fqdn)s'
	label = '%(fqdn)s'
	regex = re.compile( '(?=^.{1,254}$)(^(?:(?!\d+\.)[a-zA-Z0-9_\-]{1,63}\.?)+(?:[a-zA-Z0-9]{2,})$)' ) #'(^[a-zA-Z])(([a-zA-Z0-9-_]*)([a-zA-Z0-9]$))?$' )
	error_message = _( 'Not a valid FQDN' )
	simple = True

class DomainController( IComputer_FQDN ):
	udm_modules = ( 'computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave' )

class Windows_Server( IComputer_FQDN ):
	udm_modules = ( 'computers/windows', 'computers/windows_domaincontroller' )

class UCS_Server( IComputer_FQDN ):
	udm_modules = ( 'computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver' )

class ServicePrint_FQDN( IComputer_FQDN ):
	udm_modules = ( 'computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver' )
	udm_filter = 'service=Print'

class KDE_Profile( UDM_Attribute ):
	udm_module = 'settings/default'
	attribute = 'defaultKdeProfiles'

class primaryGroup(ldapDn):
	searchFilter='objectClass=posixGroup'
	description=_('Primary Group')

class primaryGroup2(ldapDn):
	searchFilter='objectClass=posixGroup'
	description=_('Primary Group')

class network( UDM_Objects ):
	udm_modules = ( 'networks/network', )
	description=_('Network')
	label = '%(name)s'
	empty_value = True
	size = 'TwoThirds'

class IP_AddressList( select ):
	choices = ()
	depends = 'ip'
	size = 'One'

	@classmethod
	def parse( cls, text ):
		return text

class MAC_AddressList( select ):
	choices = ()
	depends = 'mac'
	size = 'TwoThirds'

	@classmethod
	def parse( cls, text ):
		return text

class DNS_ForwardZone( UDM_Objects ):
 	description=_('DNS forward zone')
	udm_modules = ( 'dns/forward_zone', )
	empty_value = True
	size = 'TwoThirds'

class DNS_ReverseZone( UDM_Objects ):
 	description=_('DNS reverse zone')
	udm_modules = ( 'dns/reverse_zone', )
	empty_value = True
	size = 'TwoThirds'

class dnsEntry( complex ):
 	description=_('DNS Entry')
	subsyntaxes = ( ( _( 'DNS forward zone' ), DNS_ForwardZone ), ( _( 'IP address' ), IP_AddressList ) )
	min_elements = 1

class dnsEntryReverse( complex ):
 	description=_('DNS Entry Reverse')
	subsyntaxes = ( ( _( 'DNS reverse zone' ), DNS_ReverseZone ), ( _( 'IP address' ), IP_AddressList ) )
	min_elements = 1

class DNS_ForwardZoneList( select ):
	depends = 'dnsEntryZoneForward'
	size = 'TwoThirds'

class dnsEntryAlias( complex ):
	description=_('DNS Entry Alias')
	subsyntaxes = ( ( _( 'Zone of existing host record' ), DNS_ForwardZoneList ), ( _( 'DNS forward zone' ), DNS_ForwardZone ), ( _( 'Alias' ), DNS_Name ) )

class dhcpService( UDM_Objects ):
	udm_modules = ( 'dhcp/service', )
	description=_('DHCP service')
	label = '%(name)s'
	empty_value = True
	size = 'TwoThirds'

class dhcpEntry( complex ):
	subsyntaxes= ( ( _( 'DHCP service' ), dhcpService ), ( _( 'IP address' ), IP_AddressList ), ( _( 'MAC address' ), MAC_AddressList ) )
	description=_( 'DHCP Entry' )

	@classmethod
	def parse( self, value ):
		return value

class WritableShare( UDM_Objects ):
	udm_modules = ( 'shares/share', )
	udm_filter = 'writeable=1'
	size = 'OneAndAHalf'

# class share(ldapDnOrNone):
# 	searchFilter='(objectClass=univentionShare)'
# 	description=_('Share')

class AllowDenyIgnore(select):
	choices=[
		('', ''),
		('allow', 'allow'),
		('deny', 'deny'),
		('ignore', 'ignore')
	]

class IStates( select ):
	values = []

	@ClassProperty
	def choices( cls ):
		return map( lambda x: ( x[ 1 ] ), cls.values )

	@classmethod
	def parse( cls, text ):
		if isinstance( text, basestring ):
			return text
		for value, choice in cls.values:
			if text == value:
				return choice[ 0 ]
		return text

class AllowDeny( IStates ):
	values = (
		( None, ('', '') ),
		( True, ( 'allow', 'allow' ) ),
		( False, ('deny', 'deny') )
	)

class booleanNone( IStates ):
	values = (
		( None, ( '', '' ) ),
		( True, ('yes', 'Yes' ) ),
		( False, ( 'no', 'No' ) )
	)

class TrueFalse( IStates ):
	values = (
		( None, ( '', '' ) ),
		( True, ( 'true', 'True' ) ),
		( False, ( 'false', 'False') )
	)

class TrueFalseUpper( IStates ):
	values = (
		( None, ( '', '' ) ),
		( True, ( 'TRUE', 'TRUE' ) ),
		( False, ( 'FALSE', 'FALSE' ) )
	)

class TrueFalseUp( IStates ):
	values = (
		( True, ( 'TRUE', 'TRUE' ) ),
		( False, ( 'FALSE', 'FALSE' ) )
	)

class OkOrNot( IStates ):
	values = (
		( True, ( 'OK', 'OK' ) ),
		( False, ( 'Not', 'KO' ) )
	)

class ddnsUpdateStyle(select):
	choices=[
		('', ''),
		('ad-hoc', 'ad-hoc'),
		('interim', 'interim'),
		('none', 'none')
	]

class ddnsUpdates( IStates ):
	values = (
		( None, ( '', '' ) ),
		( True, ( 'on', 'on' ) ),
		( False, ( 'off', 'off' ) )
	)

class netbiosNodeType(select):
	choices=[
		('', ''),
		('1', '1 B-node: Broadcast - no WINS'),
		('2', '2 P-node: Peer - WINS only'),
		('4', '4 M-node: Mixed - broadcast, then WINS'),
		('8', '8 H-node: Hybrid - WINS, then broadcast'),
	]

class kdeProfile(select):
	choices=[
		('', 'none'),
		('/home/kde.restricted', 'restricted'),
		('/home/kde.lockeddown', 'locked down'),
	]



class language(select):
	choices=[
		('', ''),
		('af_ZA', 'Afrikaans/South Africa'),
		('af_ZA.UTF-8', 'Afrikaans/South Africa(UTF-8)'),
		('sq_AL', 'Albanian/Albania'),
		('sq_AL.UTF-8', 'Albanian/Albania(UTF-8)'),
		('am_ET', 'Amharic/Ethiopia'),
		('ar_DZ', 'Arabic/Algeria'),
		('ar_DZ.UTF-8', 'Arabic/Algeria(UTF-8)'),
		('ar_BH', 'Arabic/Bahrain'),
		('ar_BH.UTF-8', 'Arabic/Bahrain(UTF-8)'),
		('ar_EG', 'Arabic/Egypt'),
		('ar_EG.UTF-8', 'Arabic/Egypt(UTF-8)'),
		('ar_IN', 'Arabic/India'),
		('ar_IQ', 'Arabic/Iraq'),
		('ar_IQ.UTF-8', 'Arabic/Iraq(UTF-8)'),
		('ar_JO', 'Arabic/Jordan'),
		('ar_JO.UTF-8', 'Arabic/Jordan(UTF-8)'),
		('ar_KW', 'Arabic/Kuwait'),
		('ar_KW.UTF-8', 'Arabic/Kuwait(UTF-8)'),
		('ar_LB', 'Arabic/Lebanon'),
		('ar_LB.UTF-8', 'Arabic/Lebanon(UTF-8)'),
		('ar_LY', 'Arabic/Libyan Arab Jamahiriya'),
		('ar_LY.UTF-8', 'Arabic/Libyan Arab Jamahiriya(UTF-8)'),
		('ar_MA', 'Arabic/Morocco'),
		('ar_MA.UTF-8', 'Arabic/Morocco(UTF-8)'),
		('ar_OM', 'Arabic/Oman'),
		('ar_OM.UTF-8', 'Arabic/Oman(UTF-8)'),
		('ar_QA', 'Arabic/Qatar'),
		('ar_QA.UTF-8', 'Arabic/Qatar(UTF-8)'),
		('ar_SA', 'Arabic/Saudi Arabia'),
		('ar_SA.UTF-8', 'Arabic/Saudi Arabia(UTF-8)'),
		('ar_SD', 'Arabic/Sudan'),
		('ar_SD.UTF-8', 'Arabic/Sudan(UTF-8)'),
		('ar_SY', 'Arabic/Syrian Arab Republic'),
		('ar_SY.UTF-8', 'Arabic/Syrian Arab Republic(UTF-8)'),
		('ar_TN', 'Arabic/Tunisia'),
		('ar_TN.UTF-8', 'Arabic/Tunisia(UTF-8)'),
		('ar_AE', 'Arabic/United Arab Emirates'),
		('ar_AE.UTF-8', 'Arabic/United Arab Emirates(UTF-8)'),
		('ar_YE', 'Arabic/Yemen'),
		('ar_YE.UTF-8', 'Arabic/Yemen(UTF-8)'),
		('an_ES', 'Aragonese/Spain'),
		('an_ES.UTF-8', 'Aragonese/Spain(UTF-8)'),
		('hy_AM', 'Armenian/Armenia'),
		('az_AZ', 'Azeri/Azerbaijan'),
		('eu_ES@euro', 'Basque/Spain'),
		('eu_ES.UTF-8', 'Basque/Spain(UTF-8)'),
		('be_BY', 'Belarusian/Belarus'),
		('be_BY.UTF-8', 'Belarusian/Belarus(UTF-8)'),
		('bn_BD', 'Bengali/BD'),
		('bn_IN', 'Bengali/India'),
		('bs_BA', 'Bosnian/Bosnia and Herzegowina'),
		('bs_BA.UTF-8', 'Bosnian/Bosnia and Herzegowina(UTF-8)'),
		('br_FR@euro', 'Breton/France'),
		('br_FR.UTF-8', 'Breton/France(UTF-8)'),
		('bg_BG', 'Bulgarian/Bulgaria'),
		('bg_BG.UTF-8', 'Bulgarian/Bulgaria(UTF-8)'),
		('ca_ES@euro', 'Catalan/Spain'),
		('ca_ES.UTF-8', 'Catalan/Spain(UTF-8)'),
		('zh_HK', 'Chinese/Hong Kong'),
		('zh_HK.UTF-8', 'Chinese/Hong Kong(UTF-8)'),
		('zh_CN', 'Chinese/P.R. of China'),
		('zh_CN.UTF-8', 'Chinese/P.R. of China(UTF-8)'),
		('zh_SG', 'Chinese/Singapore'),
		('zh_SG.UTF-8', 'Chinese/Singapore(UTF-8)'),
		('zh_TW', 'Chinese/Taiwan R.O.C.'),
		('zh_TW.UTF-8', 'Chinese/Taiwan R.O.C.(UTF-8)'),
		('kw_GB', 'Cornish/Britain'),
		('kw_GB.UTF-8', 'Cornish/Britain(UTF-8)'),
		('hr_HR', 'Croatian/Croatia'),
		('hr_HR.UTF-8', 'Croatian/Croatia(UTF-8)'),
		('cs_CZ', 'Czech/Czech Republic'),
		('cs_CZ.UTF-8', 'Czech/Czech Republic(UTF-8)'),
		('da_DK', 'Danish/Denmark'),
		('da_DK.UTF-8', 'Danish/Denmark(UTF-8)'),
		('nl_BE@euro', 'Dutch/Belgium'),
		('nl_BE.UTF-8', 'Dutch/Belgium(UTF-8)'),
		('nl_NL@euro', 'Dutch/Netherlands'),
		('nl_NL.UTF-8', 'Dutch/Netherlands(UTF-8)'),
		('en_AU', 'English/Australia'),
		('en_AU.UTF-8', 'English/Australia(UTF-8)'),
		('en_BW', 'English/Botswana'),
		('en_BW.UTF-8', 'English/Botswana(UTF-8)'),
		('en_CA', 'English/Canada'),
		('en_CA.UTF-8', 'English/Canada(UTF-8)'),
		('en_DK', 'English/Denmark'),
		('en_DK.UTF-8', 'English/Denmark(UTF-8)'),
		('en_GB', 'English/Great Britain'),
		('en_GB.UTF-8', 'English/Great Britain(UTF-8)'),
		('en_HK', 'English/Hong Kong'),
		('en_HK.UTF-8', 'English/Hong Kong(UTF-8)'),
		('en_IN', 'English/India'),
		('en_IE@euro', 'English/Ireland'),
		('en_IE.UTF-8', 'English/Ireland(UTF-8)'),
		('en_NZ', 'English/New Zealand'),
		('en_NZ.UTF-8', 'English/New Zealand(UTF-8)'),
		('en_PH', 'English/Philippines'),
		('en_PH.UTF-8', 'English/Philippines(UTF-8)'),
		('en_SG', 'English/Singapore'),
		('en_SG.UTF-8', 'English/Singapore(UTF-8)'),
		('en_ZA', 'English/South Africa'),
		('en_ZA.UTF-8', 'English/South Africa(UTF-8)'),
		('en_US', 'English/USA'),
		('en_US.UTF-8', 'English/USA(UTF-8)'),
		('en_ZW', 'English/Zimbabwe'),
		('en_ZW.UTF-8', 'English/Zimbabwe(UTF-8)'),
		('eo_EO', 'Esperanto/Esperanto'),
		('et_EE', 'Estonian/Estonia'),
		('et_EE.UTF-8', 'Estonian/Estonia(UTF-8)'),
		('fo_FO', 'Faroese/Faroe Islands'),
		('fo_FO.UTF-8', 'Faroese/Faroe Islands(UTF-8)'),
		('fi_FI@euro', 'Finnish/Finland'),
		('fi_FI.UTF-8', 'Finnish/Finland(UTF-8)'),
		('fr_BE@euro', 'French/Belgium'),
		('fr_BE.UTF-8', 'French/Belgium(UTF-8)'),
		('fr_CA', 'French/Canada'),
		('fr_CA.UTF-8', 'French/Canada(UTF-8)'),
		('fr_FR@euro', 'French/France'),
		('fr_FR.UTF-8', 'French/France(UTF-8)'),
		('fr_LU@euro', 'French/Luxemburg'),
		('fr_LU.UTF-8', 'French/Luxemburg(UTF-8)'),
		('fr_CH', 'French/Switzerland'),
		('fr_CH.UTF-8', 'French/Switzerland(UTF-8)'),
		('gl_ES@euro', 'Galician/Spain'),
		('gl_ES.UTF-8', 'Galician/Spain(UTF-8)'),
		('ka_GE', 'Georgian/Georgia'),
		('ka_GE.UTF-8', 'Georgian/Georgia(UTF-8)'),
		('de_AT@euro', 'German/Austria'),
		('de_AT.UTF-8', 'German/Austria(UTF-8)'),
		('de_BE@euro', 'German/Belgium'),
		('de_BE.UTF-8', 'German/Belgium(UTF-8)'),
		('de_DE', 'German/Germany'),
		('de_DE.UTF-8', 'German/Germany(UTF-8)'),
		('de_DE@euro', 'German/Germany(euro)'),
		('de_LU@euro', 'German/Luxemburg'),
		('de_LU.UTF-8', 'German/Luxemburg(UTF-8)'),
		('de_CH', 'German/Switzerland'),
		('de_CH.UTF-8', 'German/Switzerland(UTF-8)'),
		('el_GR@euro', 'Greek/Greece'),
		('el_GR.UTF-8', 'Greek/Greece(UTF-8)'),
		('kl_GL', 'Greenlandic/Greenland'),
		('kl_GL.UTF-8', 'Greenlandic/Greenland(UTF-8)'),
		('iw_IL', 'Hebrew/Israel'),
		('iw_IL.UTF-8', 'Hebrew/Israel(UTF-8)'),
		('he_IL', 'Hebrew/Israel'),
		('he_IL.UTF-8', 'Hebrew/Israel(UTF-8)'),
		('hi_IN', 'Hindi/India'),
		('hu_HU', 'Hungarian/Hungary'),
		('hu_HU.UTF-8', 'Hungarian/Hungary(UTF-8)'),
		('is_IS', 'Icelandic/Iceland'),
		('is_IS.UTF-8', 'Icelandic/Iceland(UTF-8)'),
		('id_ID', 'Indonesian/Indonesia'),
		('id_ID.UTF-8', 'Indonesian/Indonesia(UTF-8)'),
		('ga_IE@euro', 'Irish/Ireland'),
		('ga_IE.UTF-8', 'Irish/Ireland(UTF-8)'),
		('it_IT@euro', 'Italian/Italy'),
		('it_IT.UTF-8', 'Italian/Italy(UTF-8)'),
		('it_CH', 'Italian/Switzerland'),
		('it_CH.UTF-8', 'Italian/Switzerland(UTF-8)'),
		('ja_JP', 'Japanese/Japan'),
		('ko_KR', 'Korean/Republic of Korea'),
		('lo_LA', 'Lao/Laos'),
		('lv_LV', 'Latvian/Latvia'),
		('lv_LV.UTF-8', 'Latvian/Latvia(UTF-8)'),
		('lt_LT', 'Lithuanian/Lithuania'),
		('lt_LT.UTF-8', 'Lithuanian/Lithuania(UTF-8)'),
		('lug_UG', 'Luganda/Uganda'),
		('mk_MK', 'Macedonian/Macedonia'),
		('mk_MK.UTF-8', 'Macedonian/Macedonia(UTF-8)'),
		('ms_MY', 'Malay/Malaysia'),
		('ms_MY.UTF-8', 'Malay/Malaysia(UTF-8)'),
		('ml_IN', 'Malayalam/India'),
		('mt_MT', 'Maltese/malta'),
		('mt_MT.UTF-8', 'Maltese/malta(UTF-8)'),
		('gv_GB', 'Manx Gaelic/Britain'),
		('gv_GB.UTF-8', 'Manx Gaelic/Britain(UTF-8)'),
		('mi_NZ', 'Maori/New Zealand'),
		('mi_NZ.UTF-8', 'Maori/New Zealand(UTF-8)'),
		('mr_IN', 'Marathi/India'),
		('mn_MN', 'Mongolian/Mongolia'),
		('se_NO', 'Northern Saami/Norway'),
		('nn_NO', 'Norwegian, Nynorsk/Norway'),
		('nn_NO.UTF-8', 'Norwegian, Nynorsk/Norway(UTF-8)'),
		('no_NO', 'Norwegian/Norway'),
		('no_NO.UTF-8', 'Norwegian/Norway(UTF-8)'),
		('oc_FR', 'Occitan/France'),
		('oc_FR.UTF-8', 'Occitan/France(UTF-8)'),
		('fa_IR', 'Persian/Iran'),
		('pl_PL', 'Polish/Poland'),
		('pl_PL.UTF-8', 'Polish/Poland(UTF-8)'),
		('pt_BR', 'Portuguese/Brasil'),
		('pt_BR.UTF-8', 'Portuguese/Brasil(UTF-8)'),
		('pt_PT@euro', 'Portuguese/Portugal'),
		('pt_PT.UTF-8', 'Portuguese/Portugal(UTF-8)'),
		('ro_RO', 'Romanian/Romania'),
		('ro_RO.UTF-8', 'Romanian/Romania(UTF-8)'),
		('ru_RU', 'Russian/Russia'),
		('ru_RU.UTF-8', 'Russian/Russia(UTF-8)'),
		('ru_UA', 'Russian/Ukraine'),
		('ru_UA.UTF-8', 'Russian/Ukraine(UTF-8)'),
		('gd_GB', 'Scots Gaelic/Great Britain'),
		('gd_GB.UTF-8', 'Scots Gaelic/Great Britain(UTF-8)'),
		('sr_YU@cyrillic', 'Serbian/Yugoslavia'),
		('sk_SK', 'Slovak/Slovak'),
		('sk_SK.UTF-8', 'Slovak/Slovak(UTF-8)'),
		('sl_SI', 'Slovenian/Slovenia'),
		('sl_SI.UTF-8', 'Slovenian/Slovenia(UTF-8)'),
		('st_ZA', 'Sotho/South Africa'),
		('st_ZA.UTF-8', 'Sotho/South Africa(UTF-8)'),
		('es_AR', 'Spanish/Argentina'),
		('es_AR.UTF-8', 'Spanish/Argentina(UTF-8)'),
		('es_BO', 'Spanish/Bolivia'),
		('es_BO.UTF-8', 'Spanish/Bolivia(UTF-8)'),
		('es_CL', 'Spanish/Chile'),
		('es_CL.UTF-8', 'Spanish/Chile(UTF-8)'),
		('es_CO', 'Spanish/Colombia'),
		('es_CO.UTF-8', 'Spanish/Colombia(UTF-8)'),
		('es_CR', 'Spanish/Costa Rica'),
		('es_CR.UTF-8', 'Spanish/Costa Rica(UTF-8)'),
		('es_DO', 'Spanish/Dominican Republic'),
		('es_DO.UTF-8', 'Spanish/Dominican Republic(UTF-8)'),
		('es_EC', 'Spanish/Ecuador'),
		('es_EC.UTF-8', 'Spanish/Ecuador(UTF-8)'),
		('es_SV', 'Spanish/El Salvador'),
		('es_SV.UTF-8', 'Spanish/El Salvador(UTF-8)'),
		('es_GT', 'Spanish/Guatemala'),
		('es_GT.UTF-8', 'Spanish/Guatemala(UTF-8)'),
		('es_HN', 'Spanish/Honduras'),
		('es_HN.UTF-8', 'Spanish/Honduras(UTF-8)'),
		('es_MX', 'Spanish/Mexico'),
		('es_MX.UTF-8', 'Spanish/Mexico(UTF-8)'),
		('es_NI', 'Spanish/Nicaragua'),
		('es_NI.UTF-8', 'Spanish/Nicaragua(UTF-8)'),
		('es_PA', 'Spanish/Panama'),
		('es_PA.UTF-8', 'Spanish/Panama(UTF-8)'),
		('es_PY', 'Spanish/Paraguay'),
		('es_PY.UTF-8', 'Spanish/Paraguay(UTF-8)'),
		('es_PE', 'Spanish/Peru'),
		('es_PE.UTF-8', 'Spanish/Peru(UTF-8)'),
		('es_PR', 'Spanish/Puerto Rico'),
		('es_PR.UTF-8', 'Spanish/Puerto Rico(UTF-8)'),
		('es_ES@euro', 'Spanish/Spain'),
		('es_ES.UTF-8', 'Spanish/Spain(UTF-8)'),
		('es_US', 'Spanish/USA'),
		('es_US.UTF-8', 'Spanish/USA(UTF-8)'),
		('es_UY', 'Spanish/Uruguay'),
		('es_UY.UTF-8', 'Spanish/Uruguay(UTF-8)'),
		('es_VE', 'Spanish/Venezuela'),
		('es_VE.UTF-8', 'Spanish/Venezuela(UTF-8)'),
		('sv_FI@euro', 'Swedish/Finland'),
		('sv_FI.UTF-8', 'Swedish/Finland(UTF-8)'),
		('sv_SE', 'Swedish/Sweden'),
		('sv_SE.UTF-8', 'Swedish/Sweden(UTF-8)'),
		('tl_PH', 'Tagalog/Philippines'),
		('tl_PH.UTF-8', 'Tagalog/Philippines(UTF-8)'),
		('tg_TJ', 'Tajik/Tajikistan'),
		('tg_TJ.UTF-8', 'Tajik/Tajikistan(UTF-8)'),
		('ta_IN', 'Tamil/India'),
		('tt_RU', 'Tatar/Tatarstan'),
		('te_IN', 'Telgu/India'),
		('th_TH', 'Thai/Thailand'),
		('th_TH.UTF-8', 'Thai/Thailand(UTF-8)'),
		('ti_ER', 'Tigrigna/Eritrea'),
		('ti_ET', 'Tigrigna/Ethiopia'),
		('tr_TR', 'Turkish/Turkey'),
		('tr_TR.UTF-8', 'Turkish/Turkey(UTF-8)'),
		('uk_UA', 'Ukrainian/Ukraine'),
		('uk_UA.UTF-8', 'Ukrainian/Ukraine(UTF-8)'),
		('ur_PK', 'Urdu/Pakistan'),
		('uz_UZ', 'Uzbek/Uzbekistan'),
		('uz_UZ.UTF-8', 'Uzbek/Uzbekistan(UTF-8)'),
		('vi_VN', 'Vietnamese/Vietnam'),
		('wa_BE@euro', 'Walloon/Belgium'),
		('wa_BE.UTF-8', 'Walloon/Belgium(UTF-8)'),
		('cy_GB', 'Welsh/Great Britain'),
		('cy_GB.UTF-8', 'Welsh/Great Britain(UTF-8)'),
		('xh_ZA', 'Xhosa/South Africa'),
		('xh_ZA.UTF-8', 'Xhosa/South Africa(UTF-8)'),
		('yi_US', 'Yiddish/USA'),
		('yi_US.UTF-8', 'Yiddish/USA(UTF-8)'),
		('zu_ZA', 'Zulu/South Africa'),
		('zu_ZA.UTF-8', 'Zulu/South Africa(UTF-8)'),	
	]

class Month(select):
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
	choices=[
		('', ''),
		('all', _( 'all' ) ),
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

class UNIX_AccessRight( simple ):
	pass

class sambaGroupType(select):
	choices=[
		('2', _('Domain Group')),
		('3', _('Local Group')),
		('5', _('Well-Known Group'))
	]

class SambaLogonHours( MultiSelect ):
	choices = [ ( idx *24 + hour, '%s %d-%d' % (day, hour, hour +1) ) for idx, day in ( ( 0, _( 'Sun' ) ), ( 1, _( 'Mon' ) ), ( 2, _( 'Tue' ) ), ( 3, _( 'Wed' ) ), ( 4, _( 'Thu' ) ), ( 5, _( 'Fri' ) ), ( 6, _( 'Sat' ) ) ) for hour in range( 24 ) ]

	@classmethod
	def parse( self, value ):
		# required for UDM CLI: in this case the keys MUST be of type int
		if isinstance( value, basestring ):
			value = map( lambda x: int( x ), shlex.split( value ) )

		return MultiSelect.parse.im_func( self, value )

class SambaPrivileges( select ):
	empty_value = True
	choices = [
		( 'SeMachineAccountPrivilege', _( 'Add machines to domain' ) ),
		( 'SeSecurityPrivilege', _( 'Manage auditing and security log' ) ),
		( 'SeTakeOwnershipPrivilege', _( 'Take ownership of files or other objects' ) ),
		( 'SeBackupPrivilege', _( 'Back up files and directories' ) ),
		( 'SeRestorePrivilege', _( 'Restore files and directories' ) ),
		( 'SeRemoteShutdownPrivilege', _( 'Force shutdown from a remote system' ) ),
		( 'SePrintOperatorPrivilege', _( 'Manage printers' ) ),
		( 'SeAddUsersPrivilege', _( 'Add users and groups to the domain' ) ),
		( 'SeDiskOperatorPrivilege', _( 'Manage disk shares' ) ),
	]

class ServiceMail( UDM_Objects ):
	udm_modules = ( 'computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver' )
	udm_filter = 'service=SMTP'

class ServicePrint( UDM_Objects ):
	udm_modules = ( 'computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver' )
	udm_filter = 'service=Print'

class Service( UDM_Objects ):
	udm_modules = ( 'settings/service', )
	regex = None
	key = '%(name)s'
	label = '%(name)s'
	simple = True

class nfssync(select):
	choices=[
		('sync', _( 'synchronous' ) ),
		('async', _( 'asynchronous' ) )
	]

class univentionAdminModules(select):
	# we need a fallback
	choices=[('computers/managedclient', 'Computer: Managed Client'), ('computers/domaincontroller_backup', 'Computer: Domain Controller Backup'), ('computers/domaincontroller_master', 'Computer: Domain Controller Master'), ('computers/domaincontroller_slave', 'Computer: Domain Controller Slave'), ('computers/trustaccount', 'Computer: Domain Trust Account'), ('computers/ipmanagedclient', 'Computer: IP Managed Client'), ('computers/macos', 'Computer: Mac OS X Client'), ('computers/memberserver', 'Computer: Member Server'), ('computers/mobileclient', 'Computer: Mobile Client'), ('computers/thinclient', 'Computer: Thin Client'), ('computers/windows', 'Computer: Windows'), ('container/cn', 'Container: Container'), ('container/dc', 'Container: Domain'), ('container/ou', 'Container: Organizational Unit'), ('dhcp/host', 'DHCP: Host'), ('dhcp/pool', 'DHCP: Pool'), ('dhcp/server', 'DHCP: Server'), ('dhcp/service', 'DHCP: Service'), ('dhcp/shared', 'DHCP: Shared Network'), ('dhcp/sharedsubnet', 'DHCP: Shared Subnet'), ('dhcp/subnet', 'DHCP: Subnet'), ('dns/alias', 'DNS: Alias Record'), ('dns/forward_zone', 'DNS: Forward Lookup Zone'), ('dns/host_record', 'DNS: Host Record'), ('dns/ptr_record', 'DNS: Pointer'), ('dns/reverse_zone', 'DNS: Reverse Lookup Zone'), ('dns/srv_record', 'DNS: Service Record'), ('dns/zone_mx_record', 'DNS: Zone Mail Exchanger'), ('dns/zone_txt_record', 'DNS: Zone Text'), ('groups/group', 'Group: Group'), ('mail/folder', 'Mail: IMAP Folder'), ('mail/domain', 'Mail: Mail Domains'), ('mail/lists', 'Mail: Mailing Lists'), ('networks/network', 'Networks: Network'), ('policies/autostart', 'Policy: Autostart'), ('policies/clientdevices', 'Policy: Client Devices'), ('policies/dhcp_scope', 'Policy: DHCP Allow/Deny'), ('policies/dhcp_boot', 'Policy: DHCP Boot'), ('policies/dhcp_dns', 'Policy: DHCP DNS'), ('policies/dhcp_dnsupdate', 'Policy: DHCP DNS Update'), ('policies/dhcp_leasetime', 'Policy: DHCP Lease Time'), ('policies/dhcp_netbios', 'Policy: DHCP Netbios'), ('policies/dhcp_routing', 'Policy: DHCP Routing'), ('policies/dhcp_statements', 'Policy: DHCP Statements'), ('policies/desktop', 'Policy: Desktop'), ('policies/xfree', 'Policy: Display'), ('policies/ldapserver', 'Policy: LDAP Server'), ('policies/mailquota', 'Policy: Mail Quota'), ('policies/maintenance', 'Policy: Maintenance'), ('policies/managedclientpackages', 'Policy: Packages Managed Client'), ('policies/masterpackages', 'Policy: Packages Master'), ('policies/memberpackages', 'Policy: Packages Member'), ('policies/mobileclientpackages', 'Policy: Packages Mobile Client'), ('policies/slavepackages', 'Policy: Packages Slave'), ('policies/pwhistory', 'Policy: Password Policy'), ('policies/print_quota', 'Policy: Print Quota'), ('policies/printserver', 'Policy: Print Server'), ('policies/release', 'Policy: Release'), ('policies/repositoryserver', 'Policy: Repository Server'), ('policies/repositorysync', 'Policy: Repository Sync'), ('policies/sound', 'Policy: Sound'), ('policies/thinclient', 'Policy: Thin Client'), ('policies/admin_container', 'Policy: Univention Admin Container Settings'), ('policies/share_userquota', 'Policy: Userquota-Policy'), ('settings/default', 'Preferences: Default'), ('settings/directory', 'Preferences: Path'), ('settings/admin', 'Preferences: Univention Admin Global Settings'), ('settings/user', 'Preferences: Univention Admin User Settings'), ('settings/xconfig_choices', 'Preferences: X Configuration Choices'), ('shares/printer', 'Print-Share: Printer'), ('shares/printergroup', 'Print-Share: Printer Group'), ('settings/license', 'Settings: License'), ('settings/lock', 'Settings: Lock'), ('settings/packages', 'Settings: Package List'), ('settings/printermodel', 'Settings: Printer Driver List'), ('settings/printeruri', 'Settings: Printer URI List'), ('settings/prohibited_username', 'Settings: Prohibited Usernames'), ('settings/sambaconfig', 'Settings: Samba Configuration'), ('settings/sambadomain', 'Settings: Samba Domain'), ('settings/service', 'Settings: Service'), ('settings/usertemplate', 'Settings: User Template'), ('shares/share', 'Share: Directory'), ('settings/cn', 'Univention Settings'), ('users/user', 'User'), ('users/passwd', 'User: Password'), ('users/self', 'User: Self')]

	@classmethod
	def parse(self, text):
		for choice in self.choices:
			if choice[0] == text:
				return text
		raise univention.admin.uexceptions.valueInvalidSyntax, _('"%s" is not a Univention Admin Module.') % text

# Unfortunately, Python doesn't seem to support (static) class methods;
# however, (static) class variables such as "choices" seem to work;
# so, we'll modify "choices" using this global method
def univentionAdminModules_update():
	temp = []
	for name, mod in univention.admin.modules.modules.items():
		if not univention.admin.modules.virtual( mod ):
			temp.append( ( name, univention.admin.modules.short_description( mod ) ) )

	univentionAdminModules.choices = sorted( temp, key = operator.itemgetter( 1 ) )

__register_choice_update_function(univentionAdminModules_update)

class UDM_PropertySelect( complex ):
	subsyntaxes = ( ( _( 'UDM module' ), string ), ( _( 'property' ), string ) )

# old syntax required by settings/syntax. Should be removed after migrating to UDM_PropertySelect
class listAttributes(string):
	@classmethod
	def parse(self, text):
		return text

class timeSpec(select):
	"""Time format used by 'at'."""
	_times  = [(time, time) for hour in range(0, 24)
				for minute in range(0, 60, 15)
				for time in ('%02d:%02d' % (hour, minute),)]
	choices = [
		('', _('No Reboot')),
		('now', _('Immediately')),
	] + _times

class optionsUsersUser(select):
	choices = [
		('groupware', _('Groupware Account')),
		('kerberos', _('Kerberos Principal')),
		('person', _('Personal Information')),
		('samba', _('Samba Account')),
		('posix', _('POSIX Account')),
		('mail', _('Mail Account')),
	]

class CTX_BrokenTimedoutSession( select ):
	'''The keys of the choices are the hexdecimal values that represent
	the options value within the munged dial flags'''
	choices = (
		( '0000', _( 'Disconnect' ) ),
		( '0400', _( 'Reset' ) ),
		)

class CTX_ReconnectSession( select ):
	'''The keys of the choices are the hexdecimal values that represent
	the options value within the munged dial flags'''
	choices = (
		( '0000', _( 'All Clients' ) ),
		( '0200', _( 'Previously used Client' ) ),
		)

class CTX_Shadow( select ):
	'''The keys of the choices are the hexdecimal values that represent
	the options value within the munged dial flags'''
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
	choices = (
		( 'E', _( 'Disabled' ) ),
		( 'w', _( 'Enabled: Set by Caller' ) ),
		( 'k', _( 'Enabled: No Call Back' ) ),
		)
	#( ' ', _( 'Enabled: Preset To' ) ),


class nagiosHostsEnabledDn( UDM_Objects ):
	udm_modules = ( 'computers/computer', )
	udm_filter = '(&(objectClass=univentionNagiosHostClass)(univentionNagiosEnabled=1)(aRecord=*))'

class nagiosServiceDn( UDM_Objects ):
	udm_modules = ( 'nagios/service', )

class UCR_Variable( complex ):
	subsyntaxes = ( ( _( 'Variable' ), string ), ( _( 'Value' ), string ) )

class LDAP_Search( select ):
	"""Selection list from LDAP search.

	Searches can be either defined dynamically via a UDM settings/syntax
	definition and using

	>>> LDAP_Search( syntax_name = '<NAME>' )

	or programmatically	by directly instantiating

	>>> LDAP_Search( filter = '<LDAP-Search-Filter>', attribute = [ '<LDAP attributes>', ... ], value = '<LDAP attribute>', base = '<LDAP base>' )
	"""
	FILTER_PATTERN = '(&(objectClass=univentionSyntax)(cn=%s))'

	def __init__( self, syntax_name = None, filter = None, attribute = [], base = '', value = 'dn', viewonly = False, addEmptyValue = False ):
		"""Creates an syntax object providing a list of choices defined
		by a LDAP objects

		syntax_name: name of the syntax LDAP object

		filter: an LDAP filter to find the LDAP objects providing the
		list of choices. The filter may contain patterns, that are

		attribute: a list of UDM module attributes definitions like
		'shares/share: dn' to be used as human readable representation
		for each element of the choices.

		value: the UDM modul attribute that will be stored to identify
		the selected element. The value is specified like 'shares/share:
		dn'

		viewonly: If set to True the values can not be changed

		addEmptyValue: If set to True an empty value is add to the list
		of choices
	    """
		self.syntax = syntax_name
		if filter is not None:
			# programmatically
			self.syntax = None
			self.filter = filter
			self.attributes = attribute
			self.base = base
			self.value = value

		self.choices = []
		self.name = self.__class__.__name__
		self.viewonly = viewonly
		self.addEmptyValue = addEmptyValue

	@classmethod
	def parse( self, text ):
		return text

	def _load( self, lo ):
		"""Loads an LDAP_Search object from the LDAP directory. If no
		syntax name is given the object is expected to be created with
		the required settings programmatically."""

		if not self.syntax:
			# programmatically
			if self.viewonly:
				self.value = 'dn'
			return

		# get values from UDM settings/syntax
		try:
			filter = LDAP_Search.FILTER_PATTERN % self.syntax
			dn, attrs = lo.search( filter = filter )[ 0 ]
		except:
			return

		if dn:
			self.__dn = dn
			self.filter = attrs[ 'univentionSyntaxLDAPFilter' ][ 0 ]
			self.attributes = attrs[ 'univentionSyntaxLDAPAttribute' ]
			if attrs.has_key( 'univentionSyntaxLDAPBase' ):
				self.base = attrs[ 'univentionSyntaxLDAPBase' ][ 0 ]
			else:
				self.__base = ''
			if attrs.has_key( 'univentionSyntaxLDAPValue' ):
				self.value = attrs[ 'univentionSyntaxLDAPValue' ][ 0 ]
			else:
				self.value = 'dn'
			if attrs.get( 'univentionSyntaxViewOnly', [ 'FALSE' ] )[ 0 ] == 'TRUE':
				self.viewonly = True
				self.value = 'dn'
			self.addEmptyValue = ( attrs.get( 'univentionSyntaxAddEmptyValue', [ '0' ] )[ 0 ].upper() in [ 'TRUE', '1' ] )

	def _prepare( self, lo, filter = None ):
		if filter is None:
			filter = self.filter
		self.choices = []
		self.values = []
		for dn in lo.searchDn( filter = filter, base = self.base ):
			# self.attributes: pass on all display attributes so the frontend has a chance to supoport it some day
			if not self.viewonly:
				self.values.append( ( dn, self.value, self.attributes ) )
			else:
				self.values.append( ( dn, self.attributes ) )

class nfsMounts(complex):
	subsyntaxes=[(_('NFS share'), LDAP_Search( filter = 'objectClass=univentionShareNFS', attribute = [ 'shares/share: printablename' ], value = 'shares/share: dn' )), ('Mount point', string)]
	all_required=1

class languageCode(string):
	min_length=5
	max_length=5
	_re = re.compile('^[a-z][a-z]_[A-Z][A-Z]$')

	@classmethod
	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _('Language code must be in format "xx_XX"!')


class translationTuple(complex):
	delimiter = ': '
	subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Text'), string)]
	all_required = 1

class translationTupleShortDescription(translationTuple):
	subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Translated short description'), string)]

class translationTupleLongDescription(translationTuple):
	subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Translated long description'), string)]

class translationTupleTabName(translationTuple):
	subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Translated tab name'), string)]

class I18N_GroupName( translationTuple ):
	subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), ( _( 'Translated group name' ), string )]

class disabled( select ):
	choices = (
		( 'none', _( 'None' ) ),
		( 'all', _( 'All disabled' ) ),
		( 'none2', '----' ),
		( 'windows', _( 'Windows disabled' ) ),
		( 'kerberos', _( 'Kerberos disabled' ) ),
		( 'posix', _( 'POSIX disabled' ) ),
		( 'windows_posix', _( 'Windows and POSIX disabled' ) ),
		( 'windows_kerberos', _( 'Windows and Kerberos disabled' ) ),
		( 'posix_kerberos', _( 'POSIX and Kerbeors disabled' ) ),
	)

class locked( select ):
	choices = (
		( 'none', _( 'None locked login method' ) ),
		( 'all', _( 'Locked all login method' ) ),
		( 'windows', _( 'Locked Windows/Kerberos only' ) ),
		( 'posix', _( 'Locked POSIX/LDAP only' ) ),
	)

# printing stuff

class Printers( UDM_Objects ):
	udm_modules = ( 'shares/printer', )
	depends = 'spoolHost'
	simple = True
	key = '%(name)s'

	@classmethod
	def udm_filter( self, options ):
		return 'spoolHost=%s' % '|'.join( options[ Printers.depends ] )

class PrinterNames( UDM_Objects ):
	udm_modules = ( 'shares/printer', )
	depends = 'spoolHost'
	simple = True
	key = '%(name)s'
	regex = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9_-]*([a-zA-Z0-9]$)')

	@classmethod
	def udm_filter( self, options ):
		return 'spoolHost=%s' % '|'.join( options[ Printers.depends ] )

class PrintQuotaGroup( complex ):
	subsyntaxes = ( ( _( 'Soft limit' ), integer ), ( _( 'Hard limit' ), integer ), ( _( 'Group' ), GroupName ) )

class PrintQuotaGroupPerUser( complex ):
	subsyntaxes = ( ( _( 'Soft limit' ), integer ), ( _( 'Hard limit' ), integer ), ( _( 'Group' ), GroupName ) )

class PrintQuotaUser( complex ):
	subsyntaxes = ( ( _( 'Soft limit' ), integer ), ( _( 'Hard limit' ), integer ), ( _( 'User' ), UserName ) )

class printerName(simple):
	min_length=1
	max_length=16
	_re = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9_-]*([a-zA-Z0-9]$)')

	@classmethod
	def parse(self, text):
		if self._re.match(text) != None:
			return text
		else:
			raise univention.admin.uexceptions.valueError, _("Value may not contain other than numbers, letters, underscore (\"_\") and minus (\"-\")!")

class printerModel(complex):
	subsyntaxes=[(_('Driver'), string), (_('Description'), string)]
	all_required=1

class PrinterDriverList( UDM_Attribute ):
	udm_module = 'settings/printermodel'
	attribute = 'printmodel'
	is_complex = True
	key_index = 0
	label_index = 1
	udm_filter = 'dn'
	depends = 'producer'

class PrinterProducerList( UDM_Objects ):
	udm_modules = ( 'settings/printermodel', )
	label = '%(name)s'

class PrinterProtocol( UDM_Attribute ):
	udm_module = 'settings/printeruri'
	attribute = 'printeruri'
	is_complex = False

class PrinterURI( complex ):
	subsyntaxes = ( ( _( 'Protocol' ), PrinterProtocol ), ( _( 'Destination' ), string ) )


if __name__ == '__main__':
	import doctest
	doctest.testmod()
