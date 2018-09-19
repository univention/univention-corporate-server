#!/bin/sh
set -e -u

eval "$(sed -rne 's,^deb\s+(\[[^]]*\]\s+)?(.+/)([0-9]+)\.([0-9]+)/maintained/\3\.\4-([0-9]+)\s+ucs[0-9]+\s+main,url=\2 major=\3 minor=\4 patch=\5,p' /etc/apt/sources.list)"
(
    seq -f "$major.$minor-%.0f" $patch -1 1
    seq -f "$major.%.0f-0" $minor -1 0
) |
while read -r rel
do
    echo "deb-src [trusted=yes] ${url}${rel%-*}/unmaintained ${rel}/source/"
done |
    tee /etc/apt/sources.list.d/unmaintained.list
apt-get -qq update
