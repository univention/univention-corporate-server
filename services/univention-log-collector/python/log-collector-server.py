#!/usr/bin/python2.7
#
# Univention Log Collector Server
#   collects log file from other hosts
#
# Copyright 2007-2014 Univention GmbH
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

import socket
import signal
import fcntl
import os
import struct
import json
import sys
import grp

from optparse import OptionParser
from univention.config_registry import ConfigRegistry
import notifier
from OpenSSL import SSL

from univention.debug import MAIN, init, set_level, debug, reopen, FLUSH, NO_FUNCTION, ERROR, WARN, PROCESS, INFO

MAX_JSON_ID = 999999
MIN_JSON_ID = 1

ucr = ConfigRegistry()
ucr.load()


def log(level, msg):
	try:
		debug(MAIN, level, msg)
	except TypeError:
		# null byte
		debug(MAIN, level, repr(msg))


class HackingAttempt(Exception):
	pass


class LogCollectorServer(object):

	def __init__(self, port=7450):
		self._port = port
		self._connectionstates = {}
		self._ack_queue = []

		self._targetdir = ucr.get('logcollector/targetdir', '/root/log/')

		self._logrot_keepcnt = 99
		try:
			self._logrot_keepcnt = int(ucr.get('logcollector/logrotation/keepcount', 99))
		except ValueError:
			log(ERROR, 'WARNING: ucr variable "logcollector/logrotation/keepcount" contains invalid value')
			sys.exit(1)

		self._logrot_maxsize = ucr.get('logcollector/logrotation/maxsize', '')
		if not self._logrot_maxsize:
			self._logrot_maxsize = '10M'
			log(ERROR, 'WARNING: ucr variable "logcollector/logrotation/maxsize" is not set')
			log(ERROR, 'WARNING: using "logcollector/logrotation/maxsize=%s" as default' % self._logrot_maxsize)

		multi = ''
		if self._logrot_maxsize[-1].upper() in 'KMG':
			multi = self._logrot_maxsize[-1].upper()
			self._logrot_maxsize = self._logrot_maxsize[:-1]

		try:
			val = int(self._logrot_maxsize)
		except ValueError:
			val = 10
			multi = 'M'
		if multi == 'K':
			val *= 1024
		elif multi == 'M':
			val *= 1024 * 1024
		elif multi == 'G':
			val *= 1024 * 1024 * 1024
		self._logrot_maxsize = val

		self._realsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._realsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._realsocket.setblocking(0)
		fcntl.fcntl(self._realsocket.fileno(), fcntl.F_SETFD, 1)

		self.crypto_context = SSL.Context(SSL.SSLv23_METHOD)
		self.crypto_context.set_cipher_list('DEFAULT')
		self.crypto_context.set_options(SSL.OP_NO_SSLv2)
		self.crypto_context.set_verify(SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT, self._verify_cert_cb)
		dir = '/etc/univention/ssl/%s' % ucr['hostname']
		self.crypto_context.use_privatekey_file(os.path.join(dir, 'private.key'))
		self.crypto_context.use_certificate_file(os.path.join(dir, 'cert.pem'))
		self.crypto_context.load_verify_locations(os.path.join(dir, '/etc/univention/ssl/ucsCA', 'CAcert.pem'))

		self.connection = SSL.Connection(self.crypto_context, self._realsocket)
		self.connection.setblocking(0)
		self.connection.bind(('', self._port))
		log(INFO, 'Server listening to SSL connects')
		self.connection.listen(20)

		notifier.socket_add(self.connection, self._incoming_connection)

	def _verify_cert_cb(self, conn, cert, errnum, depth, ok):
		log(INFO, 'Got certificate: %s' % cert.get_subject())
		log(INFO, 'Got certificate issuer: %s' % cert.get_issuer())
		log(INFO, 'errnum=%d  depth=%d  ok=%d' % (errnum, depth, ok))
		return ok

	def _incoming_connection(self, socket):
		socket, addr = socket.accept()
		socket.setblocking(0)
		if addr:
			client = '%s:%d' % (addr[0], addr[1])
		else:
			client = ''

		log(ERROR, 'incoming connection: %s' % client)

		# create new state
		state = {
			'clientaddr': client,
			'nextId': 1,
			'inbuffer': '',
			'outbuffer': '',
			'targetdir': '',
			'filelist': {}
		}
		self._connectionstates[socket] = state
		notifier.socket_add(socket, self._receive_data)

		return True

	def _receive_data(self, sock):
		log(INFO, 'GOT NEW DATA')

		if sock not in self._connectionstates:
			log(ERROR, 'unknown socket')
			return True

		state = self._connectionstates[sock]
		data = ''

		try:
			data = sock.recv(16384)
		except SSL.WantReadError:
			# this error can be ignored (SSL need to do something)
			log(INFO, 'SSL.WantReadError')
			return True
		except (SSL.SysCallError, SSL.Error) as error:
			log(PROCESS, 'SSL error: %s. Probably the socket was closed by the client.' % (error,))

		if not data:
			notifier.socket_remove(sock)
			del self._connectionstates[sock]
			sock.close()
			return False

		state['inbuffer'] += data

		log(INFO, 'BUFFER: len=%d got %d bytes' % (len(state['inbuffer']), len(data)))

		# repeat while enough data is present
		while len(state['inbuffer']) > 4:
			# get length of pickle object
			plen = struct.unpack('!I', state['inbuffer'][0:4])[0]
			if plen + 4 <= len(state['inbuffer']):
				# unpickle data
				packet = json.loads(state['inbuffer'][4:4 + plen])
				# remove data from buffer
				state['inbuffer'] = state['inbuffer'][4 + plen:]

				# handle packet
				if isinstance(packet, dict):
					action = {
						'SETUP': self._handle_packet_setup,
						'DATA': self._handle_packet_data
					}.get(packet.get('action'))
					if action:
						action(sock, state, packet)
			else:
				# not enough data
				break

		# send ACKs
		if self._ack_queue:
			packet = {'id': 0, 'action': 'ACK', 'data': self._ack_queue}
			self._send_serialized(sock, packet)
			self._ack_queue = []

		return True

	def _handle_packet_data(self, sock, state, packet):
		log(INFO, 'PACKET_DATA: id=%s' % packet['id'])
		log(INFO, 'PACKET_DATA: fn=%s' % packet['filename'])
		log(INFO, 'PACKET_DATA: len=%s' % len(packet['data']))
		state = self._connectionstates[sock]
		basename = os.path.basename(packet['filename'])
		fn = self._secure_path_join(state['targetdir'], state['filelist'][packet['filename']], basename)
		logfd = open(fn, 'ab')
		logfd.write(packet['data'])
		logfd.seek(0, 2)  # seek to end of file
		length = logfd.tell()
		logfd.close()
		log(INFO, 'LENGTH=%d   MAXSIZE=%d' % (length, self._logrot_maxsize))
		if length > self._logrot_maxsize:
			self._rotate_file(fn)

		self._ack_queue.append(packet['id'])

	def _handle_packet_setup(self, sock, state, packet):
		log(INFO, 'Got SETUP')
		addr = state['clientaddr']
		addr = addr[: addr.rfind(':')]
		targetdir = self._secure_path_join(self._targetdir, addr)
		if not os.path.exists(targetdir):
			os.makedirs(targetdir, 0o700)
			log(WARN, 'INFO: created %s' % targetdir)

		log(ERROR, 'Client %s:' % addr)

		state['targetdir'] = targetdir
		try:
			for fn, fdir in packet['data']:
				absfdir = self._secure_path_join(targetdir, fdir)
				state['filelist'][fn] = fdir
				if not os.path.exists(absfdir):
					os.makedirs(absfdir, 0o700)
					log(PROCESS, 'INFO: created %s' % absfdir)

				basename = os.path.basename(fn)
				logfn = self._secure_path_join(absfdir, basename)
				if os.path.exists(logfn) and packet['rotate']:
					self._rotate_file(logfn)
				log(ERROR, '  added %s' % logfn)
		except HackingAttempt as exc:
			response = {'id': 0, 'action': 'SETUP', 'data': 'FAIL'}
			log(ERROR, 'Hacking attempt: %s' % (exc,))
		else:
			response = {'id': 0, 'action': 'SETUP', 'data': 'OK'}
			log(INFO, 'Sending SETUP:OK')
		self._send_serialized(sock, response)

	def _rotate_file(self, fn):
		if os.path.exists('%s.%d.gz' % (fn, self._logrot_keepcnt)):
			log(INFO, ' REMOVE %s.%d.gz' % (fn, self._logrot_keepcnt))
			os.remove('%s.%d.gz' % (fn, self._logrot_keepcnt))
		for i in range(self._logrot_keepcnt - 1, -1, -1):
			if os.path.exists('%s.%d.gz' % (fn, i)):
				log(INFO, ' RENAME %s.%d.gz ==> %s.%d.gz' % (fn, i, fn, i + 1))
				os.rename('%s.%d.gz' % (fn, i), '%s.%d.gz' % (fn, i + 1))
		if os.path.exists(fn) and self._logrot_keepcnt > 0:
			log(INFO, ' RENAME %s ==> %s.%d' % (fn, fn, 1))
			os.rename(fn, '%s.1' % fn)
			os.system('gzip %s.1' % fn)

	def _send_outbuffer(self, sock):
		state = self._connectionstates[sock]
		if len(state['outbuffer']):
			try:
				length = sock.send(state['outbuffer'])
				log(INFO, 'SEND SEND: %s <> %s' % (length, len(state['outbuffer'])))
				state['outbuffer'] = state['outbuffer'][length:]
			except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
				pass
			except:
				log(WARN, 'ERROR: sending send_queue failed')
		if len(state['outbuffer']):
			return True
		return False

	def _add_to_outbuffer(self, sock, data):
		self._connectionstates[sock]['outbuffer'] += data
		notifier.socket_add(sock, self._send_outbuffer, condition=notifier.IO_WRITE)

	def _send_serialized(self, sock, data):
		# set correct id
		state = self._connectionstates[sock]
		data['id'] = state['nextId']

		# bump id
		state['nextId'] += 1
		if state['nextId'] > MAX_JSON_ID:
			state['nextId'] = MIN_JSON_ID

		# create network data
		buf = json.dumps(data, -1)
		buflen = struct.pack('!I', len(buf))
		buf = buflen + buf

		self._add_to_outbuffer(sock, buf)

	def _secure_path_join(self, a, *p):
		path = os.path.join(a, *p)
		if not os.path.realpath(path).startswith(self._targetdir):
			raise HackingAttempt('%r not underneath of %r' % (path, self._targetdir))
		return path


def main():
	parser = OptionParser()
	parser.add_option('-d', '--debug', action='store', type='int', dest='debug', default=0, help='if given then debugging is activated and set to the specified level')

	(options, args) = parser.parse_args()
	loglevel = int(ucr.get('logcollector/debug/level', 0))
	if options.debug > 0:
		loglevel = options.debug

	filename = '/var/log/univention/log-collector-server.log'
	init(filename, FLUSH, NO_FUNCTION)
	adm = grp.getgrnam('adm')
	os.chown(filename, 0, adm.gr_gid)
	os.chmod(filename, 0o640)
	set_level(MAIN, loglevel)

	signal.signal(signal.SIGHUP, lambda signum, frame: reopen())

	notifier.init()
	LogCollectorServer()
	notifier.loop()


if __name__ == '__main__':
	try:
		main()
	except (SystemExit, KeyboardInterrupt):
		raise
	except:
		import traceback
		log(ERROR, traceback.format_exc())
		raise
