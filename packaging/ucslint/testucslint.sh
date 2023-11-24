#!/bin/bash
#
# Run test suite for ucslint
#
declare -i RETVAL=0

die () { # Print error and exit
  echo "$*" >&2
  exit 1
}
usage () { # Print usage
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
    exit "${1:-0}"
}

TEMP=$(getopt -o 'vqch' --long 'update,verbose,clean,quiet,color,help' -n "$0" -- "$@") ||
    usage 2 >&2
eval set -- "$TEMP"
while [ $# -ge 1 ]
do
    case "$1" in
    --update) update=1 ;;
    --verbose|-v) verbose=1 ;;
    --clean) clean=1 ;;
    --quiet|-q) quiet=1 ;;
    --color|-c) red=$(tput setaf 1) green=$(tput setaf 2) norm=$(tput op) ;;
    --help|-h) usage 0 ;;
    --) shift ; break ;;
    *) die "Internel error" ;;
    esac
    shift
done

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
tmpresult="$tmpdir/result"
tmpdiff="$tmpdir/diff"
tmperr="$tmpdir/err"

BINPATH="$PWD/ucslint"

match () {
    local arg name="$1"
    shift
    [ $# -eq 0 ] && return 0
    for arg in "${@#testframework/}"
    do
        [ "$arg" = "$name" ] && return 0
    done
    return 1
}

for dir in testframework/*
do
    [ -d "$dir" ] || continue
    NAME=$(basename "$dir")
    match "$NAME" "${@%/}" || continue

        [ -z "$quiet" ] && echo -n "Testing $dir "

        MODULE="${NAME:0:4}"

        ( cd "./$dir" && "$BINPATH" -m "$MODULE" >"$tmpresult" 2>"$tmperr" )
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
done

exit "$RETVAL"
