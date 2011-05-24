#!/bin/sh

if [ $# -lt 1 ]; then
	echo usage: module ...
fi

for size in 64 32 24 16; do
	for i in "$@"; do
		cat << EOF
.icon$size-$i {
	background-image: url( '../images/icons/${size}x${size}/$i.png' );
}

EOF
	done
done
