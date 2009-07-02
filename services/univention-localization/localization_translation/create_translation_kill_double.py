#!/usr/bin/python

msg = ""
id = ""
res = {}

import sys

for line in open(sys.argv[1]).readlines():
	if line.startswith("msgid"):
		id = line.strip()
		if not id in res:
			res[id] = []		
	elif line.startswith("msgstr") and id!= "":
		msg = line.strip()
		if not id in res:
			print "UNKNOWN"
			res[id] = []
		res[id].append(msg)
for id in res:
	print id
	print res[id][0]
	#if len(res[id]) != 1:
#i		print "DOUBLE: %s = %s" % (id, res[id])
