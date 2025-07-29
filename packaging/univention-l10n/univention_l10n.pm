#!/usr/bin/perl
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
use warnings;
use strict;
use Debian::Debhelper::Dh_Lib;

insert_before("dh_auto_build", "univention-l10n-build");
insert_before("dh_auto_install", "univention-l10n-install");
add_command_options("dh_install", "-Xde.po");

1;
