#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention System Setup
# cleanup script called after the appliance wizard setup
#
# Copyright 2011-2014 Univention GmbH
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

import sys
import re
import subprocess
import psutil

from univention.management.console.modules.setup import util
import univention.config_registry

PATH_BROWSER_PID = '/var/cache/univention-system-setup/browser.pid'
LOG_FILE = '/var/log/univention/setup.log'
PATH_CLEANUP_PRE_SCRIPTS = '/usr/lib/univention-system-setup/cleanup-pre.d/'
PATH_CLEANUP_POST_SCRIPTS = '/usr/lib/univention-system-setup/cleanup-post.d/'
RE_IPV4_TYPE = re.compile('^interfaces/[^/]*/type$')
CMD_ENABLE_EXEC_WITH_RESTART = '/usr/share/univention-updater/enable-apache2-umc'
CMD_DISABLE_EXEC = '/usr/share/univention-updater/disable-apache2-umc'

def cleanup():
	# re-direct stdout to setup log file
	sys.stdout = open(LOG_FILE, 'a')

	# write header before executing scripts
	print '\n\n=== Cleanup (%s) ===' % util.timestamp()
	sys.stdout.flush()

	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()

	# The browser was only started, if system/setup/boot/start is true
	if ucr.is_true('system/setup/boot/start', False):
		print 'Appliance mode: try to shut down the browser'
		try:
			fpid = open(PATH_BROWSER_PID)
			strpid = fpid.readline().strip()
			pid = int(strpid)
			p = psutil.Process(pid)
			p.kill()
		except IOError:
			print 'WARN: cannot open browser PID file: %s' % PATH_BROWSER_PID
		except ValueError:
			print 'ERROR: browser PID is not a number: "%s"' % strpid
		except psutil.NoSuchProcess:
			print 'ERROR: cannot kill process with PID: %s' % pid

		# Maybe the system-setup CMD tool was started
		for p in psutil.process_iter():
			if p.name == 'python2.7' and '/usr/share/univention-system-setup/univention-system-setup' in p.cmdline:
				p.kill()

	# Run cleanup-pre scripts
	util.run_scripts_in_path(PATH_CLEANUP_PRE_SCRIPTS, sys.stdout, "cleanup-pre")

	# unset the temporary interface if set
	for var in ucr.keys():
		if RE_IPV4_TYPE.match(var) and ucr.get(var) == 'appliance-mode-temporary':
			print 'unset %s' % var
			keys = [var]
			for k in ['netmask', 'address', 'broadcast', 'network']:
				keys.append(var.replace('/type', '/%s' % k))
			univention.config_registry.handler_unset(keys)
			# Shut down temporary interface
			subprocess.call(['ifconfig', var.split('/')[1].replace('_', ':'), 'down'])

	# force a restart of UMC servers and apache
	subprocess.call(CMD_DISABLE_EXEC, stdout = sys.stdout, stderr = sys.stdout)
	subprocess.call(CMD_ENABLE_EXEC_WITH_RESTART, stdout = sys.stdout, stderr = sys.stdout)

	# Run cleanup-post scripts
	util.run_scripts_in_path(PATH_CLEANUP_POST_SCRIPTS, sys.stdout, "cleanup-post")

	print '\n=== DONE (%s) ===\n\n' % util.timestamp()
	sys.stdout.flush()
	sys.stdout.close()
	sys.exit(0)

if __name__ == "__main__":
	cleanup()

