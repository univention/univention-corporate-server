# -*- coding: utf-8 -*-
#
# Univention Directory Manager
#  the univention directory manager start module
#
# Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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

import sys, os, getopt, string, copy, socket, select, locale

sys.path.append('/usr/share/univention-webui/modules/')
ldir = '/usr/share/univention-directory-manager/uniconf/'
sys.path.append(ldir)
os.chdir(ldir)

import univention.debug

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
	debugging = 0
	language='de_DE.utf8'
	https = 0 

	# parse command line arguments
	opts, args = getopt.getopt(argv[1:], 's:t:d:l:e:')
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

	if debugging >0:
		univention.debug.init('/var/log/univention/directory-manager-web.log', 1, 1)
		univention.debug.set_level(univention.debug.LDAP, debugging)
		univention.debug.set_level(univention.debug.ADMIN, debugging)
	else:
		univention.debug.init('/dev/null', 0, 0)

	os.environ["HTTPS"] = https
	os.environ["LC_MESSAGES"]=language
	locale.setlocale( locale.LC_MESSAGES, language )

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
	session=requests.session(uaccess, name = 'Univention Directory Manager')

	sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	sock.bind(socket_filename)
	try:
		sock.listen(1)
		daemonize()
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'waiting for connections')

		while 1:
			rfds, wfds, xfds = select.select([sock], [], [], socket_timeout)
			if not rfds:
				break # timeout
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

			if debugging >= 2:
				open('/tmp/xmlin', 'w').write(xmlin)
			xmlout = session.startRequest(xmlin, number, meta=meta)
			if debugging >= 2:
				open('/tmp/xmlout', 'w').write(xmlout)

			# send output
			conn.send(xmlout+'\0')
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'sent output')
			conn.close()

			# Do cleanup work after the connection has been closed,
			# so that the response will not be delayed
			session.finishRequest(number)
	finally:
		os.unlink(socket_filename)

if __name__ == '__main__':
	main(sys.argv)
