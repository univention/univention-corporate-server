#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  thread-safe queue for UMC requests
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

import univention.management.console.protocol as umcp
import univention.debug as ud

import copy
import threading

class RequestContainer( object ):
	def __init__( self, request, thread = None, action = None ):
		self._request = request
		self._response = None
		self._thread = thread
		self.unseen = True
		self.finished = False
		self.action = action

	def request( self ):
		return self._request

	def id( self ):
		if self._request:
			return self._request.id()
		else:
			return None

	def append( self, response ):
		if isinstance( response, bool ) or response.isFinal():
			self.finished = True

		self._response = response

	def response( self ):
		resp = self._response
		self._response = None
		return resp

	def response_available( self ):
		return self._response != None

class RequestGroup( object ):
	_group_id = 0
	def __init__( self, requests ):
		self.__requests = requests
		self.__responses = []
		self.__message = None
		self.__ids = []
		self.finished = False
		self.event = None
		self.__id_lock = threading.Lock()
		self.__id_lock.acquire()
		self.__id = 'group-%d' % RequestGroup._group_id
		RequestGroup._group_id +=1
		self.__id_lock.release()

	def id( self ):
		return self.__id

	def ids( self ):
		return self.__ids

	def requests( self ):
		return self.__requests

	def append( self, response ):
		if response.isFinal():
			self.__responses.append( response )
		else:
			self.__message = response

	def responses( self ):
		return self.__responses

	def message( self ):
		msg = self.__message
		self.__message = None
		return msg

	def message_available( self ):
		return self.__message != None

	def isMember( self, id ):
		return id in self.__ids

	def pop( self ):
		if self.__requests:
			req = self.__requests.pop( 0 )
			self.__ids.append( req.id() )
			return RequestContainer( req )
		return None

	def isComplete( self ):
		return not self.__requests

class RequestQueue( list ):
	def __init__( self ):
		list.__init__( self )
		self.__groups = []
		self._lock = threading.Lock()

	def _exists( self, id ):
		for req in self:
			if req.id() == id:
				return True
		return False

	def newRequestGroup( self, requests ):
		grp = RequestGroup( requests )
		self._lock.acquire()
		self.__groups.append( grp )
		request_container = grp.pop()
		if not self._exists( request_container.id() ):
			ud.debug( ud.ADMIN, ud.INFO, 'Queue: append new request from group(%s): %s' % ( grp.id(), request_container.id() ) )
			self.append( request_container )
		self._lock.release()

		return grp.id()

	def newRequest( self, request, thread = None ):
		ret = None
		self._lock.acquire()
		if not self._exists( request.id() ):
			self.append( RequestContainer( request, thread ) )
			ret = request.id()
		self._lock.release()

		return ret

	def newAction( self, action, thread = None ):
		self._lock.acquire()
		ud.debug( ud.ADMIN, ud.INFO, 'Queue: new action %s' % action )
		self.append( RequestContainer( None, thread, action ) )
		self._lock.release()

	def setActionResult( self, action, result ):
		ret = False
		wakeup = None
		self._lock.acquire()
		ud.debug( ud.ADMIN, ud.INFO, 'Queue: set action %s: %s' % \
				  ( action, str( result ) ) )
		for req in self:
			if req.action == action:
				ud.debug( ud.ADMIN, ud.INFO, 'Queue: append result to %s' % action )
				req.append( result )
				wakeup = req._thread
				ret = True
				break
		self._lock.release()
		if wakeup:
			wakeup.set()

		return ret

	def getActionResult( self, action ):
		ret = False
		ud.debug( ud.ADMIN, ud.INFO, 'Queue: get action %s' % action )
		self._lock.acquire()
		for req in copy.copy( self ):
			if req.action == action:
				ud.debug( ud.ADMIN, ud.INFO, 'Queue: found action %s' % action )
				ret = req.response()
				ud.debug( ud.ADMIN, ud.INFO, 'Queue: value of action %s' % ret )
				wakeup = req._thread
 				self.remove( req )
				break
		self._lock.release()
		return ret

	def setGroupEvent( self, id, event ):
		ret = False
		self._lock.acquire()
		for grp in self.__groups:
			if grp.id() == id:
				grp.event = event
				ret = True
				break
		self._lock.release()

		return ret

	def setEvent( self, id, event ):
		ret = False
		self._lock.acquire()
		for req in self:
			if req.id() == id:
				req._thread = event
				ret = True
				break
		self._lock.release()

		return ret

# 	def removeRequest( self, id ):
# 		ret = False
# 		self._lock.acquire()
# 		for req in self:
# 			if req.id() == id:
# 				self.remove( req )
# 				ret = True
# 				break
# 		self._lock.release()

# 		return ret

	def getUnseenRequest( self ):
		new = None
		self._lock.acquire()
		for req in self:
			if req.unseen:
				if req.action:
					new = copy.copy( req.action )
				else:
					new = copy.deepcopy( req.request() )
				req.unseen = False
				break
		self._lock.release()

		return new

	def appendResponse( self, response ):
		ret = False
		wakeup = None
		self._lock.acquire()
		ud.debug( ud.ADMIN, ud.INFO, 'Queue: appendResponse: %s' % \
				  str( response.id() ) )
		for req in self:
			if req.id() == response.id() and not req.finished:
				req.append( response )
				wakeup = req._thread
				ret = True
				# check for request group membership
				for grp in self.__groups:
					if grp.isMember( response.id() ):
						grp.append( response )
						if not grp.isComplete():
							self.append( grp.pop() )
						else:
							grp.finished = True
							wakeup = grp.event
				break
		self._lock.release()
		if wakeup:
			wakeup.set()
		return ret

	def isFinished( self, id ):
		ret = False
		self._lock.acquire()
		for req in self:
			if req.id() == id and req.finished:
				ret = True
				break
		self._lock.release()

		return ret

	def removeById( self, ids ):
		self._lock.acquire()
		for req in copy.copy( self ):
			if req.id() in ids:
				self.remove( req )
		self._lock.release()

	def getGroupResponse( self, id ):
		ret = None
		ids = []
		self._lock.acquire()
		for grp in copy.copy( self.__groups ):
			if grp.id() == id:
				if grp.finished:
					ret = copy.deepcopy( grp.responses() )
					ids = copy.copy( grp.ids() )
					self.__groups.remove( grp )
				elif grp.message_available():
					ret = copy.deepcopy( grp.message() )
				break
		self._lock.release()
		if ids:
			self.removeById( ids )

		return ret

	def getLastResponse( self, id ):
		ret = None
		self._lock.acquire()
		for req in copy.copy( self ):
			if req.id() == id:
				ret = copy.deepcopy( req.response() )
				if req.finished:
					self.remove( req )
				break
		self._lock.release()

		return ret

	def getResponses( self, id ):
		ret = None
		self._lock.acquire()
		for req in self:
			if req.id() == id:
				ret = copy.deepcopy( req.response() )
				break
		self._lock.release()

		return ret

	def isResponseGroupAvailable( self, id ):
		ret = False
		self._lock.acquire()
		for grp in self.__groups:
			if grp.id() == id:
				ret = grp.finished or grp.message_available()
				break
		self._lock.release()

		return ret

	def isResponseAvailable( self, id ):
		ret = False
		self._lock.acquire()
		for req in self:
			if req.id() == id:
				ret = req.response_available()
				break
		self._lock.release()

		return ret
