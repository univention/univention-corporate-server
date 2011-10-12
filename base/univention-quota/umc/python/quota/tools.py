#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: modify quota settings
#
# Copyright 2006-2011 Univention GmbH
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

import subprocess
import re
import math

import notifier.popen
import univention.management.console as umc
from univention.management.console.log import MODULE

from univention.lib import fstab

_ = umc.Translation('univention-management-console-modules-quota').translate

class UserQuota(dict):
	def __init__(self, partitionDevice, user, sizeLimitUsed, sizeLimitSoft,
	             sizeLimitHard, sizeLimitTime, fileLimitUsed, fileLimitSoft,
	             fileLimitHard, fileLimitTime):
		self['id'] = '{0}@{1}'.format(partitionDevice, user)
		self['partitionDevice'] = partitionDevice
		self['user'] = user
		self['sizeLimitUsed'] = sizeLimitUsed
		self['sizeLimitSoft'] = sizeLimitSoft
		self['sizeLimitHard'] = sizeLimitHard

		self['fileLimitUsed'] = fileLimitUsed
		self['fileLimitSoft'] = fileLimitSoft
		self['fileLimitHard'] = fileLimitHard

		self.set_time('sizeLimitTime', sizeLimitTime)
		self.set_time('fileLimitTime', fileLimitTime)

	def set_time(self, time, value):
		if not value:
			self[time] = '-'
		elif value == 'none':
			self[time] = _('Expired')
		elif value.endswith('days'):
			self[time] = _('%s Days') % value[:-4]
		elif ':' in value:
			self[time] = value

def repquota(partition, callback, user = None):
	args = ''

	# find filesystem type
	fs = fstab.File()
	part = fs.find(spec = partition)
	if part.type == 'xfs':
		args += '-F xfs '

	# grep a single user
	if user:
		args += "| /bin/grep '^%s '" % user
	# -C == do not try to resolve all users at once
	# -v == verbose
	cmd = '/usr/sbin/repquota -C -v %s %s' % (partition, args)
	proc = notifier.popen.Shell(cmd, stdout = True)
	proc.signal_connect('finished', callback)
	proc.start()

def repquota_parse(partition, output):
	result = []
	if not output:
		return result

	regex = re.compile('(?P<user>[^ ]*) *[-+]+ *(?P<sizeLimitUsed>[0-9]*) *(?P<sizeLimitSoft>[0-9]*) *(?P<sizeLimitHard>[0-9]*) *((?P<sizeLimitTime>([0-9]*days|none|[0-9]{2}:[0-9]{2})))? *(?P<fileLimitUsed>[0-9]*) *(?P<fileLimitSoft>[0-9]*) *(?P<fileLimitHard>[0-9]*) *((?P<fileLimitTime>([0-9]*days|none|[0-9]{2}:[0-9]{2})))?')
	for line in output:
		matches = regex.match(line)
		if not matches:
			break
		grp = matches.groupdict()
		grp['sizeLimitTime'] = str(grp['sizeLimitTime'])
		grp['fileLimitTime'] = str(grp['fileLimitTime'])
		grp['id'] = '{0}@{1}'.format(grp['user'], partition)
		#if not grp['user'] or grp['user'] == 'root':
		#	continue
		#info = UserQuota(partition, grp['user'], grp['bused'], grp['bsoft'],
		#                 grp['bhard'], grp['btime'], grp['fused'],
		#                 grp['fsoft'], grp['fhard'], grp['ftime'])
		result.append(grp)
	return result

def setquota(partition, user, bsoft, bhard, fsoft, fhard):
	cmd = ('/usr/sbin/setquota', '-u', user, str(bsoft), str(bhard),
	       str(fsoft), str(fhard), partition)
	MODULE.error(str(cmd))
	result = subprocess.call(cmd)
	return result

def activate_quota(partition, activate, callback):
	if not isinstance(partition, list):
		partitions = [partition]
	else:
		partitions = partition
	func = notifier.Callback(_do_activate_quota, partitions, activate)
	thread = notifier.threads.Simple('quota', func, callback)
	thread.run()

def _do_activate_quota(partitions, activate):
	fs = fstab.File()
	failed = {}
	for device in partitions:
		part = fs.find(spec = device)
		if not part:
			failed[device] = (False, _('Device could not be found'))
			continue
		if activate:
			if not 'usrquota' in part.options:
				part.options.append('usrquota')
				fs.save()
			else:
				# operation successful: nothing to be done
				continue
			if part.type == 'xfs':
				status, text = _activate_quota_xfs(part)
			elif part.type in ('ext2', 'ext3'):
				status, text = _activate_quota_ext(part, True)
			failed[device] = (status, text)
		else:
			if not 'usrquota' in part.options:
				continue
			else:
				part.options.remove('usrquota')
				fs.save()
			if part.type == 'xfs':
				status, text = _activate_quota_xfs(part)
			elif part.type in ('ext2', 'ext3'):
				status, text = _activate_quota_ext(part, True)
			failed[device] = (status, text)

	return failed

def _activate_quota_xfs(partition):
	if subprocess.call(('umount', partition.spec)):
		return (False, _('Unmounting the partition has failed'))
	if subprocess.call(('mount', partition.spec)):
		return (False, _('Mounting the partition has failed'))
	if subprocess.call(('invoke-rc.d', 'quota', 'restart')):
		return (False, _('Restarting the quota services has failed'))

	return (True, _('Operation was successful'))

def _activate_quota_ext(partition, create):
	if subprocess.call(('mount', '-o', 'remount', partition.spec)):
		return (False, _('Remounting the partition has failed'))
	if create:
		if subprocess.call(('/sbin/quotacheck', '-u', partition.mount_point)):
			return (False, _('Generating the quota information file failed'))
	if subprocess.call(('invoke-rc.d', 'quota', 'restart')):
		return (False, _('Restarting the quota services has failed'))

	return (True, _('Operation was successful'))

_units = ('B', 'KB', 'MB', 'GB', 'TB')
_size_regex = re.compile('(?P<size>[0-9.]+)(?P<unit>(B|KB|MB|GB|TB))?')

def block2byte(size, block_size = 1024):
	global _units
	size = long(size) * float(block_size)
	unit = 0
	while size > 1024.0 and unit < (len(_units) - 1) :
		size /= 1024.0
		unit += 1

	return '%.1f%s' % (size, _units[unit])

def byte2block(size, block_size = 1024):
	size = float(size) * math.pow(1024, 2)
	return long(size / float(block_size))
