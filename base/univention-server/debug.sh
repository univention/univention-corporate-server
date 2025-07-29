#!/bin/bash
#
# SPDX-FileCopyrightText: 2022-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

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