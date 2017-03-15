# -*- coding: utf-8 -*-
#
"""config registry module for autostart handling."""
#
# Copyright 2017 Univention GmbH
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

from subprocess import Popen, PIPE
from univention.service_info import ServiceInfo
from logging import getLogger


NO, MANUALLY, YES = range(3)


def check(string):
	"""
	Translate UCRV */autostart string into enumeration.
	"""
	string = string.lower() if isinstance(string, basestring) else ''
	if string in ('false', 'no'):
		return NO
	elif string in ('manually',):
		return MANUALLY
	else:
		return YES


def ctl(cmd, service):
	log = getLogger(__name__).getChild('cmd')

	cmd = ('systemctl', cmd, service)
	log.debug('Calling %r...', cmd)
	proc = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
	out, err = proc.communicate()
	rv = proc.wait()
	if rv:
		log.error('Failed %d (%s)[%s]', rv, out, err)


def handler(configRegistry, changes):
	log = getLogger(__name__)

	log.debug('Loading service informations...')
	si = ServiceInfo()
	for name in si.get_services():
		service = si.get_service(name)
		if not service:
			log.debug('Service not found: %s', name)
			continue

		try:
			var = service['start_type']
			unit = service.get('systemd', '%s.service' % (name,))
		except KeyError:
			log.debug('Incomplete service information: %s', service)
			continue

		try:
			old, new = changes[var]
			old = check(old)
			new = check(new)
		except KeyError:
			log.debug('Not changed: %s', name)
			continue

		if old == new:
			log.debug('No change: %s: %s', name, old)
			continue

		if new == NO:
			log.info('Disabling %s...', unit)
			ctl('disable', unit)
			ctl('mask', unit)
		elif new == MANUALLY:
			log.info('Manual %s...', unit)
			ctl('unmask', unit)
			ctl('disable', unit)
		elif new == YES:
			log.info('Enabling %s...', unit)
			ctl('unmask', unit)
			ctl('enable', unit)
		else:
			log.error('Unknown mode %s for %s', new, unit)


# vim:set sw=4 ts=4 noet:
