#!/bin/sh
# Copyright 2021-2022 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

set -e

SRC_FOLDER="$(dirname "$0")"/src
echo looking in $SRC_FOLDER for .vue files
rm -r $SRC_FOLDER/tmp/ || true
mkdir $SRC_FOLDER/tmp/
for f in $(ls $SRC_FOLDER/views/*.vue $SRC_FOLDER/views/*/*.vue $SRC_FOLDER/components/*.vue $SRC_FOLDER/components/*/*.vue); do
	mkdir -p "$SRC_FOLDER/tmp/ts/$(dirname "$f")"
	sed -n '/^<script/,/^<\/script/p' "$f" | sed '1d;$ d' > "$SRC_FOLDER/tmp/ts/$f"
	#mkdir -p "$SRC_FOLDER/tmp/html/$(dirname "$f")"
	#sed -n '/^<template/,/^<\/template/p' "$f" | sed '1d;$ d' | sed -e '/^\s*</d;/^\s*\//d' > "$SRC_FOLDER/tmp/html/$f"
done
