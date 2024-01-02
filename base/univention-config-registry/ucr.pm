#!/usr/bin/perl
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2020-2024 Univention GmbH
use warnings;
use strict;
use Debian::Debhelper::Dh_Lib;

insert_before("dh_auto_install", "univention-install-config-registry");

1;
