# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  methods and defines for the samba munged dial attribute
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

import univention.admin
import univention.admin.localization

import univention.debug as ud

import base64

translation=univention.admin.localization.translation('univention.admin')
_=translation.translate

properties = {
	'CtxCfgPresent': univention.admin.property(
			short_description=_('CTX Present'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxCfgTSLogon': univention.admin.property(
			short_description=_('Allow Windows terminal server login'),
			long_description=(''),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
			),
	'CtxCfgClientDrivers': univention.admin.property(
			short_description=_('Connect client drives at login'),
			long_description=(''),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
			),
	'CtxCfgClientPrinters': univention.admin.property(
			short_description=_('Connect client printers at login'),
			long_description=(''),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
			),
	'CtxCfgDefaultClientPrinters': univention.admin.property(
			short_description=_('Make client default printer the default printer for Windows terminal services'),
			long_description=(''),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
			),
	'CtxCfgFlags1': univention.admin.property(
			short_description=_('CTX Flags1'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=0,
			identifies=0,
		),
	'CtxCallback': univention.admin.property(
			short_description=_('CTX Callback'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxShadow': univention.admin.property(
			short_description=_('CTX Mirroring'),
			long_description=(''),
			syntax=univention.admin.syntax.CTX_Shadow,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxBrokenSession' : univention.admin.property(
			short_description = _( 'Terminated or timed-out sessions' ),
			long_description = ( ''),
			syntax = univention.admin.syntax.CTX_BrokenTimedoutSession,
			multivalue = 0,
			options = [ 'samba' ],
			license=['UGS', 'UCS'],
			required = 0,
			dontsearch = 1,
			may_change = 1,
			identifies = 0,
		),
	'CtxReconnectSession' : univention.admin.property(
			short_description = _( 'Reconnect session' ),
			long_description = ( '' ),
			syntax = univention.admin.syntax.CTX_ReconnectSession,
			multivalue = 0,
			options = [ 'samba' ],
			license=['UGS', 'UCS'],
			required = 0,
			dontsearch = 1,
			may_change = 1,
			identifies = 0,
		),
	'CtxMaxConnectionTime': univention.admin.property(
			short_description=_('CTX maximum connection time'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxMaxDisconnectionTime': univention.admin.property(
			short_description=_('CTX maximum disconnection time'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxMaxIdleTime': univention.admin.property(
			short_description=_('CTX maximum idle time'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxKeyboardLayout': univention.admin.property(
			short_description=_('Keyboard layout'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxMinEncryptionLevel': univention.admin.property(
			short_description=_('CTX minimal encryption level'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxWorkDirectory': univention.admin.property(
			short_description=_('Working directory for startup command'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxNWLogonServer': univention.admin.property(
			short_description=_('CTX NW Logon Server'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxWFHomeDir': univention.admin.property(
			short_description=_('Home directory for Windows terminal services'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxWFHomeDirDrive': univention.admin.property(
			short_description=_('Home drive for Windows terminal services'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxWFProfilePath': univention.admin.property(
			short_description=_('Profile directory for Windows terminal services'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxStartprogramClient': univention.admin.property(
			short_description=_('Use client configuration for startup command'),
			long_description=(''),
			syntax=univention.admin.syntax.boolean,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxInitialProgram': univention.admin.property(
			short_description=_('Startup command'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxCallbackNumber': univention.admin.property(
			short_description=_('CTX Callback Number'),
			long_description=(''),
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),
	'CtxRASDialin': univention.admin.property(
			short_description=_('CTX RAS Dialin'),
			long_description=(''),
			syntax=univention.admin.syntax.CTX_RASDialin,
			multivalue=0,
			options=['samba'],
			license=['UGS', 'UCS'],
			required=0,
			dontsearch=1,
			may_change=1,
			identifies=0,
		),

}

tab = univention.admin.tab( _( 'Windows Advanced' ), _( 'Windows Terminal server settings' ), [
		[ univention.admin.field( "CtxWFHomeDir" ), univention.admin.field( "CtxWFHomeDirDrive" ) ],
		[ univention.admin.field( "filler" ), univention.admin.field( "filler" ) ],
		[ univention.admin.field( "CtxInitialProgram" ), univention.admin.field( "CtxWorkDirectory" ) ],
		[ univention.admin.field( "CtxStartprogramClient" ), univention.admin.field( "filler" ) ],
		[ univention.admin.field( "filler"), univention.admin.field( "filler" ) ],
		[ univention.admin.field( "CtxWFProfilePath"), univention.admin.field( "CtxKeyboardLayout" ) ],
		[ univention.admin.field( "filler"), univention.admin.field( "filler" ) ],
		[ univention.admin.field( "CtxCfgTSLogon"), univention.admin.field( "CtxCfgClientDrivers" ) ],
		[ univention.admin.field( "CtxCfgClientPrinters"), univention.admin.field( "CtxCfgDefaultClientPrinters" ) ],
		[ univention.admin.field( 'CtxShadow' ) ],
		[ univention.admin.field( 'CtxBrokenSession' ), univention.admin.field( 'CtxReconnectSession' ) ],
		[ univention.admin.field( 'CtxRASDialin' ) ],
	], advanced = True )

class Support( object ):
	def __init__( self ):
		self.sambaMungedHexValues = [ 'CtxMinEncryptionLevel', 'CtxWorkDirectory', 'CtxNWLogonServer',
									  'CtxWFHomeDir', 'CtxWFHomeDirDrive', 'CtxWFProfilePath',
									  'CtxInitialProgram', 'CtxCallbackNumber' ]
		self.sambaMungedValues = [ 'CtxCfgPresent', 'CtxCfgFlags1', 'CtxCallback', 'CtxShadow', 'CtxMaxConnectionTime',
								   'CtxMaxDisconnectionTime', 'CtxMaxIdleTime', 'CtxKeyboardLayout',
								   'CtxMinEncryptionLevel', 'CtxWorkDirectory', 'CtxNWLogonServer', 'CtxWFHomeDir',
								   'CtxWFHomeDirDrive', 'CtxInitialProgram', 'CtxCallbackNumber', 'CtxWFProfilePath' ]

	def sambaMungedDialMap( self ):
		changed=0
		for val in self.sambaMungedValues:
			if self.info.has_key(val) and self.hasChanged(val):
				changed=1
				break

		for val in [ 'CtxStartprogramClient', 'CtxCfgTSLogon', 'CtxCfgClientDrivers', 'CtxCfgClientPrinters', 'CtxCfgDefaultClientPrinters', 'CtxReconnectSession', 'CtxBrokenSession', 'CtxRASDialin' ]:
			if self.info.has_key(val) and self.hasChanged(val):
				changed=1
				break

		if changed == 1:
			enc={}
			for val in self.sambaMungedHexValues:
				if self[val]:
					enc[val]=''
					for i in range(0,len(self[val])):
						enc[val]+=hex(ord(self[val][i])).replace('0x','')
				else:
					enc[val]=''
					#enc[val]=chr(0)
			for val in self.sambaMungedValues:
				if not val in self.sambaMungedHexValues:
					enc[val]=self[val]

			#sambaMungedDial=base64.decodestring('bQAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABkAAkCAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAUAAQAA==')
			if self.info.has_key('CtxRASDialin'):
				dialin_val=self['CtxRASDialin']
			else:
				dialin_val='e'
			#sambaMungedDial=base64.decodestring('bQAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABkAA%sAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAAAIAAgACAAIAAgACAAIAAgACAAUAAQ==' % dialin_val)
			sambaMungedDial=base64.decodestring( 'bQAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABkAA%sAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAUAAFAA==' % dialin_val )
			sambaMungedDial=sambaMungedDial.strip('\n')

			# FIXME: value_len can be replaced by len( enc[ k ] )
			for k in self.sambaMungedValues:
				name=''
				for i in range(0,len(k)):
					name+=k[i]
					name+=chr(0)
				name_len=len(name)
				if k == 'CtxCfgPresent':
					#35 35 31 65 30 62 62 30
					value_len=8
					enc[k]="551e0bb0"
				elif k == 'CtxCfgFlags1':
					#30 30 65 30 30 30 31 30
					# FIXME: this should be done by bitwise OR and finally "%08X" % value
					enc[k]="00000000"
					if self.info.has_key('CtxCfgTSLogon') and self['CtxCfgTSLogon'] == '1':
						enc[k]="%s0%s" % (enc[k][0:5],enc[k][6:])
					else:
						enc[k]="%s1%s" % (enc[k][0:5],enc[k][6:])
					val=0
					if self.info.has_key('CtxCfgClientDrivers') and self['CtxCfgClientDrivers'] == '1':
						val = val | 8
					if self.info.has_key('CtxCfgClientPrinters') and self['CtxCfgClientPrinters'] == '1':
						val = val | 4
					if self.info.has_key('CtxCfgDefaultClientPrinters') and self['CtxCfgDefaultClientPrinters'] == '1':
						val = val | 2
					enc[k]="%s%s%s" % (enc[k][0:2],str(hex(val)[2]),enc[k][3:])

					value = 0x00000000
					for opt in ( 'CtxReconnectSession', 'CtxBrokenSession' ):
						if self.has_key( opt ) and self[ opt ]:
							value |= int( self[ opt ], 16 )

					enc[ k ] = "%08X" % ( int( enc[ k ], 16 ) | value )

					if self.info.has_key('CtxStartprogramClient') and self['CtxStartprogramClient'] == '1':
						enc[k]="%s1%s" % (enc[k][0:6],enc[k][7:])
					value_len=8
				elif enc[k]:
					# find not required '0' values
					zero = ''
					for i in range( len( enc[ k ] ) ):
						zero += '0'
					if zero == enc[ k ]:
						continue
					value_len=len(enc[k])
				else:
					continue
				final=chr(name_len)
				final+=chr(0)
				final+=chr(value_len)
				final+=chr(0)
				final+=chr(1)
				final+=chr(0)
				final+=name
				if enc[k]:
					final+=enc[k]
				else:
					final+=chr(0)

				sambaMungedDial+=final

			sambaMungedDialResult=base64.encodestring(sambaMungedDial)

			return sambaMungedDialResult.replace('\n', '').replace('\r','')

	def sambaMungedDialUnmap(self):
		for i in self.sambaMungedValues:
			self.info[i]=''
		sambaMungedDial=self.oldattr.get('sambaMungedDial', [''])[0]
		if sambaMungedDial:
			munged=base64.decodestring(sambaMungedDial)
			munged_len=len(munged)
			i=0
			while i<munged_len-10:
				if munged[i+6] == 'C' and munged[i+8] == 't' and munged[i+10] == 'x':
					name_len=ord(munged[i])
					nname=''
					for j in range(i+6,i+6+name_len):
						if munged[j] != '\x00':
							nname+=munged[j]
					value_len=ord(munged[i+2])
					value=''
					for j in range(i+6+name_len,i+6+name_len+value_len):
						value+=munged[j]

					value_dec=''
					if nname in self.sambaMungedHexValues:
						j=0
						for k in range(0,len(value)-1):
							if k % 2 != 0:
								continue
							if value[k] == '0' and value[k+1] == '0':
								continue

							value_dec+=chr(int('%c%c' % (value[k],value[k+1]), 16))
					else:
						value_dec=value

					self.info[nname]=str(value_dec)

					i=i+6+name_len+value_len
				else:
					i=i+1

			munged_len=len(sambaMungedDial)
			i=0
			dialin_val='E'
			while i<munged_len-10:
				if sambaMungedDial[i:i+8] == 'AAIABkAA' or sambaMungedDial[i:i+8] == 'AAIABkAH':
					dialin_val = sambaMungedDial[i+8]
					i=i+1
				else:
					i=i+1
			self.info['CtxRASDialin'] = dialin_val

	def sambaMungedDialParse( self ):
		if self.info.has_key('CtxCfgFlags1') and len(self.info['CtxCfgFlags1']) > 7 and self.info['CtxCfgFlags1'][6] != '0':
			self.info['CtxStartprogramClient']='1'
		else:
			self.info['CtxStartprogramClient']='0'
		if self.info.has_key('CtxCfgFlags1') and len(self.info['CtxCfgFlags1']) > 6 and self.info['CtxCfgFlags1'][5] == '1':
			self.info['CtxCfgTSLogon']='0'
		else:
			self.info['CtxCfgTSLogon']='1'

		def hex_value(val):
			val=val.lower()
			if val == 'a': return 10
			elif val == 'b': return 11
			elif val == 'c': return 12
			elif val == 'd': return 13
			elif val == 'e': return 14
			elif val == 'f': return 15
			else: return int(val)

		self.info['CtxCfgClientDrivers']='0'
		self.info['CtxCfgClientPrinters']='0'
		self.info['CtxCfgDefaultClientPrinters']='0'
		if self.info.has_key('CtxCfgFlags1'):
			if len(self.info['CtxCfgFlags1']) > 3:
				value=hex_value(self.info['CtxCfgFlags1'][2])
				if (value & 8 ):
					self.info['CtxCfgClientDrivers'] = '1'
				if (value & 4 ):
					self.info['CtxCfgClientPrinters'] = '1'
				if (value & 2 ):
					self.info['CtxCfgDefaultClientPrinters'] = '1'
			try:
				value = int( self.info[ 'CtxCfgFlags1' ], 16 )
				# CTX reconnect session
				if value & 0x0200:
					self[ 'CtxReconnectSession' ] = '0200'
				# CTX broken or timed out session
				if value & 0x0400:
					self[ 'CtxBrokenSession' ] = '0400'
			except ValueError:
				self[ 'CtxBrokenSession' ] = '0000'
				self[ 'CtxReconnectSession' ] = '0000'

		if self.info['CtxKeyboardLayout'] == '00000000':
			self.info['CtxKeyboardLayout']=None

		if not self[ 'CtxShadow' ]:
			self[ 'CtxShadow' ] = '00000000'
