#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  Utility functions
#
# Copyright 2015-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.
#

import os
import os.path
import re
import shutil
from subprocess import Popen, PIPE, STDOUT, list2cmdline
import pipes
from threading import Thread
from uuid import uuid4
import time
import urllib2
import urllib
import httplib
import ipaddr
import ssl
from hashlib import md5, sha256
import socket
import tempfile
from locale import getlocale
from ConfigParser import RawConfigParser, ParsingError

from univention.lib.i18n import Translation
from univention.config_registry.misc import key_shell_escape
from univention.config_registry import interfaces
from univention.appcenter.log import get_base_logger
from univention.appcenter.ucr import ucr_get, ucr_keys

# "global" translation for univention-appcenter
# also provides translation for univention-appcenter-docker etc
_ = Translation('univention-appcenter').translate


utils_logger = get_base_logger().getChild('utils')


def read_ini_file(filename, parser_class=RawConfigParser):
	parser = parser_class()
	try:
		with open(filename, 'rb') as f:
			parser.readfp(f)
	except TypeError:
		pass
	except EnvironmentError:
		pass
	except ParsingError as exc:
		utils_logger.warn('Could not parse %s' % filename)
		utils_logger.warn(str(exc))
	else:
		return parser
	# in case of error return empty parser
	return parser_class()


def docker_bridge_network_conflict():
	docker0_net = ipaddr.IPv4Network(ucr_get('docker/daemon/default/opts/bip', '172.17.42.1/16'))
	for name, iface in interfaces.Interfaces().ipv4_interfaces:
		if 'network' in iface and 'netmask' in iface:
			my_net = ipaddr.IPv4Network('%s/%s' % (iface['network'], iface['netmask']))
			if my_net.overlaps(docker0_net):
				return True
	return False


def app_is_running(app):
	from univention.appcenter.app_cache import Apps
	if isinstance(app, basestring):
		app = Apps().find(app)
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
	'''Returns a list for ports of an App:
	[(app_id, container_port, host_port), ...]'''
	ret = []
	for key in ucr_keys():
		match = re.match(r'^appcenter/apps/(.*)/ports/(\d*)', key)
		if match:
			try:
				ret.append((match.groups()[0], int(match.groups()[1]), int(ucr_get(key))))
			except ValueError:
				pass
	return sorted(ret)


def app_ports_with_protocol():
	'''Returns a list for ports of an App:
	[(app_id, container_port, host_port, protocol), ...]'''
	ret = []
	for app_id, container_port, host_port in app_ports():
		protocol = ucr_get('appcenter/apps/%s/ports/%s/protocol' % (app_id, container_port), 'tcp')
		for proto in protocol.split(', '):
			ret.append((app_id, container_port, host_port, proto))
	return ret


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


def generate_password():
	return get_sha256(str(uuid4()) + str(time.time()))


def underscore(value):
	if value:
		return re.sub('([a-z])([A-Z])', r'\1_\2', value).lower()


def capfirst(value):
	if value:
		return value[0].upper() + value[1:]


def camelcase(value):
	if value:
		return ''.join(capfirst(part) for part in value.split('_'))


def shell_safe(value):
	return underscore(key_shell_escape(value))


def mkdir(directory):
	if os.path.exists(directory):
		return
	parent, child = os.path.split(directory)
	mkdir(parent)
	if child:
		os.mkdir(directory)


def rmdir(directory):
	if os.path.exists(directory):
		shutil.rmtree(directory)


def call_process2(cmd, logger=None, env=None, cwd=None):
	if logger is None:
		logger = utils_logger
	# make sure we log strings only
	str_cmd = [str(x) for x in cmd]
	if cwd:
		logger.debug('Running in %s:' % cwd)
	logger.info('Running command: {0}'.format(' '.join(str_cmd)))
	out = str()
	ret = 0
	try:
		p = Popen(cmd, stdout=PIPE, stderr=STDOUT, bufsize=1, close_fds=True, env=env, cwd=cwd)
		while p.poll() is None:
			stdout = p.stdout.readline()
			if stdout:
				out += stdout
				if logger:
					logger.info(stdout.strip())
		ret = p.returncode
	except Exception as err:
		out = str(err)
		ret = 1
	if ret:
		logger.error('Command {} failed with: {} ({})'.format(' '.join(str_cmd), out.strip(), ret))
	return ret, out


def call_process(args, logger=None, env=None, cwd=None):
	process = Popen(args, stdout=PIPE, stderr=PIPE, bufsize=1, close_fds=True, env=env, cwd=cwd)
	if logger is not None:
		if cwd:
			logger.debug('Calling in %s:' % cwd)
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


def call_process_as(user, args, logger=None, env=None):
	args = list2cmdline(args)
	args = ['/bin/su', '-', user, '-c', args]
	return call_process(args, logger, env)


def verbose_http_error(exc):
	strerror = ''
	if hasattr(exc, 'getcode'):
		code = exc.getcode()
		if code == 404:
			strerror = _('%s could not be downloaded. This seems to be a problem with the App Center server. Please try again later.') % exc.url
		elif code >= 500:
			strerror = _('This is a problem with the App Center server. Please try again later.')
	if hasattr(exc, 'reason'):
		if isinstance(exc.reason, ssl.SSLError):
			strerror = _('There is a problem with the certificate of the App Center server %s.') % get_server()
			strerror += ' (' + str(exc.reason) + ')'
	while hasattr(exc, 'reason'):
		exc = exc.reason
	if hasattr(exc, 'errno'):
		version = ucr_get('version/version')
		errno = exc.errno
		strerror += getattr(exc, 'strerror', '') or ''
		if errno == 1:  # gaierror(1, something like 'SSL Unknown protocol')  SSLError(1, '_ssl.c:504: error:14090086:SSL routines:ssl3_get_server_certificate:certificate verify failed')
			link_to_doc = _('https://docs.software-univention.de/manual-%s.html#ip-config:Web_proxy_for_caching_and_policy_management__virus_scan') % version
			strerror += '. ' + _('This may be a problem with the firewall or proxy of your system. You may find help at %s.') % link_to_doc
		if errno == -2:  # gaierror(-2, 'Name or service not known')
			link_to_doc = _('https://docs.software-univention.de/manual-%s.html#networks:dns') % version
			strerror += '. ' + _('This is probably due to the DNS settings of your server. You may find help at %s.') % link_to_doc
	if not strerror.strip():
		strerror = str(exc)
	if isinstance(exc, ssl.CertificateError):
		strerror = _('There is a problem with the certificate of the App Center server %s.') % get_server() + ' (' + strerror + ')'
	if isinstance(exc, httplib.BadStatusLine):
		strerror = _('There was a problem with the HTTP response of the server (BadStatusLine). Please try again later.')
	return strerror


class HTTPSConnection(httplib.HTTPSConnection):

	def connect(self):
		sock = socket.create_connection((self.host, self.port), self.timeout, self.source_address)
		if self._tunnel_host:
			self.sock = sock
			self._tunnel()
		self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, cert_reqs=ssl.CERT_REQUIRED,
			ca_certs="/etc/ssl/certs/ca-certificates.crt")


class HTTPSHandler(urllib2.HTTPSHandler):

	def https_open(self, req):
		return self.do_open(HTTPSConnection, req)


def urlopen(request):
	if not urlopen._opener_installed:
		handler = []
		proxy_http = ucr_get('proxy/http')
		if proxy_http:
			handler.append(urllib2.ProxyHandler({'http': proxy_http, 'https': proxy_http}))
		handler.append(HTTPSHandler())
		opener = urllib2.build_opener(*handler)
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


def get_sha256(content):
	m = sha256()
	m.update(str(content))
	return m.hexdigest()


def get_sha256_from_file(filename):
	if os.path.exists(filename):
		with open(filename, 'r') as f:
			return get_sha256(f.read())


def get_current_ram_available():
	''' Returns RAM currently available in MB, excluding Swap '''
	# return (psutil.avail_phymem() + psutil.phymem_buffers() + psutil.cached_phymem()) / (1024*1024) # psutil is outdated. re-enable when methods are supported
	# implement here. see http://code.google.com/p/psutil/source/diff?spec=svn550&r=550&format=side&path=/trunk/psutil/_pslinux.py
	with open('/proc/meminfo', 'r') as f:
		splitlines = map(lambda line: line.split(), f.readlines())
		meminfo = dict([(line[0], int(line[1]) * 1024) for line in splitlines])  # bytes
	avail_phymem = meminfo['MemFree:']  # at least MemFree is required

	# see also http://code.google.com/p/psutil/issues/detail?id=313
	phymem_buffers = meminfo.get('Buffers:', 0)  # OpenVZ does not have Buffers, calculation still correct, see Bug #30659
	cached_phymem = meminfo.get('Cached:', 0)  # OpenVZ might not even have Cached? Don't know if calculation is still correct but it is better than raising KeyError
	return (avail_phymem + phymem_buffers + cached_phymem) / (1024 * 1024)


def get_free_disk_space():
	''' Returns disk space currently free in MB'''
	docker_path = '/var/lib/docker'
	try:
		fd = os.open(docker_path, os.O_RDONLY)
		stats = os.fstatvfs(fd)
		bytes_free = stats.f_bsize * stats.f_bfree  # block size * number of free blocks
		mb_free = bytes_free * 1e-6
		return mb_free
	except Exception as exc:
		utils_logger.warn('Free disk space could not be determined.')
	finally:
		try:
			os.close(fd)
		except (NameError, OSError):
			# file has not been opened
			pass
	return


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


def unique(sequence):
	# uniquifies any list; preserves ordering
	seen = set()
	return [val for val in sequence if val not in seen and not seen.add(val)]


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

		cmd = (
			'gpg',
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


def get_local_fqdn():
	return '%s.%s' % (ucr_get('hostname'), ucr_get('domainname'))


def get_server():
	from univention.appcenter.app_cache import default_server
	return default_server()


def container_mode():
	''' returns True if this system is an container '''
	return bool(ucr_get('docker/container/uuid'))


def send_information(action, app=None, status=200, value=None):
	app_id = app and app.id
	utils_logger.debug('send_information: action=%s app=%s value=%s status=%s' % (action, app_id, value, status))

	server = get_server()
	url = '%s/postinst' % server

	uuid = '00000000-0000-0000-0000-000000000000'
	system_uuid = '00000000-0000-0000-0000-000000000000'
	if not app or app.notify_vendor:
		uuid = ucr_get('uuid/license', uuid)
		system_uuid = ucr_get('uuid/system', system_uuid)
	if action == 'search':
		uuid = '00000000-0000-0000-0000-000000000000'
		system_uuid = None

	values = {
		'action': action,
		'status': status,
		'uuid': uuid,
		'role': ucr_get('server/role'),
	}
	if app:
		values['app'] = app.id
		values['version'] = app.version
	if value:
		values['value'] = value
	if system_uuid:
		values['system-uuid'] = system_uuid
	utils_logger.debug('tracking information: %s' % str(values))
	try:
		request_data = urllib.urlencode(values)
		request = urllib2.Request(url, request_data)
		urlopen(request)
	except Exception as exc:
		utils_logger.info('Error sending app infos to the App Center server: %s' % exc)


def find_hosts_for_master_packages():
	from univention.appcenter.udm import get_machine_connection, search_objects
	lo, pos = get_machine_connection()
	hosts = []
	for host in search_objects('computers/domaincontroller_master', lo, pos):
		hosts.append((host.info.get('fqdn'), True))
	for host in search_objects('computers/domaincontroller_backup', lo, pos):
		hosts.append((host.info.get('fqdn'), False))
	try:
		local_fqdn = '%s.%s' % (ucr_get('hostname'), ucr_get('domainname'))
		local_is_master = ucr_get('server/role') == 'domaincontroller_master'
		hosts.remove((local_fqdn, local_is_master))
	except ValueError:
		# not in list
		pass
	return hosts
