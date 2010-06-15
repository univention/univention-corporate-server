#!/bin/sh
#
# Script to compare revisions and ignore files that should be different, and
# differences in revision numbers.
# Syntax: ./compare_revisions.sh FIRST_FOLDER SECOND_FOLDER ['ADDITIONAL PARAMETERS']

diff -r -I "\$Horde" -I "\$Revision" -I "\$Date" --exclude version.php --exclude CHANGES --exclude CREDITS --exclude '*.po' --exclude '*.pot' --exclude locale --exclude CVS --exclude '.#*' --exclude '*~' --exclude '*.bak' $3 $4 $5 $6 $7 $8 $9 $1 $2 | grep -v "config/.*\.php "
