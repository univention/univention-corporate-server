#!/bin/bash
#
# Run test suite for ucslint
#
set -e -u -o pipefail

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
update=false verbose=false clean=false quiet=false red='' green='' norm=''
while [ $# -ge 1 ]
do
    case "$1" in
    --update) update=true ;;
    --verbose|-v) verbose=true ;;
    --clean) clean=true ;;
    --quiet|-q) quiet=true ;;
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

BINPATH="$PWD/univention/ucslint/main.py"

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

test_cd () {
    ( cd "./$dir" && "$BINPATH" -m "$MODULE" )
}

test_arg () {
    "$BINPATH" -m "$MODULE" "$dir" | sed -e "s|${dir%/}/||g"
    return "${PIPESTATUS[0]}"
}

for dir in testframework/*
do
    [ -d "$dir" ] || continue
    NAME=$(basename "$dir")
    match "$NAME" "${@%/}" || continue

    "$quiet" || echo -n "Testing $dir "

    MODULE="${NAME:0:4}"

    for run_test in test_cd test_arg
    do
        ret=0
        "$run_test" >"$tmpresult" 2>"$tmperr" || ret=$?
        ./ucslint-sort-output.py "$tmpresult" >"${dir}.test"

        if diff -u "${dir}.correct" "${dir}.test" >"$tmpdiff" 2>&1 && [ 1 -ne "$ret" ]
        then
            "$quiet" || echo -n "${green}OK${norm}[${run_test#test_}]"
            "$clean" && rm -f "${dir}.test"
        else
            "$quiet" || echo "${red:-}FAILED${norm}[${run_test#test_}]"
            [ 2 -ne "$ret" ] && cat "$tmperr"
            RETVAL+=1
            "$verbose" && sed "s/^+/${red}&/;s/^-/${green}&/;s/$/${norm}/" "$tmpdiff"

            if "$update"
            then
                echo "USING TESTRESULT AS NEW TEST TEMPLATE"
                cp "${dir}.test" "${dir}.correct"
            fi
        fi
    done
    echo
done

exit "$RETVAL"
