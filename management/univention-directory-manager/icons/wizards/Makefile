#!/usr/bin/make -f
all: wizards_about.png wizards_network.png

about_small.png: about.png
	convert -resize 12x12 $^ $@

network_small.png: network.png
	convert -resize 12x12 $^ $@

wizards_about.png: about_small.png test.png
	composite -compose src-over -gravity Center $^ $@

wizards_network.png: network_small.png test.png
	composite -compose src-over -gravity Center $^ $@

test.png: group.png policy.png computer.png print.png
	montage $^ -gravity Center -mode Concatenate  -tile 2x2 -background none -geometry +0+0 -size 64x64 tmp_$@
	convert -resize 32x32 tmp_$@ $@


clean:
	@rm -f wizards_about.png wizards_network.png test.png tmp_test.png *_small.png
