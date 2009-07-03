#!/usr/bin/python2.4
# -*- coding: utf-8 -*-

cerg={}
id=""
import sys
langs = [sys.argv[1]]

import os
#kdebase_dir="/root/kdebase-3.5.9.dfsg.1"
kdebase_dir="/usr/share/locale"


if not os.path.exists("%s/l10n/" % kdebase_dir):
	sys.exit(0)

for item in os.listdir("%s/l10n/" % kdebase_dir):
	item = item.strip()
	if os.path.isdir("%s/l10n/%s" %(kdebase_dir,item)) and len(item) == 2:
		langs.append(item)
#TODO name[xx] could be name[xx_XX]
for lang in langs:
	id=""
	country_file="%s/l10n/%s/entry.desktop" % (kdebase_dir,lang)
	if not os.path.exists(country_file):
		sys.exit(0)
	for line in open(country_file).readlines():
		line = line.strip()
		if line.startswith("Name="):
			id = line[5:]
		elif id != "" and line.startswith("Name["):
			lid=""
			for c in line[5:]:
				if c == ']':
					break
				lid+=c
			if len(lid) > 0:
				if not id in cerg:
					cerg[id] = {}
				if not lid in cerg[id]:
					cerg[id][lid] = line[9:]
				



l = sys.argv[1]
for id in cerg:	
	if l in cerg[id] and len(cerg[id][l]) > 0:
		if id != cerg[id][l]:
			print "msgid \"%s\"" % id
			print "msgstr \"%s\"" % cerg[id][l]
