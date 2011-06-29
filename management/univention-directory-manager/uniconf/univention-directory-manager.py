# -*- coding: utf-8 -*-
#
# Univention Directory Manager
#  the univention directory manager start module
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

import sys, os, getopt, string, copy, socket, select, locale, time

sys.path.append('/usr/share/univention-webui/modules/')
ldir = '/usr/share/univention-directory-manager/uniconf/'
sys.path.append(ldir)
os.chdir(ldir)

import univention.debug
import univention.config_registry

configRegistry=univention.config_registry.ConfigRegistry ()
configRegistry.load ()

LANG_DE = 'de_DE.utf8'
LANG_EN = 'C'

def daemonize():
	pid = os.fork()
	if pid > 0:
		os._exit(0)

	null = os.open('/dev/null', os.O_RDWR)
	os.dup2(null, sys.stdin.fileno())
	os.dup2(null, sys.stdout.fileno())
	os.dup2(null, sys.stderr.fileno())
	os.setsid()

def main(argv):

	socket_filename=''
	socket_timeout=60*5
	socket_timeout_short = 5
	debugging = 0
	language = configRegistry.get ('directory/manager/web/language', LANG_EN)
	https = 0 
	http_host = None

	# parse command line arguments
	opts, args = getopt.getopt(argv[1:], 's:t:d:l:e:h:')
	for opt, val in opts:
		if opt == '-s':
			if val != '-':
				socket_filename = val
			else:
				socket_filename = sys.stdin.read()
				if socket_filename[-1] == '\n':
					socket_filename = socket_filename[0:-1]
		elif opt == '-t':
			tmp = int(val)
			if tmp <= 30:
				# the minimum timeout is 30 seconds
				# set socket_timeout to default timeout
				tmp = 15*60
			socket_timeout = tmp
		elif opt == '-d':
			debugging = int(val)
		elif opt == '-l':
			language = val
		elif opt == '-e':
			https = val
		elif opt == '-h':
			http_host = val

	if debugging >0:
		univention.debug.init('/var/log/univention/directory-manager-web.log', 1, 1)
		univention.debug.set_level(univention.debug.LDAP, debugging)
		univention.debug.set_level(univention.debug.ADMIN, debugging)
	else:
		univention.debug.init('/dev/null', 0, 0)

	os.environ["HTTP_HOST"] = http_host
	os.environ["HTTPS"] = https
	os.environ["LC_MESSAGES"]=language
	try:
		locale.setlocale( locale.LC_MESSAGES, language )
	except:
		pass

	from uniparts import *
	import requests

	if not socket_filename:
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'Socket filename missing.')

	# initialize global structures
	try:
		uaccess = requests.new_uaccess()
		uaccess.requireLicense()
	except:
		uaccess=None
	session=requests.session(uaccess)

	sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	sock.bind(socket_filename)
	try:
		sock.listen(1)
		daemonize()
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'waiting for connections')

		RequestCount = -1
		while 1:
			RequestCount += 1
			if RequestCount <= 1:
				rfds, wfds, xfds = select.select([sock], [], [], socket_timeout_short)
			else:
				rfds, wfds, xfds = select.select([sock], [], [], socket_timeout)
			if not rfds and not wfds and not xfds:
				break # timeout
			elif not rfds:
				if xfds:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'New ignored event from select: exceptional conditions')
				if wfds:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'New ignored event from select: write data')
				continue
			conn, addr = sock.accept()
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'accepted new connection')

			# receive input
			input = ''
			while 1:
				buf = conn.recv(1024)
				if buf[-1] == '\0':
					buf = buf[0:-1]
					input += buf
					break
				else:
					input += buf

			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'received input')

			# split into meta text and xml text
			pos = input.find('\n\n')
			if pos >= 0:
				metatext = input[:pos]
				xmlin = input[pos+2:]
			else:
				metatext = ''
				xmlin = input

			# parse metatext
			meta = {}
			for line in metatext.split('\n'):
				pos = line.find(': ')
				if pos < 1:
					continue
				meta[line[:pos]] = line[pos+2:]

			number = int(meta.get('Number', '-1'))
			if number != -1 and meta.has_key ('Sessioninvalid'):
				del meta['Sessioninvalid']

			if debugging >= 99:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Logging XML representation of input:')
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, str(xmlin))
			xmlout = session.startRequest(xmlin, number, meta=meta)
			if debugging >= 99:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Logging XML representation of output:')
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, str(xmlout))

			# convert unicode to bytestring (UTF-8)
			data = (xmlout+'\0').encode('UTF-8')
			datalen = len(data)
			while data:
				sent = conn.send(data)
				if sent == 0:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'sent output failed: socket seems to be bad - stopping here and closing socket')
					data = None
				elif sent >= 0 and sent < datalen:
					# data has been sent only partial - retrying with remaining data
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'udm: sent chunk of %d bytes to frontend' % sent)
					data = data[sent:]
					datalen = len(data)
					time.sleep(0.005) # sleep 5ms and try again
				elif sent == datalen:
					# everythin has been sent
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'udm: sent last chunk of %d bytes to frontend' % sent)
					data = None
				# elif sent < 0 ==> try again

			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'sent output')
			conn.close()

			# Do cleanup work after the connection has been closed,
			# so that the response will not be delayed
			session.finishRequest(number)
	finally:
		os.unlink(socket_filename)

if __name__ == '__main__':
	main(sys.argv)
