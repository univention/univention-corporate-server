#!/usr/bin/python2.7
#
# Univention Log Collector Client
#   send log files to central loghost
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

# python packages
import socket, fcntl, os, sys, random, errno, stat, struct, json, time
import cPickle

# external packages
from optparse import OptionParser
import univention.config_registry as ub
import inspect
import notifier
from OpenSSL import SSL
from cStringIO import StringIO

MAX_JSON_ID = 999999
MIN_JSON_ID = 1
MAX_LENGTH_RESEND_QUEUE = 20

LOGERROR = 0
LOGWARN = 1
LOGINFO = 2
LOGDEBUG = 4

loglevel = 0
logobj = None

baseconfig = ub.ConfigRegistry()
baseconfig.load()


def debug( level, msg ):
	global logobj, loglevel
	if level <= loglevel:
		if not logobj:
			logobj = open('/var/log/univention/log-collector-client.log','a')

		info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
		printInfo=[]
		if len(info[0])>30:
			printInfo.append('...'+info[0][-27:])
		else:
			printInfo.append(info[0])
		printInfo.extend(info[1:3])
		logobj.write( "%s [L%s]: %s\n" % (time.asctime( time.localtime()), printInfo[1], msg) )
		logobj.flush()


def save_unpickle(data):
	fd = StringIO(data)
	unpickler = cPickle.Unpickler(fd);
	unpickler.find_global = None

	try:
		return unpickler.load()
	except cPickle.UnpicklingError:
		return {}


class LogCollectorClient( object ):
	def __init__( self, server, port = 7450 ):
		'''Initialize a socket-connection to the server.'''
		self._port = port
		self._server = server
		self._nextId = random.randint( 100000, 999999)
		self._resendQueue = {}
		self._inbuffer = ''
		self._config = {}
		self._socket_ready = False
		self._outbuffer = ''

		self._read_config()

		self._crypto_context = SSL.Context(SSL.SSLv23_METHOD)
#		self._crypto_context.set_info_callback(self._info_callback)
		self._crypto_context.set_cipher_list('DEFAULT')
		self._crypto_context.set_verify( SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT, self._verify_cert_cb )
#		dir = '/etc/univention/ssl/%s' % umc.baseconfig[ 'hostname' ]
#		self._crypto_context.use_privatekey_file( os.path.join( dir, 'private.key' ) )
#		self._crypto_context.use_certificate_file( os.path.join( dir, 'cert.pem' ) )
		self._crypto_context.load_verify_locations( os.path.join( dir, '/etc/univention/ssl/ucsCA', 'CAcert.pem' ) )

		self._init_socket()
		self.connect()

	def _verify_cert_cb( self, conn, cert, errnum, depth, ok ):
		debug( LOGDEBUG, 'Got certificate subject: %s' % cert.get_subject() )
		debug( LOGDEBUG, 'Got certificate issuer: %s' % cert.get_issuer() )
		debug( LOGDEBUG, 'errnum=%d  depth=%d  ok=%d' % (errnum, depth, ok) )
		if depth == 0 and ok == 0:
			debug( LOGERROR, 'got invalid certificate from server - dying')
			sys.exit(1)
		return ok

	def _info_callback( self, conn, fkt, status ):
		debug( LOGDEBUG, 'fkt=%s  status=%s' % (fkt, status) )

	def _init_socket( self ):
		self._realsocket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
		self._realsocket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
		fcntl.fcntl(self._realsocket.fileno(), fcntl.F_SETFD, 1)
		self._socket = SSL.Connection( self._crypto_context, self._realsocket )

	def reconnect( self ):
		debug( LOGDEBUG, 'RECONNECT')
		self.connect()
		return False

	def connect( self ):
		if not self._realsocket or not self._socket:
			self._init_socket()
		try:
			self._socket.connect( ( self._server, self._port ) )
			self._socket.setblocking( 0 )
			notifier.socket_add( self._socket, self._receive_data )
			debug( LOGERROR, 'SSL connection established' )

			self._send_setup()
		except:
			debug( LOGERROR, 'SSL connection failed' )
			self._socket = None
			notifier.timer_add( 5000, notifier.Callback( self.reconnect ) )
			return False

		return True

	def _send_setup( self ):
		filelist = []
		for fobj,fdict in self._config.items():
			filelist.append( ( fdict['filename'], fdict['serverdir'] ) )

		packet = { 'id': 0,
				   'action': 'SETUP',
				   'data': filelist,
				   'rotate': (fdict['pos'] == -1) }     # rotate on startup, not on reconnect
		debug( LOGDEBUG, 'Sending SETUP')
		self._send_serialized( packet, resendQueue = False )

	def _receive_data( self, sock ):
		debug( LOGDEBUG, 'GOT NEW DATA' )

		try:
			recv = sock.recv( 16384 )
		except SSL.SysCallError:
			# lost connection or any other unfixable error
			recv = None
		except SSL.Error:
			error = sock.getsockopt( socket.SOL_SOCKET, socket.SO_ERROR )
			if error == errno.EPIPE:
				# lost connection: server died probably
				debug( LOGDEBUG, 'EPIPE' )
				recv = None
			else:
				return True

		if not recv:
			sock.close()
			notifier.socket_remove( sock )
			notifier.socket_remove( sock, condition = notifier.IO_WRITE )
			self._socket = None
			notifier.timer_add( 1000, notifier.Callback( self.reconnect ) )
			return False

		self._inbuffer += recv

		debug( LOGDEBUG, 'BUFFER: len=%d    got %d bytes' % (len(self._inbuffer), len(recv)))

		# repeat while enough data is present
		while len(self._inbuffer) > 4:
			# get length of pickle object
			plen = struct.unpack('!I', self._inbuffer[0:4])[0]
			if plen+4 <= len(self._inbuffer):
				# unpickle data
				data = self._inbuffer[4:4+plen]
				try:
					packet = json.loads(data)
				except ValueError:
					# try old format
					packet = save_unpickle(data)
				# remove data from buffer
				self._inbuffer = self._inbuffer[4+plen:]

				# handle packet
				if type(packet) == type({}):
					if packet.has_key('action'):
						if packet['action'] == 'SETUP':
							self._handle_packet_setup( packet )
						elif packet['action'] == 'ACK':
							self._handle_packet_ack( packet )
			else:
				# not enough data
				break

		return True

	def _handle_packet_setup( self, packet ):
		debug( LOGDEBUG, 'Got SETUP' )
		if packet['data'] == 'OK':
			self._socket_ready = True
			if len(self._resendQueue):
				self._resend_unacked_packets()
		else:
			debug( LOGERROR, 'ERROR: got negative SETUP msg' )

	def _handle_packet_ack( self, packet ):
		debug( LOGDEBUG, 'Got ACK')
		for ackid in packet['data']:
			if self._resendQueue.has_key(ackid):
				del self._resendQueue[ackid]

# config files in /etc/logcollector.d/
# config file format:
# LOGFILE [TAB] SUBDIR
	def _read_config(self):
		# iterate over config dir
		configdir = '/etc/logcollector.d/'
		if os.path.exists(configdir):
			fnlist = os.listdir(configdir)
			for f in fnlist:
				fn = os.path.join(configdir, f)
				mode = os.stat(fn)[stat.ST_MODE]
				# fetch all files
				if not stat.S_ISDIR(mode):
					# read file
					fd = open(fn, 'r')
					content = fd.read()
					fd.close()
					# iterate over lines
					for line in content.splitlines():
						items = line.split('\t')
						if len(items) < 2:
							items.append('')

						# if file exists open file
						if items[0] and os.path.exists(items[0]):
							try:
								fd = open( items[0], 'rb' )
								self._config[ fd ] = { 'filename': items[0], 'serverdir': items[1], 'pos': -1 }
							except:
								debug( LOGERROR, 'ERROR: cannot open %s - ignoring file' % items[0])
		if len(self._config) == 0:
			debug( LOGERROR, 'ERROR: there is no file to read - please update config')
			sys.exit(1)
		else:
			notifier.timer_add( 50, notifier.Callback( self._check_new_data ) )

	def _check_new_data( self ):
		if self._socket and self._socket_ready:
			for fobj in self._config.keys():
				pos = fobj.tell()
				fobj.seek(0,2)  # seek to end of file
				length_fd = fobj.tell()
				self._config[fobj]['pos'] = length_fd
				fobj.seek(pos)  # seek back to current position
				length_fn = os.stat( self._config[fobj]['filename'] )[6]

				if pos < length_fd:
					# still missing data to read
					self._new_data_in_file( fobj )
				if ( length_fn < length_fd and pos == length_fd ) or ( length_fd < pos ):
					# file has been read completely and file seems to be rotated or truncated

					newfd = open( self._config[fobj]['filename'], 'rb' )
					self._config[newfd] = self._config[fobj]
					del self._config[fobj]
					fobj.close()
					debug( LOGERROR, 'file seems to be rotated - using new one')

		return True

	def _new_data_in_file( self, sock ):
		if len(self._resendQueue) < MAX_LENGTH_RESEND_QUEUE:
			# read data from file
			data = sock.read(65535)
			if data:
				debug( LOGDEBUG, 'new data in file: %s' % self._config[ sock ][ 'filename' ])
				self._config[ sock ][ 'pos' ] = sock.tell()

				# create packet
				packet = { 'id': 0,
						   'action': 'DATA',
						   'filename': self._config[ sock ][ 'filename' ],
						   'data': data }

				self._send_serialized( packet )

		return True

	def _send_outbuffer( self, foo = None ):
		if len(self._outbuffer):
			try:
				length = self._socket.send( self._outbuffer )
				self._outbuffer = self._outbuffer[length:]
			except ( SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError ):
				pass
			except:
				debug( LOGWARN, 'ERROR: sending send_queue failed')
		if len(self._outbuffer):
			return True
		return False

	def _add_to_outbuffer( self, data ):
		self._outbuffer += data
		if self._socket:
			notifier.socket_add( self._socket, self._send_outbuffer, condition = notifier.IO_WRITE )

	def _resend_unacked_packets( self ):
		for packetid, buf in self._resendQueue.items():
			self._add_to_outbuffer( buf )

	def _send_serialized( self, data, resendQueue = True ):
		if resendQueue:
			# set valid id
			data['id'] = self._nextId

		# create network data
		buf = cPickle.dumps(data,-1)  # FIXME: s/cPickle/json/
		buflen = struct.pack('!I', len(buf))
		buf = buflen + buf

		if resendQueue:
			# put data into resend queue
			self._resendQueue[ self._nextId ] = buf

			# bump id
			self._nextId += 1
			if self._nextId > MAX_JSON_ID:
				self._nextId = MIN_JSON_ID

		self._add_to_outbuffer( buf )


if __name__ == '__main__':

	if baseconfig.has_key('logcollector/debug/level'):
		loglevel = baseconfig['logcollector/debug/level']

	loghost = ''
	if baseconfig.has_key('logcollector/loghost'):
		loghost = baseconfig['logcollector/loghost']
	elif baseconfig.has_key('ldap/master'):
		loghost = baseconfig['ldap/master']

	parser = OptionParser()
	parser.add_option( '-d', '--debug', action = 'store', type = 'int',
					   dest = 'debug', default = 0,
					   help = 'if given then debugging is activated and set to the specified level' )
	parser.add_option( '-l', '--loghost', action = 'store', type = 'string',
					   dest = 'host', default = '',
					   help = 'if given then the specified loghost is used' )

	( options, args ) = parser.parse_args()
	if options.host:
		loghost = options.host
	if options.debug > 0:
		loglevel = options.debug

	debug(LOGERROR, 'using %s as loghost' % loghost )

	notifier.init()

	logserver = LogCollectorClient( loghost )
	notifier.loop()
