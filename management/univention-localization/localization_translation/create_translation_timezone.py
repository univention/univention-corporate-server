#!/usr/bin/python2.4
# -*- coding: utf-8 -*-


import sys
import os
tzdata_dir=sys.argv[1].strip()

po_files = []
for item in os.listdir("%s/debian/po/" % tzdata_dir):
	item = item.strip()
	if len(item) == 5 and item[2:5] == ".po":
		po_files.append(item)

id=""
msg=""

l = sys.argv[2]

for po_file in po_files:
	if po_file == "%s.po" % l: 
		for line in open("%s/debian/po/%s" % (tzdata_dir, po_file)).readlines():
			line = str(line)
			if line.startswith("msgid "):
				id=line.strip()
			elif line.startswith("msgstr "):
				msg=line.strip()
			else:
				msg=""
			if len(msg) > 0 and len(id)>0 and msg!=id and msg[-2:] != "\"\"" and id[-2:] != "\"\"":
				try:
					a = unicode(id,"latin-1")
				except:
					a = id
					
				try:
					b = unicode(msg,"latin-1")
				except:
					b = msg

				print a
				print b
