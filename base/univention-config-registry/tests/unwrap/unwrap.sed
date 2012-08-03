#!/bin/sed -f
1{
	h # hold := pattern
	$n # print and next/quit
	d
}
/^[ \t]/{
	H # hold += "\n" + pattern
	g # pattern := hold
	s/\n[ \t]//
	$n # print and next/quit
	h # hold := pattern
	d
}
x # hold <=> pattern
${
	p # print pattern
	x # hold <=> pattern
}
