#!/bin/bash
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2022 Univention GmbH <https://www.univention.de/>
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

function debug_info ()
{
    IFS='.,' read ESEC NSEC <<<"$EPOCHREALTIME"
    printf "[%(%F %T)T.%06.0f]  DEBUG at %s:%s:%s: %s\n" "$ESEC" "$NSEC" "${BASH_SOURCE[1]}" "${BASH_LINENO[0]}" "${FUNCNAME[1]}" "$BASH_COMMAND" >&4
}


PAUSE_DEBUG ()
{
    set +o functrace
    trap - DEBUG
    IFS='.,' read ESEC NSEC <<<"$EPOCHREALTIME"
    printf "[%(%F %T)T.%06.0f]  PAUSE DEBUG\n" "$ESEC" "$NSEC" >&4
}

RESUME_DEBUG ()
{
    IFS='.,' read ESEC NSEC <<<"$EPOCHREALTIME"
    printf "[%(%F %T)T.%06.0f]  RESUME DEBUG\n" "$ESEC" "$NSEC" >&4
    set -o functrace
    trap "debug_info" DEBUG
}


set -o functrace
trap "debug_info" DEBUG