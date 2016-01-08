#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  Utility functions
#
# Copyright 2015-2016 Univention GmbH
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
#

import os
import os.path
import re
import shutil
from subprocess import Popen, PIPE
import pipes
from threading import Thread
import time
import urllib2
from hashlib import md5
import socket
import tempfile
from locale import getlocale

from univention.lib.i18n import Translation
from univention.config_registry.misc import key_shell_escape

from univention.appcenter.ucr import ucr_get, ucr_keys

# "global" translation for univention-appcenter
# also provides translation for univention-appcenter-docker etc
_ = Translation('univention-appcenter').translate


def app_is_running(app):
	from univention.appcenter.app import AppManager
	if isinstance(app, basestring):
		app = AppManager.find(app)
	if app:
		if not app.docker:
			return False
		if not app.is_installed():
			return False
		try:
			from univention.appcenter.docker import Docker
		except ImportError:
			return None
		else:
			docker = Docker(app)
			return docker.is_running()
	else:
		return None


def docker_is_running():
	return call_process(['invoke-rc.d', 'docker', 'status']).returncode == 0


def app_ports():
	ret = []
	for key in ucr_keys():
		match = re.match(r'^appcenter/apps/(.*)/ports/(\d*)', key)
		if match:
			try:
				ret.append((match.groups()[0], int(match.groups()[1]), int(ucr_get(key))))
			except ValueError:
				pass
	return sorted(ret)


class NoMorePorts(Exception):
	pass


def currently_free_port_in_range(lower_bound, upper_bound, blacklist):
	for port in range(lower_bound, upper_bound):
		if port in blacklist:
			continue
		s = socket.socket()
		try:
			s.bind(('', port))
		except:
			pass
		else:
			s.close()
			return port
	raise NoMorePorts()


def underscore(value):
	if value:
		return re.sub('([a-z])([A-Z])', r'\1_\2', value).lower()


def shell_safe(value):
	return underscore(key_shell_escape(value))


def mkdir(directory):
	if os.path.exists(directory):
		return
	parent = os.path.split(directory)[0]
	mkdir(parent)
	os.mkdir(directory)


def rmdir(directory):
	if os.path.exists(directory):
		shutil.rmtree(directory)


def call_process(args, logger=None, env=None):
	process = Popen(args, stdout=PIPE, stderr=PIPE, bufsize=1, close_fds=True, env=env)
	if logger is not None:
		logger.debug('Calling %s' % ' '.join(pipes.quote(arg) for arg in args))
		remove_ansi_escape_sequence_regex = re.compile(r'\x1B\[[0-9;]*[a-zA-Z]')

		def _handle_output(out, handler):
			for line in iter(out.readline, b''):
				if line.endswith('\n'):
					line = line[:-1]
				line = remove_ansi_escape_sequence_regex.sub(' ', line)
				handler(line)
			out.close()

		stdout_thread = Thread(target=_handle_output, args=(process.stdout, logger.info))
		stdout_thread.daemon = True
		stdout_thread.start()
		stderr_thread = Thread(target=_handle_output, args=(process.stderr, logger.warn))
		stderr_thread.daemon = True
		stderr_thread.start()

		while stdout_thread.is_alive() or stderr_thread.is_alive():
			time.sleep(0.2)
		process.wait()
	else:
		process.communicate()
	return process


def verbose_http_error(exc):
	strerror = ''
	if hasattr(exc, 'getcode'):
		code = exc.getcode()
		if code == 404:
			strerror = _('%s could not be downloaded. This seems to be a problem with the App Center server. Please try again later.') % exc.url
		elif code >= 500:
			strerror = _('This is a problem with the App Center server. Please try again later.')
	while hasattr(exc, 'reason'):
		exc = exc.reason
	if hasattr(exc, 'errno'):
		version = ucr_get('version/version')
		errno = exc.errno
		strerror += getattr(exc, 'strerror', '') or ''
		if errno == 1:  # gaierror(1, something like 'SSL Unknown protocol')
			link_to_doc = _('https://docs.software-univention.de/manual-%s.html#ip-config:Web_proxy_for_caching_and_policy_management__virus_scan') % version
			strerror += '. ' + _('This may be a problem with the proxy of your system. You may find help at %s.') % link_to_doc
		if errno == -2:  # gaierror(-2, 'Name or service not known')
			link_to_doc = _('https://docs.software-univention.de/manual-%s.html#networks:dns') % version
			strerror += '. ' + _('This is probably due to the DNS settings of your server. You may find help at %s.') % link_to_doc
	if not strerror.strip():
		strerror = str(exc)
	return strerror


def urlopen(request):
	if not urlopen._opener_installed:
		proxy_http = ucr_get('proxy/http')
		if proxy_http:
			proxy = urllib2.ProxyHandler({'http': proxy_http, 'https': proxy_http})
			opener = urllib2.build_opener(proxy)
			urllib2.install_opener(opener)
		urlopen._opener_installed = True
	return urllib2.urlopen(request, timeout=60)
urlopen._opener_installed = False


def get_md5(content):
	m = md5()
	m.update(str(content))
	return m.hexdigest()


def get_md5_from_file(filename):
	if os.path.exists(filename):
		with open(filename, 'r') as f:
			return get_md5(f.read())


def get_current_ram_available():
	''' Returns RAM currently available in MB, excluding Swap '''
	#return (psutil.avail_phymem() + psutil.phymem_buffers() + psutil.cached_phymem()) / (1024*1024) # psutil is outdated. reenable when methods are supported
	# implement here. see http://code.google.com/p/psutil/source/diff?spec=svn550&r=550&format=side&path=/trunk/psutil/_pslinux.py
	with open('/proc/meminfo', 'r') as f:
		splitlines = map(lambda line: line.split(), f.readlines())
		meminfo = dict([(line[0], int(line[1]) * 1024) for line in splitlines])  # bytes
	avail_phymem = meminfo['MemFree:']  # at least MemFree is required

	# see also http://code.google.com/p/psutil/issues/detail?id=313
	phymem_buffers = meminfo.get('Buffers:', 0)  # OpenVZ does not have Buffers, calculation still correct, see Bug #30659
	cached_phymem = meminfo.get('Cached:', 0)  # OpenVZ might not even have Cached? Dont know if calculation is still correct but it is better than raising KeyError
	return (avail_phymem + phymem_buffers + cached_phymem) / (1024 * 1024)


def flatten(list_of_lists):
	# return [item for sublist in list_of_lists for item in sublist]
	# => does not work well for strings in list
	ret = []
	for sublist in list_of_lists:
		if isinstance(sublist, (list, tuple)):
			ret.extend(flatten(sublist))
		else:
			ret.append(sublist)
	return ret


def get_locale():
	# returns currently set locale: de_AT.UTF-8 -> de
	# may return None if not set (i.e. 'C')
	locale = getlocale()[0]
	if locale:
		locale = locale.split('_', 1)[0]
	return locale


def gpg_verify(filename, detached_sig_filename=None, content=None, keyringFileName=None):

	if not keyringFileName:
		keyringFileName = '/usr/share/keyrings/univention-archive-key-ucs-4x.gpg'

	gpg_homedirname = tempfile.mkdtemp()
	try:

		cmd = ('gpg',
				'--no-options',
				'--no-default-keyring', '--keyring', keyringFileName,
				'--batch', '--quiet', '--no-tty',
				# '--logger-file', '/dev/null'
				'--with-colons', '--utf8-strings',
				'--no-auto-check-trustdb', '--no-auto-key-locate', '--no-use-agent',
				'--no-random-seed-file',
				'--trust-model', 'always',
				'--homedir', gpg_homedirname,
				'--verify',
				)

		if detached_sig_filename:
			cmd += (detached_sig_filename,)

		cmd += (filename,)

		p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
		if filename == '-':
			stdout, stderr = p.communicate(content)
		else:
			stdout, stderr = p.communicate()
	finally:
		rmdir(gpg_homedirname)
	return (p.returncode, stderr)
