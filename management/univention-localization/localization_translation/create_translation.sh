#!/bin/sh
cd $1

echo "Tested with: tzdata_2008h, kdekdebase-3.5.9 and  kdelibs-3.5.10"
echo "WARNING - you should! verify that the po and py files are correct"
echo "WARNING - check (e.g. with 'file') that the .po files are utf-8 encoded"

#create temp dir
TMP_DIR="$(mktemp -d)"

if [ -z "$TMP_DIR" ] ; then
	echo "ERROR not tempdir"
	exit 1
fi


#get tzdata-source
mkdir "$TMP_DIR/tzdata"
TZDATA_DIR="$TMP_DIR/tzdata"
OLD_DIR=$PWD
cp "tzdata_2008h-2.5.200904110104.tar.gz" "$TZDATA_DIR/"
cd $TZDATA_DIR
tar xfz "tzdata_2008h-2.5.200904110104.tar.gz" 
cd $OLD_DIR

TZDATA_DIR="$TZDATA_DIR/tzdata-2008h"

MODULE_DIR="../modules/univention/management/console/wizards/localization/"

for l in "de" "en"; do
	./create_translation_language.py $l >  ${TMP_DIR}/${l}_test.po
	./create_translation_country.py $l >>  ${TMP_DIR}/${l}_test.po
	./create_translation_timezone.py $TZDATA_DIR $l >>  ${TMP_DIR}/${l}_test.po	
	./static_translation.py ${l} >> ${TMP_DIR}/${l}_test.po

	#########
	{
	echo "# SOME DESCRIPTIVE TITLE."
	echo "# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER"
	echo "# This file is distributed under the same license as the PACKAGE package."
	echo "# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR."
	echo "#"
	echo "msgid \"\""
	echo "msgstr \"\""
	#echo "\"Content-Type: text/plain; charset=ISO-8859-1\\n\""
	#echo "\"Content-Transfer-Encoding: 8-bit\\n\""
	echo "\"Content-Type: text/plain; charset=UTF-8\\n\""
	echo "\"Content-Transfer-Encoding: unicode\\n\""
	echo ""
	} > ${TMP_DIR}/$l.po


	./create_translation_kill_double.py ${TMP_DIR}/${l}_test.po >> ${TMP_DIR}/$l.po
	#msgfmt ${TMP_DIR}/${l}.po -o ${TMP_DIR}/${l}.mo

	mv ${TMP_DIR}/$l.po "$MODULE_DIR"
	#mv ${TMP_DIR}/$l.mo "$MODULE_DIR"
done

./create_translation_ids.sh > ${TMP_DIR}/translation.py
mv ${TMP_DIR}/translation.py "$MODULE_DIR"

rm -r "$TMP_DIR"
