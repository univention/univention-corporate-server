# -*- coding: utf-8 -*-
#
# Univention Webui
#  requests.py
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

import sys, os, re, string, copy, codecs, types, threading, cPickle
import univention.debug
import univention.admin.uldap
import unidialog
from localwebui import _
from uniparts import *
import uniwait
import waitdialog
import univention.config_registry
import v

ldir = '/usr/share/univention-admin/uniconf/'

def new_uaccess():

	host = ''
	base = ''
	port = ''
	ridbase = ''

	errors=0
	try:
		import univention_baseconfig
		ubc=univention_baseconfig.baseConfig()
		ubc.load()
		host=ubc["ldap/master"]
		base=ubc["ldap/base"]
		port=ubc["ldap/port"]
	except ImportError:
		errors=1
	except IOError:
		errors=1

	if not port:
		# should be safe to fall back to default LDAP port
		port = "389"

	return univention.admin.uldap.access(host=host, port=int(port), base=base)

class new_saver:
	def __init__(self):
		self.dict={}
	def put(self, var, content):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'saver put %s=%s' % (var, content))
		self.dict[var]=content
	def get(self, var, default=''):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'saver get %s=%s' % (var, self.dict.get(var, '')))
		if var in ["uc_submodule","uc_module","noorder"] and not self.dict.has_key(var):
			return None
		return self.dict.get(var, default)
	def clear(self):
		dontclear=["uc_module","uc_virtualmodule","uc_submodule","user","pass","ldap_position","modok","thinclients_off","thinclients_checked","auth_ok","settings"]
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'saver clear')
		for key in self.dict.keys():
			if not key in dontclear:
				del self.dict[key]

def genErrorMessage(head, messagelines, mailto = None, atts = None):
	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()
	# options for a default-layout
	myatts = {  'layout_type'     : '' ,
		    'site_title'      : _('Univention Directory Manager') ,
		    'header_img'      : 'style/header_admin.gif',
		    'main_table_type' : 'content_main',
		    'header_table_type' : 'content_header' }

	# overwrite defaults if atts is given
	if atts:
		for att in myatts.keys():
			if atts.has_key ( att ):
				myatts[ att ] = atts[ att ]

	#TODO: Use existing XML objects instead of directly printing XML
	utfxml = '<?xml version="1.0" encoding="UTF-8"?>'
	# header
	utfxml += '<dialog header_img="%s" id="main" layout_type="%s" main="">' % (myatts['header_img'], myatts['layout_type'])
	utfxml += '<title id="main_title">%s</title>' % myatts['site_title']
	utfxml += '<dialog id="main_dialog"><table class="border" id="main_dialog_table" type="%s">' % myatts['header_table_type']
	utfxml += '<row class="border" id="main_dialog_table_row"><col class="border" id="main_dialog_table_row_col"/></row></table>'
	# tabs
	utfxml += '<notebook id="main_dialog_notebook"><var internal="1"><name>selected</name><content>0</content></var><var internal="1"><name>selected</name><content>0</content></var><button><text>%s</text><helptext>%s</helptext><var><name>pressed</name><content/></var><active>1</active></button></notebook>' % (_("Error"),_("Error"))
	# content
	utfxml += '<table class="border" id="main_dialog_table1" type="%s">' % myatts['main_table_type']




	utfxml += '<row class="border" id="main_dialog_table1_row"><col class="border" id="main_dialog_table1_row_col">'
	utfxml += '<header id="main_header" type="3"><htmltext>%s</htmltext></header><header id="main_spacer" type="2"><text> </text></header>'%head
	utfxml += '</col></row>'
	utfxml += '<row class="border" id="main_dialog_table1_row"><col class="border" id="main_dialog_table1_row_col">'


	small=1
	import cgi
	for n, i in enumerate(messagelines):
		utfxml +='<header id="exception%d" type="%d"><text>%s</text></header><break />' % (n, 3+small, cgi.escape(i.replace(" ","&nbsp;")))

	utfxml += '</col></row>'
	def htmltext(text):
		result = '<row class="border" id="main_dialog_table1_row"><col class="border" id="main_dialog_table1_row_col">'
		result += '<htmltext><htmltext>%s</htmltext></htmltext>' % cgi.escape(text)
		result += '</col></row>'
		return result
	utfxml += htmltext('&nbsp;')
	if mailto:
		text = _('Report this error to %s &lt;%s&gt;' % (ucr.get('directory/manager/web/feedback/description', 'Univention Feedback'), ucr.get('directory/manager/web/feedback/mail', 'feedback@univention.de')))
		link = '<a href="%s">%s</a>' % (mailto, text)
		utfxml += htmltext(link)
		utfxml += htmltext('&nbsp;')
	utfxml += htmltext('<a href="index.php">%s</a>' % _('Login'))
	utfxml += '</table>'
	utfxml += '</col></row></table></dialog><menu id="main_menu"/></dialog>'
	return utfxml

def genErrorMailto(messagelines):
	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()
	from urllib import quote, urlencode
	from urlparse import urlunparse
	scheme = 'mailto'
	address = quote('%s <%s>' % (ucr.get('directory/manager/web/feedback/description', 'Univention Feedback'), ucr.get('directory/manager/web/feedback/mail', 'feedback@univention.de')))
	subject = _('Bugreport: Univention Directory Manager Traceback')
	body = '''%s:
1) %s
2) %s
3) %s

----------

''' % (_('Please take a second to provide the following information'),
       _('steps to reproduce the failure'),
       _('expected result'),
       _('actual result'))
	for line in messagelines:
		body += line
	body += '''
----------

'''
	body += 'Univention Directory Manager Version: %s - %s' % (v.version, v.build)
	query = { 'subject': subject,
		  'body':    body }
	url = urlunparse((scheme, '', address, '', urlencode(query), ''))
	return url.replace('+', '%20')

class request:

	def __init__(self, save, uaccess, xmlin, meta={}, session=None):
		self.meta = meta
		self.session = session
		self.save = save
		self.uaccess = uaccess
		self.xmlin = xmlin
		self.xmlout = None
		self.thread = None
		self.thread_event = None
		self.thread_exception = None
		self.dialog = None

	# This method starts the request in a new thread.
	def start(self):

		self.thread_event = threading.Event()
		self.thread = threading.Thread(target=self.run_request)
		self.thread.start()

	# This method waits until the thread has finished or the timeout elapses.
	def wait(self, timeout=3.0):

		self.thread_event.wait( timeout )
		return self.xmlout or self.thread_exception

	# If an exception has occured inside the thread, this method returns it.
	# Otherwise, it returns None.
	def exception(self):

		return self.thread_exception

	# This method returns dialog's result XML.
	def result(self):

		return self.xmlout

	# This method is called inside the thread and runs the dialog.
	# If an exception occures, it is saved in self.thread_exception.
	def run_request(self):

		try:
			if not self.xmlin:
				got_input = 0
				self.xmlin = Document()
			else:
				got_input = 1

			self.dialog = unidialog.unidialog("",{"main":""},{'req':self, "messagedir":ldir+"messages/"})
			self.dialog.save = self.save
			self.dialog.uaccess = self.uaccess
			self.dialog.init(got_input, self.xmlin, self.xmlin.documentElement)
			self.dialog.check()
			self.dialog.apply()

			# we have to reinitialize because of changes in the structure
			xmlout=Document()
			self.dialog = unidialog.unidialog("",{"main":None},{'req':self, "messagedir":ldir+"messages/"})
			self.dialog.save = self.save # write back the status of the main module
			self.dialog.uaccess = self.uaccess
			self.dialog.init(0,xmlout,xmlout.documentElement)

			self.save.put("noorder","")
			self.xmlout=self.dialog.xmlrepr(xmlout,xmlout)
		except:
			self.thread_exception = sys.exc_info()
		self.thread_event.set()

	# This method is called if the waiting dialog has previously been shown.
	# It evaluates the input from the waiting dialog, in particular, it checks
	# if the cancel button has been pressed.
	def waitingInput(self, xmlobj):

		if not xmlobj:
			return

		dialog = uniwait.create("",{"main":""},{"messagedir":ldir+"messages/"})
		dialog.save = self.save
		dialog.uaccess = self.uaccess
		if not self.dialog:
			return
		dialog.pending_dialog = self.dialog.mod
		dialog.init(1,xmlobj,xmlobj.documentElement)
		dialog.check()

		if not hasattr(dialog, 'cancel_button'):
			return
		if dialog.cancel_button.pressed():

			# The waitcancel() method shall take care of stopping
			# the thread. Unfortunately, in Python 2.3, all signals
			# are blocked within a thread. (Python 2.4 supposedly
			# will fix this.) As a workaround, we call the waitcancel
			# method which usually sets a class variable "cancel".
			# Any code that may take a while (such as removing a
			# bunch of objects) needs to check for that variable, and
			# raise SystemExit it the variable is set.
			if hasattr(self.dialog.mod, 'waitcancel'):
				self.dialog.mod.waitcancel()

			return 'cancel'

	# This methods returns the XML for the waiting dialog. It should be used
	# when the real dialog has not finished yet.
	def waitingDialog(self, xmlobj):

		if not xmlobj:
			xmlobj = Document()

		dialog = uniwait.create("",{"main":""},{"messagedir":ldir+"messages/"})
		dialog.save = self.save
		dialog.uaccess = self.uaccess
		dialog.pending_dialog = self.dialog.mod
		dialog.init(0, xmlobj, xmlobj.documentElement)
		self.save.put("noorder","")

		return dialog.xmlrepr(xmlobj,xmlobj)

	def statusDialog(self, done=0):

		xmlobj = Document()
		if done:
			atts = {'done': '1'}
		else:
			atts = {}
		dialog = waitdialog.create("",atts,{})
		dialog.save = self.save
		dialog.uaccess = self.uaccess
		dialog.pending_dialog = self.dialog.mod
		dialog.init(0, xmlobj, xmlobj.documentElement)

		return dialog.xmlrepr(xmlobj,xmlobj)

class session:

	def __init__(self, uaccess):

		self.uaccess=uaccess
		self.save=new_saver()

		# The "saver history" holds pickled copies of the saver for
		# previous session IDs. If the user uses the browser's back
		# button, we can restore the old saver
		self.saver_history={}

		# The session ID of the last request
		self.previous_number=-1

		# 'request' object for pending request
		self.background_request=None

		# If there is a backgrounded request, this variable holds the
		# last session ID before going to background. If the user
		# cancels the operation, we can return to the previous dialog.
		self.before_background_number=-1

	def loadSaver(self, number):

		if number != self.previous_number+1 and self.saver_history.has_key(number-1):
			# for some reason, handler objects can't be deepcopied
			# as a workaround, we'll try to pickle them at times it
			# shouldn't cause too much delay; strangely that works
			return cPickle.loads(self.saver_history[number-1])
		else:
			return self.save

	# This method takes exception information as return by sys.exc_info() as
	# input and returns an error message XML.
	def exceptionXML(self, info):
		import traceback
		atts = {}
		for att in [ 'layout_type' , 'site_title' , 'header_img', 'main_table_type' ]:
			if self.save.get( att , False):
				atts[ att ] = self.save.get( att , False)

		if len(info) > 0 and info[0] == univention.admin.uexceptions.ldapError:
			return genErrorMessage(_("Can not process LDAP request:"),["%s: %s"%(_('LDAP error'),info[1]),_("You need to login again.")], atts = atts)
		else:
			lines = traceback.format_exception(*info)
			return genErrorMessage(_("A Python exception has occured:"), lines, genErrorMailto(lines), atts = atts)

	# This method takes the input XML and session number as input and returns
	# the output XML.
	def startRequest(self, xmltext, number, ignore_ldap_connection = False, timeout = 2, meta={}):

		if not ignore_ldap_connection and not self.uaccess:
			return genErrorMessage(_("No connection to the LDAP server"),[_("The LDAP server could not be contacted. Please try again later.")])

		# parse XML
		xmlin=None
		xmlout=None
		dialog_type=''
		if xmltext:
			try:
				xmlin=parseString(xmltext)
				dialog_type=xmlin.documentElement.tagName
			except Exception, e:
				sys.stderr.write("\nError while parsing: "+str(e)+"\n"+xmltext[0:4])

		# Only "dialog"s have meaningful input. If this is a
		# "waitdialog" discard, discard the input.
		if dialog_type != 'dialog':
			xmlin = None

		self.save = self.loadSaver(number)
		try:

			# background request is running, let's see if it has finished yet
			if self.background_request:
				if dialog_type == 'waitdialog':
					# We are done. Exit waiting dialog.
					done = (self.background_request.result() or self.background_request.exception())

					xmlout = self.background_request.statusDialog(done)

				elif self.background_request.waitingInput(xmlin) == 'cancel':
					self.background_request = None
					self.save = self.loadSaver(self.before_background_number)

				else:
					if self.background_request.exception():
						return self.exceptionXML(self.background_request.exception())

					xmlout = self.background_request.result()
					if xmlout:
						# background process has finished, clean up
						self.background_request = None
					else:
						# background process still running
						xmlout = self.background_request.waitingDialog(xmlin)
				xmlin = None

			# no background request, start new request
			if not xmlout:
				req = request(self.save, self.uaccess, xmlin, meta=meta, session=self)
				req.start()
				if self.save.get('background_request') or not req.wait(timeout = timeout):
					self.save.put('background_request', '')
					self.background_request = req
					self.before_background_number = number
					xmlout = req.waitingDialog(None)
				else:
					if req.exception():
						return self.exceptionXML(req.exception())
					xmlout = req.result()

			self.save.put("infobox_information_text",'')

			# return XML
			if type(xmlout) == types.StringType or type(xmlout) == types.UnicodeType:
				return xmlout
			xmltext=xmlout.toxml()
			templist=xmltext.split("\n")
			templist[0]="<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
			xmltext=string.join(templist,"\n")
			return xmltext

		except univention.admin.uexceptions.ldapError, msg:
			return genErrorMessage(_("An LDAP error has occured:"),["%s: %s"%(_('ldapError'),msg),_("You need to login again.")])

		except:
			info = sys.exc_info()
			return self.exceptionXML(info)

	# This method is called when the result has been returned to the client.
	# We save the saver here.
	def finishRequest(self, number):

		# the saver history will get infinitively long; we should
		# only support a limited amount of steps
		if number >= 0:
			self.saver_history[number]=cPickle.dumps(self.save)
			self.previous_number=number
