#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Python VNC automate
#
# Copyright 2016 Univention GmbH
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

import subprocess


# TODO: Use the pycountry library here. (Adds additional dependency...)
def iso_639_1_to_iso_639_2(language_code):
	if language_code == 'en':
		return 'eng'
	elif language_code == 'de':
		return 'deu'
	elif language_code == 'fr':
		return 'fra'


def iso_639_1_to_english_name(language_code):
	if language_code == 'en':
		return "English"
	elif language_code == 'de':
		return "German"
	elif language_code == 'fr':
		return "French"


def execute_through_ssh(password, command, ip):
	p = subprocess.Popen((
		'sshpass',
		'-p', password,
		'ssh',
		'-o', 'StrictHostKeyChecking=no',
		'root@%s' % (ip,),
		command
	), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	stdout, _ = p.communicate()
	if p.returncode:
		p = subprocess.Popen((
			'ps', 'aux'
		), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		stdout_ps, _ = p.communicate()
		raise Exception(p.returncode, stdout, stdout_ps)


def copy_through_ssh(password, source_file, target_file):
	subprocess.check_call((
		'sshpass',
		'-p', password,
		'scp',
		'-r',
		'-o', 'StrictHostKeyChecking=no',
		source_file, target_file
	))


def remove_old_sshkey(ip):
	subprocess.check_call((
		'ssh-keygen',
		'-R',
		ip
	))
