#!/bin/sed -f
# SPDX-FileCopyrightText: 2014-2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
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
