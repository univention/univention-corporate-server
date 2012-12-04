#!/bin/bash

PATH_TO_COMPARE_LDIF='../compareldif'

PATH_TO_COMPARE_LDIF=$(readlink -m "$PATH_TO_COMPARE_LDIF")
for directory in */
do
   echo "$directory"
    cd "$directory" 
    if cmp --quiet <("$PATH_TO_COMPARE_LDIF" InputA.ldif InputB.ldif) Output
    then
       echo "OK"
    else
	echo "FAIL"
    fi
   cd ..
done
