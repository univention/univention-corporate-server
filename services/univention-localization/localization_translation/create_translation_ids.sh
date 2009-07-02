#!/bin/sh
echo "#!/usr/bin/python2.4"
echo "# -*- coding: utf8 -*-"

TZDATA_DIR="/usr/share/zoneinfo"

#echo "zone_tab = {"
#while read LINE; do
#	comment="$(echo "$LINE" | sed 's/^#.*//g')"
#	if [ -n "$comment" ] ; then
#		country_code="$(echo "$LINE" | cut -f1)"
##		location="$(echo "$LINE" | cut -f2)"
#		name="$(echo "$LINE" | cut -f3)"
##
##		cont="$(echo "$name" | sed 's|/.*||g')"
##		city="$(echo "$name" | sed 's|^.*/||g')"
#		echo "\"$country_code\" : [ \"$name\" ],"
#	fi
#done < "${TZDATA_DIR}/zone.tab"
#echo "}"
#echo ""

echo '
zone_tab = {}

for line in open("/usr/share/zoneinfo/zone.tab").readlines():
        line = line.strip()
        if not line.startswith("#") and len(line) > 0:
                items = line.split("\t")
                if len(items) > 2:
                        id = items[0].strip()
                        name = items[2].strip()
                        if not id in zone_tab:
                                zone_tab[id] = [name]
                        else:
                                zone_tab[id].append(name)
                        zone_tab[id].sort()
print "zone_tab = %s" % zone_tab
' | /usr/bin/python2.4


echo "country_tab = {"
while read LINE; do
	comment="$(echo "$LINE" | sed 's/^#.*//g')"
	if [ -n "$comment" ] ; then
		country_code="$(echo "$LINE" | cut -f1)"
		name="$(echo "$LINE" | cut -f2)"

		echo "\"$country_code\" : \"$name\","
	fi
done < "${TZDATA_DIR}/iso3166.tab"
echo "}"

echo ""

#echo '
#language_code = ""
#language_names = {}
#lines = open("/usr/share/locale/all_languages").readlines()
#
## get all language names in english to use them as ids
#
#print "language_code_to_name = {",
#for line in lines:
#	if line.startswith("["):
#		language_code = line.replace("[","").replace("]","").strip()
#	elif line.startswith("Name="):
#		print "\"%s\" : \"%s\"," % (language_code, line[5:].strip()),
#print "}",' | /usr/bin/python2.4

echo '
language_code = ""
language_names = {}
lines = open("/usr/share/locale/all_languages").readlines()

# get all language names in english to use them as ids

added = False
print "language_code_to_name = {",
for line in lines:
        if line.startswith("["):
                language_code = line.replace("[","").replace("]","").strip()
                if added:
                        print "},"
                added = False
        elif line.startswith("Name="):
                print "\"%s\" : { \"default\" : \"%s\", " % (language_code, line.split("=")[1].strip())
        elif line.startswith("Name["):
                        lcode = ""
                        if "[" in line:
                                lcode=line.split("[")
                                if len(lcode)>0:
                                        lcode=lcode[1]
                                else:
                                        lcode = ""
                        else:
                                lcode = ""
                        if "]" in lcode:
                                lcode = lcode.split("]")[0].strip()
                        else:
                                lcode = ""
                        if lcode != "" and "=" in line:
                                print "\"%s\" : \"%s\"," % (lcode, line.split("=")[1].replace("\"","\\\"").strip())
                                added = True
if added:
        print "},"
print "}",' | /usr/bin/python2.4
