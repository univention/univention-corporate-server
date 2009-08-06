#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Samba 
#  this script creates samba configurations from ucr values
#
# Copyright (C) 2004-2009 Univention GmbH
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

import univention_baseconfig, re, os, pprint, sys, string

# defaults
pp             = pprint.PrettyPrinter(indent=4)
baseConfig     = univention_baseconfig.baseConfig()
shares_dir     = "/etc/samba/local.config.d"
shares_udm_dir = "/etc/samba/shares.conf.d"
postfix        = ".local.config.conf"
prefix         = "printer."
include_conf   = "/etc/samba/local.config.conf"
global_conf    = "/etc/samba/local.config.d/global.local.config.conf"

# global hashes
include = {}
shares = {}
globals = {}
printers = {}

baseConfig.load()

# delete all conf's in shares_dir and include_conf
def delete_confs(shares_dir, postfix, include_conf):

	if not os.path.isdir(shares_dir): os.makedirs(shares_dir)
	if os.path.isfile(include_conf): os.remove(include_conf)
	if os.path.isfile(global_conf): os.remove(global_conf)

	for item in os.listdir(shares_dir):
		file = os.path.join(shares_dir,item)
		if os.path.isfile(file) and file.endswith(postfix):
			os.remove(file)

# parse invalid/valid users in samba conf
def parse_users (users_line):

	users = []

	for pattern in [' @\w+', ' @"[^"]+"', '"@[^"]+"', ' \w+ ', ' \w+$']:
		reg = re.compile(pattern, re.IGNORECASE)
		users = users + reg.findall(users_line)

	users = map(lambda x: x.strip(), users)

	return users


# get invalid user from samba share conf
def get_shares():

	reg_smb = re.compile('\s*\[([^\]]+)\]')

	if not os.path.isdir(shares_udm_dir):
		return

	for file in os.listdir(shares_udm_dir):

		filename = os.path.join(shares_udm_dir, file)
		file = open(filename)
		smb_name = ""
		users = []

		for line in file.readlines():
			m_smb = reg_smb.match(line)

			if "invalid users" in line: users = parse_users(line)
			if m_smb: smb_name = m_smb.group(1)

		if smb_name:
			shares[smb_name] = {}
			shares[smb_name]['invalid users'] = {}
			for user in users:
				shares[smb_name]["invalid users"].update({user : 1})
	
# set invalid users to -> shares
def set_invalids (match, value):

        if match and match.group(1) and match.group(2) and value == "true":

		share = match.group(1)
		user = match.group(2)

		if not shares.has_key(share): shares[share] = {}
		if not shares[share].has_key("invalid users"): shares[share]["invalid users"] = {}

		shares[share]["ucr"] = 1

		if " " in user: shares[share]["invalid users"].update({"\"@" + user + "\"" : 1})
		else: shares[share]["invalid users"].update({"@" + user : 1})


# set global options to -> globals
def set_globals (match, value):
	
	if match and match.group(1) and value:
		globals[match.group(1)] = value

# set share options to -> shares
def set_options (match, value):

	if match and match.group(1) and match.group(2) and value:
		
		share = match.group(1)
		option = match.group(2)

		if not shares.has_key(share): shares[share] = {}
		if not shares[share].has_key(option): shares[share][option] = {}

		shares[share]["ucr"] = 1
		shares[share][option].update({value : 1})

# get invalid/valid users from cups and samba config
def get_printers():
	
	if os.path.isfile("/etc/cups/printers.conf"):
		etc = open("/etc/cups/printers.conf")

		reg_cups = re.compile('\s*<Printer\s+([^>]+)>')
		reg_smb = re.compile('\s*\[([^\]]+)\]')
		reg_smb_cups = re.compile('\s*printer name =(.*)')
		reg_invalid = re.compile('\s*invalid users =(.*)')
		reg_valid = re.compile('\s*valid users =(.*)')

		# cups
		for line in etc.readlines():
			m_cups = reg_cups.match(line)

			if m_cups:
				printer = m_cups.group(1).strip()
				printers[printer] = {}
			

	# samba
	for file in os.listdir('/etc/samba/printers.conf.d'):
		fd = open(os.path.join("/etc/samba/printers.conf.d", file))

		smb = ""
		printer = ""
		valid = ""
		invalid = ""

		for line in fd.readlines():
			m_smb = reg_smb.match(line)
			m_smb_cups = reg_smb_cups.match(line)
			m_valid = reg_valid.match(line)
			m_invalid = reg_invalid.match(line)

			if m_smb: smb = m_smb.group(1).strip()
			if m_smb_cups: printer = m_smb_cups.group(1).strip()
			if m_valid: valid = m_valid.group(1)
			if m_invalid: invalid = m_invalid.group(1)

		if smb and printer:
			printers[printer] = {}
			printers[printer]['smbname'] = smb

			if valid:
				users = parse_users(valid)
				printers[printer]['valid users'] = {}
				for user in users:
					printers[printer]["valid users"].update({user : 1})
			if invalid:
				users = parse_users(invalid)
				printers[printer]['invalid users'] = {}
				for user in users:
					printers[printer]["invalid users"].update({user : 1})


def set_printmode(group, mode):

	group = "@" + group
	if " " in group: group = "\"" + group + "\""

	if mode == "none":
		for key in printers.keys():
			printers[key]["ucr"] = 1
			printers[key]['invalid'] = 1
			if printers[key].has_key('invalid users'):
				printers[key]['invalid users'].update({group : 1})
			else:
				printers[key]['invalid users'] = {group : 1}
	if mode == "all":
		for key in printers.keys():
			printers[key]["ucr"] = 1
			printers[key]['valid'] = 1
			if printers[key].has_key('valid users'):
				printers[key]['valid users'].update({group : 1})
			else:
				printers[key]['valid users'] = {group : 1}

# append group to invalid users for all shares, 
# except shares group (the groupname) and marktplatz
def set_othershares(group, invalid):

	if group and invalid == "true":

		groupname = "@" + group
		if " " in groupname: groupname = "\"" + groupname + "\""

		for share in shares.keys():
			if share == group: continue
			if share == "marktplatz": continue
			if not shares[share].has_key("invalid users"): shares[share]["invalid users"] = {}
			shares[share]["invalid users"].update({groupname : 1})
			shares[share]["ucr"] = 1
			
			

# parse baseConfig 
def parse_config():

	others = {}

	for key in baseConfig.keys():

		reg_users = re.compile('samba/share/([^\/]+)/usergroup/([^\/]+)/invalid')
		reg_options = re.compile('samba/share/([^\/]+)/options/(.*)')
		reg_globals = re.compile('samba/global/options/(.*)')
		reg_printmode = re.compile('samba/printmode/usergroup/(.*)')
		reg_othershares = re.compile('samba/othershares/usergroup/([^\/]+)/invalid')

		m_users = reg_users.match(key)
		m_options = reg_options.match(key)
		m_globals = reg_globals.match(key)
		m_printmode = reg_printmode.match(key)
		m_othershares = reg_othershares.match(key)

		if m_users: set_invalids(m_users, baseConfig[key])
		elif m_options: set_options(m_options, baseConfig[key])
		elif m_globals: set_globals(m_globals, baseConfig[key])
		elif m_printmode: set_printmode(m_printmode.group(1), baseConfig[key])
		elif m_othershares: others = {m_othershares.group(1): baseConfig[key]}


	for group in others.keys():
		set_othershares(group, others[group])


# main

# delete old conf
delete_confs(shares_dir, postfix, include_conf)

# get available cups samba printers and valid/invalid users 
get_printers()

# get invalid users for shares from samba config
get_shares()

# get ucr options
parse_config()

#pp.pprint(shares)
#pp.pprint(globals)
#pp.pprint(printers)
#sys.exit(0)

# write conf file with global options
if not len(globals) == 0:
	file = open(global_conf, "w")
	file.write("[global]\n")
	for key in globals.keys(): file.write(key + " = " + globals[key] + "\n")
	file.close()
	include.update({"include = " + global_conf : 1})

# write share configs files with options and invalid users
for key in shares.keys():

	# write share conf only if we have ucr settings
	if not shares[key].has_key('ucr'): continue

	share = shares_dir + "/" + key + postfix
	file = open(share, "w")
	file.write("[" + key + "]\n")

	for option in shares[key].keys():
		if option == "ucr": continue
		file.write(option + " = ")
		for value in shares[key][option].keys(): file.write(" " + value)
		file.write("\n")
	file.close()
	include.update({"include = " + share : 1})

# write print share configs
for key in printers.keys():

	# write prin share conf only if we have a proper ucr setting
	if not printers[key].has_key('ucr'): continue 

	filename = shares_dir + "/" + prefix + key + postfix
	fd = open(filename, "w")

	if printers[key].has_key('smbname'):
		fd.write("[" + printers[key]["smbname"] + "]\n")
	else:
		fd.write("[" + key + "]\n")
		fd.write("printer name = " + key + "\n")
		fd.write("path = /tmp\n")
		fd.write("guest ok = yes\n")
		fd.write("printable = yes\n")

	if printers[key].has_key('valid'):
		if printers[key].has_key('valid users'):
			fd.write("valid users =")
			for user in printers[key]["valid users"]: fd.write(" " + user)
			fd.write("\n")

	if printers[key].has_key('invalid'):
		if printers[key].has_key('invalid users'):
			fd.write("invalid users =")
			for user in printers[key]["invalid users"]: fd.write(" " + user)
			fd.write("\n")

	file.close
	include.update({"include = " + filename : 1})		
	
# all include statements go to this file
if not len(include) == 0:
	file = open(include_conf, "w")
	for key in include.keys(): file.write(key + "\n")
	file.close()

