#!/bin/sh
#
RETVAL=0

if [ "$1" = "--update" ] ; then
	update="1"
fi

TMPFN=$(mktemp)

for dir in testframework/* ; do
  if [ -d "$dir" ] ; then
	  echo "---------------------------------------------------------------"
	  echo "Testing $dir"
	  echo "---------------------------------------------------------------"

	  DIRNAME=$(basename $dir)
	  MODULE="${DIRNAME:0:4}"

	  ./ucslint.py -p "ucslint" -m $MODULE "${dir}" > $TMPFN
	  ./ucslint-sort-output.py $TMPFN > ${dir}.test

	  diff "${dir}.correct" "${dir}.test" > /dev/null
	  RET="$?"
	  echo -n "Testresult: "
	  if [ ! "$RET" = "0" ] ; then
          RETVAL=1
		  echo "FAILED"
	  else
		  echo "OK"
      fi

	  if [ -n "$update" ] ; then
		  echo "USING TESTRESULT AS NEW TEST TEMPLATE"
		  cp "${dir}.test" "${dir}.correct"
	  fi

	  echo
  fi
done

exit $RETVAL
