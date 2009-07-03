#!/usr/bin/python2.4
# -*- coding: utf-8 -*-


erg={}
id=""
import sys
l = sys.argv[1]
langs = [l]
language_file="/usr/share/locale/all_languages"
for lang in langs:
	for line in open(language_file).readlines():
		line = line.strip()
		if line.startswith("Name="):
			id = line[5:]
		elif id != "" and line.startswith("Name[%s" % lang):
			if not id in erg:
				erg[id] = {}
			erg[id][lang] = line[9:]

for id in erg:	
	if "de" in erg[id] and len(erg[id]["de"]) > 0:
		if erg[id] != len(erg[id]["de"]):
			print "msgid \"%s\"" % id
			print "msgstr \"%s\"" % erg[id]["de"]


