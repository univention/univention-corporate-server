#!/bin/bash
#
# Run test suite for ucslint
#
declare -i RETVAL=0

usage () { # Printusage
    cat <<__USAGE__
${0##*/}"
Options:
  --update   Save current result as expected result
  --verbose  Show diff of failed tests
  --clean    Remove current result after run
  --quiet    Hide verbose output
  --color    Colorize output
  --         Separate options from following arguments
__USAGE__
    exit ${1:-0}
}

while [ $# -ge 1 ]
do
    case "$1" in
    --update) update=1 ;;
    --verbose) verbose=1 ;;
    --clean) clean=1 ;;
    --quiet) quiet=1 ;;
    --color) red=$(tput setaf 1) green=$(tput setaf 2) norm=$(tput op) ;;
    --help) usage 0 ;;
    --) shift ; break ;;
    -*) echo "Unknown option $1; See ${0##*/} --help" >&2 ; exit 2 ;;
    *) break ;;
    esac
    shift
done

tmpdir=$(mktemp -d)
trap "rm -rf '$tmpdir'" EXIT
tmpresult="$tmpdir/result"
tmpdiff="$tmpdir/diff"
tmperr="$tmpdir/err"

export PYTHONPATH="$PWD:$PYTHONPATH"
BINPATH="$PWD/bin/ucslint"
UCSLINTPATH=(
	-p "$PWD/ucslint"
	-p "$PWD/ucslint-univention"
	)

for dir in testframework/$@*
do
    if [ -d "$dir" ]
    then
        [ -z "$quiet" ] && echo -n "Testing $dir "

        DIRNAME=$(basename "$dir")
        MODULE="${DIRNAME:0:4}"

        ( cd "$dir" && "$BINPATH" "${UCSLINTPATH[@]}" -m "$MODULE" >"$tmpresult" 2>"$tmperr" )
        ret=$?
        ./ucslint-sort-output.py "$tmpresult" >"${dir}.test"

        if diff -u "${dir}.correct" "${dir}.test" >"$tmpdiff" 2>&1 && [ 1 -ne "$ret" ]
        then
            [ -z "$quiet" ] && echo "${green}OK${norm}"
            [ -n "$clean" ] && rm -f "${dir}.test"
        else
            [ -z "$quiet" ] && echo "${red}FAILED${norm}"
            [ 2 -ne "$ret" ] && cat "$tmperr"
            RETVAL+=1
            [ -n "$verbose" ] && sed "s/^+/${red}&/;s/^-/${green}&/;s/$/${norm}/" "$tmpdiff"

            if [ -n "$update" ]
            then
                echo "USING TESTRESULT AS NEW TEST TEMPLATE"
                cp "${dir}.test" "${dir}.correct"
            fi
        fi
    fi
done

exit $RETVAL
