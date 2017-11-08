# -*- coding: utf-8 -*-
#
# Univention Configuration Registry
#  Service information: read information about registered Config Registry
#  variables
#
# Copyright 2007-2017 Univention GmbH
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

import os
import shlex
from logging import getLogger

import univention.info_tools as uit


class Service(uit.LocalizedDictionary):

	REQUIRED = frozenset(('description', 'programs'))
	OPTIONAL = frozenset(('start_type', 'systemd', 'icon'))
	KNOWN = REQUIRED | OPTIONAL

	def __init__(self, *args, **kwargs):
		uit.LocalizedDictionary.__init__(self, *args, **kwargs)
		self.running = False

	def __repr__(self):
		return '%s(%s)' % (
			self.__class__.__name__,
			dict.__repr__(self),
		)

	def check(self):
		"""Check service entry for validity, returning list of incomplete entries."""
		incomplete = [key for key in self.REQUIRED if not self.get(key, None)]
		unknown = [key for key in self.keys() if key.lower() not in self.KNOWN]
		return incomplete + unknown

	def _update_status(self):
		for prog in self['programs'].split(','):
			prog = prog.strip()
			if prog and not pidof(prog):
				self.running = False
				break
		else:
			self.running = True


def pidof(name, docker='/var/run/docker.pid'):
	"""
	Return list of process IDs matching name.
	>>> import os,sys;os.getpid() in list(pidof(os.path.realpath(sys.executable))) + list(pidof(sys.executable)) + list(pidof(sys.argv[0]))
	True
	"""
	result = set()
	log = getLogger(__name__)

	children = {}
	if isinstance(docker, basestring):
		try:
			with open(docker, 'r') as fd:
				docker = int(fd.read(), 10)
			log.info('Found docker.pid=%d', docker)
		except (EnvironmentError, ValueError) as ex:
			log.info('No docker found: %s', ex)

	cmd = shlex.split(name)
	for proc in os.listdir('/proc'):
		try:
			pid = int(proc, 10)
		except ValueError:
			continue
		cmdline = os.path.join('/proc', proc, 'cmdline')
		try:
			with open(cmdline, 'r') as fd:
				commandline = fd.read()
		except EnvironmentError:
			continue
		# kernel thread
		if not commandline:
			continue

		if docker:
			stat = os.path.join('/proc', proc, 'stat')
			try:
				with open(stat, 'r') as fd:
					status = fd.read()
				ppid = int(status.split()[3], 10)
				children.setdefault(ppid, []).append(pid)
			except (EnvironmentError, ValueError) as ex:
				log.error('Failed getting parent: %s', ex)

		args = commandline.split('\0')
		if cmd[0] not in args and not commandline.startswith(name):
			log.debug('skip %d: %s', pid, commandline)
			continue
		if len(args) >= len(cmd) > 1:
			if any(a != c for a, c in zip(args, cmd)):
				log.debug('mismatch %d: %r != %r', pid, args, cmd)
				continue
		log.info('found %d: %r', pid, commandline)
		result.add(pid)

	if docker:
		remove = children.pop(docker, [])
		while remove:
			pid = remove.pop()
			log.debug('Removing docker child %s', pid)
			result.discard(pid)
			remove += children.pop(pid, [])

	return list(result)


class ServiceInfo(object):
	BASE_DIR = '/etc/univention/service.info'
	SERVICES = 'services'
	CUSTOMIZED = '_customized'
	FILE_SUFFIX = '.cfg'

	def __init__(self, install_mode=False):
		self.services = {}
		if not install_mode:
			self.__load_services()
			self.update_services()

	def update_services(self):
		"""Update the run state of all services."""
		for serv in self.services.values():
			serv._update_status()

	def check_services(self):
		"""Return dictionary of incomplete service descriptions."""
		incomplete = {}
		for name, srv in self.services.items():
			miss = srv.check()
			if miss:
				incomplete[name] = miss
		return incomplete

	def write_customized(self):
		"""Save service cusomization."""
		filename = os.path.join(ServiceInfo.BASE_DIR, ServiceInfo.SERVICES, ServiceInfo.CUSTOMIZED)
		try:
			fd = open(filename, 'w')
		except EnvironmentError:
			return False

		cfg = uit.UnicodeConfig()
		for name, srv in self.services.items():
			cfg.add_section(name)
			for key in srv.keys():
				items = srv.normalize(key)
				for item, value in items.items():
					cfg.set(name, item, value)

		cfg.write(fd)
		fd.close()

		return True

	def read_services(self, filename=None, package=None, override=False):
		"""Read start/stop levels of services."""
		if not filename and not package:
			raise AttributeError("neither 'filename' nor 'package' is specified")
		if not filename:
			filename = os.path.join(ServiceInfo.BASE_DIR, ServiceInfo.SERVICES, package + ServiceInfo.FILE_SUFFIX)
		cfg = uit.UnicodeConfig()
		cfg.read(filename)
		for sec in cfg.sections():
			# service already known?
			if not override and sec in self.services:
				continue
			srv = Service()
			for name, value in cfg.items(sec):
				srv[name] = value
			for path in srv.get('programs', '').split(','):
				# "programs" defines the "/proc/self/cmdline" of the service,
				# not the executable, therefore we test for a leading "/":
				# check if it is a real file    split to remove parameters
				if path.startswith('/') and not os.path.exists(path.split(' ', 1)[0]):
					break  # ==> do not execute else
			else:
				self.services[sec] = srv

	def __load_services(self):
		"""Load definition of all defined services."""
		path = os.path.join(ServiceInfo.BASE_DIR, ServiceInfo.SERVICES)
		for entry in os.listdir(path):
			# customized service descrptions are read afterwards
			if entry == ServiceInfo.CUSTOMIZED:
				continue
			cfgfile = os.path.join(path, entry)
			if os.path.isfile(cfgfile) and cfgfile.endswith(ServiceInfo.FILE_SUFFIX):
				self.read_services(cfgfile)
		# read modified/added service descriptions
		self.read_customized()

	def read_customized(self):
		"""Read service cusomization."""
		custom = os.path.join(ServiceInfo.BASE_DIR, ServiceInfo.SERVICES, ServiceInfo.CUSTOMIZED)
		self.read_services(custom, override=True)

	def get_services(self):
		'''returns a list fo service names'''
		return self.services.keys()

	def get_service(self, name):
		'''returns a service object associated with the given name or
		None if it does not exist'''
		return self.services.get(name, None)

	def add_service(self, name, service):
		'''this methods adds a new service object or overrides an old
		entry'''
		if not service.check():
			self.services[name] = service


if __name__ == '__main__':
	import doctest
	doctest.testmod()
