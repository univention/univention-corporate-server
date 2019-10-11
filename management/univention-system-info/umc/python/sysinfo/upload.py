#!/usr/bin/python2.7
# Copyright (C) 2004,2005,2006,2008,2009 Fabien SEISEN
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, see
# <https://www.gnu.org/licenses/>.
#
# you can contact me at: <fabien@seisen.org>
# http://fabien.seisen.org/python/
#
# Also modified by Adam Ambrose (aambrose @T pacbell.net) to write data in
# chunks (hardcoded to CHUNK_SIZE for now), so the entire contents of the file
# don't need to be kept in memory.
#

import httplib
import mimetools
import mimetypes
import os
import os.path
import socket
import stat
import sys
import urllib
import urllib2

CHUNK_SIZE = 65536


def get_content_type(filename):
	return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

# if sock is None, return the estimate size


def send_data(v_vars, v_files, boundary, sock=None):
	length = 0
	for (k, v) in v_vars:
		buffer = ''
		buffer += '--%s\r\n' % boundary
		buffer += 'Content-Disposition: form-data; name="%s"\r\n' % k
		buffer += '\r\n'
		buffer += v + '\r\n'
		if sock:
			sock.send(buffer)
		length += len(buffer)
	for (k, v) in v_files:
		fd = v
		# Special case for StringIO
		print(type(fd))
		if not isinstance(fd, file) and fd.__module__ in ("StringIO", "cStringIO"):
			name = k
			fd.seek(0, 2)  # EOF
			file_size = fd.tell()
			fd.seek(0)  # START
		else:
			file_size = os.fstat(fd.fileno())[stat.ST_SIZE]
		name = fd.name.split('/')[-1]
		if isinstance(name, unicode):
			name = name.encode('UTF-8')
		buffer = ''
		buffer += '--%s\r\n' % boundary
		buffer += 'Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (k, name)
		buffer += 'Content-Type: %s\r\n' % get_content_type(name)
		buffer += 'Content-Length: %s\r\n' % file_size
		buffer += '\r\n'

		length += len(buffer)
		if sock:
			sock.send(buffer)
			if hasattr(fd, 'seek'):
				fd.seek(0)
		while True:
			chunk = fd.read(CHUNK_SIZE)
			if not chunk:
				break
			if sock:
				sock.send(chunk)
		length += file_size
	buffer = '\r\n'
	buffer += '--%s--\r\n' % boundary
	buffer += '\r\n'
	if sock:
		sock.send(buffer)
	length += len(buffer)
	return length

# mainly a copy of HTTPHandler from urllib2


class newHTTPHandler(urllib2.BaseHandler):

	def http_open(self, req):
		return self.do_open(httplib.HTTP, req)

	def do_open(self, http_class, req):
		data = req.get_data()
		v_files = []
		v_vars = []
		# mapping object (dict)
		if req.has_data() and not isinstance(data, str):
			if hasattr(data, 'items'):
				data = data.items()
			else:
				try:
					if len(data) and not isinstance(data[0], tuple):
						raise TypeError
				except TypeError:
					ty, va, tb = sys.exc_info()
					raise TypeError, "not a valid non-string sequence or mapping object", tb

			for (k, v) in data:
				if hasattr(v, 'read'):
					v_files.append((k, v))
				else:
					v_vars.append((k, v))
		# no file ? convert to string
		if len(v_vars) > 0 and len(v_files) == 0:
			data = urllib.urlencode(v_vars)
			v_files = []
			v_vars = []
		host = req.get_host()
		if not host:
			raise urllib2.URLError('no host given')
		h = http_class(host)  # will parse host:port
		if req.has_data():
			h.putrequest('POST', req.get_selector())
			if 'Content-type' not in req.headers:
				if len(v_files) > 0:
					boundary = mimetools.choose_boundary()
					length = send_data(v_vars, v_files, boundary)
					h.putheader('Content-Type', 'multipart/form-data; boundary=%s' % boundary)
					h.putheader('Content-length', str(length))
				else:
					h.putheader('Content-type', 'application/x-www-form-urlencoded')
					if 'Content-length' not in req.headers:
						h.putheader('Content-length', '%d' % len(data))
		else:
			h.putrequest('GET', req.get_selector())

		scheme, sel = urllib.splittype(req.get_selector())
		sel_host, sel_path = urllib.splithost(sel)
		h.putheader('Host', sel_host or host)
		for name, value in self.parent.addheaders:
			name = name.capitalize()
			if name not in req.headers:
				h.putheader(name, value)
		for k, v in req.headers.items():
			h.putheader(k, v)
		# httplib will attempt to connect() here.  be prepared
		# to convert a socket error to a URLError.
		try:
			h.endheaders()
		except socket.error as err:
			raise urllib2.URLError(err)

		if req.has_data():
			print v_files
			if len(v_files) > 0:
				length = send_data(v_vars, v_files, boundary, h)
			elif len(v_vars) > 0:
				# if data is passed as dict ...
				data = urllib.urlencode(v_vars)
				h.send(data)
			else:
				# "normal" urllib2.urlopen()
				h.send(data)

		code, msg, hdrs = h.getreply()
		fp = h.getfile()
		if code == 200:
			resp = urllib.addinfourl(fp, hdrs, req.get_full_url())
			resp.code = code
			resp.msg = msg
			return resp
		else:
			return self.parent.error('http', req, fp, code, msg, hdrs)


urllib2._old_HTTPHandler = urllib2.HTTPHandler
urllib2.HTTPHandler = newHTTPHandler


class newHTTPSHandler(newHTTPHandler):

	def https_open(self, req):
		return self.do_open(httplib.HTTPS, req)


urllib2.HTTPSHandler = newHTTPSHandler
