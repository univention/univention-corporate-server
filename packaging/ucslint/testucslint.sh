#!/bin/bash
#
declare -i RETVAL=0

if [ "$1" = "--update" ] ; then
	update="1"
fi

TMPFN=$(mktemp)
trap "rm -f '$TMPFN'" EXIT

export PYTHONPATH="$(pwd):$PYTHONPATH"
UCSLINTPATH="$(pwd)/ucslint"

for dir in testframework/* ; do
  if [ -d "$dir" ] ; then
	  echo -n "Testing $dir "

	  DIRNAME=$(basename "$dir")
	  MODULE="${DIRNAME:0:4}"

	  ( cd "$dir" ; ../../bin/ucslint -p "$UCSLINTPATH" -m "$MODULE" >"$TMPFN" 2>/dev/null)
	  ./ucslint-sort-output.py "$TMPFN" >"${dir}.test"

	  if diff "${dir}.correct" "${dir}.test" >/dev/null 2>&1
	  then
		  echo "OK"
	  else
		  echo "FAILED"
		  RETVAL+=1
      fi

	  if [ -n "$update" ] ; then
		  echo "USING TESTRESULT AS NEW TEST TEMPLATE"
		  cp "${dir}.test" "${dir}.correct"
	  fi
  fi
done

exit $RETVAL
