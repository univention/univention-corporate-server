#!/bin/bash
#
# holdingproper.sh 
# suche holdingsdumps aus history.txt, prüfe, ob Datei noch 
# vorhanden ist und entferne den Eintrag aus der history.txt, wenn Datei nicht mehr vorhanden.
# 
# es wäre schön, wenn diese Funktion unter Perl in das Script "uniflush" integriert werden 
# könnte und mit dem Parameter "uniflush -clean" aufgerufen werden kann.
#
#
#set -x


MYDIR="/var/lib/unidump";
MYHIST="history.txt";
TMPFILE="history.tmp";

echo 
echo $0 | sed "s@.*/@@";
echo
echo "Comparing $MYDIR/$MYHIST to $MYDIR/hd";
echo

for datei in `cat $MYDIR/$MYHIST|grep "$MYDIR/hd"|cut -f6 -d\ `; do
     echo -n "looking for $datei...";
     test -e $datei && { 
        echo "OK.";
        continue;
    } || {
        echo -n "not on holdingdisk - removing entry from $MYHIST...";
        cat $MYDIR/$MYHIST | grep -v $datei > $MYDIR/$TMPFILE;
        cp $MYDIR/$TMPFILE $MYDIR/$MYHIST;
        rm $MYDIR/$TMPFILE;
        echo "OK."
    }
done;
echo
echo "done.";



