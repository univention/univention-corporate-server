#!/bin/bash

HORDE_LOG="/var/log/horde/horde3.log"

SUIDS=`grep "add: " $HORDE_LOG | sed -e 's/.*add: \([^ ]*\) \[pid.*/\1/'`

for SUID in $SUIDS
do 
	MAP=`grep "created Map for cuid.* suid=$SUID" $HORDE_LOG`
	if [ -z "$MAP" ]; then 
		echo "Mapping failed for server UID: $SUID"
	fi
done
