#! /usr/bin/perl -w
#
# Copyright 2004-2014 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.
#
# console-data: /usr/share/console/lists/keymaps/console-data.keymaps
# is part of the package console-data, we use it to generate a list
# of default kmaps for a given country (or all kmaps for a given country)

use strict;
use vars qw($keymaps);
use Data::Dumper;

$keymaps = {};
require "/usr/share/console/lists/keymaps/console-data.keymaps";

my $mapdir = "/usr/share/keymaps/i386";
my %standKeymaps = ();
my %allKeymaps = ();
my $all = 0;

if (scalar(@ARGV) > 0 and ($ARGV[0] eq "--all" or $ARGV[0] eq "-a")) {
	$all = 1
}

sub isMapFile {

	my $map = $_[0];
	my $family = $_[1];

	my $mapFile = $mapdir."/".$family."/".$map.".kmap.gz";
	if (-e $mapFile) {
		return $map;
	}
	else {
		return 0;
	}
}

foreach my $family (keys %{$keymaps->{"pc"}}) {
    next if $family eq 'default';
	my $familymaps = $keymaps->{"pc"}->{$family};
	foreach my $language (keys %$familymaps) {
		next if $language eq 'default';
		my $layoutmaps = $familymaps->{$language};
		my $mapFile;

		foreach my $kbdvariant (keys %$layoutmaps) {

			# get standard keymaps

			# test if default exists and is a keymap
			if (exists $layoutmaps->{"default"}) {
				$mapFile = isMapFile($layoutmaps->{"default"}, $family);

				# test if default value exists as key an its value is a keymap
				my $key = $layoutmaps->{"default"};
				if (exists $layoutmaps->{$key}) {
					if (exists $layoutmaps->{$key}->{"Standard"}) {
						$mapFile = isMapFile($layoutmaps->{$key}->{"Standard"}, $family);
					}
				}
			}

			# test if Standard -> Standard exists and is a keymap
			# test if Standard -> default exists and is a keymap
			if (exists $layoutmaps->{"Standard"}) {
				my $key;
				if (exists $layoutmaps->{"Standard"}->{"Standard"}) {
					$key = "Standard";
				}
				if (exists $layoutmaps->{"Standard"}->{"default"}) {
					$key = "default";
				}
				if ($key) {
					$mapFile = isMapFile($layoutmaps->{"Standard"}->{$key}, $family);
					my $value = $layoutmaps->{"Standard"}->{$key};

					# test if Standard -> default is a key in Standard and a keymap
					if (exists $layoutmaps->{"Standard"}->{$value}) {
						$mapFile = isMapFile($layoutmaps->{"Standard"}->{$value}, $family);
					}
				}
			}

			# get all keymaps

			my $variants = $layoutmaps->{$kbdvariant};
			if (ref($variants)) {
				foreach my $variantmaps (keys %$variants) {
					next if $variantmaps eq 'default';
					my $mapvariant = $variants->{$variantmaps};
					if (not ref($mapvariant)) {
						my $mf = isMapFile($mapvariant, $family);
						if ($mf) {
							$allKeymaps{"$language ($variantmaps $kbdvariant $family)"} = $mapvariant;
						}
					}
				}
			}
		}
		if ($mapFile) {
			$standKeymaps{"$language ($family)"} = $mapFile;
		}
	}
}

if ($all) {
	# print all kmaps
	foreach my $lang (sort keys %allKeymaps) {
		my $key = $lang;
		$lang =~ s/Standard Standard/Standard/;
		print $lang.":".$allKeymaps{$key}."\n"
	}
}
else {
	# print default kmap
	foreach my $lang (sort keys %standKeymaps) {
		print $lang." ".$standKeymaps{$lang}."\n"
	}
}

