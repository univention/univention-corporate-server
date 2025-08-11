#!/bin/sh
# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

THEME_DIR="/usr/share/univention-web/themes"
THEME_SRC="$THEME_DIR/$(basename "$(ucr get ucs/web/theme)").css"
THEME_DST="/var/www/univention/theme.css"

if [ ! -e "$THEME_SRC" ]; then
	echo "$THEME_SRC does not exist"
	exit 1
fi

[ -L "$THEME_DST" ] && rm "$THEME_DST"
ln -s "$THEME_SRC" "$THEME_DST"
