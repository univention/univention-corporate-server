# -*- coding: utf-8 -*-
"""
|UDM| functions for creating crontab entries.
"""
# Copyright 2004-2019 Univention GmbH
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

try:
	from typing import Mapping, Sequence, Union  # noqa F401
except ImportError:
	pass


def month_map(month):
	# type: (str) -> Union[str, int, None]
	"""
	Map English month name to 1-based numeric month-in-year.

	.. seealso::
		:py:func:`month_reverse_map`

	>>> month_map('*')
	'*'
	>>> month_map('January')
	1

	"""
	month_list = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
	if month == '*':
		return '*'
	if month in month_list:
		return month_list.index(month)


def weekday_map(weekday):
	# type: (str) -> Union[str, int, None]
	"""
	Map English day-of-week name to numeric value 1-7.

	.. seealso::
		:py:func:`weekday_reverse_map`

	>>> weekday_map('*')
	'*'
	>>> weekday_map('Monday')
	1
	"""
	weekday_list = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
	if weekday == '*':
		return '*'
	if weekday in weekday_list:
		return weekday_list.index(weekday)


def month_reverse_map(month):
	# type: (Union[str, int]) -> Union[str, None]
	"""
	Map 1-based numeric month-in-year to English month name.

	.. seealso::
		:py:func:`month_map`

	>>> month_reverse_map('*')
	'*'
	>>> month_reverse_map(1)
	'January'
	"""
	month_list = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
	if month == '*':
		return '*'
	if int(month) < len(month_list):
		return month_list[int(month)]


def weekday_reverse_map(weekday):
	# type: (Union[str, int]) -> Union[str, None]
	"""
	Map numeric day-of-week value 1-7 to English name.

	.. seealso::
		:py:func:`weekday_map`

	>>> weekday_reverse_map('*')
	'*'
	>>> weekday_reverse_map(1)
	'Monday'
	"""
	weekday_list = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
	if weekday == '*':
		return '*'
	if int(weekday) < len(weekday_list):
		return weekday_list[int(weekday)]


def cron_create(cronlist):
	# type: (Mapping[str, Sequence[Union[str, int]]]) -> str
	"""
	Create a crontab time string.

	:param cronlist: A mapping of strings to lists.

	.. seealso::
		:py:func:`cron_split`

	>>> cron_create(dict(minute=[], hour=[], day=[], month=[], weekday=[]))
	'* * * * * '
	>>> cron_create(dict(minute=[0], hour=[1], day=[2], month=['March'], weekday=['Thursday']))
	'0 1 2 3 4 '
	>>> cron_create(dict(minute=['all'], hour=['all'], day=['all'], month=['all'], weekday=['all']))
	'0,5,10,15,20,25,30,35,40,45,50,55 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31 1,2,3,4,5,6,7,8,9,10,11,12 1,2,3,4,5,6,7 '
	"""
	keys = ['minute', 'hour', 'day', 'month', 'weekday']
	string = ''
	for key in keys:
		if key in cronlist:
			if len(cronlist[key]) == 0:
				string += '* '
				continue
			for i in range(len(cronlist[key])):
				if i > 0:
					string += ','
				if key == 'month':
					if cronlist[key][i] == 'all':
						string += '1,2,3,4,5,6,7,8,9,10,11,12'
					else:
						string += '%s' % month_map(cronlist[key][i])
				elif key == 'weekday':
					if cronlist[key][i] == 'all':
						string += '1,2,3,4,5,6,7'
					else:
						string += '%s' % weekday_map(cronlist[key][i])
				elif key == 'day':
					# note: removed since only values from 1-31 are allowed for days in cron
					# if cronlist[key][i] == '00':
					# 	string+='0'
					if cronlist[key][i] == 'all':
						string += '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31'
					else:
						string += '%s' % cronlist[key][i]
				elif key == 'hour':
					if cronlist[key][i] == '00':
						string += '0'
					elif cronlist[key][i] == 'all':
						string += '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23'
					else:
						string += '%s' % cronlist[key][i]
				elif key == 'minute':
					if cronlist[key][i] == '00':
						string += '0'
					elif cronlist[key][i] == 'all':
						string += '0,5,10,15,20,25,30,35,40,45,50,55'
					else:
						string += '%s' % cronlist[key][i]
		string += ' '
	return string


def cron_split(cronlist):
	"""
	Split a crontab time string into its parts.

	:param cronlist: a crontab time string 'minute hour day month weekday'.

	.. seealso::
		:py:func:`cron_create`

	>>> cron_split('* * * * * ') == {'minute': ['*'], 'hour': ['*'], 'day': ['*'], 'month': ['*'], 'weekday': ['*']}
	True
	>>> cron_split('* * * 1 *')['month']
	['January']
	>>> cron_split('* * * * 1')['weekday']
	['Monday']
	"""
	cron = cronlist.split(' ')
	res = {}
	keys = ['minute', 'hour', 'day', 'month', 'weekday']
	pos = 0
	for entry in cron:
		if not entry:
			continue
		if keys[pos] == 'month':
			res[keys[pos]] = []
			for i in entry.split(','):
				try:
					res[keys[pos]].append(month_reverse_map(i))
				except:
					res[keys[pos]].append(i)
		elif keys[pos] == 'weekday':
			res[keys[pos]] = []
			for i in entry.split(','):
				try:
					res[keys[pos]].append(weekday_reverse_map(i))
				except:
					res[keys[pos]].append(i)
		elif keys[pos] == 'day' and "55" in entry.split(','):
			res[keys[pos]] = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31']
		else:
			res[keys[pos]] = entry.split(',')

		pos += 1
	return res


if __name__ == '__main__':
	import doctest
	doctest.testmod()
