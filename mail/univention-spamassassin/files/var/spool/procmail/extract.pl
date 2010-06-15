#!/usr/bin/perl
#
# Univention Spamassassin
#  extract attachment from mail
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

my $hdrs = '';
while (<STDIN>) {
	/^$/ and last;
	$hdrs .= $_;
}
$hdrs =~ s/\n[ \t]+/ /gs;

if ($hdrs !~ /^Content-Type: multipart\/mixed\;\s+boundary=\"(\S+)\"$/m) {
	exit 1;
}

my $tophdrs = $hdrs;
my $bound = $1;

while (1) {
	while (<STDIN>) {
		/^\Q--${bound}\E$/ and last;
	}
	exit 1 if eof(STDIN);

	my $hdrs = '';
	while (<STDIN>) {
		/^$/ and last;
		$hdrs .= $_;
	}
	$hdrs =~ s/\n[ \t]+/ /gs;

	if ($hdrs !~ /^Content-Type: message\/rfc822(?:\;|$)/m) {
		next;
	}

	##warn "found message/rfc822 part: $hdrs\n";
	while (<STDIN>) {
		/^\Q--${bound}--\E$/ and exit 0;
		/^\Q--${bound}\E$/ and last;
		print;
	}
	exit 0;
}

exit 1;

