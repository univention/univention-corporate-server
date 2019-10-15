#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: modify quota settings
#
# Copyright 2006-2019 Univention GmbH
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

from __future__ import absolute_import

import subprocess
import os
import re
import math

import notifier.popen
import univention.management.console as umc
from univention.management.console.log import MODULE
from univention.management.console.config import ucr
from univention.config_registry import handler_set

from . import mtab
from univention.lib import fstab

_ = umc.Translation('univention-management-console-module-quota').translate


class UserQuota(dict):

	def __init__(self, partition, user, bused, bsoft, bhard, btime, fused, fsoft, fhard, ftime):
		self['id'] = '%s@%s' % (user, partition)
		self['partitionDevice'] = partition
		self['user'] = user
		self['sizeLimitUsed'] = block2byte(bused, 'MB')
		self['sizeLimitSoft'] = block2byte(bsoft, 'MB')
		self['sizeLimitHard'] = block2byte(bhard, 'MB')

		self['fileLimitUsed'] = fused
		self['fileLimitSoft'] = fsoft
		self['fileLimitHard'] = fhard

		self.set_time('sizeLimitTime', btime)
		self.set_time('fileLimitTime', ftime)

	def set_time(self, time, value):
		if not value:
			self[time] = '-'
		elif value == 'none':
			self[time] = _('Expired')
		elif value.endswith('days'):
			self[time] = _('%s Days') % value[:-4]
		elif ':' in value:
			self[time] = value


def repquota(partition, callback, user=None):
	args = ''

	# find filesystem type
	fs = fstab.File()
	part = fs.find(spec=partition)
	if part.type == 'xfs':
		args += '--format xfs '

	# grep a single user
	if user:
		args += "| /bin/grep '^%s '" % user
	# -C == do not try to resolve all users at once
	# -v == verbose
	cmd = '/usr/sbin/repquota -C -v %s %s' % (partition, args)
	proc = notifier.popen.Shell(cmd, stdout=True)
	proc.signal_connect('finished', callback)
	proc.start()


def repquota_parse(partition, output):
	result = []
	if not output:
		return result

	regex = re.compile('(?P<user>[^ ]*) *[-+]+ *(?P<bused>[0-9]*) *(?P<bsoft>[0-9]*) *(?P<bhard>[0-9]*) *((?P<btime>([0-9]*days|none|[0-9]{2}:[0-9]{2})))? *(?P<fused>[0-9]*) *(?P<fsoft>[0-9]*) *(?P<fhard>[0-9]*) *((?P<ftime>([0-9]*days|none|[0-9]{2}:[0-9]{2})))?')
	for line in output:
		matches = regex.match(line)
		if not matches:
			break
		grp = matches.groupdict()
		if not grp['user'] or grp['user'] == 'root':
			continue
		quota = UserQuota(partition, grp['user'], grp['bused'], grp['bsoft'], grp['bhard'], grp['btime'], grp['fused'], grp['fsoft'], grp['fhard'], grp['ftime'])
		result.append(quota)
	return result


def setquota(partition, user, bsoft, bhard, fsoft, fhard):
	cmd = ('/usr/sbin/setquota', '-u', user, str(bsoft), str(bhard), str(fsoft), str(fhard), partition)
	return subprocess.call(cmd)


class QuotaActivationError(Exception):
	pass


def usrquota_is_active(fstab_entry, mt=None):
	if not mt:
		try:
			mt = mtab.File()
		except IOError as error:
			raise QuotaActivationError(_('Could not open %s') % error.filename)

	mtab_entry = mt.get(fstab_entry.spec)
	if not mtab_entry:
		raise QuotaActivationError(_('Device is not mounted'))

	# First remount the partition with option "usrquota" if it isn't already
	if 'usrquota' in mtab_entry.options:
		return True
	else:
		return False


def quota_is_enabled(fstab_entry):
	local_env = os.environ.copy()
	local_env["LC_MESSAGES"] = "C"
	cmd = ("/sbin/quotaon", "-p", "-u", fstab_entry.mount_point)
	p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=local_env)
	stdout, stderr = p1.communicate()
	if "not found or has no quota enabled" in stdout:
		return False
	else:
		# match lines like "quota on / (/dev/disk/by-uuid/5bf2a723-b25a) is on"
		pattern = re.compile("user quota on %s \([^)]*\) is (on|off)" % fstab_entry.mount_point)
		match = pattern.match(stdout)
		if match:
			if match.group(1) == "on":
				return True
			else:
				return False
		else:
			return None  # tertium datur


def activate_quota(partition, activate, callback):
	if not isinstance(partition, list):
		partitions = [partition]
	else:
		partitions = partition
	func = notifier.Callback(_do_activate_quota, partitions, activate)
	thread = notifier.threads.Simple('quota', func, callback)
	thread.run()


def _do_activate_quota(partitions, activate):
	result = []
	try:
		fs = fstab.File()
	except IOError as error:
		result.append({'partitionDevice': None, 'success': False, 'message': _('Could not open %s') % error.filename})

	for device in partitions:
		fstab_entry = fs.find(spec=device)
		if not fstab_entry:
			result.append({'partitionDevice': device, 'success': False, 'message': _('Device could not be found')})
			continue

		try:
			status = _do_activate_quota_partition(fs, fstab_entry, activate)
		except QuotaActivationError as exc:
			result.append({'partitionDevice': fstab_entry.spec, 'success': False, 'message': str(exc)})
			continue

		if fstab_entry.mount_point == '/' and fstab_entry.type == 'xfs':
			try:
				enable_quota_in_kernel(activate)
			except QuotaActivationError as exc:
				result.append({'partitionDevice': fstab_entry.spec, 'success': False, 'message': str(exc)})
				continue
		result.append(status)
	return result


def _do_activate_quota_partition(fs, fstab_entry, activate):
	quota_enabled = quota_is_enabled(fstab_entry)
	if not (activate ^ quota_enabled):
		return {'partitionDevice': fstab_entry.spec, 'success': True, 'message': _('Quota already en/disabled')}

	# persistently change the option in /etc/fstab:
	if activate:
		if 'usrquota' not in fstab_entry.options:
			fstab_entry.options.append('usrquota')
	else:
		if 'usrquota' in fstab_entry.options:
			fstab_entry.options.remove('usrquota')
	fs.save()

	if fstab_entry.type == 'xfs':
		activation_function = _activate_quota_xfs
	elif fstab_entry.type in ('ext2', 'ext3', 'ext4'):
		activation_function = _activate_quota_ext
	else:
		return {'partitionDevice': fstab_entry.spec, 'success': True, 'message': _('Unknown filesystem')}

	try:
		activation_function(fstab_entry, activate)
	except QuotaActivationError as exc:
		return {'partitionDevice': fstab_entry.spec, 'success': False, 'message': str(exc)}

	return {'partitionDevice': fstab_entry.spec, 'success': True, 'message': _('Operation was successful')}


def _activate_quota_xfs(fstab_entry, activate=True):
	if fstab_entry.mount_point != '/':
		if subprocess.call(('/bin/umount', fstab_entry.spec)):
			raise QuotaActivationError(_('Unmounting the partition has failed'))

		if subprocess.call(('/bin/mount', fstab_entry.spec)):
			raise QuotaActivationError(_('Mounting the partition has failed'))

	if subprocess.call(('/usr/sbin/invoke-rc.d', 'quota', 'restart')):
		raise QuotaActivationError(_('Restarting the quota services has failed'))


def enable_quota_in_kernel(activate):
	ucr.load()
	grub_append = ucr.get('grub/append', '')
	flags = []
	option = 'usrquota'
	match = re.match(r'rootflags=([^\s]*)', grub_append)
	if match:
		flags = match.group(1).split(',')
	if activate and option not in flags:
		flags.append(option)
	elif not activate and option in flags:
		flags.remove(option)

	flags = ','.join(flags)
	if flags:
		flags = 'rootflags=%s' % (flags,)

	new_grub_append = grub_append
	if 'rootflags=' not in grub_append:
		if flags:
			new_grub_append = '%s %s' % (grub_append, flags)
	else:
		new_grub_append = re.sub(r'rootflags=[^\s]*', flags, grub_append)

	if new_grub_append != grub_append:
		MODULE.info('Replacing grub/append from %s to %s' % (grub_append, new_grub_append))
		handler_set(['grub/append=%s' % (new_grub_append,)])
		status = _('enable') if activate else _('disable')
		raise QuotaActivationError(_('To %s quota support for the root filesystem the system has to be rebooted.') % (status,))


def _activate_quota_ext(fstab_entry, activate=True):
	if activate:
		# First remount the partition with option "usrquota" if it isn't already
		if not usrquota_is_active(fstab_entry):
			# Since the usrquota option is set in fstab remount will pick it up automatically
			if subprocess.call(('/bin/mount', '-o', 'remount', fstab_entry.spec)):
				raise QuotaActivationError(_('Remounting the partition has failed'))

		# Then make sure that quotacheck can run on the partition by running quotaoff on this partition.
		if subprocess.call(('/sbin/quotaoff', '-u', fstab_entry.spec)):  # exit status should always be zero, even if off already
			raise QuotaActivationError(_('Restarting the quota services has failed'))

		# Run quotacheck to create the aquota.user quota file on the partition
		# Note: This part is the one that makes activation take some time.
		args = ['/sbin/quotacheck']
		if fstab_entry.mount_point == '/':
			args.append('-m')
		args.extend(['-uc', fstab_entry.mount_point])
		if subprocess.call(args):
			raise QuotaActivationError(_('Generating the quota information file failed'))

		# Finally turn on the quota for the partition.
		if subprocess.call(('/sbin/quotaon', '-u', fstab_entry.spec)):  # exit status should be zero
			raise QuotaActivationError(_('Restarting the quota services has failed'))
	else:
		# First turn the userquota off as requested, otherwise "mount -o remount,noquota" fails.
		if subprocess.call(('/sbin/quotaoff', '-u', fstab_entry.spec)):  # exit status should always be zero, even if off already
			raise QuotaActivationError(_('Restarting the quota services has failed'))

		# Then we could turn of the usrquota option on the partition.
		# Note: This is not strictly required technically, we might as well leave it on (until the machine is rebootet).
		# The important point is that the usrquota option has been removed from fstab, that's what /etc/init.d/quota checks.
		#
		# Note2: If the usrquota option is set in mtab but removed in fstab, then remount doesn't automatically pick it up.
		#
		# if subprocess.call(('/bin/mount', '-o', 'remount,noquota', fstab_entry.spec)):
		# 	raise QuotaActivationError(_('Remounting the partition has failed'))


_units = ('B', 'KB', 'MB', 'GB', 'TB')
_size_regex = re.compile('(?P<size>[0-9.]+)(?P<unit>(B|KB|MB|GB|TB))?')


def block2byte(size, convertTo, block_size=1024):
	size = long(size) * float(block_size)
	unit = 0
	if convertTo in _units:
		while _units[unit] != convertTo:
			size /= 1024.0
			unit += 1
	return size


def byte2block(size, unit='MB', block_size=1024):
	factor = 0
	if unit in _units:
		while _units[factor] != unit:
			factor += 1
		size = float(size) * math.pow(1024, factor)
		return long(size / float(block_size))
	else:
		return ''
