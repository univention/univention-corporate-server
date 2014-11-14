#!/bin/bash

#schleife: 
# for i in *.png; do ~/image-shadow.sh $i; done
in=$1
out=$2
if [[ $out == "" ]] ; then
	out=${in%.*}-shadow.${in##*.}
fi
echo "Converting file : $in -> $in with shadow"
convert $in \( +clone -background black -shadow 40x5+0+0 \) +swap -background transparent -layers merge +repage $in
