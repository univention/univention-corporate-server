#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Setup
#  ldap rewrite script
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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

import sys, ldap, string, ldap, ldif

# Parameter 1: "old_dn"
# Parameter 2: "new_dn"
# Parameter 3: "infile"
# Parameter 4: "outfile"

if len(sys.argv) != 5:
	sys.exit(1)

old_dn=sys.argv[1]
new_dn=sys.argv[2]
infile=sys.argv[3]
outfile=sys.argv[4]

f_infile=open(infile)
ldif_input=ldif.ParseLDIF(f_infile)
f_infile.close()


base_object_dn=ldif_input[0][0]
base_object_attr=ldif_input[0][1]

new_base_type=new_dn.split('=')[0]
old_base_type=old_dn.split('=')[0]

new_base_object_domain=new_dn.split('=')[1].split(',')[0]

if old_base_type == new_base_type:
	new_base_object_attr={}
	new_base_object_dn=new_dn
	for key in base_object_attr.keys():
		new_base_object_attr[key]=[]
		if key == new_base_type:
			new_base_object_attr[key].append(new_base_object_domain)
		else:
			for member in base_object_attr[key]:
				new_base_object_attr[key].append(member.replace(old_dn,new_dn))
else:
	attribute_append=[]
	if old_base_type == 'dc':
		objectClass_remove='domain'
		attribute_remove=['dc', 'structuralObjectClass']
	elif old_base_type == 'o':
		objectClass_remove='organization'
		attribute_remove=['o', 'structuralObjectClass']
	elif old_base_type == 'ou':
		objectClass_remove='organizationalRole'
		attribute_remove=['ou', 'structuralObjectClass']
	elif old_base_type == 'l':
		objectClass_remove='organization'
		attribute_remove=['l', 'o', 'structuralObjectClass']
	elif old_base_type == 'cn':
		objectClass_remove='organizationUnit'
		attribute_remove=['cn', 'structuralObjectClass']
	elif old_base_type == 'c':
		objectClass_remove='country'
		attribute_remove=['c', 'structuralObjectClass']

	if new_base_type == 'dc':
		objectClass_append='domain'
		attribute_append=['dc']
	elif new_base_type == 'o':
		objectClass_append='organization'
		attribute_append=['o']
	elif new_base_type == 'ou':
		objectClass_append='organizationalRole'
		attribute_append=['ou']
	elif new_base_type == 'l':
		objectClass_append='organization'
		attribute_append=['l', 'o']
	elif new_base_type == 'cn':
		objectClass_append='organizationUnit'
		attribute_append=['cn']
	elif new_base_type == 'c':
		objectClass_append='country'
		attribute_append=['c']

	new_base_object_dn=new_dn
	new_base_object_attr={}
	for key in base_object_attr.keys():
		if not key in attribute_append:
			new_base_object_attr[key]=[]
			if key == 'objectClass':
				for member in base_object_attr[key]:
					if member != objectClass_remove:
						new_base_object_attr[key].append(member.replace(old_dn,new_dn))
				new_base_object_attr[key].append(objectClass_append)
			elif key in attribute_remove:
				continue
			else:
				for member in base_object_attr[key]:
					new_base_object_attr[key].append(member.replace(old_dn,new_dn))
		for i in attribute_append:
			new_base_object_attr[i]=[new_base_object_domain]


f=open(outfile, 'w+')
ldif_writer=ldif.LDIFWriter(f)

ldif_writer.unparse(new_base_object_dn,new_base_object_attr)

for attr in ldif_input[1:-1]:
	attr_dict={}
	for key in attr[1].keys():
		attr_dict[key]=[]
		for member in attr[1][key]:
			attr_dict[key].append(member.replace(old_dn,new_dn))
	ldif_writer.unparse(attr[0].replace(old_dn, new_dn),attr_dict)
f.close()

