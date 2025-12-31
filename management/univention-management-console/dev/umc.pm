#!/usr/bin/perl
#
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
use warnings;
use strict;
use Debian::Debhelper::Dh_Lib;

insert_before("dh_auto_build", "dh-umc-module-build");
remove_command("dh-univention-join-install");
insert_before("dh_auto_install", "dh-univention-join-install");
insert_before("dh_auto_install", "dh-umc-module-install");

1;
