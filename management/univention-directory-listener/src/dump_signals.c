/*
 * Univention Directory Listener
 *  dump_signals.c
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
#include <signal.h>
#include <sys/types.h>
#include <wait.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

void signals_block(void) {
}

void signals_unblock(void) {
}

void exit_handler(int sig) {
	exit(0);
}

void reload_handler(int sig) {
}

void signals_init(void) {
}
