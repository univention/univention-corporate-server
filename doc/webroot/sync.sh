#!/bin/sh 

if [ "$1" = "-h" -o "$1" = "--help" ] ; then
	echo "syntax: $(basename "$0") [<prefix>]"
	echo
	echo "Sync local manual/docs to docs mirror. If <prefix> is given, only pdf/html files"
	echo "with given prefix will be copied. Otherwise all files will be copied to omar."
	echo "In any case, the script does a dry-run first"
	exit 0
fi

do_sync () {
	local PREFIX="$1"
	shift
	if [ -z "$PREFIX" ] ; then
		rsync -avc "$@" --exclude '*.svn' \
			illustrations \
			images \
			css \
			js \
			img \
			de \
			en \
			*.html \
			*.pdf \
			*.css \
			omar:/mnt/omar/vmwares/mirror/ftp/download/docs/
	else
		rsync -avc "$@" --exclude '*.svn' \
			"${PREFIX}"*".html" \
			"${PREFIX}"*".pdf" \
			omar:/mnt/omar/vmwares/mirror/ftp/download/docs/
	fi
}

do_sync "$1" --dry-run

echo
while echo -n "Perform sync to omar? [yn] " && read answer
do
	case "$answer" in
	[yY]) do_sync "$1" ; exit $? ;;
	[nN]) exit 0 ;;
	esac
done
